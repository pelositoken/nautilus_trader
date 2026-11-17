"""
Live circulating-supply source for paper trading: CoinGecko public API
(market_caps / prices, daily). Token Terminal is not available after the trial.

`fetch_supply(days)` -> DataFrame(date x token) of circulating supply, where the
value for date D is CoinGecko's daily point stamped D 00:00 UTC.
"""

from __future__ import annotations

import json
import time
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen

import pandas as pd


COINGECKO_IDS = {
    "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin", "NEAR": "near", "UNI": "uniswap",
    "ENA": "ethena", "TRX": "tron", "SUI": "sui", "LINK": "chainlink", "AVAX": "avalanche-2",
    "AAVE": "aave", "INJ": "injective-protocol", "FIL": "filecoin", "ARB": "arbitrum",
    "CRV": "curve-dao-token", "APT": "aptos", "JUP": "jupiter-exchange-solana", "TIA": "celestia",
    "POL": "polygon-ecosystem-token", "CAKE": "pancakeswap-token", "OP": "optimism", "RAY": "raydium",
    "ETHFI": "ether-fi", "SEI": "sei-network", "LDO": "lido-dao", "ATOM": "cosmos", "PENDLE": "pendle",
    "JTO": "jito-governance-token",
}
URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=usd&days={days}&interval=daily"


def _get(url: str, retries: int = 5) -> dict:
    for i in range(retries):
        try:
            with urlopen(Request(url, headers={"User-Agent": "research-client"}), timeout=60) as r:
                return json.load(r)
        except HTTPError as e:
            if e.code == 429:  # rate limited: back off
                time.sleep(20 * (i + 1))
                continue
            raise
        except Exception:
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"CoinGecko request failed: {url}")


def fetch_supply(days: int = 40, tokens: list[str] | None = None, pause: float = 2.5) -> pd.DataFrame:
    out = {}
    for tok in tokens or list(COINGECKO_IDS):
        d = _get(URL.format(id=COINGECKO_IDS[tok], days=days))
        px = pd.Series({pd.Timestamp(t, unit="ms").normalize(): v for t, v in d.get("prices", [])})
        mc = pd.Series({pd.Timestamp(t, unit="ms").normalize(): v for t, v in d.get("market_caps", [])})
        s = (mc / px).where((mc > 0) & (px > 0))
        out[tok] = s[~s.index.duplicated(keep="first")]
        time.sleep(pause)
    return pd.DataFrame(out).sort_index()
