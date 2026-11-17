"""Combinatorially symmetric cross-validation (CSCV) and the Probability of
Backtest Overfitting (Bailey, Borwein, Lopez de Prado & Zhu, 2014)."""

from __future__ import annotations

from itertools import combinations

import numpy as np


def pbo(daily: np.ndarray, n_blocks: int = 16) -> dict:
    """daily: (T days x N strategies) matrix of daily returns.

    Splits T into `n_blocks` contiguous blocks; for every half/half split picks the
    strategy with the best in-sample Sharpe and records its out-of-sample relative
    rank. PBO = share of splits where that strategy ranks below the OOS median.
    """
    T, N = daily.shape
    L = T // n_blocks
    x = daily[: L * n_blocks].reshape(n_blocks, L, N)
    s1, s2 = x.sum(axis=1), (x ** 2).sum(axis=1)  # per-block sums, (n_blocks, N)
    logits, degr = [], []
    for is_blocks in combinations(range(n_blocks), n_blocks // 2):
        m = np.zeros(n_blocks, bool)
        m[list(is_blocks)] = True
        sr_is = _sharpe(s1[m].sum(0), s2[m].sum(0), m.sum() * L)
        sr_oos = _sharpe(s1[~m].sum(0), s2[~m].sum(0), (~m).sum() * L)
        best = int(np.argmax(sr_is))
        rank = (sr_oos < sr_oos[best]).sum() + 0.5 * ((sr_oos == sr_oos[best]).sum() - 1) + 1
        w = rank / (N + 1)
        logits.append(np.log(w / (1 - w)))
        degr.append((sr_is[best], sr_oos[best]))
    logits = np.array(logits)
    d = np.array(degr)
    slope = np.polyfit(d[:, 0], d[:, 1], 1)[0] if len(d) > 2 else np.nan
    return {"pbo": float((logits <= 0).mean()), "n_splits": len(logits), "median_logit": float(np.median(logits)),
            "mean_oos_sr_of_is_best": float(d[:, 1].mean()), "is_oos_slope": float(slope),
            "p_oos_sr_lt_0": float((d[:, 1] < 0).mean())}


def _sharpe(s1: np.ndarray, s2: np.ndarray, n: int) -> np.ndarray:
    mean = s1 / n
    var = np.maximum(s2 / n - mean ** 2, 1e-18) * n / max(n - 1, 1)
    return mean / np.sqrt(var)
