"""
BUILD-period sweep of all 710 pre-registered trials, walk-forward selection per
idea family, DSR on BUILD, and finalist selection (preregistration §9 step 2).
Never reads HOLDOUT trades.

Outputs: results/build_sweep.csv, results/build_wfa.csv, results/finalists.json,
data/cache/build_daily.npz
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edgehunt.config import CACHE  # noqa: E402
from edgehunt.config import EXEC_SETS  # noqa: E402
from edgehunt.config import N_TRIALS_TOTAL  # noqa: E402
from edgehunt.config import RESULTS  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.engine import Engine  # noqa: E402
from edgehunt.engine import period_days  # noqa: E402
from edgehunt.gates import DAYS  # noqa: E402
from edgehunt.gates import IDEAS  # noqa: E402
from edgehunt.gates import GateBuilder  # noqa: E402
from edgehunt.gates import all_variations  # noqa: E402
from edgehunt.stats import daily_stats  # noqa: E402
from edgehunt.stats import deflated_sharpe  # noqa: E402
from edgehunt.stats import trade_stats  # noqa: E402


PERIOD = "build"
MIN_FINALIST_TRADES = 150
WFA_IS_MONTHS, WFA_OOS_MONTHS, WFA_MIN_IS_TRADES = 12, 3, 30


def sweep(engine: Engine, gb: GateBuilder, period: str = PERIOD):
    rows, daily, trades = [], {}, {}
    ones = np.ones((len(DAYS), 30), bool)
    trials = [("BASE", e, None) for e in EXEC_SETS] + [(v.idea, v.exec_set, v) for v in all_variations()]
    gate_cache = {}
    for idea, e, v in trials:
        if v is None:
            vid, lo, so, de = f"B-{e}", ones, ones, ones
        else:
            vid = v.vid
            key = (v.idea, v.g, v.k)
            if key not in gate_cache:
                lo_, so_, de_ = gb.gate(v.idea, v.g, v.k)
                gate_cache[key] = (engine.to_np(lo_), engine.to_np(so_), engine.to_np(de_))
            lo, so, de = gate_cache[key]
        idx = engine.run(e, lo, so, period)
        d = engine.daily(e, idx, period)
        r = engine.c[e]["r"][idx]
        row = {"vid": vid, "idea": idea, "exec": e, **trade_stats(r), **daily_stats(d),
               "n_long": int((engine.c[e]["dir"][idx] > 0).sum())}
        if len(idx):
            ts = engine.c[e]["entry_ts"][idx]
            row["first_entry"], row["last_entry"] = str(ts.min())[:10], str(ts.max())[:10]
        rows.append(row)
        daily[vid], trades[vid] = d, idx
    return pd.DataFrame(rows), daily, trades


def walk_forward(df: pd.DataFrame, daily: dict, trades: dict, engine: Engine, period: str = PERIOD,
                 oos_from: pd.Timestamp | None = None) -> pd.DataFrame:
    d0, _ = period_days(period)
    bdays = DAYS[d0:d0 + len(next(iter(daily.values())))]
    out = []
    for idea in IDEAS:
        fam = df[df.idea == idea]
        vids = fam.vid.tolist()
        mat = np.vstack([daily[v] for v in vids])
        oos_start = bdays[0] + pd.DateOffset(months=WFA_IS_MONTHS) if oos_from is None else oos_from
        oos_r, oos_d, picks = [], [], []
        while oos_start < bdays[-1]:
            oos_end = oos_start + pd.DateOffset(months=WFA_OOS_MONTHS)
            is_m = (bdays >= oos_start - pd.DateOffset(months=WFA_IS_MONTHS)) & (bdays < oos_start)
            oos_m = (bdays >= oos_start) & (bdays < oos_end)
            best, best_sr = None, -np.inf
            for i, v in enumerate(vids):
                e = fam.iloc[i]["exec"]
                tdays = engine.c[e]["day"][trades[v]] - d0
                n_is = int(is_m[np.clip(tdays, 0, len(bdays) - 1)].sum())
                x = mat[i, is_m]
                sd = x.std(ddof=1)
                sr = x.mean() / sd if sd > 0 else -np.inf
                if n_is >= WFA_MIN_IS_TRADES and sr > best_sr:
                    best, best_sr = i, sr
            if best is not None:
                v = vids[best]
                e = fam.iloc[best]["exec"]
                tdays = engine.c[e]["day"][trades[v]] - d0
                sel = oos_m[np.clip(tdays, 0, len(bdays) - 1)]
                oos_r.append(engine.c[e]["r"][trades[v]][sel])
                oos_d.append(mat[best, oos_m])
                picks.append(f"{str(oos_start)[:7]}:{v}")
            oos_start = oos_end
        r = np.concatenate(oos_r) if oos_r else np.array([])
        dd = np.concatenate(oos_d) if oos_d else np.array([0.0])
        out.append({"idea": idea, "name": IDEAS[idea]["name"], **{f"wfa_{k}": val for k, val in trade_stats(r).items()},
                    "wfa_sharpe_ann": daily_stats(dd)["sharpe_ann"], "wfa_picks": " ".join(picks)})
    return pd.DataFrame(out)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    engine = Engine()
    gb = GateBuilder(load_fundamentals(), lag=1)
    df, daily, trades = sweep(engine, gb)
    var_all = float(df["sr_day"].var(ddof=1))
    fam_var = df.groupby("idea")["sr_day"].var(ddof=1).to_dict()
    for col, nt, var in (("dsr_n710", N_TRIALS_TOTAL, None), ("dsr_n100", 100, "fam")):
        df[col] = [
            deflated_sharpe(r.sr_day, r.T, r.skew, r.kurt, var_all if var is None else fam_var[r.idea], nt)["dsr"]
            for r in df.itertuples()
        ]
    df.to_csv(RESULTS / "build_sweep.csv", index=False)
    np.savez_compressed(CACHE / "build_daily.npz", **daily)
    np.savez_compressed(CACHE / "build_trades.npz", **trades)
    wfa = walk_forward(df, daily, trades, engine)
    wfa.to_csv(RESULTS / "build_wfa.csv", index=False)
    finalists = {}
    for idea in IDEAS:
        fam = df[(df.idea == idea) & (df.n >= MIN_FINALIST_TRADES)]
        if len(fam):
            finalists[idea] = fam.sort_values("sharpe_ann", ascending=False).iloc[0]["vid"]
    meta = {"finalists": finalists, "var_sr_day_all": var_all, "var_sr_day_family": fam_var,
            "n_trials_total": N_TRIALS_TOTAL, "rule": "max BUILD sharpe_ann with n >= 150"}
    (RESULTS / "finalists.json").write_text(json.dumps(meta, indent=2))
    cols = ["vid", "pf", "n", "win", "avg_r", "max_dd_r", "max_losing_streak", "sharpe_ann", "dsr_n710", "dsr_n100"]
    print(df[df.vid.isin(finalists.values()) | df.vid.str.startswith("B-")][cols].round(3).to_string(index=False))
    print(wfa.drop(columns="wfa_picks").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
