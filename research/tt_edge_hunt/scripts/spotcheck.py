"""
Integrity spot check of the connector export.

`sample`: draw random saved cells (stratified by metric) -> data/tt/spotcheck_sample.csv
`compare`: read data/tt/spotcheck_requery.csv (token,metric,date,requery_value written
           from independent single-project re-queries) and report agreement. Values are
           3 s.f. on both sides, so agreement means |a-b|/max(|a|,|b|) <= 1%.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TT = ROOT / "data" / "tt"
NAMES = {
    "ETH": "Ethereum", "SOL": "Solana", "BNB": "BNB Chain", "NEAR": "NEAR Protocol", "UNI": "Uniswap",
    "ENA": "Ethena", "TRX": "Tron", "SUI": "Sui", "LINK": "Chainlink", "AVAX": "Avalanche",
    "AAVE": "Aave", "INJ": "Injective", "FIL": "Filecoin", "ARB": "Arbitrum One", "CRV": "Curve",
    "APT": "Aptos", "JUP": "Jupiter", "TIA": "Celestia", "POL": "Polygon", "CAKE": "PancakeSwap",
    "OP": "OP Mainnet", "RAY": "Raydium", "ETHFI": "Ether.fi", "SEI": "Sei Network",
    "LDO": "Lido Finance", "ATOM": "Cosmos Hub", "PENDLE": "Pendle", "JTO": "Jito",
}
PER_METRIC = {"fees": 10, "revenue": 10, "tvl": 6, "user_dau": 7, "token_supply_circulating": 7}


def sample() -> None:
    df = pd.read_csv(TT / "fundamentals_long.csv", parse_dates=["date"])
    df = df[df.token.isin(NAMES) & (df.value != 0)]
    rng = np.random.default_rng(20261116)
    parts = [g.iloc[rng.choice(len(g), size=min(PER_METRIC[m], len(g)), replace=False)]
             for m, g in df.groupby("metric") if m in PER_METRIC]
    out = pd.concat(parts)
    out["project"] = out.token.map(NAMES)
    out[["token", "project", "metric", "date", "value"]].to_csv(TT / "spotcheck_sample.csv", index=False)
    print(f"{len(out)} cells sampled")


def compare() -> None:
    s = pd.read_csv(TT / "spotcheck_sample.csv", parse_dates=["date"])
    r = pd.read_csv(TT / "spotcheck_requery.csv", parse_dates=["date"])
    m = s.merge(r, on=["token", "metric", "date"], how="left")
    rel = (m.value - m.requery_value).abs() / np.maximum(m.value.abs(), m.requery_value.abs())
    m["agree"] = rel <= 0.01
    m.to_csv(TT / "spotcheck_result.csv", index=False)
    n = m.requery_value.notna().sum()
    print(f"re-queried {n}/{len(m)}; agree {int(m.agree.sum())}/{n}")
    print(m[~m.agree & m.requery_value.notna()].to_string(index=False))


if __name__ == "__main__":
    {"sample": sample, "compare": compare}[sys.argv[1]]()
