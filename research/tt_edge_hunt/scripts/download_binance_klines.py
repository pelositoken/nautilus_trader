"""
Download Binance spot 5m klines from the public bulk archive (data.binance.vision).

Monthly zips for complete months, daily zips for the current month. Output is one
Parquet file per token under data/ohlcv/{TOKEN}_5m.parquet with columns:
ts (UTC, bar open), open, high, low, close, volume, quote_volume, trades.

Symbol renames are stitched (MATIC->POL, RNDR->RENDER); both pairs traded 1:1.
Binance switched spot archive timestamps from ms to us on 2025-01-01; handled.
"""

from __future__ import annotations

import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from datetime import timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ohlcv"
BASE = "https://data.binance.vision/data/spot"
START = date(2022, 5, 1)
END = date(2026, 11, 15)  # last complete UTC day at snapshot

TOKENS = (
    "ETH SOL BNB NEAR UNI ENA TRX SUI LINK AVAX AAVE INJ FIL ONDO ARB CRV APT JUP "
    "TIA RENDER POL CAKE OP RAY ETHFI SEI LDO ATOM PENDLE JTO"
).split()
# token -> list of (symbol, first_month_inclusive or None, last_month_inclusive or None)
RENAMES = {
    "POL": [("MATICUSDT", None, date(2024, 9, 1)), ("POLUSDT", date(2024, 9, 1), None)],
    "RENDER": [("RNDRUSDT", None, date(2024, 7, 1)), ("RENDERUSDT", date(2024, 7, 1), None)],
}
COLS = ["ts", "open", "high", "low", "close", "volume", "close_ts", "quote_volume", "trades",
        "tb_base", "tb_quote", "ignore"]


def fetch(url: str, retries: int = 4) -> bytes | None:
    for i in range(retries):
        try:
            with urlopen(url, timeout=60) as r:
                return r.read()
        except HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2**i)
        except Exception:
            time.sleep(2**i)
    raise RuntimeError(f"failed: {url}")


def parse_zip(blob: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        with z.open(z.namelist()[0]) as f:
            df = pd.read_csv(f, header=None, names=COLS)
    if not str(df.iloc[0, 0]).isdigit():  # some files carry a header row
        df = df.iloc[1:]
    ts = df["ts"].astype("int64")
    unit = "us" if ts.iloc[0] > 10**14 else "ms"
    out = pd.DataFrame({"ts": pd.to_datetime(ts, unit=unit, utc=True)})
    for c in ["open", "high", "low", "close", "volume", "quote_volume"]:
        out[c] = df[c].astype("float64").to_numpy()
    out["trades"] = df["trades"].astype("int64").to_numpy()
    return out


def months(a: date, b: date):
    d = date(a.year, a.month, 1)
    while d <= b:
        yield d
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def urls_for(token: str) -> list[str]:
    segs = RENAMES.get(token, [(f"{token}USDT", None, None)])
    cur_month = date(END.year, END.month, 1)
    urls = []
    for m in months(START, END):
        sym = next(s for s, lo, hi in segs if (lo is None or m >= lo) and (hi is None or m < hi))
        if m < cur_month:
            urls.append(f"{BASE}/monthly/klines/{sym}/5m/{sym}-5m-{m:%Y-%m}.zip")
        else:
            d = m
            while d <= END:
                urls.append(f"{BASE}/daily/klines/{sym}/5m/{sym}-5m-{d:%Y-%m-%d}.zip")
                d += timedelta(days=1)
    return urls


def download(token: str) -> str:
    path = OUT / f"{token}_5m.parquet"
    if path.exists():
        return f"{token}: cached"
    urls = urls_for(token)
    with ThreadPoolExecutor(8) as ex:
        blobs = list(ex.map(fetch, urls))
    frames = [parse_zip(b) for b in blobs if b]
    if not frames:
        return f"{token}: NO DATA"
    df = pd.concat(frames).drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    df.to_parquet(path, index=False)
    missing = sum(b is None for b in blobs)
    return f"{token}: {len(df)} bars {df.ts.iloc[0]:%Y-%m-%d}..{df.ts.iloc[-1]:%Y-%m-%d} (files missing: {missing})"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for t in sys.argv[1:] or TOKENS:
        print(download(t), flush=True)
