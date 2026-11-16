"""
NautilusTrader cross-check of the vectorised engine.

The research engine decides WHEN to trade (trigger + fundamental gate). This
script hands that signal schedule to a NautilusTrader strategy that executes it
through Nautilus' own matching engine: market entry, bracket stop-loss
(stop-market) + take-profit (limit) from the same ATR geometry, time exit after
H hours, taker fee folded with slippage. Then it compares per-trade R and
aggregate stats with the vectorised result.

Usage: python nautilus/replicate.py <vid> <period> <TOKEN>
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.config import RiskEngineConfig
from nautilus_trader.config import StrategyConfig
from nautilus_trader.execution import MakerTakerFeeModel
from nautilus_trader.model import AccountType
from nautilus_trader.model import Bar
from nautilus_trader.model import BarType
from nautilus_trader.model import Currency
from nautilus_trader.model import CurrencyPair
from nautilus_trader.model import CurrencyType
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Symbol
from nautilus_trader.model import Money
from nautilus_trader.model import OmsType
from nautilus_trader.model import OrderSide
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import TraderId
from nautilus_trader.model import Venue
from nautilus_trader.testkit.providers import TestInstrumentProvider
from nautilus_trader.trading import Strategy


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from edgehunt.config import EXEC_SETS  # noqa: E402
from edgehunt.config import TOKENS  # noqa: E402
from edgehunt.config import cost_per_side  # noqa: E402
from edgehunt.data import load_5m  # noqa: E402
from edgehunt.data import load_fundamentals  # noqa: E402
from edgehunt.engine import Engine  # noqa: E402
from edgehunt.gates import GateBuilder  # noqa: E402
from edgehunt.stats import trade_stats  # noqa: E402


class ScheduleConfig(StrategyConfig):
    def __init__(self, *, instrument_id, bar_type, schedule, hold_bars, target_r, **_kw) -> None:
        super().__init__()
        self.instrument_id = instrument_id
        self.bar_type = bar_type
        self.schedule = schedule  # ts_event(ns) of the bar whose close triggers -> (dir, stop_dist)
        self.hold_bars = hold_bars
        self.target_r = target_r


class ScheduleStrategy(Strategy):
    def __init__(self, config: ScheduleConfig) -> None:
        super().__init__(config)
        self.bars_in_trade = 0
        self.in_trade = False

    def on_start(self) -> None:
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        iid = self.config.instrument_id
        flat = self.portfolio.is_net_flat(iid)
        if self.in_trade:
            self.bars_in_trade += 1
            if flat:
                self.in_trade = False
                self.cancel_all_orders(iid)
            elif self.bars_in_trade >= self.config.hold_bars:
                self.cancel_all_orders(iid)
                self.close_all_positions(iid)
                self.in_trade = False
                return
        sig = self.config.schedule.get(bar.ts_event)
        if sig is None or not self.portfolio.is_net_flat(iid) or self.in_trade:
            return
        d, sd = sig
        inst = self.cache.instrument(iid)
        px = float(bar.close)
        side = OrderSide.BUY if d > 0 else OrderSide.SELL
        sl = px - sd if d > 0 else px + sd
        tp = px + self.config.target_r * sd if d > 0 else px - self.config.target_r * sd
        if sl <= 0 or tp <= 0:
            return
        order_list = self.order_factory.bracket(
            iid, side, inst.make_qty(Decimal(str(round(1000.0 / px, 3)))),
            sl_trigger_price=inst.make_price(sl), tp_price=inst.make_price(tp),
        )
        self.submit_order_list(order_list)
        self.in_trade = True
        # entry bar counts as bar 1 of the holding window (research engine convention)
        self.bars_in_trade = 0


def make_instrument(token: str, median_px: float) -> CurrencyPair:
    """Binance-like spot pair; price precision scaled to the token's price level."""
    pp = int(min(8, max(2, 4 - np.floor(np.log10(median_px)))))
    sp = 2 if median_px < 50 else 5
    try:
        base = Currency.from_str(token)
    except Exception:  # not in the built-in registry
        base = Currency(token, 8, 0, token, CurrencyType.CRYPTO)
    usdt = Currency.from_str("USDT")
    return CurrencyPair(
        instrument_id=InstrumentId(Symbol(f"{token}USDT"), Venue("BINANCE")), raw_symbol=Symbol(f"{token}USDT"),
        base_currency=base, quote_currency=usdt, price_precision=pp, size_precision=sp,
        price_increment=Price(10.0**-pp, precision=pp), size_increment=Quantity(10.0**-sp, precision=sp),
        ts_event=0, ts_init=0, max_quantity=Quantity(1e9, precision=sp), min_quantity=Quantity(10.0**-sp, precision=sp),
        min_notional=Money(1.00, usdt), max_price=Price(1e7, precision=pp), min_price=Price(10.0**-pp, precision=pp),
        margin_init=Decimal("1.00"), margin_maint=Decimal("0.35"),
    )


def main(vid: str, period: str, token: str) -> None:
    if token == "ALL":
        e = vid.split("-")[-1]
        frames = []
        for t in TOKENS:
            try:
                frames.append(run_one(vid, period, t))
            except NoTrades:
                continue
        allr = pd.concat(frames)
        out = pd.DataFrame([{"engine": k, **trade_stats(g["r"].to_numpy())} for k, g in allr.groupby("engine")])
        print(out.round(4).to_string(index=False))
        out.to_csv(ROOT / "results" / f"nautilus_xcheck_{vid}_{period}_ALL.csv", index=False)
        return
    out = run_one(vid, period, token)
    print(pd.DataFrame([{"engine": k, **trade_stats(g["r"].to_numpy())} for k, g in out.groupby("engine")]).round(4).to_string(index=False))


class NoTrades(Exception):
    pass


def run_one(vid: str, period: str, token: str) -> pd.DataFrame:
    engine_r = Engine([vid.split("-")[-1]])
    gb = GateBuilder(load_fundamentals(), lag=1)
    if vid.startswith("B-"):
        e = vid[2:]
        ones = np.ones((len(gb.dcl), len(TOKENS)), bool)
        lo = so = ones
    else:
        idea, g, k, e = vid.split("-")
        lo_, so_, _ = gb.gate(idea, int(g[1:]), int(k[1:]))
        lo, so = engine_r.to_np(lo_), engine_r.to_np(so_)
    idx = engine_r.run(e, lo, so, period)
    c = engine_r.c[e]
    tok_id = TOKENS.index(token)
    idx = idx[c["tok"][idx] == tok_id]
    if len(idx) == 0:
        raise NoTrades(token)
    es = EXEC_SETS[e]
    df5 = load_5m(token)
    o, h, l = (df5[k].to_numpy() for k in ("open", "high", "low"))
    ts5 = df5.index.asi8
    five = 300_000_000_000
    # stop distance used by the research engine: recover from candidate geometry via ATR at signal
    from build_candidates_shim import stop_distances  # noqa: E402
    sd = stop_distances(token, es, c["ei"][idx])
    schedule = {int(ts5[ei]): (int(dv), float(s)) for ei, dv, s in zip(c["ei"][idx], c["dir"][idx], sd)}

    inst = make_instrument(token, float(df5["close"].median()))
    bar_type = BarType.from_str(f"{inst.id}-5-MINUTE-LAST-EXTERNAL")
    lo_t, hi_t = c["entry_ts"][idx].min(), c["exit_ts"][idx].max() if hasattr(c, "exit_ts") else None
    win = df5.loc[pd.Timestamp(lo_t) - pd.Timedelta("1D"): pd.Timestamp(c["entry_ts"][idx].max()) + pd.Timedelta("1D")]
    bars = [
        Bar(bar_type, inst.make_price(r.open), inst.make_price(r.high), inst.make_price(r.low),
            inst.make_price(r.close), inst.make_qty(max(r.volume, 1.0)),
            int(t.value) + five, int(t.value) + five)
        for t, r in zip(win.index, win.itertuples())
    ]
    fee = Decimal(str(cost_per_side(token)))
    bt = BacktestEngine(BacktestEngineConfig(trader_id=TraderId.from_str("XCHECK-001"),
                                             risk_engine=RiskEngineConfig(bypass=True)))
    bt.add_venue(venue=Venue("BINANCE"), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
                 base_currency=Currency.from_str("USDT"), starting_balances=[Money(10_000_000, Currency.from_str("USDT"))],
                 fee_model=MakerTakerFeeModel(maker_rate=fee, taker_rate=fee))
    bt.add_instrument(inst)
    bt.add_data(bars)
    # schedule keyed by Nautilus ts_event of the 5m bar that CLOSES at the research entry time
    sched = {k: v for k, v in schedule.items()}
    bt.add_strategy(ScheduleStrategy(ScheduleConfig(instrument_id=inst.id, bar_type=bar_type, schedule=sched,
                                                    hold_bars=es.hold_hours * 12, target_r=es.target_r)))
    bt.run()
    pos = bt.generate_positions_report()
    if "--debug" in sys.argv:
        print(list(pos.columns)); print(pos[["ts_opened", "avg_px_open", "realized_pnl"]].head(3).to_string()); print(sorted(schedule)[:3])
    pnl = pos["realized_pnl"].astype(str).str.split().str[0].astype(float).to_numpy()
    entry_px = pos["avg_px_open"].astype(float).to_numpy()
    qty = pos["peak_qty"].astype(float).to_numpy() if "peak_qty" in pos else pos["buy_qty"].astype(float).to_numpy()
    open_ts = pd.to_datetime(pos["ts_opened"], utc=True).astype("datetime64[ns, UTC]").astype("int64").to_numpy()
    sd_by_ts = {k: v[1] for k, v in schedule.items()}
    risk = np.array([sd_by_ts.get(int(t), np.nan) for t in open_ts]) * qty
    r_naut = pnl / risk
    r_naut = r_naut[np.isfinite(r_naut)]
    r_vec = c["r"][idx]
    bt.dispose()
    return pd.concat([pd.DataFrame({"engine": "vectorised", "token": token, "r": r_vec}),
                      pd.DataFrame({"engine": "nautilus", "token": token, "r": r_naut})])


if __name__ == "__main__":
    main(*sys.argv[1:4])
