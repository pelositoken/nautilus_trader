"""
Forward paper test of three supply-emission short variations (paper/PREREGISTRATION.md).

Deterministic and catch-up safe: every run processes all 4h bars that closed
since the last processed bar, using the same rules as the backtest engine
(entry at the next 5m open, stop = s x ATR14(4h), target = t x stop, same-bar
stop/target = loss, 12h time exit, 0.10% taker + slippage per side, one position
per token per variation). Live inputs: Binance public klines
(data-api.binance.vision) and CoinGecko circulating supply.

Usage:
  python paper/paper_trade.py                       # live run, state in paper/state/
  python paper/paper_trade.py --start 2026-10-01 --end 2026-11-15 --state DIR --supply tt   # replay check
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path
from urllib.request import Request
from urllib.request import urlopen

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from edgehunt.config import UNIVERSE  # noqa: E402
from edgehunt.config import cost_per_side  # noqa: E402
from edgehunt.data import atr  # noqa: E402
from edgehunt.sim import simulate  # noqa: E402


KLINES = "https://data-api.binance.vision/api/v3/klines"
SYMBOL = {t: f"{t}USDT" for t in UNIVERSE}
H4 = pd.Timedelta("4h")
HOLD_BARS = 12 * 12  # 12h of 5m bars
GATE = 0.01  # 7-day supply growth threshold
PERP_COST = 0.0005  # alternative cost model (perpetual taker), reported alongside

VARIATIONS = {
    # vid: (BTC vol-regime cap or None, exhaustion filter, stop ATR, target R)
    "R2-V0X1R0G1": (None, True, 1.0, 1.5),
    "R2-V0X1R0G3": (None, True, 1.5, 1.5),
    "R2-V2X1R0G1": (1.00, True, 1.0, 1.5),
}
LEDGER_COLS = ["vid", "token", "signal_close", "entry_ts", "entry_px", "stop_dist", "stop_px", "target_px",
               "e7", "m_atr_regime", "f_rel_7d", "status", "exit_ts", "exit_px", "reason", "r", "r_perp_cost"]


def _get(url: str, params: dict, retries: int = 5):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    for i in range(retries):
        try:
            with urlopen(Request(f"{url}?{q}", headers={"User-Agent": "research-client"}), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"request failed: {url}?{q}")


def klines(symbol: str, interval: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Complete klines with open time in [start, end)."""
    rows, t = [], int(start.value // 1_000_000)
    end_ms = int(end.value // 1_000_000)
    while t < end_ms:
        batch = _get(KLINES, {"symbol": symbol, "interval": interval, "startTime": t, "limit": 1000})
        if not batch:
            break
        rows += batch
        t = batch[-1][0] + 1
        if len(batch) < 1000:
            break
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close"])
    df = pd.DataFrame(rows).iloc[:, :7]
    df.columns = ["ts", "open", "high", "low", "close", "volume", "close_ts"]
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df[(df["ts"] < end) & (pd.to_datetime(df["close_ts"], unit="ms", utc=True) < end + pd.Timedelta("1ms"))]
    return df.set_index("ts")[["open", "high", "low", "close"]].astype(float)


def regime(bars: pd.DataFrame) -> pd.DataFrame:
    a = atr(bars, 14)
    out = pd.DataFrame(index=bars.index)
    out["atr"] = a
    out["atr_regime"] = a / a.rolling(180, min_periods=120).median()
    out["ret_7d"] = np.log(bars["close"] / bars["close"].shift(42))
    out["short_sig"] = bars["close"] < bars["low"].rolling(20).min().shift(1)
    return out


def supply_table(kind: str, state: Path) -> pd.DataFrame:
    if kind == "tt":  # replay check against the research data
        from edgehunt.data import load_fundamentals
        # no index shift: e7 then uses TT values dated D-1 and D-8, exactly the backtest's lag-1 gate
        return load_fundamentals()["token_supply_circulating"].copy()
    from supply_source import fetch_supply
    s = fetch_supply(days=40, tokens=UNIVERSE)
    snap = s.stack().rename("supply").reset_index()
    snap.columns = ["date", "token", "supply"]
    snap["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path = state / "supply_snapshots.csv"
    snap.to_csv(path, mode="a", header=not path.exists(), index=False)  # keeps every snapshot (restatement record)
    return s


def e7(supply: pd.DataFrame, token: str, entry_day: pd.Timestamp) -> float:
    """ln(S[D-1]/S[D-8]) using CoinGecko points stamped D-1 and D-8 (>= 1 day lag)."""
    if token not in supply:
        return np.nan
    s = supply[token]
    a, b = s.get(entry_day - pd.Timedelta("1D")), s.get(entry_day - pd.Timedelta("8D"))
    return float(np.log(a / b)) if a and b and a > 0 and b > 0 else np.nan


def resolve(trade: dict, now: pd.Timestamp) -> dict:
    """Simulate a trade with the backtest's exit rules on 5m bars available so far."""
    entry = pd.Timestamp(trade["entry_ts"])
    bars = klines(SYMBOL[trade["token"]], "5m", entry, min(now, entry + HOLD_BARS * pd.Timedelta("5min")))
    if bars.empty:
        return trade
    o, h, l, c = (bars[k].to_numpy(np.float64) for k in ("open", "high", "low", "close"))
    trade["entry_px"] = float(o[0])
    sd = float(trade["stop_dist"])
    trade["stop_px"], trade["target_px"] = o[0] + sd, o[0] - VARIATIONS[trade["vid"]][3] * sd
    cost = cost_per_side(trade["token"])
    xi, r, why = simulate(o, h, l, c, np.array([0]), np.array([-1], np.int8), np.array([sd]),
                          VARIATIONS[trade["vid"]][3], HOLD_BARS, cost)
    complete = len(o) >= HOLD_BARS
    if why[0] == 3 and not complete:
        trade.update(status="open", r=float(r[0]), exit_ts="", exit_px=float(c[-1]), reason="unrealised")
        return trade
    j = int(xi[0])
    exit_px = {1: trade["stop_px"], 2: trade["target_px"], 3: float(c[j])}[int(why[0])]
    if j > 0 and int(why[0]) in (1, 2) and ((why[0] == 1 and o[j] >= trade["stop_px"]) or (why[0] == 2 and o[j] <= trade["target_px"])):
        exit_px = float(o[j])  # gapped through the level
    risk = sd / o[0]
    gross = 1.0 - exit_px / o[0]
    trade.update(status="closed", exit_ts=str(bars.index[j] + (pd.Timedelta("5min") if why[0] == 3 else pd.Timedelta(0))),
                 exit_px=float(exit_px), reason={1: "stop", 2: "target", 3: "time"}[int(why[0])], r=float(r[0]),
                 r_perp_cost=float((gross - 2 * (PERP_COST + (cost - 0.001))) / risk))
    return trade


def run(start: pd.Timestamp | None, end: pd.Timestamp, state: Path, supply_kind: str) -> None:
    state.mkdir(parents=True, exist_ok=True)
    meta_p, ledger_p = state / "meta.json", state / "ledger.csv"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    last = pd.Timestamp(meta["last_bar_close"]) if "last_bar_close" in meta else None
    if last is None:
        last = (start or end.floor("4h")) - pd.Timedelta("1ns")
        meta["started"] = str(last.ceil("4h"))
    ledger = pd.read_csv(ledger_p, dtype=str).to_dict("records") if ledger_p.exists() else []
    now = end

    # 1) resolve open trades with data available now
    for t in ledger:
        if t["status"] == "open":
            resolve(t, now)

    # 2) new 4h bars since `last`
    first_close = last.floor("4h") + H4
    if first_close > now.floor("4h"):
        print("no new 4h bar closed")
    else:
        hist_start = first_close - pd.Timedelta("45D")
        btc = regime(klines("BTCUSDT", "4h", hist_start, now.floor("4h")))
        supply = supply_table(supply_kind, state)
        closes = pd.date_range(first_close, now.floor("4h"), freq="4h")
        for tok in UNIVERSE:
            fb = regime(klines(SYMBOL[tok], "4h", hist_start, now.floor("4h")))
            for close in closes:
                bar_open = close - H4
                if bar_open not in fb.index or not bool(fb.at[bar_open, "short_sig"]) or not np.isfinite(fb.at[bar_open, "atr"]):
                    continue
                if bar_open not in btc.index:
                    continue
                g = e7(supply, tok, close.normalize().tz_localize(None))
                rel = fb.at[bar_open, "ret_7d"] - btc.at[bar_open, "ret_7d"]
                mreg = btc.at[bar_open, "atr_regime"]
                for vid, (vcap, xfilt, s_atr, _t) in VARIATIONS.items():
                    if not (np.isfinite(g) and g >= GATE):
                        continue
                    if xfilt and not (np.isfinite(rel) and rel >= -0.20):
                        continue
                    if vcap is not None and not (np.isfinite(mreg) and mreg <= vcap):
                        continue
                    busy = any(x["vid"] == vid and x["token"] == tok and
                               (x["status"] == "open" or pd.Timestamp(x["exit_ts"]) > close)
                               for x in ledger)
                    if busy:
                        continue
                    trade = {"vid": vid, "token": tok, "signal_close": str(close), "entry_ts": str(close),
                             "stop_dist": float(s_atr * fb.at[bar_open, "atr"]), "e7": g,
                             "m_atr_regime": float(mreg), "f_rel_7d": float(rel), "status": "open"}
                    ledger.append(resolve(trade, now))
    # bars closing after this point are processed next run (also set on the very first run)
    meta["last_bar_close"] = str(max(now.floor("4h"), last.ceil("4h") if last is not None else now.floor("4h")))
    meta["last_run"] = str(now)
    df = pd.DataFrame(ledger, columns=LEDGER_COLS).sort_values(["entry_ts", "vid", "token"])
    df.to_csv(ledger_p, index=False)
    meta_p.write_text(json.dumps(meta, indent=2))
    report(df, state, meta)


def report(df: pd.DataFrame, state: Path, meta: dict) -> None:
    lines = ["# Paper test status", "", f"Started: {meta.get('started')}  ·  last run: {meta.get('last_run')}  ·  "
             f"last 4h bar processed: {meta.get('last_bar_close')}", "",
             "| variation | closed | open | win rate | PF | mean R | total R | mean R (perp costs) | max DD (R) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for vid in VARIATIONS:
        d = df[df.vid == vid]
        c = d[d.status == "closed"]
        r = c["r"].astype(float).to_numpy()
        if len(r):
            eq = np.cumsum(r)
            dd = float((np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq).max())
            pf = r[r > 0].sum() / max(1e-9, -r[r < 0].sum())
            lines.append(f"| {vid} | {len(r)} | {int((d.status == 'open').sum())} | {(r > 0).mean():.2f} | {pf:.2f} | "
                         f"{r.mean():+.3f} | {r.sum():+.2f} | {c['r_perp_cost'].astype(float).mean():+.3f} | {dd:.1f} |")
        else:
            lines.append(f"| {vid} | 0 | {int((d.status == 'open').sum())} | – | – | – | – | – | – |")
    lines += ["", "Verdict is due once each variation has >= 100 closed trades (see PREREGISTRATION.md)."]
    (state / "STATUS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--state", default=str(Path(__file__).resolve().parent / "state"))
    ap.add_argument("--supply", default="coingecko", choices=["coingecko", "tt"])
    a = ap.parse_args()
    end = pd.Timestamp(a.end, tz="UTC") if a.end else pd.Timestamp.now(tz="UTC")
    run(pd.Timestamp(a.start, tz="UTC") if a.start else None, end, Path(a.state), a.supply)
