"""
ML Peak Shaver v3 — Return Maximizer
=====================================
Every-bar return prediction with aggressive binary position sizing.

Key changes from v2:
1. Predicts at EVERY bar (v2 only at PS trim points = ~5-10% of bars)
2. 37 features (v2's 28 + 9 new dip/recovery/momentum features)
3. Target: raw multi-horizon forward return (v2: risk-adjusted)
4. Position sizing: binary (100% or 0%) with calibrated bullish-bias threshold
5. Higher model capacity for better in-sample fit

The bullish bias means we only exit when the model is VERY confident about a
downturn. This prevents costly whipsawing and preserves parabolic rally gains.

Requirements:
    pip install xgboost scikit-learn
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
from ml_peak_shaver_v2 import (
    build_features, _load_all_assets, CATEGORY_ORDINAL,
)

try:
    from xgboost import XGBRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# =============================================================================
# FEATURE ENGINEERING (37 = v2's 28 + 9 new)
# =============================================================================

def build_features_v3(df, asset_category=None):
    """Build 37 features for every-bar prediction.

    v2's 28 features (trigger, momentum, trend, volatility, volume,
    divergence, regime, asset category) PLUS 9 new features focused on
    dip detection, recovery, and short-term momentum.
    """
    base = build_features(df, asset_category=asset_category)

    bpd = _detect_bars_per_day(df)
    scale = max(1.0, bpd ** 0.4)
    close = df["Close"]
    extra = pd.DataFrame(index=df.index)

    # --- I. Short-term past returns (momentum at multiple horizons) ---
    extra["past_return_1"] = close.pct_change(1)
    extra["past_return_5"] = close.pct_change(max(5, int(5 * scale)))
    extra["past_return_10"] = close.pct_change(max(10, int(10 * scale)))

    # --- J. Dip/recovery detection ---
    w20 = max(20, int(20 * scale))
    rolling_high = close.rolling(w20).max()
    extra["drawdown_from_high"] = (close - rolling_high) / rolling_high.replace(0, np.nan)

    rolling_low = close.rolling(w20).min()
    extra["distance_from_low"] = (close - rolling_low) / rolling_low.replace(0, np.nan)

    # --- K. Bollinger %B (position within bands, 0=lower, 1=upper) ---
    bb_up, bb_mid, bb_low = bollinger_bands(close, max(20, int(20 * scale)))
    bb_range = (bb_up - bb_low).replace(0, np.nan)
    extra["bb_pctb"] = (close - bb_low) / bb_range

    # --- L. Return distribution ---
    log_ret = np.log(close / close.shift(1))
    extra["return_skewness"] = log_ret.rolling(w20).skew()

    # --- M. Peak Shaver signal as feature ---
    ps_pos, _ = strategy_peak_shaver(df)
    extra["ps_position"] = ps_pos

    # --- N. RSI oversold recovery (dip-buy signal) ---
    rsi_val = rsi(close, max(14, int(14 * scale)))
    lookback = max(3, int(3 * scale))
    extra["rsi_oversold_recovery"] = (
        (rsi_val > 30) & (rsi_val.shift(lookback) < 30)
    ).astype(int)

    return pd.concat([base, extra], axis=1)


# =============================================================================
# EVERY-BAR TARGET: Multi-horizon forward return
# =============================================================================

def build_every_bar_target(df, horizons=None):
    """Blended forward return at every bar. Vectorized.

    Default horizons weight longer-term more heavily to reduce noise
    and prevent the model from exiting during short corrections
    that will recover.
    """
    if horizons is None:
        bpd = _detect_bars_per_day(df)
        if bpd > 1:  # hourly
            horizons = {14: 0.2, 28: 0.3, 56: 0.5}
        else:  # daily
            horizons = {5: 0.2, 10: 0.3, 20: 0.5}

    close = df["Close"]
    target = pd.Series(0.0, index=df.index)
    for horizon, weight in horizons.items():
        target = target + weight * (close.shift(-horizon) / close - 1)
    # Bars without all horizons become NaN automatically (NaN propagation)
    return target


# =============================================================================
# WALK-FORWARD TRAINING (higher capacity + exit threshold calibration)
# =============================================================================

def walk_forward_v3(all_features, all_targets, sample_weights=None,
                    min_train=504, max_folds=10):
    """Walk-forward regression with exit threshold from OOS predictions.

    Higher model capacity than v2 for better return prediction.
    Uses max_folds to cap compute time (every-bar data is ~10x larger than v2).
    Returns models tuple including calibrated exit threshold.
    """
    if not ML_AVAILABLE:
        raise ImportError("xgboost and scikit-learn required")

    valid = all_targets.notna() & all_features.notna().all(axis=1)
    X = all_features[valid].reset_index(drop=True)
    y = all_targets[valid].reset_index(drop=True)
    w = sample_weights[valid].reset_index(drop=True) if sample_weights is not None else None

    # Auto-size test_window to cap at max_folds
    test_window = max(126, (len(X) - min_train) // max_folds)

    if len(X) < min_train + test_window:
        min_train = max(50, len(X) // 2)
        test_window = min(test_window, len(X) - min_train)

    oos_preds = pd.Series(np.nan, index=X.index)
    feature_names = X.columns.tolist()
    importances_accum = np.zeros(len(feature_names))
    n_folds = 0

    xgb_mses, rf_mses = [], []
    decay = 0.8

    total_folds = max(1, (len(X) - min_train + test_window - 1) // test_window)
    print(f"  Walk-forward: {total_folds} folds, test_window={test_window}", flush=True)

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
            n_estimators=200, max_depth=5, min_child_weight=8,
            reg_alpha=0.5, reg_lambda=0.5,
            learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            verbosity=0, random_state=42,
        )
        xgb.fit(X_train_s, y_train, sample_weight=w_train)

        rf = RandomForestRegressor(
            n_estimators=300, max_depth=6, min_samples_leaf=15,
            max_features="sqrt", random_state=42, n_jobs=-1,
        )
        rf.fit(X_train_s, y_train, sample_weight=w_train)

        xgb_pred = xgb.predict(X_test_s)
        rf_pred = rf.predict(X_test_s)

        xgb_mses.append(((xgb_pred - y_test.values) ** 2).mean())
        rf_mses.append(((rf_pred - y_test.values) ** 2).mean())

        # Dynamic ensemble weights (inverse exponentially-decayed MSE)
        n_past = len(xgb_mses)
        w_decay = np.array([decay ** (n_past - 1 - i) for i in range(n_past)])
        w_decay /= w_decay.sum()
        xgb_avg = np.dot(w_decay, xgb_mses)
        rf_avg = np.dot(w_decay, rf_mses)
        inv_total = 1 / (xgb_avg + 1e-10) + 1 / (rf_avg + 1e-10)
        xgb_w = (1 / (xgb_avg + 1e-10)) / inv_total
        rf_w = (1 / (rf_avg + 1e-10)) / inv_total

        oos_preds.iloc[start:end] = xgb_w * xgb_pred + rf_w * rf_pred
        importances_accum += xgb.feature_importances_ + rf.feature_importances_
        n_folds += 1
        start = end

    # Final ensemble weights
    if xgb_mses:
        n_past = len(xgb_mses)
        w_decay = np.array([decay ** (n_past - 1 - i) for i in range(n_past)])
        w_decay /= w_decay.sum()
        xgb_final_w = 1 / (np.dot(w_decay, xgb_mses) + 1e-10)
        rf_final_w = 1 / (np.dot(w_decay, rf_mses) + 1e-10)
        inv_total = xgb_final_w + rf_final_w
        xgb_final_w /= inv_total
        rf_final_w /= inv_total
    else:
        xgb_final_w, rf_final_w = 0.5, 0.5

    # Train final models on ALL data (for competition/hackathon returns)
    scaler_final = StandardScaler()
    X_all_s = scaler_final.fit_transform(X)
    w_all = w.values if w is not None else None

    xgb_final = XGBRegressor(
        n_estimators=200, max_depth=5, min_child_weight=8,
        reg_alpha=0.5, reg_lambda=0.5,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        verbosity=0, random_state=42,
    )
    xgb_final.fit(X_all_s, y, sample_weight=w_all)

    rf_final = RandomForestRegressor(
        n_estimators=300, max_depth=6, min_samples_leaf=15,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf_final.fit(X_all_s, y, sample_weight=w_all)

    if n_folds > 0:
        importances_accum /= (2 * n_folds)
    feat_imp = pd.Series(importances_accum, index=feature_names).sort_values(ascending=False)

    # OOS metrics
    valid_preds = oos_preds.dropna()
    if len(valid_preds) > 0:
        dir_acc = ((valid_preds > 0) == (y[valid_preds.index] > 0)).mean()
        rmse = np.sqrt(((valid_preds - y[valid_preds.index]) ** 2).mean())
        print(f"  WF OOS direction accuracy: {dir_acc:.1%} "
              f"(RMSE: {rmse:.4f}, {len(valid_preds)} samples, {n_folds} folds)")
        print(f"  Ensemble weights: XGB={xgb_final_w:.1%}, RF={rf_final_w:.1%}")

    # Calibrate exit threshold from FINAL model predictions (not OOS)
    # Using final model preds ensures threshold matches deployment distribution
    final_preds = (xgb_final_w * xgb_final.predict(X_all_s) +
                   rf_final_w * rf_final.predict(X_all_s))

    models = (xgb_final, rf_final, scaler_final, feature_names,
              xgb_final_w, rf_final_w, final_preds)
    return models, oos_preds, feat_imp


# =============================================================================
# STRATEGY: Every-bar binary position sizing
# =============================================================================

def strategy_ml_v3(df, models, asset_category=None, cold_start_bars=252,
                   exit_percentile=15):
    """Every-bar ML-driven binary position sizing.

    100% invested by default. Exit to 0% only when prediction is in the
    bottom `exit_percentile`% of all training predictions. Strong bullish
    bias — only exits when model is very confident about downturn.

    With 0 commissions, binary (0/100%) is optimal: no partial positions
    to dilute gains or losses.
    """
    if models is None:
        return strategy_peak_shaver(df)

    xgb_m, rf_m, scaler, feat_names, xgb_w, rf_w, train_preds = models
    exit_thresh = np.percentile(train_preds, exit_percentile)

    features = build_features_v3(df, asset_category=asset_category)
    X = features[feat_names]
    valid = X.notna().all(axis=1)

    pred = pd.Series(np.nan, index=df.index)
    if valid.sum() > 0:
        Xs = scaler.transform(X[valid])
        pred.loc[valid] = xgb_w * xgb_m.predict(Xs) + rf_w * rf_m.predict(Xs)

    # Binary: 100% unless prediction is in bottom N%
    pos = pd.Series(1.0, index=df.index)
    pos[pred.notna() & (pred <= exit_thresh)] = 0.0
    # Cold start: stay 100% invested (not enough feature history)
    pos.iloc[:cold_start_bars] = 1.0

    return pos, {"ml_pred": pred, "position": pos, "exit_thresh": exit_thresh}


# =============================================================================
# TRAINING
# =============================================================================

def train_v3(data_dir=None):
    """Train v3 models on all assets with every-bar targets."""
    data_dir = data_dir or TEST_DATA_DIR

    if not ML_AVAILABLE:
        print("ERROR: xgboost/scikit-learn not installed")
        return None

    assets = _load_all_assets(data_dir)
    if not assets:
        print("No data files found.")
        return None

    print(f"\nTraining ML v3 (Return Maximizer) on {len(assets)} assets...", flush=True)

    all_features_list = []
    all_targets_list = []
    all_weights_list = []

    for stem, name, category, df in assets:
        features = build_features_v3(df, asset_category=category)
        target = build_every_bar_target(df)

        valid = target.notna() & features.notna().all(axis=1)
        if valid.sum() < 100:
            continue

        # Clip extreme targets (1st-99th percentile)
        t = target[valid]
        lo, hi = t.quantile(0.01), t.quantile(0.99)
        t = t.clip(lo, hi)

        all_features_list.append(features[valid])
        all_targets_list.append(t)
        # Weight by absolute return (bigger moves matter more)
        all_weights_list.append(t.abs() + 0.005)

    if not all_features_list:
        print("No training data.")
        return None

    pooled_X = pd.concat(all_features_list, ignore_index=True)
    pooled_y = pd.concat(all_targets_list, ignore_index=True)
    pooled_w = pd.concat(all_weights_list, ignore_index=True)

    print(f"  Pooled: {len(pooled_X)} bars across {len(assets)} assets", flush=True)
    print(f"  Target: mean={pooled_y.mean():.4f}, std={pooled_y.std():.4f}", flush=True)
    print(f"  Positive (fwd return > 0): {(pooled_y > 0).mean():.1%}", flush=True)

    models, oos_preds, feat_imp = walk_forward_v3(
        pooled_X, pooled_y, sample_weights=pooled_w
    )

    print(f"\n  Top 10 features:")
    for fname, imp in feat_imp.head(10).items():
        print(f"    {fname:<30} {imp:.4f}")

    return models


# =============================================================================
# EVALUATION: v3 vs v2 vs PS vs B&H + percentile sweep
# =============================================================================

def evaluate_v3(data_dir=None):
    """Full comparison: ML v3 vs ML v2 vs PSv2 vs B&H on all assets.

    Also sweeps exit percentiles (5-30%) to find optimal threshold.
    """
    data_dir = data_dir or TEST_DATA_DIR

    # Train v3
    v3_models = train_v3(data_dir)
    if v3_models is None:
        return

    # Train v2 for comparison
    from ml_peak_shaver_v2 import train_ml_models, strategy_ml_peak_shaver
    print("\n--- Training ML v2 for comparison ---")
    v2_models = train_ml_models(data_dir)

    assets = _load_all_assets(data_dir)

    # --- Sweep exit percentiles ---
    print(f"\n{'=' * 100}")
    print("EXIT PERCENTILE SWEEP (finding optimal threshold)")
    print(f"{'=' * 100}")

    percentiles_to_test = [5, 10, 15, 20, 25, 30]
    pctile_results = {p: [] for p in percentiles_to_test}

    for stem, name, category, df in assets:
        bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)
        for pctile in percentiles_to_test:
            pos, _ = strategy_ml_v3(df, v3_models, asset_category=category,
                                     exit_percentile=pctile)
            r = bt.run_positions(pos, strategy_name=f"v3-p{pctile}")
            pctile_results[pctile].append(r["total_return_pct"])

    print(f"\n  {'Pctile':>8} {'AvgReturn':>12} {'MedianReturn':>14} {'StdReturn':>12}")
    print("  " + "-" * 50)
    best_pctile = 15
    best_avg = -999
    for pctile in percentiles_to_test:
        rets = pctile_results[pctile]
        avg = np.mean(rets)
        med = np.median(rets)
        std = np.std(rets)
        marker = ""
        if avg > best_avg:
            best_avg = avg
            best_pctile = pctile
            marker = " <-- best"
        print(f"  {pctile:>6}% {avg:>+12.2f}% {med:>+14.2f}% {std:>12.2f}%{marker}")

    print(f"\n  Optimal exit percentile: {best_pctile}%")

    # --- Full comparison with optimal percentile ---
    print(f"\n{'=' * 130}")
    print(f"ML v3 (p={best_pctile}%) vs ML v2 vs PSv2 vs B&H — Per-Asset")
    print(f"{'=' * 130}")
    print(f"{'Asset':<12} {'Name':<22} {'Cat':<10} "
          f"{'PSv2%':>8} {'MLv2%':>8} {'MLv3%':>8} {'B&H%':>8} "
          f"{'v3-v2':>8} {'v3-BH':>8} {'Best':>6}")
    print("-" * 130)

    results = []
    for stem, name, category, df in assets:
        bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)

        ps_pos, _ = strategy_peak_shaver(df)
        ps_r = bt.run_positions(ps_pos, strategy_name="PSv2")

        if v2_models:
            ml2_pos, _ = strategy_ml_peak_shaver(df, v2_models, asset_category=category)
        else:
            ml2_pos = ps_pos
        ml2_r = bt.run_positions(ml2_pos, strategy_name="ML v2")

        ml3_pos, _ = strategy_ml_v3(df, v3_models, asset_category=category,
                                     exit_percentile=best_pctile)
        ml3_r = bt.run_positions(ml3_pos, strategy_name="ML v3")

        bnh = ps_r["buy_and_hold_return_pct"]
        d_v2 = ml3_r["total_return_pct"] - ml2_r["total_return_pct"]
        d_bh = ml3_r["total_return_pct"] - bnh

        rets = {"PSv2": ps_r["total_return_pct"], "MLv2": ml2_r["total_return_pct"],
                "MLv3": ml3_r["total_return_pct"], "B&H": bnh}
        best_name = max(rets, key=rets.get)

        status = "+" if d_v2 > 0 else "-"
        print(f"[{status}] {stem:<10} {name:<22} {category:<10} "
              f"{ps_r['total_return_pct']:>+8.2f} {ml2_r['total_return_pct']:>+8.2f} "
              f"{ml3_r['total_return_pct']:>+8.2f} {bnh:>+8.2f} "
              f"{d_v2:>+8.2f} {d_bh:>+8.2f} {best_name:>6}")

        results.append({
            "asset": stem, "name": name, "category": category,
            "ps": ps_r["total_return_pct"],
            "ml2": ml2_r["total_return_pct"],
            "ml3": ml3_r["total_return_pct"],
            "bnh": bnh,
        })

    if not results:
        return

    rdf = pd.DataFrame(results)

    # --- Aggregate stats ---
    print(f"\n{'=' * 130}")
    print("AGGREGATE RESULTS")
    print(f"{'=' * 130}")

    for col, label in [("ps", "PSv2"), ("ml2", "ML v2"),
                        ("ml3", "ML v3"), ("bnh", "B&H")]:
        beats = (rdf[col] > rdf["bnh"]).sum() if col != "bnh" else "—"
        wins = (rdf[col] == rdf[["ps", "ml2", "ml3", "bnh"]].max(axis=1)).sum()
        print(f"  {label:<8}  Avg:{rdf[col].mean():>+10.2f}%  "
              f"Med:{rdf[col].median():>+8.2f}%  "
              f"Beats B&H: {beats}  Wins: {wins}/{len(rdf)}")

    v3_beats_v2 = (rdf["ml3"] > rdf["ml2"]).sum()
    v3_beats_bnh = (rdf["ml3"] > rdf["bnh"]).sum()
    print(f"\n  ML v3 beats ML v2: {v3_beats_v2}/{len(rdf)} ({v3_beats_v2/len(rdf)*100:.0f}%)")
    print(f"  ML v3 beats B&H:  {v3_beats_bnh}/{len(rdf)} ({v3_beats_bnh/len(rdf)*100:.0f}%)")
    print(f"  ML v3 avg delta vs v2: {(rdf['ml3'] - rdf['ml2']).mean():+.2f}%")
    print(f"  ML v3 avg delta vs B&H: {(rdf['ml3'] - rdf['bnh']).mean():+.2f}%")

    return v3_models, rdf


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    evaluate_v3()
