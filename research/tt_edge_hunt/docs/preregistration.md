# Pre-registration — Token Terminal confluence edge hunt

Status: FROZEN at the git commit that adds this file. Written before any price
data was analysed and before any backtest was run. Any later change is made in
a separate, dated amendment section at the bottom, never by editing above it.

Disclosure: before freezing, the author saw three small raw fee tables during
connector tests (Aave Jan 2023; Aave/Uniswap/Lido Q1 2024; ETH/SOL/BNB/NEAR/UNI
Jun–Aug 2024). No prices, no signals, no results.

## 1. Thesis and null
H1: a lagged Token Terminal (TT) daily fundamental gate raises the expectancy
of an ordinary intraday price-action entry.
H0: the gate adds nothing — gated trades are no better than (a) the same
trigger ungated, (b) the same trigger under a random gate with the same pass
rate, (c) random entries with identical geometry.

## 2. Data
- Fundamentals: TT via connector, snapshot 2026-11-16, daily, 2022-06-01 ..
  2026-11-15. Metrics: fees, revenue, tvl, user_dau, token_supply_circulating.
  Values rounded to 3 s.f. by the connector (precision limit, documented).
- Prices: Binance spot USDT 5m klines (data.binance.vision), 2022-05-01 ..
  2026-11-15. 15m/1h/4h bars are resampled from 5m (left-closed, UTC).
- Universe: the 30 candidates in `docs/tt_export_protocol.md` minus any token
  that lacks BOTH fees and revenue in TT, or lacks Binance 5m data. A token is
  eligible on a given day only if it has >= 60 days of price history and the
  metric(s) the gate needs are present for the lookback.

## 3. Splits
- Warm-up: 2022-06-01 .. 2022-08-31 (indicators only, no trades).
- BUILD: 2022-09-01 .. 2025-08-31.
- HOLDOUT: 2025-09-01 .. 2026-11-15. Untouched until §9 freeze is committed.
- Walk-forward (inside BUILD, per idea family): in-sample 12 months, OOS 3
  months, step 3 months -> OOS 2023-09-01 .. 2025-08-31 (8 quarters). At each
  step pick the variation with the highest IS daily Sharpe among those with
  >= 30 IS trades; trade it OOS. After freeze the same procedure is continued
  through HOLDOUT (5 more OOS quarters) and reported separately.

## 4. Lookahead rules
- A trade entered on UTC day t may use fundamentals dated <= t-L, L = 1
  (primary). Stress tests: L = 3 and L = 7 for every finalist.
- Price-derived daily inputs (e.g. daily returns, market cap) use closes dated
  <= t-1.
- Intraday signals are computed at the close of a completed bar; entry is at
  the open of the next 5m bar.
- Restatement risk (highest first): revenue (take-rate reclassification),
  fees (methodology additions), user_dau (address attribution), tvl, supply.

## 5. Execution model
- Entry at next 5m open after the signal bar closes.
- Stop = entry -/+ s x ATR(14, Wilder, signal timeframe) at signal time.
  Target = entry +/- t x (entry-stop distance). Time stop = H hours, exit at
  the close of the last 5m bar inside H.
- Exits simulated on 5m bars starting with the entry bar. If one 5m bar
  touches both stop and target -> stop (loss). If a bar opens through the
  stop/target, fill at that open.
- Costs per side: Binance taker 0.10% + slippage (2 bp ETH/SOL/BNB, 5 bp all
  others). Applied to both legs, both directions. Shorts are priced on spot
  data with the same costs (conservative vs perps; funding ignored at <=12h,
  stated limitation).
- One open position per token per variation; overlapping signals skipped.
- Unit of P&L: R (net return / initial risk fraction). Portfolio = equal 1R
  risk per trade, daily P&L = sum of R of trades closed that UTC day.

## 6. Execution sets (trigger + geometry)
Breakout/trend set (used by ideas 1, 3, 4, 5, 6, 7):
- E1: 1h close > max(high, prior 20 bars) long / < min(low, 20) short; s=1.5, t=2.0, H=12
- E2: 15m Donchian-20 breakout; s=1.5, t=2.0, H=4
- E3: 15m Donchian-48 breakout; s=1.0, t=3.0, H=12
- E4: 1h EMA(9) crosses EMA(21) (up=long, down=short); s=1.5, t=1.5, H=12
- E5: 4h Donchian-20 breakout; s=1.0, t=1.5, H=12
Mean-reversion set (used by idea 2):
- M1: 1h RSI(14) crosses up through 30 long / down through 70 short; s=1.5, t=1.5, H=12
- M2: 15m RSI(14) crosses up through 25 / down through 75; s=1.5, t=1.5, H=4
- M3: 1h close back inside Bollinger(20,2) after a close outside; s=1.5, t=2.0, H=12
- M4: 15m Bollinger(20,2) re-entry; s=1.0, t=1.5, H=4
- M5: 4h RSI(14) crosses up through 35 / down through 65; s=1.5, t=1.5, H=12

## 7. Ideas and their 100 variations (4 gate definitions x 5 thresholds x 5 execution sets)
Thresholds are ordered loosest -> tightest; each step only removes setups.
Notation: mean_n(x) = mean of the last n daily values ending at t-L.
r(x, s, l) = mean_s(x) / mean_l(x).

I1 REVMOM — revenue/fee momentum gate (exec E1-E5)
- Gate defs: r(fees,7,30), r(fees,14,60), r(revenue,7,30), r(revenue,14,60)
- Long allowed if r >= k; short allowed if r <= 1/k; k in {1.00, 1.05, 1.10, 1.20, 1.35}

I2 DIVERGE — fundamental/price divergence, mean reversion (exec M1-M5)
- f = ln r(m,7,30) for m in {user_dau, fees}; p = ln(close_{t-1}/close_{t-1-P}), P in {7, 14}
- Gate defs: (dau,7), (dau,14), (fees,7), (fees,14)
- Long if f >= a and p <= -b; short if f <= -a and p >= b
- (a, b) in {(0,0), (0.05,0.03), (0.10,0.05), (0.15,0.08), (0.25,0.12)}

I3 TVLFLOW — TVL flow regime (exec E1-E5)
- own_excess_L = ln(TVL_{t-1}/TVL_{t-1-L}) - ln(close_{t-1}/close_{t-1-L})
- agg_raw_L = ln of summed universe TVL over L days (tokens with TVL both ends)
- Gate defs: own_excess_7, own_excess_30, agg_raw_7, agg_raw_30
- Long if flow >= c; short if flow <= -c; c in {0, 0.02, 0.05, 0.10, 0.15}

I4 UNLOCK — supply emission gate (exec E1-E5)
- e_L = ln(Supply_{t-1}/Supply_{t-1-L}), L in {7, 30}
- Mode SUPPRESS (long-only trigger): long allowed only if e_L < u, u in {5%, 3%, 2%, 1%, 0.5%}
- Mode FLIP (short-only trigger): short allowed only if e_L >= v, v in {0.5%, 1%, 2%, 3%, 5%}
- Gate defs: SUPPRESS-7, SUPPRESS-30, FLIP-7, FLIP-30 (u/v ladders as listed, loosest first)
- Limitation: realised supply changes only (no forward unlock calendar).

I5 ROTATE — sector relative-value rotation (exec E1-E5)
- Sectors: CHAINS = ETH SOL BNB NEAR TRX SUI AVAX APT ARB OP POL TIA SEI INJ ATOM;
  APPS = UNI AAVE CRV JUP RAY CAKE LDO PENDLE ETHFI JTO ENA ONDO LINK FIL RENDER
- Score defs: r(fees,7,30), r(revenue,7,30), r(user_dau,7,30), composite = mean
  of the three cross-sectional percentile ranks (needs >= 2 present)
- Long only the top-k scored tokens in each sector that day, short only the bottom-k;
  k in {5, 4, 3, 2, 1}

I6 VALUE — market-cap-to-fees valuation gate (exec E1-E5)
- mcap_{t-1} = close_{t-1} x Supply_{t-1}; PF_n = mcap / (mean_n(fees) x 365); PS_n with revenue
- Gate defs: PF_30, PF_90, PS_30, PS_90 (cross-sectional percentile rank, all eligible tokens)
- Long if rank <= q; short if rank >= 1-q; q in {0.50, 0.40, 0.30, 0.20, 0.10}

I7 SHOCK — usage-shock continuation (own idea; exec E1-E5)
- z = x_{t-1} / median_30(x) for x in {fees, user_dau}; direction d = sign of
  ln(close_{t-1}/close_{t-1-D}), D in {1, 3}
- Gate defs: (fees,1), (fees,3), (dau,1), (dau,3)
- Trade only in direction d, only if z >= k; k in {1.25, 1.5, 2.0, 2.5, 3.0}

Baselines (trials too): the 10 execution sets ungated, all eligible tokens.

Trial count for deflation: N_total = 7 x 100 + 10 = 710 (primary). Family
N = 100 also reported.

## 8. Statistics
- Sharpe: daily R series incl. zero days over the period, annualised x sqrt(365).
- Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014):
  SR0 = sqrt(V) [ (1-g) Z^-1(1-1/N) + g Z^-1(1-1/(N e)) ], g = 0.5772,
  V = variance of BUILD per-day Sharpe across the N trials;
  DSR = Z( (SR - SR0) sqrt(T-1) / sqrt(1 - skew SR + (kurt-1)/4 SR^2) ),
  SR, skew, kurt of the evaluated daily series (non-annualised), T = days.
  Significant if DSR >= 0.95.
- Random-entry benchmark: same count, same direction mix, same geometry, entry
  at uniformly random 5m bars of eligible tokens in the same period; 1000 draws.
  Delta = mean R(strategy) - mean R(random); p = share of draws >= strategy.
- Timing null (Monte Carlo 1): each trade re-entered at a random 5m bar on the
  same token, same UTC day, same direction, same geometry; 1000 draws -> percentile.
- Trade-sequence bootstrap (Monte Carlo 2): 5000 resamples of the trade R list
  -> 5th/50th/95th percentile of total R, max drawdown, P(total R < 0).
- Gate placebo: same trigger, gate replaced by a random day mask with the same
  per-token, per-direction pass rate; 1000 draws -> p-value of gate lift.
- Gate lift: mean R(gated) - mean R(same exec ungated, same token-days with the
  gate metric defined).

## 9. Freeze and holdout procedure
1. Run all 710 trials on BUILD; run walk-forward on BUILD.
2. Per idea, the FINALIST = variation with the highest BUILD Sharpe among those
   with >= 150 BUILD trades. (The walk-forward selection is reported alongside.)
3. Commit finalists + build tables (the freeze). Only then run HOLDOUT.
4. HOLDOUT: run each finalist once, plus all 710 trials for family-level
   context (no reselection).

## 10. Acceptance bar (all on HOLDOUT unless stated)
1. DSR >= 0.95 deflated against N_total = 710 (also show N = 100).
2. Profit factor > 1 after costs on >= 100 HOLDOUT trades.
3. Mean R > 0 and avg win / avg loss consistent with the geometry.
4. Beats the random-entry benchmark (p < 0.05).
5. Walk-forward OOS mean R > 0 over BUILD-OOS and over HOLDOUT-OOS; timing-null
   percentile >= 95.
"Fundamental gate adds value" additionally requires gate-placebo p < 0.05 and
positive gate lift on HOLDOUT. An edge passing 1-5 but not this is reported as
a price-action edge, not a fundamental one.
Uncorrelated set: among accepted edges, daily-P&L correlation |rho| < 0.3 on
HOLDOUT; a pair above that is treated as one edge (keep the higher DSR).

## Amendments
A1 (2026-11-16, before any full-data BUILD run; data handling, not a rule
change). The connector states that some exact zeros are left-join defaults
meaning "no data". For user_dau, tvl and token_supply_circulating an exact 0
is treated as missing (a live protocol has no zero-user/zero-TVL/zero-supply
day). Fees and revenue zeros are kept. TT reports no chain-level TVL, so I3's
own-TVL gates are undefined (no trade) for chains, per §2's eligibility rule;
agg_raw sums application TVL. RENDER (no fees or revenue) and ONDO (no fees,
no revenue) leave the universe under §2.

A2 (2026-11-16, before any full-data BUILD run; data handling, not a rule
change). Circulating supply is cleaned mechanically per token
(`edgehunt.data.clean_supply`, unit-tested): (1) values within 1% of the
2^31/10 placeholder (214,748,364, seen as OP Mainnet's constant in 2022-23)
are missing; (2) one-day blips — more than 5% from the mean of both
neighbours while the neighbours agree within 2% — are missing; (3) a one-day
change above +100% is a series break (redenomination/migration, e.g.
MATIC->POL on 2024-09-04) and all earlier values are dropped, so no emission
window spans it. Motivation: the export notes list these artefacts; left in,
they would read as unlocks to I4 and as valuation jumps to I6.
