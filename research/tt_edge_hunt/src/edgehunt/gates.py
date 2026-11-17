"""Pre-registered fundamental gates (docs/preregistration.md §7).

Each gate returns three DataFrames on a (date x token) grid:
long_ok, short_ok, defined. Row t may only use fundamentals dated <= t-lag and
prices dated <= t-1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from edgehunt.config import MR_SETS
from edgehunt.config import SECTORS
from edgehunt.config import TOKENS
from edgehunt.config import TREND_SETS
from edgehunt.data import daily_close
from edgehunt.data import rolling_mean


DAYS = pd.date_range("2022-06-01", "2026-11-15", freq="D")

IDEAS = {
    "I1": {"name": "REVMOM", "exec": TREND_SETS,
           "gdefs": [("fees", 7, 30), ("fees", 14, 60), ("revenue", 7, 30), ("revenue", 14, 60)],
           "thr": [1.00, 1.05, 1.10, 1.20, 1.35]},
    "I2": {"name": "DIVERGE", "exec": MR_SETS,
           "gdefs": [("user_dau", 7), ("user_dau", 14), ("fees", 7), ("fees", 14)],
           "thr": [(0.0, 0.0), (0.05, 0.03), (0.10, 0.05), (0.15, 0.08), (0.25, 0.12)]},
    "I3": {"name": "TVLFLOW", "exec": TREND_SETS,
           "gdefs": [("own", 7), ("own", 30), ("agg", 7), ("agg", 30)],
           "thr": [0.0, 0.02, 0.05, 0.10, 0.15]},
    "I4": {"name": "UNLOCK", "exec": TREND_SETS,
           "gdefs": [("suppress", 7), ("suppress", 30), ("flip", 7), ("flip", 30)],
           "thr": {"suppress": [0.05, 0.03, 0.02, 0.01, 0.005], "flip": [0.005, 0.01, 0.02, 0.03, 0.05]}},
    "I5": {"name": "ROTATE", "exec": TREND_SETS,
           "gdefs": ["fees", "revenue", "user_dau", "composite"],
           "thr": [5, 4, 3, 2, 1]},
    "I6": {"name": "VALUE", "exec": TREND_SETS,
           "gdefs": [("fees", 30), ("fees", 90), ("revenue", 30), ("revenue", 90)],
           "thr": [0.50, 0.40, 0.30, 0.20, 0.10]},
    "I7": {"name": "SHOCK", "exec": TREND_SETS,
           "gdefs": [("fees", 1), ("fees", 3), ("user_dau", 1), ("user_dau", 3)],
           "thr": [1.25, 1.5, 2.0, 2.5, 3.0]},
}


@dataclass(frozen=True)
class Variation:
    idea: str
    g: int
    k: int
    exec_set: str

    @property
    def vid(self) -> str:
        return f"{self.idea}-g{self.g}-k{self.k}-{self.exec_set}"


def all_variations() -> list[Variation]:
    out = []
    for idea, spec in IDEAS.items():
        for g in range(4):
            for k in range(5):
                for e in spec["exec"]:
                    out.append(Variation(idea, g, k, e))
    return out


class GateBuilder:
    def __init__(self, fundamentals: dict[str, pd.DataFrame], lag: int = 1):
        self.lag = lag
        self.F = {m: f.reindex(index=DAYS, columns=TOKENS) for m, f in fundamentals.items()}
        self.Fl = {m: f.shift(lag) for m, f in self.F.items()}
        dc = pd.DataFrame({t: daily_close(t) for t in TOKENS}).reindex(DAYS)
        self.dcl = dc.shift(1)  # close of t-1 at row t
        self._cache: dict = {}

    def _f(self, m: str) -> pd.DataFrame:
        if m not in self.Fl:
            return pd.DataFrame(np.nan, index=DAYS, columns=TOKENS)
        return self.Fl[m]

    def _ratio(self, m: str, s: int, l: int) -> pd.DataFrame:
        key = ("ratio", m, s, l)
        if key not in self._cache:
            x = self._f(m)
            a, b = rolling_mean(x, s), rolling_mean(x, l)
            r = a / b
            self._cache[key] = r.where((a > 0) & (b > 0))
        return self._cache[key]

    def _pret(self, n: int) -> pd.DataFrame:
        return np.log(self.dcl / self.dcl.shift(n))

    def gate(self, idea: str, g: int, k: int):
        spec = IDEAS[idea]
        gd = spec["gdefs"][g]
        false = pd.DataFrame(False, index=DAYS, columns=TOKENS)
        if idea == "I1":
            r = self._ratio(*gd)
            kk = spec["thr"][k]
            return r >= kk, r <= 1.0 / kk, r.notna()
        if idea == "I2":
            m, p = gd
            f = np.log(self._ratio(m, 7, 30))
            pr = self._pret(p)
            a, b = spec["thr"][k]
            return (f >= a) & (pr <= -b), (f <= -a) & (pr >= b), f.notna() & pr.notna()
        if idea == "I3":
            kind, L = gd
            tvl = self._f("tvl").where(self._f("tvl") > 0)
            if kind == "own":
                flow = np.log(tvl / tvl.shift(L)) - self._pret(L)
            else:
                prev = tvl.shift(L)
                m = tvl.notna() & prev.notna()
                agg = np.log(tvl.where(m).sum(axis=1, min_count=1) / prev.where(m).sum(axis=1, min_count=1))
                flow = pd.DataFrame(np.repeat(agg.to_numpy()[:, None], len(TOKENS), 1), index=DAYS, columns=TOKENS)
            c = spec["thr"][k]
            return flow >= c, flow <= -c, flow.notna()
        if idea == "I4":
            mode, L = gd
            s = self._f("token_supply_circulating")
            s = s.where(s > 0)
            e = np.log(s / s.shift(L))
            th = spec["thr"][mode][k]
            if mode == "suppress":
                return (e < th) & e.notna(), false, e.notna()
            return false, (e >= th) & e.notna(), e.notna()
        if idea == "I5":
            if gd == "composite":
                ranks = [self._sector_pct(self._ratio(m, 7, 30)) for m in ("fees", "revenue", "user_dau")]
                cnt = sum(r.notna().astype(int) for r in ranks)
                score = (sum(r.fillna(0) for r in ranks) / cnt.replace(0, np.nan)).where(cnt >= 2)
            else:
                score = self._ratio(gd, 7, 30)
            top = spec["thr"][k]
            long_ok, short_ok = false.copy(), false.copy()
            for toks in SECTORS.values():
                sc = score[toks]
                long_ok[toks] = sc.rank(axis=1, ascending=False, method="first") <= top
                short_ok[toks] = sc.rank(axis=1, ascending=True, method="first") <= top
            return long_ok & score.notna(), short_ok & score.notna(), score.notna()
        if idea == "I6":
            m, n = gd
            sup = self._f("token_supply_circulating")
            mcap = self.dcl * sup.where(sup > 0)
            flow = rolling_mean(self._f(m), n)
            val = (mcap / (flow * 365.0)).where(flow > 0)
            rk = val.rank(axis=1, pct=True)
            q = spec["thr"][k]
            return rk <= q, rk >= 1.0 - q, rk.notna()
        if idea == "I7":
            m, D = gd
            x = self._f(m)
            med = x.rolling(30, min_periods=24).median()
            z = (x / med).where(med > 0)
            d = np.sign(self._pret(D))
            kk = spec["thr"][k]
            hit = z >= kk
            return hit & (d > 0), hit & (d < 0), z.notna() & d.notna()
        raise ValueError(idea)

    def _sector_pct(self, score: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(np.nan, index=DAYS, columns=TOKENS)
        for toks in SECTORS.values():
            out[toks] = score[toks].rank(axis=1, pct=True)
        return out
