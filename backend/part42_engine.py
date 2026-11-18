"""Part 4.2 teaching backtester: completed 1-minute candles; long-only SMA crossing.
No real order placement. No network dependencies. Time fields are UTC epoch seconds.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class Candle:
    time: int  # minute start, UTC epoch seconds
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def validate(candles: list[Candle]) -> None:
    for i, c in enumerate(candles):
        if c.time % 60:
            raise ValueError("Candles must begin on a UTC minute boundary")
        if i and c.time <= candles[i-1].time:
            raise ValueError("Candle timestamps must increase without duplicates")
        if any(not isfinite(v) or v <= 0 for v in (c.open, c.high, c.low, c.close)):
            raise ValueError("Prices must be finite positive numbers")
        if c.high < max(c.open, c.close) or c.low > min(c.open, c.close):
            raise ValueError("Inconsistent OHLC")


def batch_indicators(candles: list[Candle], short: int = 5, long: int = 20) -> list[dict]:
    """Independent reference-style rolling mean implementation (O(N * window))."""
    if not 1 <= short < long:
        raise ValueError("Require 1 <= short SMA < long SMA")
    validate(candles)
    result: list[dict] = []
    for i, c in enumerate(candles):
        # Reset windows on gaps; missing candles must not become fabricated bars.
        start = i
        while start > 0 and candles[start].time - candles[start-1].time == 60:
            start -= 1
        segment = candles[start:i+1]
        sm = sum(x.close for x in segment[-short:]) / short if len(segment) >= short else None
        lm = sum(x.close for x in segment[-long:]) / long if len(segment) >= long else None
        result.append({"time": c.time, "short": sm, "long": lm})
    return result


def incremental_indicators(candles: list[Candle], short: int = 5, long: int = 20) -> list[dict]:
    """Independent O(N) moving-window implementation for streaming updates."""
    if not 1 <= short < long:
        raise ValueError("Require 1 <= short SMA < long SMA")
    validate(candles)
    sq, lq = deque(), deque()
    ssum = lsum = 0.0
    result = []
    prev_time = None
    for c in candles:
        if prev_time is not None and c.time - prev_time != 60:
            sq.clear(); lq.clear(); ssum = lsum = 0.0
        prev_time = c.time
        sq.append(c.close); ssum += c.close
        lq.append(c.close); lsum += c.close
        if len(sq) > short:
            ssum -= sq.popleft()
        if len(lq) > long:
            lsum -= lq.popleft()
        result.append({"time": c.time,
                       "short": ssum / short if len(sq) == short else None,
                       "long": lsum / long if len(lq) == long else None})
    return result


def signals(indicators: list[dict]) -> list[str | None]:
    out: list[str | None] = []
    for i, now in enumerate(indicators):
        if i == 0:
            out.append(None); continue
        prev = indicators[i-1]
        a, b, x, y = prev['short'], prev['long'], now['short'], now['long']
        if None in (a, b, x, y) or now['time'] - prev['time'] != 60:
            out.append(None)
        elif a <= b and x > y:
            out.append('BUY')
        elif a >= b and x < y:
            out.append('SELL')
        else:
            out.append(None)
    return out


@dataclass
class Account:
    cash: float = 10000.0
    quantity: float = 0.0
    cost_basis: float = 0.0
    realized_pnl: float = 0.0

    def buy(self, market_open: float, notional: float, fee_rate: float, slippage: float) -> dict | None:
        if self.quantity > 1e-12:
            return None  # long-only, at most one open position
        fill_price = market_open * (1 + slippage)
        gross = min(notional, self.cash / (1 + fee_rate))
        if gross < 1e-9:
            return None
        quantity = gross / fill_price
        fee = gross * fee_rate
        self.cash -= gross + fee
        self.quantity = quantity
        self.cost_basis = gross + fee
        return {"side": "BUY", "price": fill_price, "quantity": quantity,
                "gross": gross, "fee": fee, "realized_pnl": 0.0}

    def sell(self, market_open: float, fee_rate: float, slippage: float) -> dict | None:
        if self.quantity <= 1e-12:
            return None
        fill_price = market_open * (1 - slippage)
        qty = self.quantity
        gross = qty * fill_price
        fee = gross * fee_rate
        profit = gross - fee - self.cost_basis
        self.cash += gross - fee
        self.realized_pnl += profit
        self.quantity = 0.0
        self.cost_basis = 0.0
        return {"side": "SELL", "price": fill_price, "quantity": qty,
                "gross": gross, "fee": fee, "realized_pnl": profit}


def run_backtest(candles: list[Candle], short: int = 5, long: int = 20,
                 initial_cash: float = 10000.0, order_notional: float = 2000.0,
                 fee_rate: float = 0.001, slippage: float = 0.0005) -> dict:
    validate(candles)
    if not 1 <= short < long <= 200 or initial_cash <= 0 or order_notional <= 0:
        raise ValueError("Invalid strategy parameters")
    if not 0 <= fee_rate < 1 or not 0 <= slippage < 1:
        raise ValueError("Fees/slippage must be in [0, 1)")
    ind = incremental_indicators(candles, short, long)
    sig = signals(ind)
    account = Account(initial_cash)
    pending: dict | None = None
    orders: list[dict] = []
    fills: list[dict] = []
    equity_curve: list[dict] = []
    peak_equity = initial_cash
    max_drawdown = 0.0
    for i, bar in enumerate(candles):
        if pending is not None:
            # An order generated at previous bar CLOSE fills at this next bar OPEN.
            # Reject carrying orders over missing-minute gaps.
            if bar.time != pending['decision_time']:
                pending['status'] = 'CANCELLED_GAP'
            else:
                trade = (account.buy(bar.open, order_notional, fee_rate, slippage)
                         if pending['side'] == 'BUY' else
                         account.sell(bar.open, fee_rate, slippage))
                if trade:
                    pending['status'] = 'FILLED'
                    pending['fill_time'] = bar.time
                    fills.append({"order_id": pending['id'], "time": bar.time, **trade})
                else:
                    pending['status'] = 'REJECTED_NO_POSITION_OR_FUNDS'
            pending = None
        equity = account.cash + account.quantity * bar.close
        unrealized = account.quantity * bar.close - account.cost_basis
        peak_equity = max(peak_equity, equity)
        max_drawdown = max(max_drawdown, (peak_equity-equity)/peak_equity)
        equity_curve.append({"time": bar.time + 60, "equity": equity,
                             "cash": account.cash, "quantity": account.quantity,
                             "realized_pnl": account.realized_pnl,
                             "unrealized_pnl": unrealized})
        if sig[i] == 'BUY' and account.quantity <= 1e-12:
            pending = {"id": len(orders)+1, "side": "BUY", "signal_time": bar.time+60,
                       "decision_time": bar.time+60, "status": "PENDING_NEXT_OPEN"}
            orders.append(pending)
        elif sig[i] == 'SELL' and account.quantity > 1e-12:
            pending = {"id": len(orders)+1, "side": "SELL", "signal_time": bar.time+60,
                       "decision_time": bar.time+60, "status": "PENDING_NEXT_OPEN"}
            orders.append(pending)
    final_equity = equity_curve[-1]['equity'] if equity_curve else initial_cash
    closed = [f for f in fills if f['side'] == 'SELL']
    annotated = []
    for c, point, signal in zip(candles, ind, sig):
        annotated.append({"time": c.time, "open": c.open, "high": c.high,
                          "low": c.low, "close": c.close, "volume": c.volume,
                          "sma_short": point['short'], "sma_long": point['long'],
                          "signal": signal})
    return {"candles": annotated, "orders": orders, "fills": fills,
            "equity_curve": equity_curve,
            "account": {"cash": account.cash, "position_btc": account.quantity,
                        "cost_basis": account.cost_basis, "realized_pnl": account.realized_pnl,
                        "unrealized_pnl": equity_curve[-1]['unrealized_pnl'] if equity_curve else 0,
                        "equity": final_equity},
            "metrics": {"initial_cash": initial_cash, "final_equity": final_equity,
                        "net_pnl": final_equity - initial_cash,
                        "return_pct": (final_equity/initial_cash-1)*100,
                        "max_drawdown_pct": max_drawdown*100, "orders": len(orders),
                        "fills": len(fills), "closed_trades": len(closed),
                        "win_rate_pct": (sum(f['realized_pnl'] > 0 for f in closed)/len(closed)*100
                                         if closed else None)},
            "parameters": {"short": short, "long": long, "fee_rate": fee_rate,
                           "slippage": slippage, "order_notional": order_notional,
                           "execution": "signal at completed bar close; hypothetical fill at next consecutive bar open",
                           "missing_candles": "no fill-forward; reset SMA and cancel pending orders on gap",
                           "end_position": "open positions marked at final close; not force-liquidated"}}


def saved_candles(db_path, symbol: str = 'BTC-USD', now_ms: int | None = None) -> list[Candle]:
    """Read existing Part 4.1 quote schema; use only arrivals known by candle close.
    No future revisions or inferred/trade volume. Excludes current unfinished minute.
    """
    import sqlite3
    from pathlib import Path
    if now_ms is None:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    if not Path(db_path).exists():
        return []
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""SELECT observation_id, source_time_ms, received_at, revision,
                                     price, id FROM market_observations
                              WHERE symbol = ? ORDER BY source_time_ms, id""", (symbol,)).fetchall()
    latest: dict[str, dict] = {}
    for r in rows:
        try:
            ts = int(r['source_time_ms'])
            ts = ts*1000 if ts < 1_000_000_000_000 else ts
            end_ms = (ts//60000+1)*60000
            receipt = datetime.fromisoformat(str(r['received_at']).replace('Z','+00:00'))
            if receipt.tzinfo is None:
                continue
            received_ms = receipt.timestamp()*1000
            if received_ms > end_ms or received_ms > now_ms or ts > now_ms:
                continue  # unavailable at decision time: must not leak information
            price = float(r['price'])
            if not isfinite(price) or price <= 0:
                continue
            identity = str(r['observation_id'])
            item = {"ts": ts, "revision": r['revision'], "id": r['id'], "price": price}
            previous = latest.get(identity)
            if previous is None or (item['revision'], item['id']) > (previous['revision'], previous['id']):
                latest[identity] = item
        except (TypeError, ValueError, OverflowError):
            continue
    by_min: dict[int, list[dict]] = {}
    for r in latest.values():
        minute = (r['ts']//60000)*60
        if (minute+60)*1000 <= now_ms:  # never use unfinished UTC minute
            by_min.setdefault(minute, []).append(r)
    out = []
    for minute, ticks in sorted(by_min.items()):
        ticks.sort(key=lambda a: (a['ts'], a['id']))
        prices = [r['price'] for r in ticks]
        out.append(Candle(minute, prices[0], max(prices), min(prices), prices[-1]))
    return out


def sample_candles() -> list[Candle]:
    """Labeled synthetic fixtures for UI/CI demonstrations, NOT real market history."""
    from datetime import datetime, timezone
    base = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    values = [92000.0]
    for i in range(1, 151):
        slope = (-44 if i < 40 else 87 if i < 80 else -110 if i < 120 else 96)
        values.append(values[-1] + slope + (i % 7 - 3) * 3)
    return [Candle(base + i*60, values[i-1] if i else values[0],
                   max(values[i-1] if i else values[0], v),
                   min(values[i-1] if i else values[0], v), v)
            for i, v in enumerate(values)]
