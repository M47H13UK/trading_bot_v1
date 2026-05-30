"""
Pre-train ML model on ~100+ tickers, save as model.pkl for hackathon submission.
Never submitted — only run offline to produce the artifact.

Usage:
    python train_model.py                     # train on all daily + hourly data
    python train_model.py --daily-only        # skip hourly
    python train_model.py --data-dir ../test_data/daily  # custom dir

Outputs:
    submissions/model.pkl  (~2-5 MB)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import time
import warnings
warnings.filterwarnings("ignore")

try:
    from xgboost import XGBRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import joblib
except ImportError:
    print("ERROR: pip install xgboost scikit-learn joblib")
    sys.exit(1)

# Paths relative to this file (hackathon_repo/)
DAILY_DIR = Path(__file__).parent.parent / "test_data" / "daily"
HOURLY_DIR = Path(__file__).parent.parent / "test_data" / "hourly"
MODEL_PATH = Path(__file__).parent / "submissions" / "model.pkl"

TRANSACTION_COST = 0.0005
TRADING_DAYS = 252


# =============================================================================
# INDICATORS (same as strategy.py — must produce identical features)
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

def detect_bars_per_day(df):
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


# =============================================================================
# FEATURE ENGINEERING (36 features)
# =============================================================================

FEATURE_NAMES = [
    # Core (from v2 base, minus asset_category)
    "rsi_14", "roc_21", "zscore_50",
    "rsi_above_70_streak", "rsi_above_75_streak", "roc_above_10_streak", "rsi_slope_10",
    "adx_14", "plus_di_minus_di", "sma_200_distance", "ema_50_slope",
    "atr_14_ratio", "bb_width", "realized_vol_20",
    "obv_slope_20", "cmf_20", "volume_ratio",
    "macd_histogram", "macd_divergence", "price_rsi_divergence",
    "return_autocorr_20", "variance_ratio_10", "roc_acceleration",
    "consec_higher_close", "price_percentile_252",
    "vol_price_corr_20", "atr_slope_10", "intraday_range_ratio",
    # v3 extras (minus ps_position)
    "past_return_1", "past_return_5", "past_return_10",
    "drawdown_from_high", "distance_from_low", "bb_pctb",
    "return_skewness", "rsi_oversold_recovery",
    # Meta
    "bars_per_day",
]

assert len(FEATURE_NAMES) == 37, f"Expected 37, got {len(FEATURE_NAMES)}"


def build_features(df):
    """Build 36 ML features from OHLCV data."""
    bpd = detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    features = pd.DataFrame(index=df.index)

    # --- Core indicators ---
    rsi_period = max(14, int(14 * scale))
    roc_period = max(21, int(21 * scale))
    z_period = max(50, int(50 * scale))
    rsi_val = rsi(close, rsi_period)
    roc_val = roc(close, roc_period)
    z_val = zscore(close, z_period)

    features["rsi_14"] = rsi_val
    features["roc_21"] = roc_val
    features["zscore_50"] = z_val

    # Momentum persistence
    features["rsi_above_70_streak"] = compute_streak(rsi_val, 70)
    features["rsi_above_75_streak"] = compute_streak(rsi_val, 75)
    features["roc_above_10_streak"] = compute_streak(roc_val, 10)
    features["rsi_slope_10"] = compute_slope(rsi_val, max(10, int(10 * scale)))

    # Trend strength
    adx_val, plus_di, minus_di = adx(df, max(14, int(14 * scale)))
    features["adx_14"] = adx_val
    features["plus_di_minus_di"] = plus_di - minus_di
    sma_200 = sma(close, max(200, int(200 * scale)))
    features["sma_200_distance"] = (close - sma_200) / sma_200 * 100
    ema_50 = ema(close, max(50, int(50 * scale)))
    features["ema_50_slope"] = compute_slope(ema_50, max(20, int(20 * scale)))

    # Volatility
    atr_val = atr(df, max(14, int(14 * scale)))
    atr_avg = atr_val.rolling(max(63, int(63 * scale))).mean()
    features["atr_14_ratio"] = atr_val / atr_avg.replace(0, np.nan)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close, max(20, int(20 * scale)))
    features["bb_width"] = (bb_upper - bb_lower) / bb_mid.replace(0, np.nan)
    log_returns = np.log(close / close.shift(1))
    features["realized_vol_20"] = log_returns.rolling(max(20, int(20 * scale))).std()

    # Volume
    obv_val = obv(df)
    features["obv_slope_20"] = compute_slope(obv_val, max(20, int(20 * scale)))
    features["cmf_20"] = cmf(df, max(20, int(20 * scale)))
    vol_avg = volume.rolling(max(50, int(50 * scale))).mean()
    features["volume_ratio"] = volume / vol_avg.replace(0, np.nan)

    # Divergences
    macd_line, _, histogram = macd_indicator(close)
    features["macd_histogram"] = histogram
    price_high_20 = close >= close.rolling(max(20, int(20 * scale))).max()
    macd_declining = macd_line < macd_line.shift(max(5, int(5 * scale)))
    features["macd_divergence"] = (price_high_20 & macd_declining).astype(int)
    rsi_declining = rsi_val < rsi_val.shift(max(5, int(5 * scale)))
    features["price_rsi_divergence"] = (price_high_20 & rsi_declining).astype(int)

    # Regime
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

    # --- v3 extras (minus ps_position) ---
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

    return features[FEATURE_NAMES]


def build_target(df):
    """Blended forward return — multi-horizon."""
    bpd = detect_bars_per_day(df)
    if bpd > 1:  # hourly
        horizons = {14: 0.2, 28: 0.3, 56: 0.5}
    else:  # daily
        horizons = {5: 0.2, 10: 0.3, 20: 0.5}
    close = df["Close"]
    target = pd.Series(0.0, index=df.index)
    for horizon, weight in horizons.items():
        target = target + weight * (close.shift(-horizon) / close - 1)
    return target


# =============================================================================
# DATA LOADING
# =============================================================================

def load_csv(filepath):
    probe = pd.read_csv(filepath, nrows=5, header=None)
    if probe.iloc[0, 0] == "Price":
        df = pd.read_csv(filepath, header=[0, 1], index_col=0, parse_dates=True)
        df.columns = df.columns.get_level_values(0)
    else:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return None
    return df.ffill().dropna()


def load_all_assets(*dirs):
    """Load all CSVs from given directories. Returns list of (stem, df)."""
    assets = []
    seen = set()
    for d in dirs:
        d = Path(d)
        if not d.exists():
            continue
        for f in sorted(d.glob("*.csv")):
            stem = f.stem
            if stem in seen or stem == "DATA_REFERENCE":
                continue
            try:
                df = load_csv(str(f))
                if df is not None and len(df) >= 200:
                    assets.append((stem, df))
                    seen.add(stem)
            except Exception:
                pass
    return assets


# =============================================================================
# BACKTESTING (mirrors test.py exactly)
# =============================================================================

def backtest_sharpe(close, positions):
    """Backtest continuous positions using test.py methodology. Returns Sharpe."""
    returns = close.pct_change()
    shifted = positions.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    r, pos = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = pos.diff().abs().fillna(0) * TRANSACTION_COST
    strat_ret = pos * r - costs
    vol = strat_ret.std()
    if vol < 1e-8:
        return 0.0
    return float((strat_ret.mean() / vol) * np.sqrt(TRADING_DAYS))


# =============================================================================
# TRAINING
# =============================================================================

def train(daily_dir=None, hourly_dir=None, daily_only=False):
    daily_dir = daily_dir or DAILY_DIR
    hourly_dir = hourly_dir or HOURLY_DIR

    dirs = [daily_dir]
    if not daily_only and Path(hourly_dir).exists():
        dirs.append(hourly_dir)

    assets = load_all_assets(*dirs)
    if not assets:
        print("No data files found!")
        return

    print(f"Loaded {len(assets)} assets from {len(dirs)} dir(s)")

    # --- Build features + targets ---
    print("Building features and targets...")
    all_X, all_y, all_w = [], [], []
    asset_close = {}  # for calibration

    for stem, df in assets:
        features = build_features(df)
        target = build_target(df)

        valid = target.notna() & features.notna().all(axis=1)
        if valid.sum() < 100:
            continue

        t = target[valid]
        lo, hi = t.quantile(0.01), t.quantile(0.99)
        t = t.clip(lo, hi)

        all_X.append(features[valid])
        all_y.append(t)
        all_w.append(t.abs() + 0.005)
        asset_close[stem] = df

    if not all_X:
        print("No valid training data!")
        return

    X = pd.concat(all_X, ignore_index=True)
    y = pd.concat(all_y, ignore_index=True)
    w = pd.concat(all_w, ignore_index=True)

    print(f"Pooled: {len(X):,} bars, {len(asset_close)} assets")
    print(f"Target: mean={y.mean():.4f}, std={y.std():.4f}")

    # --- Train models on all data ---
    print("\nTraining XGBoost...")
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    xgb = XGBRegressor(
        n_estimators=300, max_depth=5, min_child_weight=8,
        reg_alpha=0.5, reg_lambda=0.5,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        verbosity=0, random_state=42,
    )
    xgb.fit(X_s, y, sample_weight=w.values)

    print("Training RandomForest...")
    rf = RandomForestRegressor(
        n_estimators=300, max_depth=6, min_samples_leaf=15,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf.fit(X_s, y, sample_weight=w.values)

    # Feature importances
    imp = pd.Series(
        xgb.feature_importances_ + rf.feature_importances_,
        index=FEATURE_NAMES
    ).sort_values(ascending=False)
    print("\nTop 10 features:")
    for fname, v in imp.head(10).items():
        print(f"  {fname:<30} {v:.4f}")

    # --- Calibrate continuous mapping ---
    print("\nCalibrating continuous positions...")
    # Get ensemble weights via quick OOS check
    split = int(len(X_s) * 0.8)
    X_train_s, X_val_s = X_s[:split], X_s[split:]
    y_val = y.iloc[split:]

    xgb_tmp = XGBRegressor(
        n_estimators=300, max_depth=5, min_child_weight=8,
        reg_alpha=0.5, reg_lambda=0.5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, verbosity=0, random_state=42,
    )
    xgb_tmp.fit(X_train_s, y.iloc[:split], sample_weight=w.iloc[:split].values)
    rf_tmp = RandomForestRegressor(
        n_estimators=300, max_depth=6, min_samples_leaf=15,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf_tmp.fit(X_train_s, y.iloc[:split], sample_weight=w.iloc[:split].values)

    xgb_mse = ((xgb_tmp.predict(X_val_s) - y_val.values) ** 2).mean()
    rf_mse = ((rf_tmp.predict(X_val_s) - y_val.values) ** 2).mean()
    inv_total = 1 / (xgb_mse + 1e-10) + 1 / (rf_mse + 1e-10)
    xgb_w = (1 / (xgb_mse + 1e-10)) / inv_total
    rf_w = (1 / (rf_mse + 1e-10)) / inv_total
    print(f"Ensemble weights: XGB={xgb_w:.2%}, RF={rf_w:.2%}")

    # Predict on all training data (using final models)
    full_preds = xgb_w * xgb.predict(X_s) + rf_w * rf.predict(X_s)

    # Per-asset predictions for calibration
    print("Running per-asset calibration backtest...")
    asset_preds = {}
    for stem, df in asset_close.items():
        features = build_features(df)
        X_a = features[FEATURE_NAMES]
        valid = X_a.notna().all(axis=1)
        pred = pd.Series(np.nan, index=df.index)
        if valid.sum() > 0:
            X_as = scaler.transform(X_a[valid])
            pred.loc[valid] = xgb_w * xgb.predict(X_as) + rf_w * rf.predict(X_as)
        asset_preds[stem] = pred

    # Sweep continuous mapping: position = clip(alpha * (pred - center), -max_short, max_long)
    best_sharpe = -999
    best_config = None
    pred_center = float(np.median(full_preds))

    # Helper to apply hysteresis
    def _apply_hysteresis(positions_arr, min_change=0.1):
        vals = positions_arr.copy()
        for i in range(1, len(vals)):
            if abs(vals[i] - vals[i - 1]) < min_change:
                vals[i] = vals[i - 1]
        return vals

    # Alpha sweep (scale factor)
    alphas = [5, 10, 15, 20, 30, 50, 75, 100]
    max_positions = [1.0, 1.25, 1.5, 1.75, 2.0]  # leverage options

    print("\n  Sweeping continuous configs (alpha × max_pos)...")
    for alpha in alphas:
        for max_pos in max_positions:
            sharpes = []
            for stem, df in asset_close.items():
                pred = asset_preds[stem]
                raw = alpha * (pred - pred_center)
                positions = pd.Series(0.0, index=df.index)
                valid_p = pred.notna()
                if valid_p.any():
                    positions.loc[valid_p] = np.clip(
                        raw[valid_p], -max_pos, max_pos
                    )
                positions.iloc[:200] = 1.0  # warmup
                positions = pd.Series(
                    _apply_hysteresis(positions.values), index=df.index
                )
                s = backtest_sharpe(df["Close"], positions)
                sharpes.append(s)

            avg = np.mean(sharpes)
            if avg > best_sharpe:
                best_sharpe = avg
                best_config = {
                    "mode": "continuous",
                    "alpha": float(alpha),
                    "center": pred_center,
                    "max_long": float(max_pos),
                    "max_short": float(max_pos),
                }

        # Print one line per alpha (best max_pos at that alpha)
        print(f"    alpha={alpha:3d}  best_avg_sharpe={best_sharpe:.4f}")

    # Also sweep asymmetric: different max_long vs max_short
    print("\n  Sweeping asymmetric leverage...")
    best_alpha = best_config["alpha"]
    for max_long in [1.0, 1.5, 2.0]:
        for max_short in [0.5, 1.0, 1.5, 2.0]:
            sharpes = []
            for stem, df in asset_close.items():
                pred = asset_preds[stem]
                raw = best_alpha * (pred - pred_center)
                positions = pd.Series(0.0, index=df.index)
                valid_p = pred.notna()
                if valid_p.any():
                    positions.loc[valid_p] = np.clip(
                        raw[valid_p], -max_short, max_long
                    )
                positions.iloc[:200] = 1.0
                positions = pd.Series(
                    _apply_hysteresis(positions.values), index=df.index
                )
                s = backtest_sharpe(df["Close"], positions)
                sharpes.append(s)

            avg = np.mean(sharpes)
            if avg > best_sharpe:
                best_sharpe = avg
                best_config = {
                    "mode": "continuous",
                    "alpha": float(best_alpha),
                    "center": pred_center,
                    "max_long": float(max_long),
                    "max_short": float(max_short),
                }

    print(f"\n  BEST CONFIG: {best_config}")
    print(f"  BEST AVG SHARPE: {best_sharpe:.4f}")

    # --- Save model ---
    artifact = {
        "xgb": xgb,
        "rf": rf,
        "scaler": scaler,
        "feature_names": FEATURE_NAMES,
        "xgb_w": xgb_w,
        "rf_w": rf_w,
        "config": best_config,
        "n_assets": len(asset_close),
        "n_bars": len(X),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH, compress=3)
    size_mb = MODEL_PATH.stat().st_size / 1024 / 1024
    print(f"\nSaved: {MODEL_PATH} ({size_mb:.1f} MB)")

    # --- Print summary per-asset with best config ---
    print(f"\n{'='*80}")
    print("PER-ASSET RESULTS (best config)")
    print(f"{'='*80}")

    cfg = best_config
    sharpes = []
    for stem, df in sorted(asset_close.items()):
        pred = asset_preds[stem]
        raw = cfg["alpha"] * (pred - cfg["center"])
        positions = pd.Series(0.0, index=df.index)
        valid_p = pred.notna()
        if valid_p.any():
            positions.loc[valid_p] = np.clip(
                raw[valid_p], -cfg["max_short"], cfg["max_long"]
            )
        positions.iloc[:200] = 1.0
        positions = pd.Series(
            _apply_hysteresis(positions.values), index=df.index
        )
        s = backtest_sharpe(df["Close"], positions)
        # B&H sharpe
        bh_ret = df["Close"].pct_change().dropna()
        bh_sharpe = (bh_ret.mean() / bh_ret.std()) * np.sqrt(252) if bh_ret.std() > 1e-8 else 0
        beats_str = "+" if s > bh_sharpe else "-"
        print(f"  [{beats_str}] {stem:<12}  Sharpe={s:>6.2f}  B&H={bh_sharpe:>6.2f}  delta={s-bh_sharpe:>+6.2f}")
        sharpes.append(s)

    bnh_sharpes = []
    for stem, df in asset_close.items():
        bh_ret = df["Close"].pct_change().dropna()
        bnh_sharpes.append((bh_ret.mean() / bh_ret.std()) * np.sqrt(252) if bh_ret.std() > 1e-8 else 0)

    beats = sum(1 for s, b in zip(sharpes, bnh_sharpes) if s > b)
    print(f"\nAvg Sharpe: {np.mean(sharpes):.4f}  (B&H: {np.mean(bnh_sharpes):.4f})")
    print(f"Beats B&H: {beats}/{len(sharpes)} ({beats/len(sharpes)*100:.0f}%)")

    return artifact


if __name__ == "__main__":
    t0 = time.time()
    daily_only = "--daily-only" in sys.argv
    custom_dir = None
    for i, arg in enumerate(sys.argv):
        if arg == "--data-dir" and i + 1 < len(sys.argv):
            custom_dir = sys.argv[i + 1]

    train(
        daily_dir=custom_dir or DAILY_DIR,
        hourly_dir=HOURLY_DIR,
        daily_only=daily_only,
    )
    print(f"\nTotal time: {time.time() - t0:.1f}s")
