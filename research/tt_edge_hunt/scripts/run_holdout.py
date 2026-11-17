"""
HOLDOUT evaluation (preregistration §9 steps 3-4, §10). Refuses to run unless
results/finalists.json is committed in git (the freeze).

Outputs: results/holdout_finalists.csv, results/holdout_family.csv,
results/wfa_holdout.csv, results/holdout_corr.csv, results/lag_stress.csv
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from edgehunt.config import HOLDOUT_START  # noqa: E402
from edgehunt.config import RESULTS  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.engine import Engine  # noqa: E402
from edgehunt.gates import GateBuilder  # noqa: E402
from edgehunt.nulls import gate_placebo  # noqa: E402
from edgehunt.nulls import timing_null  # noqa: E402
from edgehunt.stats import bootstrap_trades  # noqa: E402
from edgehunt.stats import daily_stats  # noqa: E402
from edgehunt.stats import deflated_sharpe  # noqa: E402
from edgehunt.stats import trade_stats  # noqa: E402
from run_build import sweep  # noqa: E402
from run_build import walk_forward  # noqa: E402


def assert_frozen() -> None:
    f = RESULTS / "finalists.json"
    out = subprocess.run(["git", "status", "--porcelain", str(f)], capture_output=True, text=True, cwd=RESULTS)
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(f)], capture_output=True, cwd=RESULTS)
    if tracked.returncode != 0 or out.stdout.strip():
        sys.exit("finalists.json must be committed unchanged before HOLDOUT is touched")


def gate_for(gb: GateBuilder, engine: Engine, vid: str):
    if vid.startswith("B-"):
        ones = np.ones((len(gb.dcl), gb.dcl.shape[1]), bool)
        return vid[2:], ones, ones, ones
    idea, g, k, e = vid.split("-")
    lo, so, de = gb.gate(idea, int(g[1:]), int(k[1:]))
    return e, engine.to_np(lo), engine.to_np(so), engine.to_np(de)


def evaluate(engine, gb, vid, period, meta, family_var):
    e, lo, so, de = gate_for(gb, engine, vid)
    idx = engine.run(e, lo, so, period)
    r = engine.c[e]["r"][idx]
    d = engine.daily(e, idx, period)
    ds = daily_stats(d)
    ts = engine.c[e]["entry_ts"][idx]
    row = {"vid": vid, **trade_stats(r), "first_entry": str(ts.min())[:10] if len(ts) else "",
           "last_entry": str(ts.max())[:10] if len(ts) else "", **ds}
    row["dsr_n710"] = deflated_sharpe(ds["sr_day"], ds["T"], ds["skew"], ds["kurt"], meta["var_sr_day_all"], 710)["dsr"]
    row["dsr_n100"] = deflated_sharpe(ds["sr_day"], ds["T"], ds["skew"], ds["kurt"], family_var, 100)["dsr"]
    return row, e, idx, d, (lo, so, de)


def main() -> None:
    assert_frozen()
    meta = json.loads((RESULTS / "finalists.json").read_text())
    engine = Engine()
    fund = load_fundamentals()
    gb = GateBuilder(fund, lag=1)

    # family context: all 710 trials on HOLDOUT (no reselection) + WFA across BUILD->HOLDOUT
    fam_df, _, _ = sweep(engine, gb, "holdout")
    fam_df.to_csv(RESULTS / "holdout_family.csv", index=False)
    all_df, all_daily, all_trades = sweep(engine, gb, "all")
    wfa = walk_forward(all_df, all_daily, all_trades, engine, "all", HOLDOUT_START.tz_localize(None))
    wfa.to_csv(RESULTS / "wfa_holdout.csv", index=False)

    rows, daily = [], {}
    for idea, vid in meta["finalists"].items():
        row, e, idx, d, (lo, so, de) = evaluate(engine, gb, vid, "holdout", meta, meta["var_sr_day_family"][idea])
        r = engine.c[e]["r"][idx]
        row["idea"] = idea
        row.update(engine.random_benchmark(e, idx, de, "holdout"))
        row.update(timing_null(engine, e, idx))
        row.update(gate_placebo(engine, e, lo, so, de, "holdout"))
        row.update(bootstrap_trades(r))
        rows.append(row)
        daily[vid] = d
        print(f"done {vid}", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "holdout_finalists.csv", index=False)
    pd.DataFrame(daily).corr().to_csv(RESULTS / "holdout_corr.csv")

    stress = []
    for lag in (3, 7):
        gbl = GateBuilder(fund, lag=lag)
        for idea, vid in meta["finalists"].items():
            for period in ("build", "holdout"):
                row, *_ = evaluate(engine, gbl, vid, period, meta, meta["var_sr_day_family"][idea])
                stress.append({"lag": lag, "period": period, **{k: row[k] for k in ("vid", "n", "pf", "avg_r", "sharpe_ann")}})
    pd.DataFrame(stress).to_csv(RESULTS / "lag_stress.csv", index=False)


if __name__ == "__main__":
    main()
