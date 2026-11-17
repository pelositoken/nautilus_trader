# Token Terminal confluence edge hunt — results and verdict

Snapshot: Token Terminal 2026-11-16 (via connector). Prices: Binance spot 5m,
2022-05-01..2026-11-15. BUILD 2022-09-01..2025-08-31, HOLDOUT
2025-09-01..2026-11-15. Pre-registration: `docs/preregistration.md` (commit
6c02aba, amendments A1-A2 logged before the build run). Freeze of finalists:
commit 602ed35, before any holdout evaluation.

## Verdict (plain English)

**No edge survived. Zero of seven ideas cleared the acceptance bar, and the
fundamental gate did not turn any ordinary intraday entry into a profitable
one after realistic costs.**

- Price action alone loses. All 10 ungated triggers (Donchian breakouts,
  EMA cross, RSI and Bollinger fades on 15m/1h/4h) have negative expectancy
  after 0.10% taker + 2-5 bp slippage per side, in BUILD and HOLDOUT
  (from -0.06R to -0.62R per trade). Costs of ~0.24-0.30% round trip are large
  next to 15m/1h ATR stops; only the 4h trigger comes close to breakeven.
- The gates mostly just trade less. In five ideas (revenue momentum, TVL
  flow, sector rotation, valuation, usage shock) the gate added nothing over a
  random gate with the same pass rate (placebo p 0.39-0.92), and the gated
  holdout P&L was no better than random entries of identical geometry.
- Two gates did carry some information, not enough to pay costs:
  - **I2 DIVERGE** (fees rising while price fell -> mean-reversion longs, and the
    reverse): holdout +0.157R/trade better than the same trigger ungated, and
    +0.170R better than random entries (p = 0.009). But it still loses
    (-0.029R/trade, PF 0.94), its placebo p is 0.091, and its walk-forward OOS
    is -0.12R (BUILD) / -0.23R (HOLDOUT).
  - **I4 UNLOCK, flip mode** (short 4h breakouts only when circulating supply grew
    >= 1% in 7 days): best BUILD result (PF 1.19, +0.074R, 669 trades), holdout
    PF 0.95, -0.020R on 212 trades; gate lift +0.108R, placebo p 0.092; its
    walk-forward continued through HOLDOUT is the only positive one, at
    +0.008R/trade (PF 1.02, 218 trades) — indistinguishable from zero. Lagging
    the gate to 3 or 7 days makes it worse (lag 7 holdout -0.117R), which is
    what a fragile or restatement-sensitive effect looks like.
    NautilusTrader replays it to PF 0.98 / -0.010R on 203 trades.
- Multiple comparisons: 710 trials were run. With that many tries, a few
  build-period winners (9 of 100 I4 variations had PF > 1) are expected by
  chance; the deflated Sharpe of every finalist is 0.000 on HOLDOUT.

**Did fundamentals help at all?** Weakly, in two places (supply emission and
fee/price divergence), by roughly +0.1 to +0.16R per trade relative to the same
trigger — never significant at 5% against the placebo gate, and never enough to
make a losing intraday trigger profitable. For revenue/fee momentum, TVL flow,
sector rotation, valuation and usage shocks the answer is plainly no.

## Results table — HOLDOUT, frozen finalists (header order as specified)

| edge | profit factor | total trade count | exact date range | win rate | avg R per trade | max drawdown (R) | longest losing streak | DSR N=710 / N=100 | walk-forward OOS mean R: BUILD / HOLDOUT | Monte Carlo (bootstrap P(total R<0)) | random-benchmark delta (p) |
|---|---:|---:|---|---:|---:|---:|---:|---|---|---|---|
| I1 REVMOM `I1-g2-k4-E5` | 0.694 | 808 | 2025-09-01..2026-11-15 | 0.391 | -0.162 | 141.3 | 10 | 0.000 / 0.000 | -0.010 / -0.195 | 1.00 | -0.037 (0.883) |
| I2 DIVERGE `I2-g2-k4-M1` | 0.938 | 222 | 2025-09-06..2026-11-15 | 0.455 | -0.029 | 17.2 | 11 | 0.000 / 0.000 | -0.123 / -0.225 | 0.68 | +0.170 (0.009) |
| I3 TVLFLOW `I3-g0-k4-E5` | 0.820 | 70 | 2025-10-02..2026-11-13 | 0.443 | -0.078 | 12.6 | 7 | 0.000 / 0.000 | -0.057 / -0.244 | 0.77 | +0.031 (0.375) |
| I4 UNLOCK `I4-g2-k1-E5` | 0.953 | 212 | 2025-09-01..2026-11-15 | 0.443 | -0.020 | 24.4 | 7 | 0.000 / 0.000 | -0.021 / +0.008 | 0.62 | +0.090 (0.089) |
| I5 ROTATE `I5-g1-k4-E5` | 0.751 | 416 | 2025-09-01..2026-11-15 | 0.421 | -0.130 | 56.9 | 11 | 0.000 / 0.000 | -0.090 / -0.100 | 1.00 | +0.006 (0.455) |
| I6 VALUE `I6-g0-k4-E5` | 0.752 | 532 | 2025-09-01..2026-11-15 | 0.415 | -0.124 | 78.2 | 11 | 0.000 / 0.000 | -0.043 / -0.114 | 1.00 | +0.004 (0.468) |
| I7 SHOCK `I7-g2-k2-E5` | 0.803 | 73 | 2025-09-02..2026-11-15 | 0.384 | -0.107 | 9.8 | 7 | 0.000 / 0.000 | -0.017 / -0.100 | 0.80 | +0.025 (0.416) |

Gate lift vs the same trigger ungated on the same token-days / placebo-gate p:
I1 -0.033/0.922, I2 +0.157/0.091, I3 +0.027/0.514, I4 +0.108/0.092,
I5 -0.000/0.597, I6 +0.004/0.464, I7 +0.024/0.390.
Full tables: `results/results_table_holdout.csv`, `results/holdout_finalists.csv`,
`results/holdout_family.csv` (all 710 trials on HOLDOUT, no reselection),
`results/build_sweep.csv`, `results/build_wfa.csv`, `results/wfa_holdout.csv`,
`results/lag_stress.csv`.

Acceptance bar (all required): every finalist fails #1 (DSR), #2 (PF > 1 on
>= 100 trades), #3 (positive expectancy) and #5 (walk-forward). Only I2 passes
#4 (beats random entry). **Surviving edges: none**, so there is no uncorrelated
set to report. For reference, the finalists' HOLDOUT daily-P&L correlations
(`results/holdout_corr.csv`) show the 4h-breakout finalists are largely one
bet (rho 0.3-0.67 between I1, I4, I5, I6, I7); I2 and I3 are near zero to
the rest.

## DSR math

DSR = Z[(SR - SR0) * sqrt(T-1) / sqrt(1 - skew*SR + (kurt-1)/4 * SR^2)],
SR0 = sqrt(V) * [(1-g) Z^-1(1-1/N) + g Z^-1(1-1/(N e))], g = 0.5772.
SR = non-annualised daily Sharpe of the HOLDOUT daily R series (T = 441 days).
V = variance of BUILD daily Sharpe across trials: 0.110 over all 710
(0.107 over the 700 gated trials). SR0 = 1.049/day for N = 710; for the I4
family, N = 100, SR0 = 0.881/day. Every finalist's holdout SR is negative
(-0.011 to -0.144/day), so DSR = 0.000 under any of these choices.
Caveat on the method: daily Sharpe across sparse and dense strategies has a
very wide spread (the 15m baselines reach -1.7/day), which inflates V and makes
SR0 unrealistically high (~20 annualised). Even a far looser bar would not
change the verdict here, because no finalist is positive out of sample.

## What the validation found wrong with itself

- **Timing-null Monte Carlo is invalid as pre-registered.** It re-enters each
  trade at a random 5m bar on the same UTC day in the same direction. For a
  breakout, the direction is only known after the breakout bar, so random
  entries earlier that day trade with information from later that day. The
  null therefore averages +0.25 to +0.36R and every breakout finalist sits at
  the 0th percentile. It is reported but not used; the random-entry benchmark
  and the gate placebo (both free of this leak) carry the inference.
- **The DSR variance estimate is dominated by dense, very negative baselines**
  (see above). Not decisive here.

## Execution cross-check (NautilusTrader 2.0.0rc9)

The vectorised engine decides when to trade; `nautilus/replicate.py` replays
that schedule through Nautilus' matching engine (market entry, bracket stop
and take-profit, time exit, fees). Ungated E5 on ETH (BUILD): 469 vs 457
trades, -0.054R vs -0.048R. I4 finalist on HOLDOUT, all tokens: 212 vs 203
trades, PF 0.953 vs 0.978, -0.020R vs -0.010R. The research engine is
slightly conservative (same-bar stop/target hits count as losses), and the
conclusions are the same in both engines.

## Data caveats

- Token Terminal was only reachable through the connector: values are rounded
  to 3 significant figures and were hand-copied by subagents. A blind re-query
  of 40 random cells agreed 40/40 (error rate < 7.5% at 95% confidence).
- One snapshot only; a second snapshot for a restatement diff was not taken.
  Visible restatement-type breaks: Injective revenue (2025-11-11 method change),
  Chainlink fees/revenue from 2026-09, NEAR/Avalanche/Sei/Aptos active users.
- No chain-level TVL in Token Terminal; RENDER and ONDO have no fees/revenue.
- Shorts are priced on spot data with spot costs (conservative vs perpetuals);
  funding is ignored.

## If you want to keep hunting (needs a fresh pre-registration)

The holdout used here is spent for these ideas, so any second round needs new
out-of-sample data: paper-trade forward from 2026-11-16, or hold out a
different asset set. The evidence points to costs, not signal, as the binding
constraint. Promising directions, in order:
1. Cheaper execution: maker/limit entries or USDT-M perpetuals (0.02% maker /
   0.05% taker), which roughly halves the round trip. Re-test I2 and I4, the
   only gates with measurable lift, at the 4h/12h horizon.
2. Longer holding (12h-3d) with the same gates: fewer trades per unit of
   signal, so costs weigh less.
3. Combine the two informative gates (supply emission for shorts, fee/price
   divergence for mean reversion). They are nearly uncorrelated (rho -0.02).
