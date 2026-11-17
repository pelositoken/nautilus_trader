"""Performance statistics, Deflated Sharpe Ratio and resampling nulls."""

from __future__ import annotations

import numpy as np
from scipy import stats as st


EULER_GAMMA = 0.5772156649


def trade_stats(r: np.ndarray) -> dict:
    n = len(r)
    if n == 0:
        return {"n": 0, "pf": np.nan, "win": np.nan, "avg_r": np.nan, "avg_win": np.nan,
                "avg_loss": np.nan, "max_losing_streak": 0, "total_r": 0.0}
    pos, neg = r[r > 0].sum(), -r[r < 0].sum()
    streak = best = 0
    for x in r:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    return {
        "n": n, "pf": pos / neg if neg > 0 else np.inf, "win": float((r > 0).mean()),
        "avg_r": float(r.mean()), "avg_win": float(r[r > 0].mean()) if (r > 0).any() else np.nan,
        "avg_loss": float(r[r < 0].mean()) if (r < 0).any() else np.nan,
        "max_losing_streak": best, "total_r": float(r.sum()),
    }


def daily_stats(d: np.ndarray) -> dict:
    """d: daily R series including zero days."""
    sd = d.std(ddof=1)
    sr = d.mean() / sd if sd > 0 else 0.0
    eq = np.cumsum(d)
    dd = float((np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq).max()) if len(d) else 0.0
    return {
        "sr_day": float(sr), "sharpe_ann": float(sr * np.sqrt(365.0)), "max_dd_r": dd,
        "skew": float(st.skew(d)) if sd > 0 else 0.0,
        "kurt": float(st.kurtosis(d, fisher=False)) if sd > 0 else 3.0, "T": len(d),
    }


def expected_max_sr(var_sr: float, n_trials: int) -> float:
    if n_trials <= 1 or var_sr <= 0:
        return 0.0
    z1 = st.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = st.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(var_sr) * ((1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2))


def deflated_sharpe(sr: float, T: int, skew: float, kurt: float, var_sr: float, n_trials: int) -> dict:
    sr0 = expected_max_sr(var_sr, n_trials)
    denom = np.sqrt(max(1e-12, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr))
    z = (sr - sr0) * np.sqrt(T - 1) / denom
    return {"sr0_day": sr0, "dsr": float(st.norm.cdf(z)), "dsr_z": float(z), "n_trials": n_trials}


def bootstrap_trades(r: np.ndarray, n_boot: int = 5000, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    tot, mdd = np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        s = r[rng.integers(0, len(r), len(r))]
        eq = np.cumsum(s)
        tot[b] = eq[-1]
        mdd[b] = (np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq).max()
    return {"total_r_p5": float(np.percentile(tot, 5)), "total_r_p50": float(np.median(tot)),
            "total_r_p95": float(np.percentile(tot, 95)), "p_total_lt_0": float((tot < 0).mean()),
            "max_dd_p50": float(np.median(mdd)), "max_dd_p95": float(np.percentile(mdd, 95))}
