# Data inventory

## Token Terminal export
- Source: Token Terminal connector (`research` tool), the only access path available.
- Snapshot date: 2026-11-16 (data through 2026-11-15). Single snapshot; a second snapshot for restatement comparison was not possible within the trial budget.
- Coverage requested: 2022-06-01 .. 2026-11-15, daily, in 18 quarterly windows.
- Raw responses saved verbatim: 482 files in `data/tt_raw/` (fees 110, rev 109, tvl 49, dau 110, supply 104).
- Parsed: `data/tt/fundamentals_long.csv`; validation log `data/tt/validation.txt`.
- Precision: connector rounds to ~3 significant figures.
- Integrity: 40 randomly sampled cells re-queried blind, one project at a time: 40/40 agree within 1% (`data/tt/spotcheck_result.csv`).
- Not covered by Token Terminal: chain-level TVL (TVL is apps only); RENDER fees/revenue; ONDO fees/revenue; Filecoin and ONDO active users; Jupiter active users; Uniswap revenue before late 2025.
- Restatement-prone series observed: Injective revenue (method change 2025-11-11), Chainlink fees/revenue (near-zero daily with weekly spikes from 2026-09), Ethena fees/revenue (sparse daily with spikes), NEAR/Avalanche/Sei/Aptos active users (level breaks). Amendments A1/A2 in the pre-registration handle zeros and supply artefacts.

## Intraday data
- Binance spot USDT 5m klines from data.binance.vision (bulk archive), 2022-05-01 .. 2026-11-15; MATIC->POL and RNDR->RENDER stitched. Stored as Parquet in `data/ohlcv/` (git-ignored; rebuild with `scripts/download_binance_klines.py`).

## Universe (28 of 30 candidates)

| token | sector | in | reason | Binance from | med. daily vol $M | fees days | rev days | tvl days | dau days | supply days |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| ETH | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 876.9 | 1629 | 1629 | 0 | 1629 | 1629 |
| SOL | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 294.9 | 1629 | 1629 | 0 | 1629 | 1629 |
| BNB | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 127.0 | 1629 | 1629 | 0 | 1629 | 1629 |
| NEAR | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 34.5 | 1629 | 1629 | 0 | 1629 | 1628 |
| UNI | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 17.6 | 1629 | 324 | 1629 | 1629 | 1629 |
| ENA | APPS | yes | TT fees/revenue + Binance 5m | 2024-04-02 | 42.5 | 1092 | 1092 | 1092 | 655 | 533 |
| TRX | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 37.7 | 1629 | 1629 | 0 | 1629 | 1266 |
| SUI | CHAINS | yes | TT fees/revenue + Binance 5m | 2023-05-03 | 67.8 | 1293 | 1293 | 0 | 1293 | 1020 |
| LINK | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 37.9 | 1264 | 1264 | 0 | 1232 | 1266 |
| AVAX | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 42.2 | 1629 | 1629 | 0 | 1629 | 1266 |
| AAVE | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 16.7 | 1629 | 1629 | 1629 | 1629 | 1629 |
| INJ | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 12.9 | 1629 | 1629 | 0 | 1629 | 1629 |
| FIL | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 18.5 | 1629 | 1629 | 0 | 0 | 1619 |
| ONDO | APPS | no | no TT fees or revenue | 2025-04-11 | 11.1 | 0 | 0 | 0 | 0 | 667 |
| ARB | CHAINS | yes | TT fees/revenue + Binance 5m | 2023-03-23 | 32.4 | 1538 | 1538 | 0 | 1538 | 1334 |
| CRV | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 11.2 | 1629 | 1629 | 1629 | 1629 | 1448 |
| APT | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-10-19 | 20.6 | 1490 | 1490 | 0 | 1496 | 1301 |
| JUP | APPS | yes | TT fees/revenue + Binance 5m | 2024-01-31 | 8.6 | 1278 | 479 | 1217 | 0 | 839 |
| TIA | CHAINS | yes | TT fees/revenue + Binance 5m | 2023-10-31 | 16.3 | 1112 | 1112 | 0 | 1112 | 625 |
| RENDER | APPS | no | no TT fees or revenue | 2022-05-01 | 11.2 | 0 | 0 | 0 | 0 | 1448 |
| POL | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 23.6 | 1629 | 1629 | 0 | 1629 | 802 |
| CAKE | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 6.6 | 1629 | 1629 | 1629 | 1629 | 1592 |
| OP | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-06-01 | 20.3 | 1629 | 1629 | 0 | 1629 | 1348 |
| RAY | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 3.4 | 1629 | 1629 | 1629 | 1629 | 1606 |
| ETHFI | APPS | yes | TT fees/revenue + Binance 5m | 2024-03-18 | 14.3 | 1280 | 910 | 1243 | 1235 | 842 |
| SEI | CHAINS | yes | TT fees/revenue + Binance 5m | 2023-08-15 | 19.0 | 586 | 586 | 0 | 903 | 916 |
| LDO | APPS | yes | TT fees/revenue + Binance 5m | 2022-05-09 | 10.6 | 1629 | 1629 | 1629 | 1629 | 1356 |
| ATOM | CHAINS | yes | TT fees/revenue + Binance 5m | 2022-05-01 | 11.1 | 1629 | 1629 | 0 | 1626 | 1356 |
| PENDLE | APPS | yes | TT fees/revenue + Binance 5m | 2023-07-03 | 9.8 | 1449 | 1449 | 1454 | 1449 | 647 |
| JTO | APPS | yes | TT fees/revenue + Binance 5m | 2023-12-07 | 6.3 | 1415 | 616 | 1476 | 1487 | 625 |
