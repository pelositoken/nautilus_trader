# Round 2 — supply-emission short: loss diagnosis, 100 variations, overfitting tests

Strategy under study (round-1 I4-g2-k1-E5): short a token when its 4h close
breaks below the prior 20 4h lows, only if its circulating supply grew >= 1%
over 7 days (supply lagged 1 day). Stop 1.0 x ATR(4h), target 1.5R, 12h time
exit, 0.10% taker + 2-5 bp slippage per side, 28 tokens.

Process: BUILD-only diagnosis -> pre-registration of 100 variations
(`docs/preregistration_round2.md`, commit 8130c12) -> BUILD sweep and finalist
freeze (commit aed9842) -> HOLDOUT second look and overfitting tests.

## Verdict

**Not demonstrated. The refinements are overfit.** The 100 variations all
looked good on BUILD (100/100 profitable, best PF 1.73), but the filters were
designed on that same data. On HOLDOUT the selected variation lost more than
the unrefined strategy, the build ranking of variations had no relationship
to holdout ranking (Spearman 0.03), and the filters did worse than randomly
deleting the same number of trades.

What survived contact with new data:
- **Exhaustion matters.** Shorting tokens already >~20% weaker than BTC over
  the past 7 days loses in both periods (bottom-quintile mean R -0.22 BUILD,
  -0.27 HOLDOUT). Removing them improved all five exit geometries on HOLDOUT,
  but only by +0.01 to +0.03R per trade, i.e. from slightly negative to ~zero.
- **Entry timing matters.** Entering at the signal bar beats a random 0-4h
  delay at the 98th-99th percentile in both periods.
- **The trigger beats random entries** of identical geometry (BUILD p < 0.001,
  HOLDOUT p = 0.089). There is some short-horizon information in supply-gated
  breakdowns; it is smaller than trading costs out of sample.

What did not survive:
- **Volatility regime** — the strongest BUILD factor (monotonic, Spearman
  -0.13) reversed on HOLDOUT: the highest-BTC-volatility quintile was the best
  (+0.42R). Filtering on it removed the best holdout trades.
- Revenue trend, supply-jump size/recency, funding, RSI, breakout depth,
  hour of day: no consistent effect.

## 1. What led to losing setups (BUILD only, 669 trades, 29 features)

| factor (known at signal close) | BUILD Spearman with R (95% CI) | quintile mean R, Q1 -> Q5 | HOLDOUT (post-hoc) |
|---|---|---|---|
| BTC volatility regime (ATR / 30d median ATR) | -0.13 (-0.20, -0.06) | +0.29, +0.24, +0.13, -0.09, -0.21 | reversed: +0.13 ... +0.42 |
| BTC ATR % | -0.12 (-0.19, -0.04) | +0.31 ... -0.26 | — |
| Token 7d return minus BTC 7d return | +0.08 (+0.01, +0.16) | -0.22, +0.14, +0.19, +0.14, +0.13 | held: -0.27 ... +0.17 |
| Token volatility regime | -0.08 (-0.15, 0.00) | +0.31 ... -0.18 | flat |
| Revenue trend (7d/30d) | -0.04 (n.s.) | non-monotonic | flat |
| Funding (last, 3d) | ~0 (n.s.) | flat | — |

29 features tested; about 1.5 expected "significant" by chance; 4 were, 3 of
them the same volatility idea. Other diagnostics:
- Exits: 27% stop (-1.09R), 27% target (+1.40R), 46% time exit (-0.01R).
- 42% of losing trades first reached +0.5R before reversing (median losing MFE
  +0.41R), which motivated the 1.0R-target geometry.
- Costs consume 0.093R per trade (gross +0.167R -> net +0.074R).
- Concentration: CAKE, ENA and SUI supply ~65% of BUILD profit; without them
  +0.033R. Hour-of-day spread (08/16 UTC strong, 12 UTC weak) was deliberately
  not used (6 buckets, classic data-mining).
Files: `results/r2_diag_features.csv`, `r2_diag_quintiles.csv`, `r2_diag_breakdowns.csv`.

## 2. The 100 variations

5 volatility filters x 2 exhaustion x 2 revenue x 5 gate/geometry
(round-number thresholds; definitions in the pre-registration):
V0 off / V1 BTC vol regime <= 1.25 / V2 <= 1.00 / V3 token vol regime <= 1.25 /
V4 V1 and V3; X1 skip if token is > 20% weaker than BTC over 7d; R1 trade only
if revenue 7d/30d < 1; G1 base, G2 target 1.0R, G3 stop 1.5 ATR, G4 gate 2%,
G5 gate 0.5%. All 100 on BUILD and HOLDOUT: `results/r2_build_sweep.csv`,
`results/r2_holdout_family.csv`.

## 3. Finalist and results (header order as in round 1)

Finalist (max BUILD Sharpe, n >= 150): **R2-V1X1R0G2** = BTC vol regime <= 1.25,
exhaustion filter, target 1.0R.

| | profit factor | trades | date range | win rate | avg R | max DD (R) | longest losing streak | DSR N=100 / N=810 | random-entry delta (p) | filter placebo p | bootstrap P(total<0) |
|---|---:|---:|---|---:|---:|---:|---:|---|---|---|---|
| Finalist, BUILD | 1.441 | 502 | 2022-09-05..2025-08-22 | 0.594 | +0.140 | 8.9 | 5 | 0.903 / 0.792 | +0.246 (0.000) | 0.000 | 0.000 |
| Finalist, HOLDOUT | 0.830 | 160 | 2025-09-01..2026-11-10 | 0.488 | -0.073 | 25.8 | 5 | 0.029 / 0.015 | +0.029 (0.326) | 0.984 | 0.861 |
| Base, BUILD | 1.192 | 669 | 2022-09-05..2025-08-22 | 0.487 | +0.074 | 13.5 | 7 | 0.394 / 0.236 | +0.185 (0.000) | n/a | 0.022 |
| Base, HOLDOUT | 0.953 | 212 | 2025-09-01..2026-11-15 | 0.443 | -0.020 | 24.4 | 7 | 0.110 / 0.069 | +0.090 (0.089) | n/a | 0.619 |

NautilusTrader replay of the finalist on HOLDOUT: 159 trades, PF 0.824,
-0.078R (vectorised engine: 160, 0.830, -0.073R).

## 4. Overfitting tests

| test | result | reading |
|---|---|---|
| PBO, CSCV 16 blocks, 12,870 splits, BUILD | 0.268 (IS->OOS Sharpe slope -0.97) | fails pre-registered bar (< 0.20) |
| PBO, BUILD + HOLDOUT | 0.591 | selecting the in-sample best is worse than picking at random |
| Rank correlation of 100 variations, BUILD vs HOLDOUT mean R | 0.03 | BUILD ranking carries no information |
| Walk-forward (12m IS / 3m OOS) | BUILD OOS +0.158R (294 trades, PF 1.47); HOLDOUT OOS +0.036R (50 trades, PF 1.10) | positive but tiny and thin out of sample |
| Neighbourhood (10 one-step neighbours) | BUILD 10/10 positive, median Sharpe 1.33; HOLDOUT 2/10, median -0.63 | a BUILD plateau that collapsed |
| Filter placebo (random removal of the same count) | BUILD p 0.000; HOLDOUT p 0.984 | filters fitted to BUILD noise |
| Random-entry benchmark | BUILD +0.246R (p 0.000); HOLDOUT +0.029R (p 0.33) | |
| Entry-delay null (0-4h later) | 98th (BUILD) / 99th (HOLDOUT) percentile | timing of entry is real |
| Leave-one-token-out (HOLDOUT) | -0.098 .. -0.049R | no single token drives the loss |
| Costs x1.5 | BUILD +0.089R; HOLDOUT -0.126R | |
| Fundamentals lagged 2 / 3 days | BUILD +0.097 / +0.059R; HOLDOUT -0.033 / -0.046R | decays with lag |
| HOLDOUT family | 30/100 variations positive, median -0.044R | |

Acceptance (pre-registered): fails PBO, holdout PF/expectancy, random-entry,
filter placebo, DSR and the cost stress. **No variation is accepted.**

## 5. Recommendation

Treat the supply-emission short as a weak, regime-dependent effect, not a
tradeable edge. Its holdout P&L alternates sign by quarter (+0.35, -0.25,
+0.29, -0.21, +0.17, -0.14R per trade). If you want to keep it alive, the only
defensible next step is a forward paper test, pre-registered now, of the
simplest version that held in both periods: base gate + exhaustion filter,
no volatility filter, with cheaper execution (perpetual maker/taker fees),
judged on >= 100 new trades. All historical data for this question has been
used; further tuning on it would only add overfitting.
