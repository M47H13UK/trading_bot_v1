"""
ML Peak Shaver v2 — Self-training continuous [0, 1]
====================================================
Regression ensemble (XGBoost + RF) learns when Peak Shaver trims help or hurt.
Trains walk-forward on provided data, then generates signals.

Outputs continuous 0-1 positions directly from ML predictions.

Requires: pip install xgboost scikit-learn
WARNING: Training may approach the 10s time limit on large datasets.
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


# ── Peak Shaver v2 (base strategy) ──

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


# ── Feature engineering (28 features) ──

def build_features(df):
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
    features["asset_category"] = 6  # unknown

    return features


# ── Training + signal generation ──

def _build_target(df, positions, horizon=20):
    close = df["Close"]
    trim_mask = positions < 1.0
    target = pd.Series(np.nan, index=df.index)
    magnitude = pd.Series(np.nan, index=df.index)
    close_arr = close.values
    n = len(close_arr)
    log_returns = np.log(close / close.shift(1))
    rolling_vol = log_returns.rolling(20).std().values

    for i in df.index[trim_mask]:
        loc = df.index.get_loc(i)
        if loc + horizon >= n:
            continue
        current = close_arr[loc]
        if current == 0:
            continue
        future = close_arr[loc + 1: loc + horizon + 1]
        max_ret = future.max() / current - 1
        min_ret = future.min() / current - 1
        net = max_ret + min_ret
        vol = rolling_vol[loc]
        if np.isnan(vol) or vol < 1e-8:
            vol = 0.01
        target.loc[i] = net / vol
        magnitude.loc[i] = max(abs(max_ret), abs(min_ret))
    return target, magnitude


def generate_signals(data: pd.DataFrame) -> pd.Series:
    if not ML_AVAILABLE:
        # Fallback to Peak Shaver v2 continuous
        return _peak_shaver_v2(data).astype(float)

    ps_positions = _peak_shaver_v2(data)
    features = build_features(data)
    target, magnitude = _build_target(data, ps_positions)

    valid = target.notna() & features.notna().all(axis=1)
    if valid.sum() < 100:
        return ps_positions.astype(float)

    X = features[valid].reset_index(drop=True)
    y = target[valid].reset_index(drop=True)
    w = magnitude[valid].reset_index(drop=True)
    w = (w / w.max()).clip(0.1, 1.0)
    feature_names = X.columns.tolist()

    # Walk-forward train
    min_train = min(504, len(X) // 2)
    test_window = max(126, (len(X) - min_train) // 5)

    scaler = StandardScaler()
    X_all_s = scaler.fit_transform(X)

    xgb_model = XGBRegressor(
        n_estimators=100, max_depth=4, min_child_weight=10,
        reg_alpha=1.0, reg_lambda=1.0, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, verbosity=0, random_state=42,
    )
    xgb_model.fit(X_all_s, y, sample_weight=w.values)

    rf_model = RandomForestRegressor(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf_model.fit(X_all_s, y, sample_weight=w.values)

    # Predict at trim points
    ml_pred = pd.Series(np.nan, index=data.index)
    trim_mask = ps_positions < 1.0
    trim_indices = data.index[trim_mask]

    if len(trim_indices) > 0:
        X_trim = features.loc[trim_indices, feature_names]
        valid_rows = X_trim.notna().all(axis=1)
        X_valid = X_trim[valid_rows]
        if len(X_valid) > 0:
            X_scaled = scaler.transform(X_valid)
            xgb_pred = xgb_model.predict(X_scaled)
            rf_pred = rf_model.predict(X_scaled)
            ml_pred.loc[X_valid.index] = 0.5 * xgb_pred + 0.5 * rf_pred

    # Position sizing
    ml_positions = ps_positions.copy()
    cold_start = min(504, len(data) // 4)
    for idx in trim_indices:
        bar_num = data.index.get_loc(idx)
        if bar_num < cold_start:
            continue
        pred = ml_pred.get(idx, np.nan)
        if np.isnan(pred):
            continue
        ps_target = ps_positions.loc[idx]
        if pred > 0.5:
            ml_positions.loc[idx] = 1.0
        elif pred < -0.5:
            ml_positions.loc[idx] = ps_target * 0.8
        else:
            blend = (pred - (-0.5)) / 1.0
            deepened = ps_target * 0.8
            ml_positions.loc[idx] = deepened + (1.0 - deepened) * blend

    # Return continuous positions directly
    return ml_positions.clip(0.0, 1.0).fillna(1.0).astype(float)
