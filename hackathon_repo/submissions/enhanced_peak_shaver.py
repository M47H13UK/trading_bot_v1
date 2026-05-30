"""
Enhanced Peak Shaver — Continuous positions [-1, 1]
====================================================
Default long (1.0), partial positions during risky regimes.

- Peak Shaver: 0.3 when RSI>70 + ROC>8% + Z>0.8 (overbought)
- Blow-off: -0.7 when RSI>85 + Z>3.0
- Bearish filter: 0.2 when ADX>25 + bearish DI + below SMA200
- Strong bearish: -0.5 when bearish + MACD<0 + SMA200 declining
- Vol filter: 0.3 when ATR > 1.5x its 63-day avg
- Oversold recovery: 1.0 when RSI<30 + Z<-1.5
- Hysteresis: suppress position changes < 0.1
"""

import pandas as pd
import numpy as np


def sma(series, window):
    return series.rolling(window=window).mean()


def ema(series, window):
    return series.ewm(span=window, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def roc(series, period=10):
    return series.pct_change(periods=period) * 100


def zscore(series, window=20):
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std.replace(0, np.nan)


def atr(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def adx(df, period=14):
    high, low = df["High"], df["Low"]
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    atr_val = atr(df, period)
    atr_val = atr_val.replace(0, np.nan)

    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_val
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_val

    di_sum = plus_di + minus_di
    di_sum = di_sum.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx_val = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx_val, plus_di, minus_di


def generate_signals(data: pd.DataFrame) -> pd.Series:
    close = data["Close"]
    n = len(data)

    rsi_val = rsi(close, 14)
    roc_val = roc(close, 21)
    z = zscore(close, 50)
    adx_val, plus_di, minus_di = adx(data, 14)
    atr_val = atr(data, 14)
    atr_63 = atr_val.rolling(63).mean()
    sma_200 = sma(close, 200)

    signal = pd.Series(1.0, index=data.index)

    # Peak Shaver — partial at overbought
    signal[(rsi_val > 70) & (roc_val > 8) & (z > 0.8)] = 0.3

    # Blow-off — partial short for mean reversion
    signal[(rsi_val > 85) & (z > 3.0)] = -0.7

    # Bearish regime — reduced long
    bearish = (adx_val > 25) & (minus_di > plus_di) & (close < sma_200)
    signal[bearish] = 0.2

    # Strong bearish — partial short
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_hist = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    sma200_slope = sma_200.pct_change(60)
    signal[bearish & (macd_hist < 0) & (sma200_slope < 0)] = -0.5

    # Vol spike — reduced long
    vol_ratio = atr_val / atr_63.replace(0, np.nan)
    signal[(vol_ratio > 1.5) & (signal > 0.5)] = 0.3

    # Oversold recovery — full long
    signal[(rsi_val < 30) & (z < -1.5)] = 1.0

    # Warmup
    signal.iloc[:200] = 1.0

    # Hysteresis — suppress changes < 0.1
    values = signal.values.copy()
    for i in range(1, n):
        if abs(values[i] - values[i - 1]) < 0.1:
            values[i] = values[i - 1]
    signal = pd.Series(values, index=data.index)

    return signal.fillna(1.0).astype(float)
