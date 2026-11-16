# Token Terminal confluence edge hunt

Tests whether Token Terminal daily fundamentals, used as a lagged regime GATE,
improve the expectancy of ordinary intraday (5m-12h) price-action entries on
liquid crypto spot markets.

- `docs/` - export protocol, pre-registration, results write-ups
- `data/tt_raw/` - verbatim Token Terminal connector responses (snapshot 2026-11-16)
- `data/tt/` - parsed daily fundamentals (CSV)
- `data/ohlcv/` - Binance 5m klines (git-ignored; rebuild with `scripts/`)
- `src/edgehunt/` - research engine (signals, backtest, validation stats)
- `scripts/` - data pulls and experiment runners
- `nautilus/` - NautilusTrader replications of surviving edges
- `results/` - frozen result tables

Runs against `nautilus_trader==2.0.0rc9` (pip, `--pre`) plus pandas/pyarrow.

## Status (2026-11-16)
Complete. Verdict and tables: `docs/report.md`. Data inventory:
`docs/data_inventory.md`. Pre-registration with amendments:
`docs/preregistration.md`. No edge survived holdout.
