# Pre-registration — round 2: supply-emission short (I4-g2-k1-E5) refinement

Status: FROZEN at the git commit that adds this file. Written after the
BUILD-only diagnosis (`scripts/r2_diagnose.py`, `results/r2_diag_*.csv`) and
before any of the 100 variations below was evaluated on any period.

## 0. What is already known (honest starting point)
- Round 1 selected I4-g2-k1-E5 on BUILD (PF 1.19, +0.074R, 669 trades) and it
  failed HOLDOUT (PF 0.95, -0.020R, 212 trades). That aggregate holdout result
  has been seen. HOLDOUT trade-level features have NOT been looked at: the
  diagnosis loaded BUILD trades only. HOLDOUT is therefore a *second-look*
  holdout for round 2: valid against the diagnosis, contaminated by the
  knowledge that the base strategy lost there. All holdout numbers below are
  reported with that label.
- Cumulative trials: 710 (round 1) + 100 (round 2) = 810.

## 1. Base strategy (unchanged)
Short only. Trigger: 4h close < min(low of prior 20 4h bars). Gate: 7-day
circulating-supply growth ln(S[t-1]/S[t-8]) >= v (supply lagged 1 day).
Entry next 5m open; stop = s x ATR(14, 4h); target = t x stop distance;
time exit 12h; same-bar stop/target = loss; 0.10% taker + 2-5 bp slippage per
side; one position per token. Universe: 28 tokens.

## 2. Diagnosis findings used (BUILD only, 669 trades, 29 features)
- BTC volatility regime m_atr_regime = ATR14(4h)/median(ATR14 over 30d):
  monotonic, Q1 +0.29R ... Q5 -0.21R, Spearman -0.13 (CI -0.20..-0.06).
- Token volatility regime f_atr_regime (same definition on the token): Q1 +0.31R,
  Q5 -0.18R, Spearman -0.08 (CI -0.15..0.00).
- Exhaustion f_rel_7d = token 7d log return - BTC 7d log return: Q1
  (<= -0.185) -0.22R, other quintiles +0.13..+0.19R.
- Revenue trend u_rev_r = mean7/mean30 of revenue: not significant, Q1 best;
  kept as a thesis-consistent fundamental filter at a non-fitted threshold (1.0).
- Not used: hour of day / weekday (6-7 buckets, high data-mining risk), funding,
  breakout depth, RSI, supply-jump size, fees/DAU trend (all insignificant).

## 3. The 100 variations = 5 x 2 x 2 x 5 (thresholds are round numbers)
V. volatility filter (skip the trade if the condition fails):
   V0 off; V1 m_atr_regime <= 1.25; V2 m_atr_regime <= 1.00;
   V3 f_atr_regime <= 1.25; V4 m_atr_regime <= 1.25 AND f_atr_regime <= 1.25
X. exhaustion filter: X0 off; X1 f_rel_7d >= -0.20
R. revenue filter: R0 off; R1 u_rev_r < 1.00 (missing revenue -> trade skipped)
G. gate threshold / geometry:
   G1 v=1%, s=1.0, t=1.5 (base); G2 v=1%, s=1.0, t=1.0; G3 v=1%, s=1.5, t=1.5;
   G4 v=2%, s=1.0, t=1.5; G5 v=0.5%, s=1.0, t=1.5
Variation id: R2-V{v}X{x}R{r}G{g}. R2-V0X0R0G1 reproduces the base.
Filters use features known at the 4h signal-bar close (`scripts/r2_features.py`).

## 4. Selection rule
FINALIST = the variation with the highest BUILD annualised Sharpe of daily R
among variations with >= 150 BUILD trades.

## 5. Overfitting tests (all reported; pass criteria in §6)
1. CSCV / PBO (Bailey et al. 2014) on the BUILD daily-R matrix (100 x days),
   S = 16 contiguous blocks, all C(16,8) = 12,870 splits, metric = Sharpe.
   Also reported on the full BUILD+HOLDOUT matrix.
2. Deflated Sharpe: BUILD and HOLDOUT, N = 100 (V = variance of BUILD daily
   Sharpe across the 100) and N = 810 (same V).
3. Walk-forward: 12-month IS / 3-month OOS, select by IS Sharpe (>= 30 IS
   trades) among the 100, through BUILD and then through HOLDOUT.
4. Filter placebo: for the finalist, remove the same number of trades from the
   unfiltered same-G strategy at random (2,000 draws); p = share of random
   removals with mean R >= the filtered mean R. BUILD and HOLDOUT.
5. Random-entry benchmark (same geometry, direction, count; 1,000 draws).
6. Entry-delay null (replaces round 1's invalid timing null): each trade
   re-entered at a uniformly random 5m bar 0-4h AFTER the signal, same
   direction/geometry (1,000 draws); report the real trades' percentile.
7. Trade bootstrap (5,000): P(total R < 0), 5/50/95% total R and max drawdown.
8. Neighbourhood: all variations differing from the finalist in one dimension:
   share with mean R > 0 and median Sharpe (plateau vs spike).
9. Leave-one-token-out mean R range; result without the top-3 tokens.
10. Stress: costs x1.5; fundamentals lagged 2 and 3 days.
11. NautilusTrader replay of the finalist on HOLDOUT.

## 6. Acceptance (finalist), all required
- PBO (BUILD) < 0.20.
- HOLDOUT (second look): PF > 1 on >= 100 trades, mean R > 0, beats random
  entry (p < 0.05), filter placebo p < 0.05, DSR (N = 810) >= 0.95.
- Walk-forward OOS mean R > 0 over BUILD-OOS and HOLDOUT-OOS.
- Survives costs x1.5 with mean R > 0 on BUILD and HOLDOUT.
Anything weaker is reported as "not demonstrated", with the reason.
