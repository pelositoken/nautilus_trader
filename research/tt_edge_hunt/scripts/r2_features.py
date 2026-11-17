"""
Round 2: feature table for every E5 (4h Donchian-20) candidate trade.

Every feature uses only information available at the close of the 4h signal bar
(= entry time): price/volume up to that bar, BTC up to that bar, funding prints
strictly before entry, and daily fundamentals dated <= entry day - FUND_LAG_DAYS.
MFE/MAE/exit reason are OUTCOME descriptors for diagnosis only, never filters.

Output: data/cache/r2_features_E5.parquet (one row per candidate, same order as
data/cache/cand_E5.parquet).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from edgehunt.config import CACHE  # noqa: E402
from edgehunt.config import DATA  # noqa: E402
from edgehunt.config import EXEC_SETS  # noqa: E402
from edgehunt.config import FUND_LAG_DAYS  # noqa: E402
from edgehunt.config import SECTORS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.data import atr  # noqa: E402
from edgehunt.data import load_5m  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.data import resample  # noqa: E402
from edgehunt.data import rolling_mean  # noqa: E402
from edgehunt.data import rsi  # noqa: E402
from edgehunt.gates import DAYS  # noqa: E402


TF = "4h"
BARS_PER_DAY = 6


def bar_features(bars: pd.DataFrame, prefix: str) -> pd.DataFrame:
    c, h, lo, v = bars["close"], bars["high"], bars["low"], bars["volume"]
    a = atr(bars, 14)
    out = pd.DataFrame(index=bars.index)
    out[f"{prefix}atr_pct"] = a / c
    out[f"{prefix}ret_1d"] = np.log(c / c.shift(BARS_PER_DAY))
    out[f"{prefix}ret_7d"] = np.log(c / c.shift(7 * BARS_PER_DAY))
    out[f"{prefix}ret_30d"] = np.log(c / c.shift(30 * BARS_PER_DAY))
    out[f"{prefix}ma50d"] = c / c.rolling(50 * BARS_PER_DAY, min_periods=40 * BARS_PER_DAY).mean() - 1.0
    out[f"{prefix}atr_regime"] = a / a.rolling(30 * BARS_PER_DAY, min_periods=20 * BARS_PER_DAY).median()
    if prefix == "f_":
        out["f_brk_depth"] = (lo.rolling(20).min().shift(1) - c) / a  # short breakout: close below 20-bar low
        out["f_brk_depth_up"] = (c - h.rolling(20).max().shift(1)) / a
        out["f_rsi4h"] = rsi(c, 14)
        out["f_dist_30d_high"] = c / h.rolling(30 * BARS_PER_DAY, min_periods=20 * BARS_PER_DAY).max() - 1.0
        out["f_vol_ratio"] = v / v.rolling(20).mean().shift(1)
        out["f_bar_range_atr"] = (h - lo) / a
    return out


@njit(cache=True)
def excursions(o, h, l, ei, xi, direction, stop_dist):
    n = ei.shape[0]
    mfe = np.empty(n)
    mae = np.empty(n)
    for k in range(n):
        entry = o[ei[k]]
        hi_ = -1e18
        lo_ = 1e18
        for j in range(ei[k], xi[k] + 1):
            hi_ = max(hi_, h[j])
            lo_ = min(lo_, l[j])
        if direction[k] > 0:
            mfe[k] = (hi_ - entry) / stop_dist[k]
            mae[k] = (entry - lo_) / stop_dist[k]
        else:
            mfe[k] = (entry - lo_) / stop_dist[k]
            mae[k] = (hi_ - entry) / stop_dist[k]
    return mfe, mae


def daily_fundamental_features() -> dict[str, pd.DataFrame]:
    F = load_fundamentals()
    lag = FUND_LAG_DAYS
    idx = DAYS
    get = lambda m: F[m].reindex(index=idx, columns=TOKENS).shift(lag) if m in F else pd.DataFrame(np.nan, index=idx, columns=TOKENS)  # noqa: E731
    sup = get("token_supply_circulating")
    d1 = np.log(sup / sup.shift(1))
    out = {
        "s_e7": np.log(sup / sup.shift(7)),
        "s_e30": np.log(sup / sup.shift(30)),
        "s_maxjump7": d1.rolling(7, min_periods=5).max(),
        "s_jumpdays7": (d1 > 0.002).astype(float).where(d1.notna()).rolling(7, min_periods=5).sum(),
    }
    big = d1 > 0.005
    pos = np.repeat(np.arange(len(idx), dtype=float)[:, None], len(TOKENS), axis=1)
    last = pd.DataFrame(np.where(big, pos, np.nan), index=idx, columns=TOKENS).ffill()
    out["s_days_since_jump"] = pd.DataFrame(pos, index=idx, columns=TOKENS) - last
    for m, name in (("fees", "u_fees_r"), ("revenue", "u_rev_r"), ("user_dau", "u_dau_r")):
        x = get(m)
        a, b = rolling_mean(x, 7), rolling_mean(x, 30)
        out[name] = (a / b).where((a > 0) & (b > 0))
    return out


def main() -> None:
    es = EXEC_SETS["E5"]
    cand = pd.read_parquet(CACHE / "cand_E5.parquet")
    cand["entry_ts"] = cand["entry_ts"].astype("datetime64[ns, UTC]")
    tf = pd.Timedelta(TF)
    btc = bar_features(resample(load_5m("BTC"), TF), "m_")
    daily = daily_fundamental_features()
    rows = []
    for tok_id, tok in enumerate(TOKENS):
        sel = cand[cand.tok_id == tok_id]
        if sel.empty:
            continue
        df5 = load_5m(tok)
        bars = resample(df5, TF)
        fb = bar_features(bars, "f_")
        sig_bar = sel["entry_ts"] - tf  # bar whose close triggered the trade
        feat = fb.reindex(pd.DatetimeIndex(sig_bar)).reset_index(drop=True)
        feat = pd.concat([feat, btc.reindex(pd.DatetimeIndex(sig_bar)).reset_index(drop=True)], axis=1)
        feat = feat.copy()
        feat["f_rel_7d"] = feat["f_ret_7d"] - feat["m_ret_7d"]
        # funding: last print strictly before entry, and mean over the prior 72h
        fpath = DATA / "funding" / f"{tok}.parquet"
        if fpath.exists():
            fd = pd.read_parquet(fpath).sort_values("ts")
            fd["ts"] = fd["ts"].astype("datetime64[ns, UTC]")
            ent = sel[["entry_ts"]].reset_index(drop=True).copy()
            ent["entry_ts"] = ent["entry_ts"].astype("datetime64[ns, UTC]")
            m = pd.merge_asof(ent.sort_values("entry_ts"), fd, left_on="entry_ts", right_on="ts",
                              allow_exact_matches=False, direction="backward").set_index(ent.sort_values("entry_ts").index)
            feat["fund_last"] = m["rate"].sort_index().to_numpy()
            roll = fd.set_index("ts")["rate"].rolling("72h").mean()
            r3 = pd.merge_asof(ent.sort_values("entry_ts"), roll.rename("r3").reset_index(), left_on="entry_ts",
                               right_on="ts", allow_exact_matches=False, direction="backward").set_index(ent.sort_values("entry_ts").index)
            feat["fund_3d"] = r3["r3"].sort_index().to_numpy()
            stale = (ent["entry_ts"] - m["ts"].sort_index()) > pd.Timedelta("12h")
            feat.loc[stale.to_numpy(), ["fund_last", "fund_3d"]] = np.nan
        else:
            feat["fund_last"] = np.nan
            feat["fund_3d"] = np.nan
        day = sel["entry_ts"].dt.tz_localize(None).dt.normalize().reset_index(drop=True)
        for k, frame in daily.items():
            feat[k] = frame[tok].reindex(day.values).to_numpy()
        feat["hour"] = sel["entry_ts"].dt.hour.to_numpy()
        feat["dow"] = sel["entry_ts"].dt.dayofweek.to_numpy()
        feat["sector"] = next((s for s, v in SECTORS.items() if tok in v), "-")
        # outcome descriptors
        o, h, l = (df5[k].to_numpy(np.float64) for k in ("open", "high", "low"))
        a5 = pd.Series(atr(bars, 14).to_numpy(), index=bars.index + tf).reindex(df5.index).to_numpy()
        sd = es.stop_atr * a5[sel["entry_idx"].to_numpy()]
        mfe, mae = excursions(o, h, l, sel["entry_idx"].to_numpy(np.int64), sel["exit_idx"].to_numpy(np.int64),
                              sel["dir"].to_numpy(np.int8), sd)
        feat["o_mfe_r"], feat["o_mae_r"] = mfe, mae
        feat["o_bars_held"] = (sel["exit_idx"] - sel["entry_idx"] + 1).to_numpy()
        feat["cand_row"] = sel.index.to_numpy()
        rows.append(feat)
    out = pd.concat(rows).set_index("cand_row").sort_index()
    out.to_parquet(CACHE / "r2_features_E5.parquet")
    print(out.shape, "\n", out.isna().mean().round(3).sort_values(ascending=False).head(12).to_string())


if __name__ == "__main__":
    main()
