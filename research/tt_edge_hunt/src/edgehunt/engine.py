"""Applies gates to cached candidates, enforces one position per token, and
produces trade lists / daily R series for a period."""

from __future__ import annotations

import numpy as np
import pandas as pd

from edgehunt.config import CACHE
from edgehunt.config import EXEC_SETS
from edgehunt.config import PERIODS
from edgehunt.config import TOKENS
from edgehunt.config import UNIVERSE
from edgehunt.gates import DAYS
from edgehunt.sim import non_overlap


DAY0 = DAYS[0]
NDAYS = len(DAYS)
IN_UNIVERSE = np.array([t in UNIVERSE for t in TOKENS])


def _day_idx(ts: pd.Series) -> np.ndarray:
    return ((ts.dt.tz_localize(None).dt.normalize() - DAY0).dt.days).to_numpy(np.int64)


def period_days(period: str) -> tuple[int, int]:
    a, b = PERIODS[period]
    return (a.tz_localize(None) - DAY0).days, min((b.tz_localize(None) - DAY0).days, NDAYS)


class Engine:
    def __init__(self, sets=None):
        self.c: dict[str, dict] = {}
        self.p: dict[str, dict] = {}
        for e in sets or EXEC_SETS:
            df = pd.read_parquet(CACHE / f"cand_{e}.parquet")
            self.c[e] = {
                "tok": df["tok_id"].to_numpy(np.int64), "day": _day_idx(df["entry_ts"]),
                "xday": _day_idx(df["exit_ts"]), "dir": df["dir"].to_numpy(np.int8),
                "ei": df["entry_idx"].to_numpy(np.int64), "xi": df["exit_idx"].to_numpy(np.int64),
                "r": df["r"].to_numpy(np.float64), "entry_ts": df["entry_ts"].to_numpy(),
            }
            pl = pd.read_parquet(CACHE / f"pool_{e}.parquet")
            self.p[e] = {"tok": pl["tok_id"].to_numpy(np.int64), "day": _day_idx(pl["entry_ts"]),
                         "dir": pl["dir"].to_numpy(np.int8), "r": pl["r"].to_numpy(np.float64)}

    @staticmethod
    def to_np(df: pd.DataFrame) -> np.ndarray:
        return df.reindex(index=DAYS, columns=TOKENS).fillna(False).to_numpy(bool)

    def run(self, e: str, long_ok: np.ndarray, short_ok: np.ndarray, period: str,
            cand_mask: np.ndarray | None = None) -> np.ndarray:
        """Indices (into candidate arrays) of kept trades entered in `period`.
        `cand_mask` (optional, one bool per candidate) removes individual setups."""
        c = self.c[e]
        d0, d1 = period_days(period)
        inp = (c["day"] >= d0) & (c["day"] < d1) & IN_UNIVERSE[c["tok"]]
        day = np.clip(c["day"], 0, NDAYS - 1)
        g = np.where(c["dir"] > 0, long_ok[day, c["tok"]], short_ok[day, c["tok"]]) & inp
        if cand_mask is not None:
            g &= cand_mask
        idx = np.flatnonzero(g)
        keep = non_overlap(c["tok"][idx], c["ei"][idx], c["xi"][idx])
        return idx[keep]

    def daily(self, e: str, idx: np.ndarray, period: str) -> np.ndarray:
        d0, d1 = period_days(period)
        xd = np.clip(self.c[e]["xday"][idx], d0, d1 - 1) - d0
        return np.bincount(xd, weights=self.c[e]["r"][idx], minlength=d1 - d0)

    def random_benchmark(self, e: str, idx: np.ndarray, defined: np.ndarray, period: str,
                         n_draws: int = 1000, seed: int = 11) -> dict:
        """Random entries, same geometry, same long/short counts, eligible token-days."""
        c, p = self.c[e], self.p[e]
        d0, d1 = period_days(period)
        rng = np.random.default_rng(seed)
        inp = (p["day"] >= d0) & (p["day"] < d1) & IN_UNIVERSE[p["tok"]]
        ok = inp & defined[np.clip(p["day"], 0, NDAYS - 1), p["tok"]]
        means = np.zeros(n_draws)
        n_long = int((c["dir"][idx] > 0).sum())
        n_short = len(idx) - n_long
        for side, n in ((1, n_long), (-1, n_short)):
            pool = p["r"][ok & (p["dir"] == side)]
            if n == 0:
                continue
            if len(pool) == 0:
                return {"rand_mean_r": np.nan, "rand_delta": np.nan, "rand_p": np.nan}
            means += rng.choice(pool, size=(n_draws, n), replace=True).sum(axis=1)
        means /= max(len(idx), 1)
        real = c["r"][idx].mean()
        return {"rand_mean_r": float(means.mean()), "rand_delta": float(real - means.mean()),
                "rand_p": float((means >= real).mean())}
