"""
Round 2 evaluation (docs/preregistration_round2.md).

  python scripts/r2_run.py build     # sweep 100 on BUILD, PBO, WFA(BUILD), finalist -> results/r2_finalist.json
  python scripts/r2_run.py holdout   # refuses unless r2_finalist.json is committed; all §5 tests
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "nautilus"))

from edgehunt.config import CACHE  # noqa: E402
from edgehunt.config import EXEC_SETS  # noqa: E402
from edgehunt.config import HOLDOUT_START  # noqa: E402
from edgehunt.config import RESULTS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.config import cost_per_side  # noqa: E402
from edgehunt.data import load_5m  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.engine import NDAYS  # noqa: E402
from edgehunt.engine import Engine  # noqa: E402
from edgehunt.engine import period_days  # noqa: E402
from edgehunt.gates import DAYS  # noqa: E402
from edgehunt.gates import GateBuilder  # noqa: E402
from edgehunt.pbo import pbo  # noqa: E402
from edgehunt.sim import simulate  # noqa: E402
from edgehunt.stats import bootstrap_trades  # noqa: E402
from edgehunt.stats import daily_stats  # noqa: E402
from edgehunt.stats import deflated_sharpe  # noqa: E402
from edgehunt.stats import trade_stats  # noqa: E402


G_SPEC = {1: ("E5", 1), 2: ("E5t10", 1), 3: ("E5s15", 1), 4: ("E5", 2), 5: ("E5", 0)}  # exec set, I4 flip k index
GATE_V = {0: 0.005, 1: 0.01, 2: 0.02}
N_TOTAL = 810
MIN_TRADES = 150


def vid(v, x, r, g):
    return f"R2-V{v}X{x}R{r}G{g}"


def all_vids():
    return [(v, x, r, g) for g in range(1, 6) for v in range(5) for x in range(2) for r in range(2)]


class R2:
    def __init__(self, fund_lag: int = 1):
        self.eng = Engine(["E5", "E5t10", "E5s15"])
        self.feat = pd.read_parquet(CACHE / "r2_features_E5.parquet")
        assert len(self.feat) == len(self.eng.c["E5"]["r"])
        if fund_lag != 1:
            from r2_features import daily_fundamental_features
            daily = daily_fundamental_features(lag=fund_lag)
            cand = pd.read_parquet(CACHE / "cand_E5.parquet")
            day = cand["entry_ts"].dt.tz_localize(None).dt.normalize()
            tok = cand["token"]
            self.feat["u_rev_r"] = [daily["u_rev_r"].at[d, t] if d in daily["u_rev_r"].index else np.nan
                                    for d, t in zip(day, tok)]
        self.gb = GateBuilder(load_fundamentals(), lag=fund_lag)
        self.gates = {}
        for k in (0, 1, 2):
            lo, so, de = self.gb.gate("I4", 2, k)
            self.gates[k] = (self.eng.to_np(lo), self.eng.to_np(so), self.eng.to_np(de))
        f = self.feat
        m, t = f["m_atr_regime"].to_numpy(), f["f_atr_regime"].to_numpy()
        self.vmask = {0: np.ones(len(f), bool), 1: m <= 1.25, 2: m <= 1.00, 3: t <= 1.25, 4: (m <= 1.25) & (t <= 1.25)}
        self.xmask = {0: np.ones(len(f), bool), 1: f["f_rel_7d"].to_numpy() >= -0.20}
        self.rmask = {0: np.ones(len(f), bool), 1: f["u_rev_r"].to_numpy() < 1.0}

    def spec(self, v, x, r, g):
        e, k = G_SPEC[g]
        return e, k, self.vmask[v] & self.xmask[x] & self.rmask[r]

    def run(self, key, period, mask_override=None):
        e, k, mask = self.spec(*key)
        lo, so, _ = self.gates[k]
        idx = self.eng.run(e, lo, so, period, mask if mask_override is None else mask_override)
        return e, idx


def sweep(r2: R2, period: str):
    rows, daily, trades = [], {}, {}
    for key in all_vids():
        e, idx = r2.run(key, period)
        d = r2.eng.daily(e, idx, period)
        rr = r2.eng.c[e]["r"][idx]
        rows.append({"vid": vid(*key), "V": key[0], "X": key[1], "R": key[2], "G": key[3], "exec": e,
                     **trade_stats(rr), **daily_stats(d)})
        daily[vid(*key)], trades[vid(*key)] = d, (e, idx)
    df = pd.DataFrame(rows)
    var = float(df["sr_day"].var(ddof=1))
    for col, n in (("dsr_n100", 100), ("dsr_n810", N_TOTAL)):
        df[col] = [deflated_sharpe(r.sr_day, r.T, r.skew, r.kurt, var, n)["dsr"] for r in df.itertuples()]
    return df, daily, trades, var


def walk_forward(r2: R2, period: str, oos_from: pd.Timestamp | None):
    df, daily, trades, _ = sweep(r2, period)
    d0, _ = period_days(period)
    vids = df.vid.tolist()
    mat = np.vstack([daily[v] for v in vids])
    days = DAYS[d0:d0 + mat.shape[1]]
    start = days[0] + pd.DateOffset(months=12) if oos_from is None else oos_from
    oos_r, picks = [], []
    while start < days[-1]:
        end = start + pd.DateOffset(months=3)
        is_m = (days >= start - pd.DateOffset(months=12)) & (days < start)
        oos_m = (days >= start) & (days < end)
        best, best_sr = None, -np.inf
        for i, v in enumerate(vids):
            e, idx = trades[v]
            td = np.clip(r2.eng.c[e]["day"][idx] - d0, 0, len(days) - 1)
            x = mat[i, is_m]
            sd = x.std(ddof=1)
            if is_m[td].sum() >= 30 and sd > 0 and x.mean() / sd > best_sr:
                best, best_sr = i, x.mean() / sd
        if best is not None:
            e, idx = trades[vids[best]]
            td = np.clip(r2.eng.c[e]["day"][idx] - d0, 0, len(days) - 1)
            oos_r.append(r2.eng.c[e]["r"][idx][oos_m[td]])
            picks.append(f"{str(start)[:7]}:{vids[best]}")
        start = end
    r = np.concatenate(oos_r) if oos_r else np.array([])
    return {**{f"wfa_{k}": v for k, v in trade_stats(r).items()}, "wfa_picks": " ".join(picks)}


def assert_committed(path: Path):
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], capture_output=True, cwd=ROOT)
    dirty = subprocess.run(["git", "status", "--porcelain", str(path)], capture_output=True, text=True, cwd=ROOT)
    if tracked.returncode != 0 or dirty.stdout.strip():
        sys.exit(f"{path.name} must be committed before HOLDOUT is evaluated")


def phase_build():
    r2 = R2()
    df, daily, _, var = sweep(r2, "build")
    df.to_csv(RESULTS / "r2_build_sweep.csv", index=False)
    mat = np.column_stack([daily[v] for v in df.vid])
    p = pbo(mat)
    wfa = walk_forward(r2, "build", None)
    elig = df[df.n >= MIN_TRADES].sort_values("sharpe_ann", ascending=False)
    fin = elig.iloc[0]
    out = {"finalist": fin.vid, "rule": "max BUILD sharpe_ann, n >= 150", "var_sr_day_100": var,
           "pbo_build": p, "wfa_build": wfa, "n_eligible": int(len(elig)),
           "build": {k: (float(fin[k]) if isinstance(fin[k], (int, float, np.floating, np.integer)) else fin[k])
                     for k in ("n", "pf", "win", "avg_r", "sharpe_ann", "max_dd_r", "max_losing_streak",
                               "dsr_n100", "dsr_n810")}}
    (RESULTS / "r2_finalist.json").write_text(json.dumps(out, indent=2, default=float))
    cols = ["vid", "n", "pf", "win", "avg_r", "sharpe_ann", "max_dd_r", "dsr_n100"]
    print(df.sort_values("sharpe_ann", ascending=False)[cols].head(15).round(3).to_string(index=False))
    print("\nbase:", df[df.vid == "R2-V0X0R0G1"][cols].round(3).to_string(index=False, header=False))
    print(f"\nshare of 100 with mean R > 0: {(df.avg_r > 0).mean():.2f}; with PF>1 & n>=150: {((df.pf > 1) & (df.n >= 150)).sum()}")
    for dim in ("V", "X", "R", "G"):
        print(f"by {dim}: " + df.groupby(dim)["avg_r"].median().round(3).to_dict().__repr__())
    print("\nPBO (BUILD):", {k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()})
    print("WFA (BUILD OOS):", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in wfa.items() if k != "wfa_picks"})
    print("FINALIST:", fin.vid, {k: round(float(fin[k]), 3) for k in ("n", "pf", "avg_r", "sharpe_ann", "dsr_n100", "dsr_n810")})


def filter_placebo(r2: R2, key, period, n_draws=2000, seed=21):
    """Drop the same number of gated candidates at random instead of by the filter."""
    e, k, mask = r2.spec(*key)
    lo, so, _ = r2.gates[k]
    c = r2.eng.c[e]
    d0, d1 = period_days(period)
    day = np.clip(c["day"], 0, NDAYS - 1)
    gated = (c["dir"] < 0) & so[day, c["tok"]] & (c["day"] >= d0) & (c["day"] < d1)
    pool = np.flatnonzero(gated)
    n_keep = int((gated & mask).sum())
    real_idx = r2.eng.run(e, lo, so, period, mask)
    real = c["r"][real_idx].mean()
    rng = np.random.default_rng(seed)
    null = np.empty(n_draws)
    for b in range(n_draws):
        mk = np.zeros(len(mask), bool)
        mk[rng.choice(pool, n_keep, replace=False)] = True
        ix = r2.eng.run(e, lo, so, period, mk)
        null[b] = c["r"][ix].mean() if len(ix) else np.nan
    null = null[np.isfinite(null)]
    return {"placebo_mean_r": float(null.mean()), "placebo_p": float((null >= real).mean())}


def entry_delay_null(r2: R2, e, idx, n_draws=1000, seed=33):
    from build_candidates_shim import stop_distances
    es = EXEC_SETS[e]
    c = r2.eng.c[e]
    rng = np.random.default_rng(seed)
    sums = np.zeros(n_draws)
    for tok_id in np.unique(c["tok"][idx]):
        tok = TOKENS[tok_id]
        sel = idx[c["tok"][idx] == tok_id]
        df5 = load_5m(tok)
        o, h, l, cl = (df5[k].to_numpy(np.float64) for k in ("open", "high", "low", "close"))
        ei0 = c["ei"][sel]
        sd = stop_distances(tok, es, ei0)
        dirs = c["dir"][sel]
        for b in range(n_draws):
            ei = np.minimum(ei0 + rng.integers(0, 49, len(ei0)), len(o) - es.hold_hours * 12 - 1)
            _, r, _ = simulate(o, h, l, cl, ei.astype(np.int64), dirs, sd, es.target_r, es.hold_hours * 12, cost_per_side(tok))
            sums[b] += r.sum()
    null = sums / len(idx)
    real = c["r"][idx].mean()
    return {"delay_null_mean_r": float(null.mean()), "delay_pctile": float((null < real).mean() * 100)}


def evaluate(r2: R2, key, period, var):
    e, idx = r2.run(key, period)
    c = r2.eng.c[e]
    rr = c["r"][idx]
    d = r2.eng.daily(e, idx, period)
    ds = daily_stats(d)
    ts = c["entry_ts"][idx]
    _, _, de = r2.gates[G_SPEC[key[3]][1]]
    row = {"period": period, **trade_stats(rr), **ds,
           "first_entry": str(ts.min())[:10] if len(ts) else "", "last_entry": str(ts.max())[:10] if len(ts) else "",
           "dsr_n100": deflated_sharpe(ds["sr_day"], ds["T"], ds["skew"], ds["kurt"], var, 100)["dsr"],
           "dsr_n810": deflated_sharpe(ds["sr_day"], ds["T"], ds["skew"], ds["kurt"], var, N_TOTAL)["dsr"],
           **r2.eng.random_benchmark(e, idx, de, period), **filter_placebo(r2, key, period),
           **entry_delay_null(r2, e, idx), **bootstrap_trades(rr)}
    # stress: costs x1.5 (extra half of the round-trip cost, in R units)
    es = EXEC_SETS[e]
    atrp = r2.feat["f_atr_pct"].to_numpy()[idx]
    extra = np.array([cost_per_side(TOKENS[t]) for t in c["tok"][idx]]) / (es.stop_atr * atrp)
    row["avg_r_cost_x1_5"] = float((rr - extra).mean())
    # leave-one-token-out and top-3 removal
    toks = c["tok"][idx]
    loto = [rr[toks != t].mean() for t in np.unique(toks)]
    tot = pd.Series(rr).groupby(toks).sum().sort_values()
    top3 = tot.index[-3:]
    row.update({"loto_min_r": float(min(loto)), "loto_max_r": float(max(loto)),
                "avg_r_ex_top3": float(rr[~np.isin(toks, top3)].mean()),
                "top3_tokens": " ".join(TOKENS[t] for t in top3), "n_tokens": int(len(tot))})
    return row, d


def phase_holdout():
    assert_committed(RESULTS / "r2_finalist.json")
    meta = json.loads((RESULTS / "r2_finalist.json").read_text())
    fin = meta["finalist"]
    key = tuple(int(fin[i]) for i in (4, 6, 8, 10))  # R2-V{v}X{x}R{r}G{g}
    r2 = R2()
    var = meta["var_sr_day_100"]
    rows = []
    for period in ("build", "holdout"):
        row, _ = evaluate(r2, key, period, var)
        rows.append({"vid": fin, **row})
        base_row, _ = evaluate(r2, (0, 0, 0, 1), period, var)
        rows.append({"vid": "R2-V0X0R0G1 (base)", **base_row})
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "r2_finalist_eval.csv", index=False)
    fam_h, daily_h, _, _ = sweep(r2, "holdout")
    fam_h.to_csv(RESULTS / "r2_holdout_family.csv", index=False)
    r2all = sweep(r2, "all")
    p_all = pbo(np.column_stack([r2all[1][v] for v in r2all[0].vid]))
    wfa_h = walk_forward(r2, "all", HOLDOUT_START.tz_localize(None))
    # neighbourhood on BUILD and HOLDOUT
    fam_b = pd.read_csv(RESULTS / "r2_build_sweep.csv")
    nb = []
    for fam, per in ((fam_b, "build"), (fam_h, "holdout")):
        f = fam.copy()
        diff = (f[["V", "X", "R", "G"]].to_numpy() != np.array(key)).sum(axis=1)
        nn = f[diff == 1]
        nb.append({"period": per, "n_neighbours": len(nn), "share_pos": float((nn.avg_r > 0).mean()),
                   "median_sharpe": float(nn.sharpe_ann.median()), "median_avg_r": float(nn.avg_r.median())})
    stress = []
    for lag in (2, 3):
        r2l = R2(fund_lag=lag)
        for per in ("build", "holdout"):
            e, idx = r2l.run(key, per)
            rr = r2l.eng.c[e]["r"][idx]
            stress.append({"lag": lag, "period": per, **trade_stats(rr)})
    extra = {"pbo_all": p_all, "wfa_holdout": wfa_h, "neighbourhood": nb, "lag_stress": stress}
    (RESULTS / "r2_holdout_extra.json").write_text(json.dumps(extra, indent=2, default=float))
    pd.set_option("display.width", 250)
    print(out.T.to_string())
    print("\nPBO all:", p_all)
    print("WFA holdout OOS:", {k: v for k, v in wfa_h.items() if k != "wfa_picks"})
    print("neighbourhood:", nb)
    print("lag stress:", pd.DataFrame(stress)[["lag", "period", "n", "pf", "avg_r"]].round(3).to_string(index=False))
    print("holdout family: share mean R>0", round((fam_h.avg_r > 0).mean(), 2), "median avg_r", round(fam_h.avg_r.median(), 3))


if __name__ == "__main__":
    {"build": phase_build, "holdout": phase_holdout}[sys.argv[1]]()
