"""
ML-Enhanced Peak Shaver v2
==========================
Regression-based ensemble (XGBRegressor + RandomForestRegressor) learns when
Peak Shaver trims are harmful (parabolic continuation) vs correct (impending drop).
Multi-horizon labeling, magnitude-weighted samples, dynamic ensemble weights.

Requirements:
    pip install xgboost scikit-learn joblib
"""

import numpy as np
import pandas as pd
from pathlib import Path

from trading_bot import (
    rsi, roc, zscore, atr, adx, obv, cmf, ema, sma,
    bollinger_bands, macd_indicator,
    strategy_peak_shaver, _detect_bars_per_day,
    Backtester, load_csv_data, TICKER_INFO, COMMISSION,
    TEST_DATA_DIR, HOURLY_DATA_DIR,
)

try:
    from xgboost import XGBRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# Category mapping for asset_category feature
CATEGORY_ORDINAL = {
    "Crypto": 0, "Stock": 1, "Sector ETF": 2, "Index ETF": 3,
    "Bond ETF": 4, "Commodity ETF": 5, "Other": 6,
}


# =============================================================================
# HELPERS
# =============================================================================

def compute_streak(series, threshold):
    """Count consecutive bars where series > threshold."""
    above = (series > threshold).astype(int)
    groups = above.ne(above.shift()).cumsum()
    streaks = above.groupby(groups).cumsum()
    return streaks


def compute_slope(series, window):
    """Rolling linear regression slope."""
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
    """Count streak of consecutive higher closes."""
    higher = (close > close.shift(1)).astype(int)
    groups = higher.ne(higher.shift()).cumsum()
    return higher.groupby(groups).cumsum()


# =============================================================================
# STEP 1: FEATURE ENGINEERING (28 features)
# =============================================================================

def build_features(df, asset_category=None):
    """Build 28 ML features from OHLCV data. Returns DataFrame aligned to df.index."""
    bpd = _detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    features = pd.DataFrame(index=df.index)

    # --- A. Trigger indicators ---
    rsi_period = max(14, int(14 * scale))
    roc_period = max(21, int(21 * scale))
    z_period = max(50, int(50 * scale))

    rsi_val = rsi(close, rsi_period)
    roc_val = roc(close, roc_period)
    z_val = zscore(close, z_period)

    features["rsi_14"] = rsi_val
    features["roc_21"] = roc_val
    features["zscore_50"] = z_val

    # --- B. Momentum persistence ---
    features["rsi_above_70_streak"] = compute_streak(rsi_val, 70)
    features["rsi_above_75_streak"] = compute_streak(rsi_val, 75)
    features["roc_above_10_streak"] = compute_streak(roc_val, 10)
    features["rsi_slope_10"] = compute_slope(rsi_val, max(10, int(10 * scale)))

    # --- C. Trend strength ---
    adx_val, plus_di, minus_di = adx(df, max(14, int(14 * scale)))
    features["adx_14"] = adx_val
    features["plus_di_minus_di"] = plus_di - minus_di

    sma_200 = sma(close, max(200, int(200 * scale)))
    features["sma_200_distance"] = (close - sma_200) / sma_200 * 100

    ema_50 = ema(close, max(50, int(50 * scale)))
    features["ema_50_slope"] = compute_slope(ema_50, max(20, int(20 * scale)))

    # --- D. Volatility regime ---
    atr_val = atr(df, max(14, int(14 * scale)))
    atr_avg = atr_val.rolling(max(63, int(63 * scale))).mean()
    features["atr_14_ratio"] = atr_val / atr_avg.replace(0, np.nan)

    bb_upper, bb_mid, bb_lower = bollinger_bands(close, max(20, int(20 * scale)))
    features["bb_width"] = (bb_upper - bb_lower) / bb_mid.replace(0, np.nan)

    log_returns = np.log(close / close.shift(1))
    features["realized_vol_20"] = log_returns.rolling(max(20, int(20 * scale))).std()

    # --- E. Volume patterns ---
    obv_val = obv(df)
    features["obv_slope_20"] = compute_slope(obv_val, max(20, int(20 * scale)))
    features["cmf_20"] = cmf(df, max(20, int(20 * scale)))

    vol_avg = volume.rolling(max(50, int(50 * scale))).mean()
    features["volume_ratio"] = volume / vol_avg.replace(0, np.nan)

    # --- F. Divergences ---
    macd_line, signal_line, histogram = macd_indicator(close)
    features["macd_histogram"] = histogram

    price_high_20 = close >= close.rolling(max(20, int(20 * scale))).max()
    macd_declining = macd_line < macd_line.shift(max(5, int(5 * scale)))
    features["macd_divergence"] = (price_high_20 & macd_declining).astype(int)

    rsi_declining = rsi_val < rsi_val.shift(max(5, int(5 * scale)))
    features["price_rsi_divergence"] = (price_high_20 & rsi_declining).astype(int)

    # --- G. Regime detection (NEW) ---
    w20 = max(20, int(20 * scale))
    w10 = max(10, int(10 * scale))
    w252 = max(252, int(252 * scale))

    # Return autocorrelation (lag-1) — positive = trending
    ret_lag = log_returns.shift(1)
    features["return_autocorr_20"] = log_returns.rolling(w20).corr(ret_lag)

    # Variance ratio (Hurst proxy) — >1.0 = trending, <1.0 = mean-reverting
    var_1 = log_returns.rolling(w20).var()
    ret_q = np.log(close / close.shift(w10))
    var_q = ret_q.rolling(w20).var()
    features["variance_ratio_10"] = var_q / (w10 * var_1).replace(0, np.nan)

    # ROC acceleration (ROC of ROC) — positive = momentum accelerating
    features["roc_acceleration"] = roc_val - roc_val.shift(max(5, int(5 * scale)))

    # Consecutive higher closes — 8+ = strong buying pressure
    features["consec_higher_close"] = compute_consecutive_higher(close)

    # Price percentile in yearly range (0-1) — near 1.0 = new highs
    roll_min = close.rolling(w252).min()
    roll_max = close.rolling(w252).max()
    features["price_percentile_252"] = (close - roll_min) / (roll_max - roll_min).replace(0, np.nan)

    # Volume-price correlation — negative = exhaustion
    features["vol_price_corr_20"] = volume.rolling(w20).corr(close)

    # ATR slope — expanding (blow-off risk) vs contracting (healthy)
    features["atr_slope_10"] = compute_slope(atr_val, w10)

    # Intraday range ratio: (High-Low)/Close normalized by ATR — wide = climax
    intraday_range = (high - low) / close.replace(0, np.nan)
    atr_norm = atr_val / close.replace(0, np.nan)
    features["intraday_range_ratio"] = intraday_range / atr_norm.replace(0, np.nan)

    # --- H. Asset category (ordinal) ---
    cat_val = CATEGORY_ORDINAL.get(asset_category, 6) if asset_category else 6
    features["asset_category"] = cat_val

    return features


# =============================================================================
# STEP 2: MULTI-HORIZON REGRESSION TARGET
# =============================================================================

def build_regression_target(df, positions, horizon=20):
    """Build continuous regression target from multi-horizon forward analysis.

    Looks across 1..horizon bars forward. Computes max rally and max drawdown.
    Target = (max_ret + min_ret) / rolling_vol  (risk-adjusted net outlook).
    Positive = rally dominated (trim harmful), negative = drop dominated (trim correct).

    Also returns raw magnitude for sample weighting.
    """
    close = df["Close"]
    trim_mask = positions < 1.0

    target = pd.Series(np.nan, index=df.index)
    magnitude = pd.Series(np.nan, index=df.index)

    close_arr = close.values
    n = len(close_arr)

    # Backward-looking rolling vol for risk-adjustment
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

        # Net outlook: positive = rally dominated, negative = drop dominated
        net = max_ret + min_ret  # min_ret is negative

        vol = rolling_vol[loc]
        if np.isnan(vol) or vol < 1e-8:
            vol = 0.01

        target.loc[i] = net / vol
        magnitude.loc[i] = max(abs(max_ret), abs(min_ret))

    return target, magnitude


# =============================================================================
# STEP 3: WALK-FORWARD TRAINING (Regression + Dynamic Ensemble Weights)
# =============================================================================

def walk_forward_train_and_predict(all_features, all_targets, sample_weights=None,
                                    min_train=504, test_window=126):
    """Walk-forward regression with dynamic ensemble weighting.

    Returns:
        (final_models, oos_predictions, feature_importances)
        final_models includes dynamic XGB/RF weights from exponential-decay MSE tracking.
    """
    if not ML_AVAILABLE:
        raise ImportError("xgboost and scikit-learn required")

    valid = all_targets.notna() & all_features.notna().all(axis=1)
    X = all_features[valid].reset_index(drop=True)
    y = all_targets[valid].reset_index(drop=True)
    w = sample_weights[valid].reset_index(drop=True) if sample_weights is not None else None

    if len(X) < min_train + test_window:
        print(f"  Warning: only {len(X)} samples, reducing min_train")
        min_train = max(50, len(X) // 2)
        test_window = min(test_window, len(X) - min_train)

    oos_preds = pd.Series(np.nan, index=X.index)
    feature_names = X.columns.tolist()
    importances_accum = np.zeros(len(feature_names))
    n_folds = 0

    # Per-fold MSE tracking for dynamic ensemble weights
    xgb_mses = []
    rf_mses = []
    decay = 0.8

    start = min_train
    while start < len(X):
        end = min(start + test_window, len(X))

        X_train, y_train = X.iloc[:start], y.iloc[:start]
        X_test, y_test = X.iloc[start:end], y.iloc[start:end]
        w_train = w.iloc[:start].values if w is not None else None

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        xgb = XGBRegressor(
            n_estimators=100, max_depth=4, min_child_weight=10,
            reg_alpha=1.0, reg_lambda=1.0,
            learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            verbosity=0, random_state=42,
        )
        xgb.fit(X_train_s, y_train, sample_weight=w_train)

        rf = RandomForestRegressor(
            n_estimators=200, max_depth=5, min_samples_leaf=20,
            max_features="sqrt", random_state=42, n_jobs=-1,
        )
        rf.fit(X_train_s, y_train, sample_weight=w_train)

        xgb_pred = xgb.predict(X_test_s)
        rf_pred = rf.predict(X_test_s)

        # Track per-fold MSE
        xgb_mses.append(((xgb_pred - y_test.values) ** 2).mean())
        rf_mses.append(((rf_pred - y_test.values) ** 2).mean())

        # Dynamic weights: inverse of exponentially-decayed MSE
        n_past = len(xgb_mses)
        w_decay = np.array([decay ** (n_past - 1 - i) for i in range(n_past)])
        w_decay /= w_decay.sum()

        xgb_avg_mse = np.dot(w_decay, xgb_mses)
        rf_avg_mse = np.dot(w_decay, rf_mses)

        inv_total = 1.0 / (xgb_avg_mse + 1e-10) + 1.0 / (rf_avg_mse + 1e-10)
        xgb_w = (1.0 / (xgb_avg_mse + 1e-10)) / inv_total
        rf_w = (1.0 / (rf_avg_mse + 1e-10)) / inv_total

        oos_preds.iloc[start:end] = xgb_w * xgb_pred + rf_w * rf_pred

        importances_accum += xgb.feature_importances_ + rf.feature_importances_
        n_folds += 1
        start = end

    # Final ensemble weights from all folds
    if xgb_mses:
        n_past = len(xgb_mses)
        w_decay = np.array([decay ** (n_past - 1 - i) for i in range(n_past)])
        w_decay /= w_decay.sum()
        xgb_final_w = (1.0 / (np.dot(w_decay, xgb_mses) + 1e-10))
        rf_final_w = (1.0 / (np.dot(w_decay, rf_mses) + 1e-10))
        inv_total = xgb_final_w + rf_final_w
        xgb_final_w /= inv_total
        rf_final_w /= inv_total
    else:
        xgb_final_w, rf_final_w = 0.5, 0.5

    # Train final models on all data
    scaler_final = StandardScaler()
    X_all_s = scaler_final.fit_transform(X)
    w_all = w.values if w is not None else None

    xgb_final = XGBRegressor(
        n_estimators=100, max_depth=4, min_child_weight=10,
        reg_alpha=1.0, reg_lambda=1.0,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        verbosity=0, random_state=42,
    )
    xgb_final.fit(X_all_s, y, sample_weight=w_all)

    rf_final = RandomForestRegressor(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf_final.fit(X_all_s, y, sample_weight=w_all)

    if n_folds > 0:
        importances_accum /= (2 * n_folds)
    feat_imp = pd.Series(importances_accum, index=feature_names).sort_values(ascending=False)

    # OOS metrics
    valid_preds = oos_preds.dropna()
    if len(valid_preds) > 0:
        direction_acc = ((valid_preds > 0) == (y[valid_preds.index] > 0)).mean()
        rmse = np.sqrt(((valid_preds - y[valid_preds.index]) ** 2).mean())
        print(f"  Walk-forward OOS direction accuracy: {direction_acc:.1%} "
              f"(RMSE: {rmse:.3f}, {len(valid_preds)} samples, {n_folds} folds)")
        print(f"  Dynamic ensemble weights: XGB={xgb_final_w:.1%}, RF={rf_final_w:.1%}")

    models = (xgb_final, rf_final, scaler_final, feature_names, xgb_final_w, rf_final_w)
    return models, oos_preds, feat_imp


# =============================================================================
# STEP 4: ML-ENHANCED STRATEGY (Regression-based Position Sizing)
# =============================================================================

def strategy_ml_peak_shaver(df, models, asset_category=None, cold_start_bars=504):
    """ML-enhanced Peak Shaver with regression-based position sizing.

    Position mapping:
        pred > +0.5  -> stay 100% (strong parabolic override)
        pred < -0.5  -> deepen trim to ps_target * 0.8 (extra conviction)
        between      -> linear interpolation
    """
    ps_positions, ps_indicators = strategy_peak_shaver(df)
    features = build_features(df, asset_category=asset_category)

    if models is None:
        return ps_positions, {**ps_indicators, "ml_pred": pd.Series(np.nan, index=df.index)}

    xgb_model, rf_model, scaler, feature_names, xgb_w, rf_w = models

    ml_pred = pd.Series(np.nan, index=df.index)
    trim_mask = ps_positions < 1.0
    trim_indices = df.index[trim_mask]

    if len(trim_indices) > 0:
        X_trim = features.loc[trim_indices, feature_names]
        valid_rows = X_trim.notna().all(axis=1)
        X_valid = X_trim[valid_rows]

        if len(X_valid) > 0:
            X_scaled = scaler.transform(X_valid)
            xgb_pred = xgb_model.predict(X_scaled)
            rf_pred = rf_model.predict(X_scaled)
            ml_pred.loc[X_valid.index] = xgb_w * xgb_pred + rf_w * rf_pred

    # Regression-based position sizing
    ml_positions = ps_positions.copy()

    OVERRIDE_THRESH = 0.5   # above -> stay 100%
    DEEPEN_THRESH = -0.5    # below -> deepen trim to ps_target * 0.8

    for idx in trim_indices:
        bar_num = df.index.get_loc(idx)
        if bar_num < cold_start_bars:
            continue

        pred = ml_pred.get(idx, np.nan)
        if np.isnan(pred):
            continue

        ps_target = ps_positions.loc[idx]

        if pred > OVERRIDE_THRESH:
            # Strong parabolic signal — stay fully invested
            ml_positions.loc[idx] = 1.0
        elif pred < DEEPEN_THRESH:
            # High conviction drop — deepen trim
            ml_positions.loc[idx] = ps_target * 0.8
        else:
            # Linear interpolation: DEEPEN -> ps_target*0.8, OVERRIDE -> 1.0
            blend = (pred - DEEPEN_THRESH) / (OVERRIDE_THRESH - DEEPEN_THRESH)
            deepened = ps_target * 0.8
            ml_positions.loc[idx] = deepened + (1.0 - deepened) * blend

    indicators = {
        **ps_indicators,
        "ml_pred": ml_pred,
        "ml_positions": ml_positions,
        "ps_positions": ps_positions,
    }
    return ml_positions, indicators


# =============================================================================
# STEP 5: EVALUATION
# =============================================================================

def _load_all_assets(data_dir):
    """Load all CSVs from a directory. Returns list of (stem, name, category, df)."""
    csv_files = sorted(Path(data_dir).glob("*.csv"))
    assets = []
    for f in csv_files:
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        try:
            df = load_csv_data(str(f))
            if len(df) >= 100:
                assets.append((stem, name, category, df))
        except Exception:
            pass
    return assets


def train_ml_models(data_dir=None):
    """Train ML models on all assets from data_dir. Returns models tuple."""
    data_dir = data_dir or TEST_DATA_DIR

    if not ML_AVAILABLE:
        print("ERROR: xgboost/scikit-learn not installed. pip install xgboost scikit-learn")
        return None

    assets = _load_all_assets(data_dir)
    if not assets:
        print("No data files found.")
        return None

    # Auto-detect timeframe from first asset
    bpd = _detect_bars_per_day(assets[0][3])
    horizon = 56 if bpd > 1 else 20

    print(f"\nTraining ML models on {len(assets)} assets (horizon={horizon})...")

    all_features_list = []
    all_targets_list = []
    all_weights_list = []

    for stem, name, category, df in assets:
        features = build_features(df, asset_category=category)
        positions, _ = strategy_peak_shaver(df)
        target, magnitude = build_regression_target(df, positions, horizon=horizon)

        trim_mask = target.notna()
        if trim_mask.sum() == 0:
            continue

        all_features_list.append(features[trim_mask])
        all_targets_list.append(target[trim_mask])
        # Sample weights: |forward magnitude| + 0.1
        all_weights_list.append(magnitude[trim_mask] + 0.1)

    if not all_features_list:
        print("No trim signals found across assets.")
        return None

    pooled_features = pd.concat(all_features_list, ignore_index=True)
    pooled_targets = pd.concat(all_targets_list, ignore_index=True)
    pooled_weights = pd.concat(all_weights_list, ignore_index=True)

    print(f"  Pooled: {len(pooled_features)} trim signals across {len(assets)} assets")
    print(f"  Target stats: mean={pooled_targets.mean():.3f}, std={pooled_targets.std():.3f}")
    print(f"  Positive (harmful trims): {(pooled_targets > 0).mean():.1%}")

    models, oos_preds, feat_imp = walk_forward_train_and_predict(
        pooled_features, pooled_targets, sample_weights=pooled_weights
    )

    print(f"\n  Top 10 features:")
    for fname, imp in feat_imp.head(10).items():
        print(f"    {fname:<25} {imp:.4f}")

    return models


def evaluate_ml_enhancement(data_dir=None):
    """Full evaluation: train ML, compare ML PS vs vanilla PS on all assets."""
    data_dir = data_dir or TEST_DATA_DIR

    models = train_ml_models(data_dir)
    if models is None:
        return

    assets = _load_all_assets(data_dir)

    print(f"\n{'=' * 100}")
    print("ML PEAK SHAVER v2 vs VANILLA PEAK SHAVER — Per-Asset Comparison")
    print(f"{'=' * 100}")
    print(f"{'Asset':<12} {'Name':<22} {'Cat':<10} "
          f"{'PS Ret%':>8} {'ML Ret%':>8} {'Delta':>8} "
          f"{'PS Sharpe':>9} {'ML Sharpe':>9} {'B&H%':>8}")
    print("-" * 100)

    results = []
    for stem, name, category, df in assets:
        bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)

        ps_pos, _ = strategy_peak_shaver(df)
        ps_result = bt.run_positions(ps_pos, strategy_name="Peak Shaver v2")

        ml_pos, _ = strategy_ml_peak_shaver(df, models, asset_category=category)
        ml_result = bt.run_positions(ml_pos, strategy_name="ML Peak Shaver v2")

        delta = ml_result["total_return_pct"] - ps_result["total_return_pct"]
        status = "+" if delta > 0 else " " if delta == 0 else "-"

        print(f"[{status}] {stem:<10} {name:<22} {category:<10} "
              f"{ps_result['total_return_pct']:>+8.2f} {ml_result['total_return_pct']:>+8.2f} "
              f"{delta:>+8.2f} {ps_result['sharpe_ratio']:>9.2f} {ml_result['sharpe_ratio']:>9.2f} "
              f"{ps_result['buy_and_hold_return_pct']:>+8.2f}")

        results.append({
            "asset": stem, "name": name, "category": category,
            "ps_return": ps_result["total_return_pct"],
            "ml_return": ml_result["total_return_pct"],
            "delta": delta,
            "ps_sharpe": ps_result["sharpe_ratio"],
            "ml_sharpe": ml_result["sharpe_ratio"],
            "bnh_return": ps_result["buy_and_hold_return_pct"],
        })

    if not results:
        return

    print(f"\n{'=' * 100}")
    print("AGGREGATE STATS")
    print(f"{'=' * 100}")

    rdf = pd.DataFrame(results)

    ml_beats_bnh = (rdf["ml_return"] > rdf["bnh_return"]).sum()
    ps_beats_bnh = (rdf["ps_return"] > rdf["bnh_return"]).sum()
    ml_beats_ps = (rdf["ml_return"] > rdf["ps_return"]).sum()

    print(f"  Vanilla PS beats B&H:   {ps_beats_bnh}/{len(rdf)} ({ps_beats_bnh/len(rdf)*100:.0f}%)")
    print(f"  ML PS v2 beats B&H:     {ml_beats_bnh}/{len(rdf)} ({ml_beats_bnh/len(rdf)*100:.0f}%)")
    print(f"  ML PS v2 beats vanilla: {ml_beats_ps}/{len(rdf)} ({ml_beats_ps/len(rdf)*100:.0f}%)")
    print(f"  Avg PS return:          {rdf['ps_return'].mean():+.2f}%")
    print(f"  Avg ML return:          {rdf['ml_return'].mean():+.2f}%")
    print(f"  Avg delta:              {rdf['delta'].mean():+.2f}%")
    print(f"  Avg PS Sharpe:          {rdf['ps_sharpe'].mean():.2f}")
    print(f"  Avg ML Sharpe:          {rdf['ml_sharpe'].mean():.2f}")

    key_assets = ["BTC_USD", "TSLA", "ETH_USD", "SPY", "XLK", "JPM"]
    tracked = rdf[rdf["asset"].isin(key_assets)]
    if not tracked.empty:
        print(f"\n  Key Asset Tracking:")
        for _, row in tracked.iterrows():
            print(f"    {row['asset']:<12} PS:{row['ps_return']:>+8.2f}%  "
                  f"ML:{row['ml_return']:>+8.2f}%  delta:{row['delta']:>+8.2f}%  "
                  f"B&H:{row['bnh_return']:>+8.2f}%")

    return models, rdf


# =============================================================================
# STANDALONE ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    evaluate_ml_enhancement()
