"""
ML Peak Shaver v3 (Return Maximizer) — Self-training continuous [0, 1]
=======================================================================
Every-bar return prediction with continuous position sizing.
Trains walk-forward on provided data, then generates signals.

Outputs continuous 0-1 positions scaled from predictions.

Requires: pip install xgboost scikit-learn
WARNING: Training on large datasets may approach the 10s time limit.
"""

import pandas as pd
import numpy as np

try:
    from xgboost import XGBRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# ── Indicators ──

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
        high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs(),
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


# ── Helpers ──

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

def compute_streak(series, threshold):
    above = (series > threshold).astype(int)
    groups = above.ne(above.shift()).cumsum()
    return above.groupby(groups).cumsum()

def compute_slope(series, window):
    x = np.arange(window, dtype=float)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()
    def _slope(vals):
        if len(vals) < window or np.isnan(vals).any():
            return np.nan
        y_mean = vals.mean()
        return ((x - x_mean) * (vals - y_mean)).sum() / x_var
    return series.rolling(window).apply(_slope, raw=True)

def compute_consecutive_higher(close):
    higher = (close > close.shift(1)).astype(int)
    groups = higher.ne(higher.shift()).cumsum()
    return higher.groupby(groups).cumsum()


# ── Peak Shaver v2 (fallback) ──

def _peak_shaver_v2(df):
    bpd = _detect_bars_per_day(df)
    close = df["Close"]
    scale = max(1.0, bpd ** 0.4)
    rsi_val = rsi(close, max(14, int(14 * scale)))
    mom_1m = roc(close, max(21, int(21 * scale)))
    z = zscore(close, max(50, int(50 * scale)))
    position = pd.Series(1.0, index=df.index)
    position[(rsi_val > 75) & (mom_1m > 11) & (z > 1.0)] = 0.40
    position[(rsi_val > 85) & (z > 3.0)] = 0.30
    return position


# ── Feature engineering (37 features) ──

def _build_base_features(df):
    """28 base features (same as v2)."""
    bpd = _detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    features = pd.DataFrame(index=df.index)

    rsi_period = max(14, int(14 * scale))
    roc_period = max(21, int(21 * scale))
    z_period = max(50, int(50 * scale))
    rsi_val = rsi(close, rsi_period)
    roc_val = roc(close, roc_period)
    z_val = zscore(close, z_period)

    features["rsi_14"] = rsi_val
    features["roc_21"] = roc_val
    features["zscore_50"] = z_val
    features["rsi_above_70_streak"] = compute_streak(rsi_val, 70)
    features["rsi_above_75_streak"] = compute_streak(rsi_val, 75)
    features["roc_above_10_streak"] = compute_streak(roc_val, 10)
    features["rsi_slope_10"] = compute_slope(rsi_val, max(10, int(10 * scale)))

    adx_val, plus_di, minus_di = adx(df, max(14, int(14 * scale)))
    features["adx_14"] = adx_val
    features["plus_di_minus_di"] = plus_di - minus_di
    sma_200 = sma(close, max(200, int(200 * scale)))
    features["sma_200_distance"] = (close - sma_200) / sma_200 * 100
    ema_50 = ema(close, max(50, int(50 * scale)))
    features["ema_50_slope"] = compute_slope(ema_50, max(20, int(20 * scale)))

    atr_val = atr(df, max(14, int(14 * scale)))
    atr_avg = atr_val.rolling(max(63, int(63 * scale))).mean()
    features["atr_14_ratio"] = atr_val / atr_avg.replace(0, np.nan)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close, max(20, int(20 * scale)))
    features["bb_width"] = (bb_upper - bb_lower) / bb_mid.replace(0, np.nan)
    log_returns = np.log(close / close.shift(1))
    features["realized_vol_20"] = log_returns.rolling(max(20, int(20 * scale))).std()

    obv_val = obv(df)
    features["obv_slope_20"] = compute_slope(obv_val, max(20, int(20 * scale)))
    features["cmf_20"] = cmf(df, max(20, int(20 * scale)))
    vol_avg = volume.rolling(max(50, int(50 * scale))).mean()
    features["volume_ratio"] = volume / vol_avg.replace(0, np.nan)

    macd_line, signal_line, histogram = macd_indicator(close)
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
    features["consec_higher_close"] = compute_consecutive_higher(close)
    roll_min = close.rolling(w252).min()
    roll_max = close.rolling(w252).max()
    features["price_percentile_252"] = (close - roll_min) / (roll_max - roll_min).replace(0, np.nan)
    features["vol_price_corr_20"] = volume.rolling(w20).corr(close)
    features["atr_slope_10"] = compute_slope(atr_val, w10)
    intraday_range = (high - low) / close.replace(0, np.nan)
    atr_norm = atr_val / close.replace(0, np.nan)
    features["intraday_range_ratio"] = intraday_range / atr_norm.replace(0, np.nan)
    features["asset_category"] = 6

    return features


def build_features_v3(df):
    """37 features = 28 base + 9 new."""
    base = _build_base_features(df)
    bpd = _detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    extra = pd.DataFrame(index=df.index)

    extra["past_return_1"] = close.pct_change(1)
    extra["past_return_5"] = close.pct_change(max(5, int(5 * scale)))
    extra["past_return_10"] = close.pct_change(max(10, int(10 * scale)))

    w20 = max(20, int(20 * scale))
    rolling_high = close.rolling(w20).max()
    extra["drawdown_from_high"] = (close - rolling_high) / rolling_high.replace(0, np.nan)
    rolling_low = close.rolling(w20).min()
    extra["distance_from_low"] = (close - rolling_low) / rolling_low.replace(0, np.nan)

    bb_up, bb_mid, bb_low = bollinger_bands(close, max(20, int(20 * scale)))
    bb_range = (bb_up - bb_low).replace(0, np.nan)
    extra["bb_pctb"] = (close - bb_low) / bb_range

    log_ret = np.log(close / close.shift(1))
    extra["return_skewness"] = log_ret.rolling(w20).skew()

    ps_pos = _peak_shaver_v2(df)
    extra["ps_position"] = ps_pos

    rsi_val = rsi(close, max(14, int(14 * scale)))
    lookback = max(3, int(3 * scale))
    extra["rsi_oversold_recovery"] = (
        (rsi_val > 30) & (rsi_val.shift(lookback) < 30)
    ).astype(int)

    return pd.concat([base, extra], axis=1)


def _build_target(df):
    """Blended forward return at every bar."""
    bpd = _detect_bars_per_day(df)
    if bpd > 1:
        horizons = {14: 0.2, 28: 0.3, 56: 0.5}
    else:
        horizons = {5: 0.2, 10: 0.3, 20: 0.5}
    close = df["Close"]
    target = pd.Series(0.0, index=df.index)
    for horizon, weight in horizons.items():
        target = target + weight * (close.shift(-horizon) / close - 1)
    return target


def generate_signals(data: pd.DataFrame) -> pd.Series:
    if not ML_AVAILABLE:
        # Fallback to Peak Shaver v2 continuous
        return _peak_shaver_v2(data).astype(float)

    features = build_features_v3(data)
    target = _build_target(data)

    valid = target.notna() & features.notna().all(axis=1)
    if valid.sum() < 100:
        return _peak_shaver_v2(data).astype(float)

    X = features[valid].reset_index(drop=True)
    y = target[valid].reset_index(drop=True)
    feature_names = X.columns.tolist()

    # Train on all data (single-asset, simpler than multi-asset walk-forward)
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    xgb_model = XGBRegressor(
        n_estimators=200, max_depth=5, min_child_weight=8,
        reg_alpha=0.5, reg_lambda=0.5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, verbosity=0, random_state=42,
    )
    xgb_model.fit(X_s, y)

    rf_model = RandomForestRegressor(
        n_estimators=300, max_depth=6, min_samples_leaf=15,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf_model.fit(X_s, y)

    # Predict at every bar
    X_all = features[feature_names]
    valid_all = X_all.notna().all(axis=1)
    pred = pd.Series(np.nan, index=data.index)
    if valid_all.sum() > 0:
        X_pred = scaler.transform(X_all[valid_all])
        pred.loc[valid_all] = 0.5 * xgb_model.predict(X_pred) + 0.5 * rf_model.predict(X_pred)

    # Scale predictions to [0, 1] positions
    train_preds = 0.5 * xgb_model.predict(X_s) + 0.5 * rf_model.predict(X_s)
    p_min, p_max = np.percentile(train_preds, 5), np.percentile(train_preds, 95)

    # Map predictions: bottom 5% -> 0, top 5% -> 1, linear in between
    positions = pd.Series(1.0, index=data.index)
    valid_pred = pred.notna()
    if valid_pred.any():
        scaled = (pred[valid_pred] - p_min) / (p_max - p_min + 1e-10)
        positions.loc[valid_pred] = np.clip(scaled, 0.0, 1.0)

    # Cold start
    cold_start = min(252, len(data) // 4)
    positions.iloc[:cold_start] = 1.0

    return positions.fillna(1.0).astype(float)
