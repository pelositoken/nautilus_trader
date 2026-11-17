"""
Round 2 diagnosis of I4-g2-k1-E5 (short 4h Donchian-20 breakdowns only when 7-day
circulating-supply growth >= 1%). BUILD trades only: HOLDOUT trades are never
loaded here, so the variations designed from this analysis keep the holdout as
untouched-by-diagnosis data.

Outputs: results/r2_diag_features.csv, results/r2_diag_quintiles.csv,
results/r2_diag_breakdowns.csv, and a printed summary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from edgehunt.config import CACHE  # noqa: E402
from edgehunt.config import RESULTS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.engine import Engine  # noqa: E402
from edgehunt.gates import GateBuilder  # noqa: E402


BASE = ("I4", 2, 1, "E5")
FEATURES = [
    "f_atr_pct", "f_brk_depth", "f_bar_range_atr", "f_rsi4h", "f_ret_1d", "f_ret_7d", "f_ret_30d",
    "f_dist_30d_high", "f_ma50d", "f_vol_ratio", "f_atr_regime", "f_rel_7d",
    "m_ret_1d", "m_ret_7d", "m_ret_30d", "m_ma50d", "m_atr_pct", "m_atr_regime",
    "fund_last", "fund_3d",
    "s_e7", "s_e30", "s_maxjump7", "s_jumpdays7", "s_days_since_jump",
    "u_fees_r", "u_rev_r", "u_dau_r",
]


def base_trades() -> pd.DataFrame:
    eng = Engine(["E5"])
    gb = GateBuilder(load_fundamentals())
    lo, so, _ = gb.gate(*BASE[:3])
    idx = eng.run("E5", eng.to_np(lo), eng.to_np(so), "build")
    cand = pd.read_parquet(CACHE / "cand_E5.parquet")
    feats = pd.read_parquet(CACHE / "r2_features_E5.parquet")
    t = cand.loc[idx].join(feats)
    t["cost_r"] = t["r"] - t["r"]  # placeholder replaced below
    from edgehunt.config import cost_per_side
    t["cost_r"] = [2 * cost_per_side(tok) / a for tok, a in zip(t["token"], t["f_atr_pct"])]  # stop = 1.0 ATR
    t["year"] = t["entry_ts"].dt.year
    return t.reset_index(drop=True)


def boot_spearman(x: np.ndarray, y: np.ndarray, n: int = 2000, seed: int = 1) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    rho = st.spearmanr(x, y).statistic
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        bs.append(st.spearmanr(x[i], y[i]).statistic)
    return float(rho), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main() -> None:
    t = base_trades()
    print(f"BUILD trades: {len(t)}  mean R {t.r.mean():+.3f}  PF {t.r[t.r>0].sum()/-t.r[t.r<0].sum():.3f}")
    print("exit reasons (1 stop, 2 target, 3 time):", t.reason.value_counts().sort_index().to_dict())
    print("mean R by exit:", t.groupby("reason").r.mean().round(3).to_dict())
    los, win = t[t.r < 0], t[t.r > 0]
    print(f"losers: n={len(los)}, median MFE {los.o_mfe_r.median():.2f}R (share reaching +0.5R first: "
          f"{(los.o_mfe_r >= 0.5).mean():.2f}); winners median MAE {win.o_mae_r.median():.2f}R")
    print(f"mean cost drag {t.cost_r.mean():.3f}R/trade; gross mean R {(t.r + t.cost_r).mean():+.3f}")

    frows, qrows = [], []
    for f in FEATURES + ["cost_r"]:
        d = t[[f, "r"]].dropna()
        if len(d) < 60 or d[f].nunique() < 5:
            continue
        rho, lo, hi = boot_spearman(d[f].to_numpy(), d["r"].to_numpy())
        q = pd.qcut(d[f].rank(method="first"), 5, labels=False)
        g = d.groupby(q)
        qm = g["r"].mean()
        frows.append({"feature": f, "n": len(d), "spearman": rho, "ci_lo": lo, "ci_hi": hi,
                      "sig": (lo > 0) or (hi < 0), "q1_mean_r": qm.iloc[0], "q5_mean_r": qm.iloc[-1],
                      "best_q": int(qm.idxmax()) + 1, "worst_q": int(qm.idxmin()) + 1})
        for qi, gg in g:
            qrows.append({"feature": f, "quintile": int(qi) + 1, "lo": gg[f].min(), "hi": gg[f].max(),
                          "n": len(gg), "mean_r": gg["r"].mean(), "win": (gg["r"] > 0).mean(),
                          "pf": gg.r[gg.r > 0].sum() / max(1e-9, -gg.r[gg.r < 0].sum())})
    fr = pd.DataFrame(frows).sort_values("spearman", key=np.abs, ascending=False)
    fr.to_csv(RESULTS / "r2_diag_features.csv", index=False)
    pd.DataFrame(qrows).to_csv(RESULTS / "r2_diag_quintiles.csv", index=False)
    print(f"\n{len(fr)} features tested; ~{0.05*len(fr):.1f} 'significant' by chance at 5%")
    print(fr.round(3).to_string(index=False))

    br = []
    for col in ("token", "sector", "year", "hour", "dow"):
        g = t.groupby(col)["r"]
        for k, s in g:
            br.append({"by": col, "key": k, "n": len(s), "mean_r": s.mean(), "total_r": s.sum(),
                       "win": (s > 0).mean()})
    br = pd.DataFrame(br)
    br.to_csv(RESULTS / "r2_diag_breakdowns.csv", index=False)
    for col in ("sector", "year", "hour", "dow"):
        print(f"\nby {col}:\n" + br[br.by == col][["key", "n", "mean_r", "total_r", "win"]].round(3).to_string(index=False))
    tok = br[br.by == "token"].sort_values("total_r")
    print("\ntokens (total R):\n" + tok[["key", "n", "mean_r", "total_r"]].round(2).to_string(index=False))
    top3 = tok.nlargest(3, "total_r")["key"].tolist()
    rest = t[~t.token.isin(top3)]
    print(f"\nwithout top-3 tokens {top3}: n={len(rest)} mean R {rest.r.mean():+.3f}")


if __name__ == "__main__":
    main()
