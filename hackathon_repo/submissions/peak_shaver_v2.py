"""
Peak Shaver v2 — Continuous positions [0, 1]
=============================================
Original continuous 0-1 positions: 100% default, 40% tier1, 30% tier2.

Tier 1: RSI(14) > 75 AND ROC(21) > 11% AND Z-score(50) > 1.0 -> 0.40
Tier 2: RSI(14) > 85 AND Z-score(50) > 3.0 -> 0.30
Timeframe-adaptive via bars-per-day scaling.
"""

import pandas as pd
import numpy as np


def _detect_bars_per_day(df):
    if len(df) < 20:
        return 1
    deltas = df.index.to_series().diff().dropna()
    median_mins = deltas.median().total_seconds() / 60
    if median_mins < 120:
        return 7
    elif median_mins < 480:
        return 2
    return 1


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


def generate_signals(data: pd.DataFrame) -> pd.Series:
    bpd = _detect_bars_per_day(data)
    close = data["Close"]

    scale = max(1.0, bpd ** 0.4)
    rsi_val = rsi(close, max(14, int(14 * scale)))
    mom_1m = roc(close, max(21, int(21 * scale)))
    z = zscore(close, max(50, int(50 * scale)))

    position = pd.Series(1.0, index=data.index)

    # Tier 1: triple confirmation -> trim to 40%
    position[(rsi_val > 75) & (mom_1m > 11) & (z > 1.0)] = 0.40
    # Tier 2: extreme overbought + extreme stretch -> trim to 30%
    position[(rsi_val > 85) & (z > 3.0)] = 0.30

    return position.fillna(1.0).astype(float)
