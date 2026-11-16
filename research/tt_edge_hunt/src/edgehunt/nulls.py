"""Monte Carlo nulls for finalists: entry-timing randomisation and gate placebo."""

from __future__ import annotations

import numpy as np
import pandas as pd

from edgehunt.config import EXEC_SETS
from edgehunt.config import TOKENS
from edgehunt.config import cost_per_side
from edgehunt.data import atr
from edgehunt.data import load_5m
from edgehunt.data import resample
from edgehunt.engine import NDAYS
from edgehunt.engine import Engine
from edgehunt.engine import period_days
from edgehunt.sim import simulate


def timing_null(engine: Engine, e: str, idx: np.ndarray, n_draws: int = 1000, seed: int = 3) -> dict:
    """Re-enter each trade at a uniformly random 5m bar of the same token and UTC day,
    same direction and geometry. Returns the real trades' percentile in the null of mean R."""
    es = EXEC_SETS[e]
    tf = pd.Timedelta(es.tf)
    max_bars = es.hold_hours * 12
    rng = np.random.default_rng(seed)
    c = engine.c[e]
    sums = np.zeros(n_draws)
    for tok_id in np.unique(c["tok"][idx]):
        tok = TOKENS[tok_id]
        sel = idx[c["tok"][idx] == tok_id]
        df5 = load_5m(tok)
        ts5 = df5.index.asi8
        o, h, l, cl = (df5[k].to_numpy(np.float64) for k in ("open", "high", "low", "close"))
        bars = resample(df5, es.tf)
        a = atr(bars, 14)
        atr5 = pd.Series(a.to_numpy(), index=bars.index + tf).reindex(df5.index, method="ffill").to_numpy()
        day_start = ((ts5 // 86_400_000_000_000) * 86_400_000_000_000)
        ent_day = (c["entry_ts"][sel].astype("datetime64[ns]").astype(np.int64) // 86_400_000_000_000) * 86_400_000_000_000
        lo = np.searchsorted(day_start, ent_day, "left")
        hi = np.searchsorted(day_start, ent_day, "right")
        hi = np.minimum(hi, len(ts5) - max_bars)
        valid = hi > lo
        lo, hi, dirs = lo[valid], hi[valid], c["dir"][sel][valid]
        if len(lo) == 0:
            continue
        for b in range(n_draws):
            ei = lo + (rng.random(len(lo)) * (hi - lo)).astype(np.int64)
            sd = es.stop_atr * atr5[ei]
            good = np.isfinite(sd)
            _, r, _ = simulate(o, h, l, cl, ei[good], dirs[good], sd[good], es.target_r, max_bars, cost_per_side(tok))
            sums[b] += r.sum()
    null = sums / len(idx)
    real = c["r"][idx].mean()
    return {"timing_null_mean": float(null.mean()), "timing_pctile": float((null < real).mean() * 100)}


def gate_placebo(engine: Engine, e: str, long_ok: np.ndarray, short_ok: np.ndarray, defined: np.ndarray,
                 period: str, n_draws: int = 1000, seed: int = 5) -> dict:
    """Permute each token's gate values across its defined days in the period (keeps the
    per-token, per-direction pass rate), rerun, compare mean R and gate lift."""
    rng = np.random.default_rng(seed)
    d0, d1 = period_days(period)
    real_idx = engine.run(e, long_ok, short_ok, period)
    real = engine.c[e]["r"][real_idx].mean() if len(real_idx) else np.nan
    base_idx = engine.run(e, defined, defined, period)
    base = engine.c[e]["r"][base_idx].mean() if len(base_idx) else np.nan
    null = np.full(n_draws, np.nan)
    rows = np.arange(d0, min(d1, NDAYS))
    for b in range(n_draws):
        lo, so = long_ok.copy(), short_ok.copy()
        for t in range(long_ok.shape[1]):
            dd = rows[defined[rows, t]]
            if len(dd) < 2:
                continue
            p = rng.permutation(len(dd))
            lo[dd, t] = long_ok[dd, t][p]
            so[dd, t] = short_ok[dd, t][p]
        ix = engine.run(e, lo, so, period)
        if len(ix):
            null[b] = engine.c[e]["r"][ix].mean()
    null = null[np.isfinite(null)]
    return {"ungated_same_days_mean_r": float(base), "gate_lift": float(real - base),
            "placebo_mean_r": float(null.mean()) if len(null) else np.nan,
            "placebo_p": float((null >= real).mean()) if len(null) else np.nan}
