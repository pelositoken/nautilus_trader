"""
Download Binance USDT-M perpetual funding-rate history (monthly archives,
data.binance.vision) for the universe. Output: data/funding/{TOKEN}.parquet with
columns ts (funding time, UTC), rate.

MATIC funding before the POL rename is stitched (MATICUSDT -> POLUSDT, 2024-09).
"""

from __future__ import annotations

import io
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_binance_klines import END  # noqa: E402
from download_binance_klines import START  # noqa: E402
from download_binance_klines import fetch  # noqa: E402
from download_binance_klines import months  # noqa: E402
from edgehunt.config import UNIVERSE  # noqa: E402


BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate"
OUT = ROOT / "data" / "funding"
SYMBOLS = {"POL": ["MATICUSDT", "POLUSDT"]}


def parse(blob: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(blob)) as z, z.open(z.namelist()[0]) as f:
        df = pd.read_csv(f)
    df.columns = [c.lower() for c in df.columns]
    tcol = next(c for c in df.columns if "time" in c)
    rcol = next(c for c in df.columns if "rate" in c and "interval" not in c)
    return pd.DataFrame({"ts": pd.to_datetime(df[tcol].astype("int64"), unit="ms", utc=True),
                         "rate": df[rcol].astype("float64")})


def download(token: str) -> str:
    urls = [f"{BASE}/{s}/{s}-fundingRate-{m:%Y-%m}.zip"
            for s in SYMBOLS.get(token, [f"{token}USDT"]) for m in months(START, END)]
    with ThreadPoolExecutor(8) as ex:
        blobs = list(ex.map(fetch, urls))
    frames = [parse(b) for b in blobs if b]
    if not frames:
        return f"{token}: no funding data"
    df = pd.concat(frames).drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    df.to_parquet(OUT / f"{token}.parquet", index=False)
    return f"{token}: {len(df)} funding prints {df.ts.iloc[0]:%Y-%m-%d}..{df.ts.iloc[-1]:%Y-%m-%d}"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for t in sys.argv[1:] or UNIVERSE:
        print(download(t), flush=True)
