"""
Build ungated candidate trades for every execution set and every token over the
full sample (trades only from BUILD_START), plus random-entry pools with the
same geometry. Gating happens later; candidates are independent of the gate.

Output: data/cache/cand_{SET}.parquet, data/cache/pool_{SET}.parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edgehunt.config import BUILD_START  # noqa: E402
from edgehunt.config import CACHE  # noqa: E402
from edgehunt.config import EXEC_SETS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.config import cost_per_side  # noqa: E402
from edgehunt.data import atr  # noqa: E402
from edgehunt.data import first_eligible_day  # noqa: E402
from edgehunt.data import load_5m  # noqa: E402
from edgehunt.data import resample  # noqa: E402
from edgehunt.data import rsi  # noqa: E402
from edgehunt.sim import simulate  # noqa: E402


POOL_PER_TOKEN_DIR = 6000
RNG = np.random.default_rng(20261116)


def signals(bars: pd.DataFrame, es) -> tuple[pd.Series, pd.Series]:
    c, h, lo = bars["close"], bars["high"], bars["low"]
    if es.kind == "donchian":
        n = es.param[0]
        return c > h.rolling(n).max().shift(1), c < lo.rolling(n).min().shift(1)
    if es.kind == "ema_cross":
        f = c.ewm(span=es.param[0], adjust=False).mean()
        s = c.ewm(span=es.param[1], adjust=False).mean()
        return (f > s) & (f.shift(1) <= s.shift(1)), (f < s) & (f.shift(1) >= s.shift(1))
    if es.kind == "rsi_cross":
        n, lo_t, hi_t = es.param
        r = rsi(c, n)
        return (r.shift(1) < lo_t) & (r >= lo_t), (r.shift(1) > hi_t) & (r <= hi_t)
    if es.kind == "boll_reentry":
        n, k = es.param
        m = c.rolling(n).mean()
        sd = c.rolling(n).std(ddof=0)
        lower, upper = m - k * sd, m + k * sd
        return ((c.shift(1) < lower.shift(1)) & (c >= lower),
                (c.shift(1) > upper.shift(1)) & (c <= upper))
    raise ValueError(es.kind)


def build_for(es) -> tuple[pd.DataFrame, pd.DataFrame]:
    tf = pd.Timedelta(es.tf)
    max_bars = es.hold_hours * 12
    cands, pools = [], []
    for tok_id, tok in enumerate(TOKENS):
        df5 = load_5m(tok)
        ts5 = df5.index.asi8
        o, h, l, c = (df5[k].to_numpy(np.float64) for k in ("open", "high", "low", "close"))
        bars = resample(df5, es.tf)
        a = atr(bars, 14)
        lng, sht = signals(bars, es)
        elig_from = pd.Timestamp(max(first_eligible_day(tok), BUILD_START.tz_localize(None)), tz="UTC")
        cost = cost_per_side(tok)

        # ---- strategy candidates
        sig = pd.DataFrame({"dir": np.where(lng, 1, np.where(sht, -1, 0)), "atr": a}, index=bars.index)
        sig = sig[(sig["dir"] != 0) & sig["atr"].notna()]
        comp = (sig.index + tf).asi8  # bar completion time = entry time
        ei = np.searchsorted(ts5, comp, side="left")
        ok = (ei < len(ts5))
        ok[ok] &= (ts5[ei[ok]] - comp[ok]) <= pd.Timedelta("1h").value  # skip across data gaps
        ok &= comp >= elig_from.value
        sig, ei = sig[ok], ei[ok]
        d = sig["dir"].to_numpy(np.int8)
        sd = (es.stop_atr * sig["atr"]).to_numpy(np.float64)
        xi, r, why = simulate(o, h, l, c, ei.astype(np.int64), d, sd, es.target_r, max_bars, cost)
        cands.append(pd.DataFrame({
            "tok_id": tok_id, "token": tok, "entry_idx": ei, "exit_idx": xi,
            "entry_ts": pd.to_datetime(ts5[ei], utc=True), "exit_ts": pd.to_datetime(ts5[xi], utc=True),
            "dir": d, "r": r, "reason": why,
        }))

        # ---- random-entry pool: uniform 5m bars, same geometry, ATR of last completed TF bar
        a_comp = pd.Series(a.to_numpy(), index=bars.index + tf)  # value known at completion
        atr5 = a_comp.reindex(df5.index, method="ffill").to_numpy(np.float64)
        lo_i = np.searchsorted(ts5, elig_from.value)
        hi_i = len(ts5) - max_bars
        if hi_i <= lo_i:
            continue
        for dirv in (1, -1):
            pi = RNG.integers(lo_i, hi_i, POOL_PER_TOKEN_DIR)
            pi = pi[np.isfinite(atr5[pi])]
            pd_ = np.full(len(pi), dirv, np.int8)
            psd = es.stop_atr * atr5[pi]
            pxi, pr, _ = simulate(o, h, l, c, pi.astype(np.int64), pd_, psd, es.target_r, max_bars, cost)
            pools.append(pd.DataFrame({
                "tok_id": tok_id, "token": tok, "entry_ts": pd.to_datetime(ts5[pi], utc=True),
                "exit_ts": pd.to_datetime(ts5[pxi], utc=True), "dir": pd_, "r": pr,
            }))
    cand = pd.concat(cands).sort_values(["tok_id", "entry_idx"]).reset_index(drop=True)
    pool = pd.concat(pools).reset_index(drop=True)
    return cand, pool


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or list(EXEC_SETS):
        cand, pool = build_for(EXEC_SETS[name])
        cand.to_parquet(CACHE / f"cand_{name}.parquet", index=False)
        pool.to_parquet(CACHE / f"pool_{name}.parquet", index=False)
        print(f"{name}: {len(cand)} candidates, pool {len(pool)}", flush=True)
