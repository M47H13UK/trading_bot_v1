"""
Pre-trained ML Strategy — LEFS Quant Hackathon Submission
=========================================================
Loads pre-trained XGBoost + RandomForest ensemble from model.pkl.
No runtime training — pure inference (~0.5s on 2500 bars).

Trained on 100+ tickers (daily + hourly), 500k+ bars.
36 features: momentum, trend, volatility, volume, regime, dip/recovery.

Continuous output: positions in [-max_short, max_long] (up to 2.0x leverage).
Fallback: Enhanced Peak Shaver if model.pkl missing or ML libs unavailable.

Requirements: pandas, numpy, joblib, xgboost, scikit-learn
"""

import pandas as pd
import numpy as np
from pathlib import Path

try:
    import joblib
    from xgboost import XGBRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Load model at module scope (cached across calls)
_MODEL = None
_MODEL_PATH = Path(__file__).parent / "model.pkl"


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if not ML_AVAILABLE or not _MODEL_PATH.exists():
        return None
    try:
        _MODEL = joblib.load(_MODEL_PATH)
        return _MODEL
    except Exception:
        return None


# =============================================================================
# INDICATORS
# =============================================================================

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
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    atr_val = atr(df, period).replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_val
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_val
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx_val = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx_val, plus_di, minus_di

def obv(df):
    direction = np.sign(df["Close"].diff())
    return (direction * df["Volume"]).cumsum()

def cmf(df, period=20):
    high, low, close, volume = df["High"], df["Low"], df["Close"], df["Volume"]
    hl_range = (high - low).replace(0, np.nan)
    mf_mult = ((close - low) - (high - close)) / hl_range
    return (mf_mult * volume).rolling(period).sum() / volume.rolling(period).sum()

def bollinger_bands(series, window=20, num_std=2):
    middle = sma(series, window)
    std = series.rolling(window=window).std()
    return middle + std * num_std, middle, middle - std * num_std

def macd_indicator(series, fast=12, slow=26, signal=9):
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


# =============================================================================
# HELPERS
# =============================================================================

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

def _compute_streak(series, threshold):
    above = (series > threshold).astype(int)
    groups = above.ne(above.shift()).cumsum()
    return above.groupby(groups).cumsum()

def _compute_slope(series, window):
    x = np.arange(window, dtype=float)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()
    def _slope(vals):
        if len(vals) < window or np.isnan(vals).any():
            return np.nan
        y_mean = vals.mean()
        return ((x - x_mean) * (vals - y_mean)).sum() / x_var
    return series.rolling(window).apply(_slope, raw=True)

def _compute_consecutive_higher(close):
    higher = (close > close.shift(1)).astype(int)
    groups = higher.ne(higher.shift()).cumsum()
    return higher.groupby(groups).cumsum()


# =============================================================================
# FEATURE ENGINEERING (36 features — must match train_model.py exactly)
# =============================================================================

def _build_features(df):
    bpd = _detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    features = pd.DataFrame(index=df.index)

    # Core
    rsi_period = max(14, int(14 * scale))
    roc_period = max(21, int(21 * scale))
    z_period = max(50, int(50 * scale))
    rsi_val = rsi(close, rsi_period)
    roc_val = roc(close, roc_period)
    z_val = zscore(close, z_period)

    features["rsi_14"] = rsi_val
    features["roc_21"] = roc_val
    features["zscore_50"] = z_val
    features["rsi_above_70_streak"] = _compute_streak(rsi_val, 70)
    features["rsi_above_75_streak"] = _compute_streak(rsi_val, 75)
    features["roc_above_10_streak"] = _compute_streak(roc_val, 10)
    features["rsi_slope_10"] = _compute_slope(rsi_val, max(10, int(10 * scale)))

    adx_val, plus_di, minus_di = adx(df, max(14, int(14 * scale)))
    features["adx_14"] = adx_val
    features["plus_di_minus_di"] = plus_di - minus_di
    sma_200 = sma(close, max(200, int(200 * scale)))
    features["sma_200_distance"] = (close - sma_200) / sma_200 * 100
    ema_50 = ema(close, max(50, int(50 * scale)))
    features["ema_50_slope"] = _compute_slope(ema_50, max(20, int(20 * scale)))

    atr_val = atr(df, max(14, int(14 * scale)))
    atr_avg = atr_val.rolling(max(63, int(63 * scale))).mean()
    features["atr_14_ratio"] = atr_val / atr_avg.replace(0, np.nan)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close, max(20, int(20 * scale)))
    features["bb_width"] = (bb_upper - bb_lower) / bb_mid.replace(0, np.nan)
    log_returns = np.log(close / close.shift(1))
    features["realized_vol_20"] = log_returns.rolling(max(20, int(20 * scale))).std()

    obv_val = obv(df)
    features["obv_slope_20"] = _compute_slope(obv_val, max(20, int(20 * scale)))
    features["cmf_20"] = cmf(df, max(20, int(20 * scale)))
    vol_avg = volume.rolling(max(50, int(50 * scale))).mean()
    features["volume_ratio"] = volume / vol_avg.replace(0, np.nan)

    macd_line, _, histogram = macd_indicator(close)
    features["macd_histogram"] = histogram
    price_high_20 = close >= close.rolling(max(20, int(20 * scale))).max()
    macd_declining = macd_line < macd_line.shift(max(5, int(5 * scale)))
    features["macd_divergence"] = (price_high_20 & macd_declining).astype(int)
    rsi_declining = rsi_val < rsi_val.shift(max(5, int(5 * scale)))
    features["price_rsi_divergence"] = (price_high_20 & rsi_declining).astype(int)

    w20 = max(20, int(20 * scale))
    w10 = max(10, int(10 * scale))
    w252 = max(252, int(252 * scale))
    ret_lag = log_returns.shift(1)
    features["return_autocorr_20"] = log_returns.rolling(w20).corr(ret_lag)
    var_1 = log_returns.rolling(w20).var()
    ret_q = np.log(close / close.shift(w10))
    var_q = ret_q.rolling(w20).var()
    features["variance_ratio_10"] = var_q / (w10 * var_1).replace(0, np.nan)
    features["roc_acceleration"] = roc_val - roc_val.shift(max(5, int(5 * scale)))
    features["consec_higher_close"] = _compute_consecutive_higher(close)
    roll_min = close.rolling(w252).min()
    roll_max = close.rolling(w252).max()
    features["price_percentile_252"] = (close - roll_min) / (roll_max - roll_min).replace(0, np.nan)
    features["vol_price_corr_20"] = volume.rolling(w20).corr(close)
    features["atr_slope_10"] = _compute_slope(atr_val, w10)
    intraday_range = (high - low) / close.replace(0, np.nan)
    atr_norm = atr_val / close.replace(0, np.nan)
    features["intraday_range_ratio"] = intraday_range / atr_norm.replace(0, np.nan)

    # v3 extras
    features["past_return_1"] = close.pct_change(1)
    features["past_return_5"] = close.pct_change(max(5, int(5 * scale)))
    features["past_return_10"] = close.pct_change(max(10, int(10 * scale)))

    rolling_high = close.rolling(w20).max()
    features["drawdown_from_high"] = (close - rolling_high) / rolling_high.replace(0, np.nan)
    rolling_low = close.rolling(w20).min()
    features["distance_from_low"] = (close - rolling_low) / rolling_low.replace(0, np.nan)

    bb_range = (bb_upper - bb_lower).replace(0, np.nan)
    features["bb_pctb"] = (close - bb_lower) / bb_range

    log_ret = np.log(close / close.shift(1))
    features["return_skewness"] = log_ret.rolling(w20).skew()

    lookback = max(3, int(3 * scale))
    features["rsi_oversold_recovery"] = (
        (rsi_val > 30) & (rsi_val.shift(lookback) < 30)
    ).astype(int)

    # Meta
    features["bars_per_day"] = bpd

    return features


# =============================================================================
# ENHANCED PEAK SHAVER FALLBACK
# =============================================================================

def _fallback_signals(data):
    """Enhanced Peak Shaver fallback — continuous positions."""
    close = data["Close"]
    n = len(data)

    rsi_val = rsi(close, 14)
    roc_val = roc(close, 21)
    z = zscore(close, 50)
    adx_val, plus_di, minus_di = adx(data, 14)
    atr_val = atr(data, 14)
    atr_63 = atr_val.rolling(63).mean()
    sma_200 = sma(close, 200)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_hist = macd_line - macd_line.ewm(span=9, adjust=False).mean()
    sma200_slope = sma_200.pct_change(60)

    signal = pd.Series(1.0, index=data.index)

    # Peak Shaver: partial at overbought
    signal[(rsi_val > 70) & (roc_val > 8) & (z > 0.6)] = 0.3
    # Blow-off: partial short
    signal[(rsi_val > 85) & (z > 3.0)] = -0.7
    # Bearish regime: reduced / short
    bearish = (adx_val > 25) & (minus_di > plus_di) & (close < sma_200)
    signal[bearish] = 0.2
    signal[bearish & (macd_hist < 0) & (sma200_slope < 0)] = -0.5
    # Vol spike: reduced
    vol_ratio = atr_val / atr_63.replace(0, np.nan)
    signal[(vol_ratio > 1.5) & (signal > 0.5)] = 0.3
    # Oversold recovery: long
    signal[(rsi_val < 30) & (z < -1.5)] = 1.0

    signal.iloc[:200] = 1.0

    # Hysteresis — suppress changes < 0.1
    values = signal.values.copy()
    for i in range(1, n):
        if abs(values[i] - values[i - 1]) < 0.1:
            values[i] = values[i - 1]

    return pd.Series(values, index=data.index).fillna(1.0).astype(float)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_signals(data: pd.DataFrame) -> pd.Series:
    """Generate continuous trading positions from OHLCV data."""
    model = _load_model()
    if model is None:
        return _fallback_signals(data)

    # Extract model components
    xgb_m = model["xgb"]
    rf_m = model["rf"]
    scaler = model["scaler"]
    feat_names = model["feature_names"]
    xgb_w = model["xgb_w"]
    rf_w = model["rf_w"]
    cfg = model["config"]

    # Build features
    features = _build_features(data)
    X = features[feat_names]
    valid = X.notna().all(axis=1)

    # Predict
    pred = pd.Series(np.nan, index=data.index)
    if valid.sum() > 0:
        X_s = scaler.transform(X[valid])
        pred.loc[valid] = xgb_w * xgb_m.predict(X_s) + rf_w * rf_m.predict(X_s)

    # Map predictions to continuous positions
    if "alpha" in cfg:
        # Continuous calibration: clip(alpha * (pred - center), -max_short, max_long)
        alpha = cfg["alpha"]
        center = cfg["center"]
        max_long = cfg["max_long"]
        max_short = cfg["max_short"]
        positions = pd.Series(0.0, index=data.index)
        valid_pred = pred.notna()
        if valid_pred.any():
            raw = alpha * (pred[valid_pred] - center)
            positions.loc[valid_pred] = np.clip(raw, -max_short, max_long)
    else:
        # Legacy discrete config — convert to continuous mapping
        long_thresh = cfg["long_thresh"]
        positions = pd.Series(0.0, index=data.index)
        positions[pred.notna() & (pred >= long_thresh)] = 1.0

        if cfg["mode"] == "long_flat_short":
            short_thresh = cfg["short_thresh"]
            positions[pred.notna() & (pred <= short_thresh)] = -1.0

    # Warmup: long for first 200 bars (not enough feature history)
    positions.iloc[:200] = 1.0

    # Hysteresis: suppress position changes < 0.1
    n = len(data)
    vals = positions.values.copy().astype(float)
    for i in range(1, n):
        if abs(vals[i] - vals[i - 1]) < 0.1:
            vals[i] = vals[i - 1]

    return pd.Series(vals, index=data.index).fillna(0.0).astype(float)
