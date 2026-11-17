# Forward paper test — pre-registration

Frozen at the commit that adds this file, before the first live bar is processed.
No rule, threshold or cost assumption below may change during the test; any
change restarts the test from zero trades.

## Variations (chosen by the user from round 2; see docs/report_round2.md)
All: short only; trigger = 4h close below the lowest low of the prior 20 4h
bars; gate = 7-day circulating-supply growth >= 1%; exhaustion filter = skip if
the token's 7-day log return minus BTC's is below -0.20; entry at the open of
the first 5m bar after the 4h close; same-bar stop/target counts as a stop;
12h time exit; one open position per token per variation; 28-token universe.

| id | extra filter | stop | target | backtest mean R: full 2022-09..2026-11 / holdout 2025-09..2026-11 |
|---|---|---|---|---|
| R2-V0X1R0G1 | — | 1.0 x ATR14(4h) | 1.5R | build +0.127, holdout -0.009 |
| R2-V0X1R0G3 | — | 1.5 x ATR14(4h) | 1.5R | build +0.067, holdout +0.029 |
| R2-V2X1R0G1 | BTC ATR14(4h) / 30-day median ATR <= 1.00 | 1.0 x ATR | 1.5R | build +0.236, holdout -0.015 |

## Data and known differences from the backtest
- Prices: Binance public spot klines (data-api.binance.vision), 4h for signals,
  5m for exits — same exchange and construction as the backtest.
- Circulating supply: CoinGecko (market cap / price, daily), because Token
  Terminal access ended with the trial. Gate uses the points stamped D-1 and
  D-8 for an entry on day D (about a 2-day lag; the backtest used 1 day).
  Over 2025-11..2026-11 the CoinGecko gate agreed with Token Terminal's on 98%
  of token-days and on 81% of the days Token Terminal's gate was on.
  Every CoinGecko snapshot is kept in state/supply_snapshots.csv.
- Implementation parity: replaying 2026-10-01..2026-11-15 with Token Terminal
  supply reproduces the research engine's 44 trades exactly (same entries, same R).

## Costs
Primary: Binance spot taker 0.10% + slippage (2 bp ETH/SOL/BNB, 5 bp others)
per side — the backtest model. Also logged: perpetual taker 0.05% + slippage.

## Evaluation (per variation, Bonferroni for 3 variations)
- Verdict when the variation has >= 100 closed trades (expected roughly 7
  months for the two V0 variations; R2-V2X1R0G1 trades less, roughly 12-15 months).
- PASS requires all of: mean R > 0 under primary costs; profit factor > 1.10;
  one-sided t-test of mean R > 0 with p < 0.0167 (0.05 / 3).
- STOP early (that variation only) if, after >= 50 closed trades, mean R < -0.15
  or cumulative R <= -15.
- Reported alongside: perpetual-cost mean R, gate disagreement with the
  backtest's lag, and the backtest's expected mean R.
