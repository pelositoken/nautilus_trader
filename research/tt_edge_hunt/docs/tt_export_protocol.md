# Token Terminal export protocol (connector-based)

Snapshot date: 2026-11-16 (data through 2026-11-15). The connector
(`mcp__Token_Terminal__research`) is the only access path; values are rounded
by the connector to 3 significant figures ("$1.23M"). This is a documented
precision limit; gates use trends/ratios, not exact values.

## Metrics (Token Terminal keys)
fees, revenue, tvl, user_dau, token_supply_circulating

## Project groups (5 per call, pivoted as columns)
- G1: Ethereum, Solana, BNB Chain, NEAR Protocol, Uniswap
- G2: Ethena, Tron, Sui, Chainlink, Avalanche
- G3: Aave, Injective, Filecoin, Ondo Finance, Arbitrum One
- G4: Curve, Aptos, Jupiter, Celestia, Render Network
- G5: Polygon, PancakeSwap, OP Mainnet, Raydium, Ether.fi
- G6: Sei Network, Lido Finance, Cosmos Hub, Pendle, Jito

## Windows
W01 2021-12-01..2022-05-31, W02 2022-06-01..2022-11-30,
W03 2022-12-01..2023-05-31, W04 2023-06-01..2023-11-30,
W05 2023-12-01..2024-05-31, W06 2024-06-01..2024-11-30,
W07 2024-12-01..2025-05-31, W08 2025-06-01..2025-11-30,
W09 2025-12-01..2026-05-31, W10 2026-06-01..2026-11-15

## Query template
"Daily {metric_label} for {p1}, {p2}, {p3}, {p4} and {p5} from {start} to
{end}, one row per calendar day, no aggregation, no gaps (write - for a day
with no data). Put all projects as columns in a single table:
Date | {p1} | {p2} | {p3} | {p4} | {p5}. Skip the metric definitions."

metric_label: fees -> "fees"; revenue -> "revenue"; tvl -> "total value
locked (TVL)"; user_dau -> "active users (daily)"; token_supply_circulating ->
"circulating supply (token count)".

## Saving rule (fidelity)
Write the connector's response VERBATIM (the whole table, unchanged) to
`data/tt_raw/{metric}__{group}__{window}.md`. Do not reformat, convert, round,
fix or fill anything. If a response is truncated, not a table, or missing
days/columns, re-ask for a shorter sub-window and save it as
`{metric}__{group}__{window}{a|b}.md`. The parser handles everything else.
