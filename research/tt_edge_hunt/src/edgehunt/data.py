"""Price loading, resampling and indicator helpers."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from edgehunt.config import MIN_PRICE_HISTORY_DAYS
from edgehunt.config import OHLCV
from edgehunt.config import TT


@lru_cache(maxsize=64)
def load_5m(token: str) -> pd.DataFrame:
    df = pd.read_parquet(OHLCV / f"{token}_5m.parquet")
    df["ts"] = pd.to_datetime(df["ts"], utc=True).astype("datetime64[ns, UTC]")
    return df.set_index("ts").sort_index()


def resample(df5: pd.DataFrame, tf: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df5.resample(tf, label="left", closed="left").agg(agg).dropna(subset=["close"])


def atr(bars: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = bars["close"].shift(1)
    tr = pd.concat([bars["high"] - bars["low"], (bars["high"] - pc).abs(), (bars["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    return 100.0 - 100.0 / (1.0 + up / dn)


def daily_close(token: str) -> pd.Series:
    """Close of each UTC day (last 5m close), indexed by naive date."""
    s = load_5m(token)["close"].resample("1D").last()
    s.index = s.index.tz_localize(None).normalize()
    return s


def first_eligible_day(token: str) -> pd.Timestamp:
    t0 = load_5m(token).index[0].tz_localize(None).normalize()
    return t0 + pd.Timedelta(days=MIN_PRICE_HISTORY_DAYS)


# Amendment A1: exact zeros are connector join defaults for these stock-like metrics.
ZERO_IS_MISSING = {"user_dau", "tvl", "token_supply_circulating"}


SUPPLY_PLACEHOLDER = 214_748_364.0  # 2^31/10 shown as a constant before real data


def clean_supply(p: pd.DataFrame) -> pd.DataFrame:
    """Amendment A2 (mechanical, per token column):
    1. values within 1% of the 2^31/10 placeholder -> missing;
    2. one-day blips: a value >5% away from the median of its two neighbours while the
       neighbours agree within 2% -> missing;
    3. series breaks: a one-day change > +100% (redenomination/migration, e.g. MATIC->POL)
       -> all values before the break are dropped, so no emission window spans it."""
    p = p.where((p - SUPPLY_PLACEHOLDER).abs() > 0.01 * SUPPLY_PLACEHOLDER)
    prev, nxt = p.shift(1), p.shift(-1)
    mid = (prev + nxt) / 2.0
    blip = ((p - mid).abs() > 0.05 * mid) & ((prev - nxt).abs() <= 0.02 * mid)
    p = p.where(~blip)
    for col in p.columns:
        s = p[col].dropna()
        jumps = s.index[(s / s.shift(1)) > 2.0]
        if len(jumps):
            p.loc[p.index < jumps[-1], col] = np.nan
    return p


def load_fundamentals() -> dict[str, pd.DataFrame]:
    """metric -> DataFrame(date x token) on a continuous daily index (no fill)."""
    df = pd.read_csv(TT / "fundamentals_long.csv", parse_dates=["date"])
    out = {}
    idx = pd.date_range("2022-06-01", "2026-11-15", freq="D")
    for m, g in df.groupby("metric"):
        p = g.pivot(index="date", columns="token", values="value").reindex(idx)
        if m in ZERO_IS_MISSING:
            p = p.where(p != 0)
        if m == "token_supply_circulating":
            p = clean_supply(p)
        out[m] = p
    return out


def rolling_mean(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(n, min_periods=int(np.ceil(0.8 * n))).mean()
