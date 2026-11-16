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

## Windows (quarterly; 5 projects x 92 days per call is the tested-safe size)
- Q01 2022-06-01..2022-08-31
- Q02 2022-09-01..2022-11-30
- Q03 2022-12-01..2023-02-28
- Q04 2023-03-01..2023-05-31
- Q05 2023-06-01..2023-08-31
- Q06 2023-09-01..2023-11-30
- Q07 2023-12-01..2024-02-29
- Q08 2024-03-01..2024-05-31
- Q09 2024-06-01..2024-08-31
- Q10 2024-09-01..2024-11-30
- Q11 2024-12-01..2025-02-28
- Q12 2025-03-01..2025-05-31
- Q13 2025-06-01..2025-08-31
- Q14 2025-09-01..2025-11-30
- Q15 2025-12-01..2026-02-28
- Q16 2026-03-01..2026-05-31
- Q17 2026-06-01..2026-08-31
- Q18 2026-09-01..2026-11-15

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
`data/tt_raw/{metric}__{group}__{window}.md` (window = Q01..Q18). Do not reformat, convert, round,
fix or fill anything. If a response is truncated, not a table, or missing
days/columns, re-ask for a shorter sub-window and save it as
`{metric}__{group}__{window}{a|b}.md`. The parser handles everything else.

## Failures
On a timeout / "fetch failed" / classifier error, retry the same call up to 3
times total. If it still fails, append one line
`{metric},{group},{window},FAILED,{error}` to `data/tt_raw/_failures.csv` and
move on. Never write a placeholder data file.
