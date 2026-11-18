"""Deterministic checks; run from repository root with python3 -m pytest tests/test_part42.py -q."""
import math
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
import pandas as pd
from backend.part42_engine import (Account, Candle, batch_indicators,
                                   incremental_indicators, run_backtest,
                                   sample_candles, saved_candles, signals)


def make_candles(closes):
    return [Candle(i*60, v, v, v, v) for i, v in enumerate(closes)]


def test_sma_known_reference_example():
    candles = make_candles([1,2,3,4,5,6,7,8])
    got = batch_indicators(candles, 2, 3)
    assert got[0]['short'] is None
    assert got[1]['short'] == 1.5
    assert got[2]['short'] == 2.5
    assert got[2]['long'] == 2.0
    assert got[-1]['long'] == 7.0


def test_incremental_matches_batch_for_every_bar():
    candles = sample_candles()
    b = batch_indicators(candles)
    inc = incremental_indicators(candles)
    assert len(b) == len(inc)
    for x,y in zip(b,inc):
        for key in ('short','long'):
            if x[key] is None:
                assert y[key] is None
            else:
                assert math.isclose(x[key],y[key],abs_tol=1e-7)
    assert signals(b) == signals(inc)


def test_crossover_definition_and_no_premature_signal():
    bars = make_candles([10,10,10,10,10, 9,8,7, 10,12,14])
    indi = batch_indicators(bars,2,3)
    cross = signals(indi)
    assert cross[:3] == [None,None,None]
    assert 'SELL' in cross and 'BUY' in cross


def test_missing_minute_resets_windows():
    bars = [Candle(i*60,10,10,10,10) for i in (0,1,2,5,6,7)]
    result = incremental_indicators(bars,2,3)
    assert result[3]['short'] is None and result[3]['long'] is None
    assert result[4]['short'] == 10 and result[4]['long'] is None
    assert result[5]['long'] == 10


def test_hand_calculated_buy_sell_account_no_fees():
    a = Account(cash=1000)
    buy = a.buy(100,1000,0,0)
    assert buy['quantity'] == 10 and a.cash == 0
    assert a.cost_basis == 1000
    sell = a.sell(110,0,0)
    assert sell['realized_pnl'] == 100
    assert a.cash == 1100 and a.quantity == 0 and a.realized_pnl == 100


def test_hand_calculated_fee_and_unrealized_pnl():
    a = Account(cash=1000)
    buy = a.buy(100,500,0.01,0)
    assert buy['quantity'] == 5
    assert a.cash == 495 and a.cost_basis == 505
    assert math.isclose(a.quantity*110-a.cost_basis,45)
    sell = a.sell(110,0.01,0)
    assert math.isclose(sell['realized_pnl'],39.5)
    assert math.isclose(a.cash,1039.5)


def test_backtest_executes_at_next_bar_open_only():
    c = sample_candles()
    b = run_backtest(c)
    assert b['metrics']['fills'] > 0
    for f in b['fills']:
        order = next(o for o in b['orders'] if o['id'] == f['order_id'])
        assert f['time'] == order['signal_time']
        assert f['time'] > c[0].time
    for point in b['equity_curve']:
        assert math.isclose(point['equity'], point['cash'] + point['quantity'] * next(
            c['close'] for c in b['candles'] if c['time'] == point['time']-60),abs_tol=1e-6)
    assert math.isclose(b['metrics']['net_pnl'], b['account']['equity']-10000, abs_tol=1e-6)


def test_no_data_no_trades():
    b = run_backtest([])
    assert b['metrics']['fills'] == 0 and b['account']['cash'] == 10000


def test_saved_candle_respects_arrival_and_incomplete_cutoff(tmp_path):
    db=tmp_path/'prices.db'
    with sqlite3.connect(db) as con:
        con.execute('''CREATE TABLE market_observations
                   (id INTEGER PRIMARY KEY, observation_id TEXT, symbol TEXT,
                    source_time_ms INTEGER, received_at TEXT, revision INTEGER, price REAL)''')
        base=datetime(2025,1,1,tzinfo=timezone.utc)
        def add(obs,minute,second,received,revision,price):
            tick=base+timedelta(minutes=minute,seconds=second)
            recv=base+timedelta(seconds=received)
            con.execute('INSERT INTO market_observations(observation_id,symbol,source_time_ms,received_at,revision,price) VALUES(?,?,?,?,?,?)',
                        (obs,'BTC-USD',int(tick.timestamp()*1000),recv.isoformat(),revision,price))
        add('a',0,2,2,1,100)
        add('b',0,50,50,1,105)
        add('a',0,2,65,2,999)  # a retrospective correction known too late; exclude
        add('c',1,2,62,1,103)  # incomplete minute when as_of 1:30
    now_ms=int((base+timedelta(seconds=90)).timestamp()*1000)
    candles=saved_candles(db,now_ms=now_ms)
    assert len(candles)==1
    assert candles[0].open==100 and candles[0].close==105


def test_bad_parameters_rejected():
    with pytest.raises(ValueError):
        run_backtest(sample_candles(),20,5)


def test_sma_and_crossovers_against_pandas_trusted_reference():
    # pandas.Series.rolling(...).mean() is the independent documented reference.
    bars = sample_candles()
    close = pd.Series([c.close for c in bars])
    sma5 = close.rolling(window=5, min_periods=5).mean()
    sma20 = close.rolling(window=20, min_periods=20).mean()
    actual = incremental_indicators(bars, 5, 20)
    for i, row in enumerate(actual):
        assert (row['short'] is None if pd.isna(sma5.iloc[i]) else
                math.isclose(row['short'], sma5.iloc[i], abs_tol=1e-7))
        assert (row['long'] is None if pd.isna(sma20.iloc[i]) else
                math.isclose(row['long'], sma20.iloc[i], abs_tol=1e-7))
    pandas_buy = (sma5.shift(1) <= sma20.shift(1)) & (sma5 > sma20)
    pandas_sell = (sma5.shift(1) >= sma20.shift(1)) & (sma5 < sma20)
    actual_signals = signals(actual)
    for i, s in enumerate(actual_signals):
        expected = 'BUY' if pandas_buy.iloc[i] else 'SELL' if pandas_sell.iloc[i] else None
        assert s == expected
