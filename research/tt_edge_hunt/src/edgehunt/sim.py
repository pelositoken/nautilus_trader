"""Numba trade simulation on 5m bars.

Conventions (pre-registered):
- entry at open of bar `ei`; exits checked from bar `ei` inclusive;
- a bar touching both stop and target counts as the stop (loss);
- a bar opening through a level fills at that open;
- time exit at the close of bar ei + max_bars - 1.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def simulate(o, h, l, c, ei, direction, stop_dist, target_r, max_bars, cost):
    n = ei.shape[0]
    nb = o.shape[0]
    exit_idx = np.empty(n, np.int64)
    r_net = np.empty(n, np.float64)
    reason = np.empty(n, np.int8)  # 1 stop, 2 target, 3 time
    for k in range(n):
        i0 = ei[k]
        d = direction[k]
        entry = o[i0]
        sd = stop_dist[k]
        if d > 0:
            stop = entry - sd
            tgt = entry + target_r * sd
        else:
            stop = entry + sd
            tgt = entry - target_r * sd
        last = min(i0 + max_bars - 1, nb - 1)
        px = c[last]
        why = 3
        j_exit = last
        for j in range(i0, last + 1):
            if d > 0:
                if j > i0 and o[j] <= stop:
                    px = o[j]; why = 1; j_exit = j; break
                if j > i0 and o[j] >= tgt:
                    px = o[j]; why = 2; j_exit = j; break
                hit_s = l[j] <= stop
                hit_t = h[j] >= tgt
                if hit_s:
                    px = stop; why = 1; j_exit = j; break
                if hit_t:
                    px = tgt; why = 2; j_exit = j; break
            else:
                if j > i0 and o[j] >= stop:
                    px = o[j]; why = 1; j_exit = j; break
                if j > i0 and o[j] <= tgt:
                    px = o[j]; why = 2; j_exit = j; break
                hit_s = h[j] >= stop
                hit_t = l[j] <= tgt
                if hit_s:
                    px = stop; why = 1; j_exit = j; break
                if hit_t:
                    px = tgt; why = 2; j_exit = j; break
        risk = sd / entry
        if d > 0:
            gross = px / entry - 1.0
        else:
            gross = 1.0 - px / entry
        r_net[k] = (gross - 2.0 * cost) / risk
        exit_idx[k] = j_exit
        reason[k] = why
    return exit_idx, r_net, reason


@njit(cache=True)
def non_overlap(token_id, entry_idx, exit_idx):
    """Greedy one-position-per-token filter. Inputs sorted by (token, entry)."""
    n = token_id.shape[0]
    keep = np.zeros(n, np.bool_)
    cur_tok = -1
    last_exit = -1
    for k in range(n):
        if token_id[k] != cur_tok:
            cur_tok = token_id[k]
            last_exit = -1
        if entry_idx[k] > last_exit:
            keep[k] = True
            last_exit = exit_idx[k]
    return keep
