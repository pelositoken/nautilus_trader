"""Frozen research configuration. Mirrors docs/preregistration.md; do not tune."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OHLCV = DATA / "ohlcv"
TT = DATA / "tt"
CACHE = DATA / "cache"
RESULTS = ROOT / "results"

WARMUP_START = pd.Timestamp("2022-06-01", tz="UTC")
BUILD_START = pd.Timestamp("2022-09-01", tz="UTC")
HOLDOUT_START = pd.Timestamp("2025-09-01", tz="UTC")
END = pd.Timestamp("2026-11-16", tz="UTC")  # exclusive

PERIODS = {"build": (BUILD_START, HOLDOUT_START), "holdout": (HOLDOUT_START, END), "all": (BUILD_START, END)}

TOKENS = (
    "ETH SOL BNB NEAR UNI ENA TRX SUI LINK AVAX AAVE INJ FIL ONDO ARB CRV APT JUP "
    "TIA RENDER POL CAKE OP RAY ETHFI SEI LDO ATOM PENDLE JTO"
).split()
# Final universe (preregistration §2; docs/data_inventory.md): no TT fees or revenue -> out.
EXCLUDED = {"RENDER", "ONDO"}
UNIVERSE = [t for t in TOKENS if t not in EXCLUDED]
SECTORS = {
    "CHAINS": "ETH SOL BNB NEAR TRX SUI AVAX APT ARB OP POL TIA SEI INJ ATOM".split(),
    "APPS": "UNI AAVE CRV JUP RAY CAKE LDO PENDLE ETHFI JTO ENA LINK FIL".split(),
}

TAKER_FEE = 0.0010
SLIPPAGE = {"ETH": 0.0002, "SOL": 0.0002, "BNB": 0.0002}
DEFAULT_SLIPPAGE = 0.0005
MIN_PRICE_HISTORY_DAYS = 60
FUND_LAG_DAYS = 1  # primary; stress tests use 3 and 7


def cost_per_side(token: str) -> float:
    return TAKER_FEE + SLIPPAGE.get(token, DEFAULT_SLIPPAGE)


@dataclass(frozen=True)
class ExecSet:
    name: str
    kind: str  # donchian | ema_cross | rsi_cross | boll_reentry
    tf: str  # pandas offset alias
    param: tuple
    stop_atr: float
    target_r: float
    hold_hours: int


EXEC_SETS = {
    "E1": ExecSet("E1", "donchian", "1h", (20,), 1.5, 2.0, 12),
    "E2": ExecSet("E2", "donchian", "15min", (20,), 1.5, 2.0, 4),
    "E3": ExecSet("E3", "donchian", "15min", (48,), 1.0, 3.0, 12),
    "E4": ExecSet("E4", "ema_cross", "1h", (9, 21), 1.5, 1.5, 12),
    "E5": ExecSet("E5", "donchian", "4h", (20,), 1.0, 1.5, 12),
    "M1": ExecSet("M1", "rsi_cross", "1h", (14, 30, 70), 1.5, 1.5, 12),
    "M2": ExecSet("M2", "rsi_cross", "15min", (14, 25, 75), 1.5, 1.5, 4),
    "M3": ExecSet("M3", "boll_reentry", "1h", (20, 2.0), 1.5, 2.0, 12),
    "M4": ExecSet("M4", "boll_reentry", "15min", (20, 2.0), 1.0, 1.5, 4),
    "M5": ExecSet("M5", "rsi_cross", "4h", (14, 35, 65), 1.5, 1.5, 12),
}
TREND_SETS = ["E1", "E2", "E3", "E4", "E5"]
MR_SETS = ["M1", "M2", "M3", "M4", "M5"]
N_TRIALS_TOTAL = 710
