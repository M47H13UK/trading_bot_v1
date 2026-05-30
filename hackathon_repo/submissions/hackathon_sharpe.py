"""
Hackathon Sharpe Maximizer — Continuous positions [-1, 1]
=========================================================
Default-long trend follower optimized for Sharpe ratio.

1) Default LONG (1.0)
2) FLAT (0.0) when SMA(20) < SMA(50)
3) SHORT (-0.7) when ALL confirm strong downtrend:
   - SMA(20) < SMA(100)
   - MACD histogram < 0
   - -DI > +DI
   - ADX > 30
   - CMF(20) < 0
4) Warmup: 0.5 for first 50 bars
"""

import pandas as pd
import numpy as np


def generate_signals(data: pd.DataFrame) -> pd.Series:
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    # SMA
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    sma_100 = close.rolling(100).mean()

    # MACD(12,26,9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_hist = macd - macd.ewm(span=9, adjust=False).mean()

    # ADX(14)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=data.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=data.index,
    )
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    atr_val = tr.ewm(alpha=1 / 14, adjust=False).mean().replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_val
    minus_di = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_val
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx_val = dx.ewm(alpha=1 / 14, adjust=False).mean()

    # CMF(20)
    hl = (high - low).replace(0, np.nan)
    mf_mult = ((close - low) - (high - close)) / hl
    cmf_val = (mf_mult * volume).rolling(20).sum() / volume.rolling(20).sum()

    # Signal generation — continuous
    signals = pd.Series(1.0, index=data.index)

    # Flat when short-term downtrend
    signals[sma_20 < sma_50] = 0.0

    # Partial short in strong confirmed downtrends
    signals[
        (sma_20 < sma_100)
        & (macd_hist < 0)
        & (minus_di > plus_di)
        & (adx_val > 30)
        & (cmf_val < 0)
    ] = -0.7

    # Warmup — partial long
    signals.iloc[:50] = 0.5
    return signals.fillna(0.0).astype(float)
