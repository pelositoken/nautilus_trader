"""
Deliverable 1: data inventory. Writes docs/data_inventory.md and
data/universe.csv from the parsed Token Terminal snapshot and the Binance files.

Universe rule (preregistration §2): Token Terminal fees OR revenue present, and
Binance 5m data present.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from edgehunt.config import SECTORS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.data import load_5m  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402


METRICS = ["fees", "revenue", "tvl", "user_dau", "token_supply_circulating"]
SHORT = {"fees": "fees", "revenue": "rev", "tvl": "tvl", "user_dau": "dau", "token_supply_circulating": "supply"}


def main() -> None:
    F = load_fundamentals()  # applies amendments A1/A2
    raw_files = sorted((ROOT / "data" / "tt_raw").glob("*.md"))
    rows = []
    for t in TOKENS:
        df5 = load_5m(t)
        row = {"token": t, "sector": next(s for s, v in SECTORS.items() if t in v),
               "binance_first": df5.index[0].strftime("%Y-%m-%d"), "binance_bars": len(df5),
               "median_daily_quote_vol_musd": round(df5["quote_volume"].resample("1D").sum().median() / 1e6, 1)}
        for m in METRICS:
            s = F[m][t].dropna() if (m in F and t in F[m]) else pd.Series(dtype=float)
            row[f"{SHORT[m]}_days"] = len(s)
            row[f"{SHORT[m]}_first"] = s.index.min().strftime("%Y-%m-%d") if len(s) else ""
        has_flow = row["fees_days"] > 0 or row["rev_days"] > 0
        row["in_universe"] = has_flow
        row["reason"] = ("TT fees/revenue + Binance 5m" if has_flow else "no TT fees or revenue")
        rows.append(row)
    u = pd.DataFrame(rows)
    u.to_csv(ROOT / "data" / "universe.csv", index=False)

    per_metric = {m: sum(1 for f in raw_files if f.name.startswith(m + "__")) for m in METRICS}
    lines = [
        "# Data inventory",
        "",
        "## Token Terminal export",
        "- Source: Token Terminal connector (`research` tool), the only access path available.",
        "- Snapshot date: 2026-11-16 (data through 2026-11-15). Single snapshot; a second "
        "snapshot for restatement comparison was not possible within the trial budget.",
        "- Coverage requested: 2022-06-01 .. 2026-11-15, daily, in 18 quarterly windows.",
        f"- Raw responses saved verbatim: {len(raw_files)} files in `data/tt_raw/` "
        + "(" + ", ".join(f"{SHORT[m]} {n}" for m, n in per_metric.items()) + ").",
        "- Parsed: `data/tt/fundamentals_long.csv`; validation log `data/tt/validation.txt`.",
        "- Precision: connector rounds to ~3 significant figures.",
        "- Integrity: 40 randomly sampled cells re-queried blind, one project at a time: "
        "40/40 agree within 1% (`data/tt/spotcheck_result.csv`).",
        "- Not covered by Token Terminal: chain-level TVL (TVL is apps only); "
        "RENDER fees/revenue; ONDO fees/revenue; Filecoin and ONDO active users; "
        "Jupiter active users; Uniswap revenue before late 2025.",
        "- Restatement-prone series observed: Injective revenue (method change 2025-11-11), "
        "Chainlink fees/revenue (near-zero daily with weekly spikes from 2026-09), "
        "Ethena fees/revenue (sparse daily with spikes), NEAR/Avalanche/Sei/Aptos active "
        "users (level breaks). Amendments A1/A2 in the pre-registration handle zeros and "
        "supply artefacts.",
        "",
        "## Intraday data",
        "- Binance spot USDT 5m klines from data.binance.vision (bulk archive), "
        "2022-05-01 .. 2026-11-15; MATIC->POL and RNDR->RENDER stitched. Stored as Parquet "
        "in `data/ohlcv/` (git-ignored; rebuild with `scripts/download_binance_klines.py`).",
        "",
        f"## Universe ({int(u.in_universe.sum())} of {len(u)} candidates)",
        "",
        "| token | sector | in | reason | Binance from | med. daily vol $M | fees days | rev days | tvl days | dau days | supply days |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in u.itertuples():
        lines.append(f"| {r.token} | {r.sector} | {'yes' if r.in_universe else 'no'} | {r.reason} | "
                     f"{r.binance_first} | {r.median_daily_quote_vol_musd} | {r.fees_days} | {r.rev_days} | "
                     f"{r.tvl_days} | {r.dau_days} | {r.supply_days} |")
    (ROOT / "docs" / "data_inventory.md").write_text("\n".join(lines) + "\n")
    print(u[["token", "in_universe", "fees_days", "rev_days", "tvl_days", "dau_days", "supply_days"]].to_string(index=False))


if __name__ == "__main__":
    main()
