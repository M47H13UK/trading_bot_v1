# ML Peak Shaver — How It Works

ML Peak Shaver wraps Peak Shaver v2 (PSv2) with an ensemble (two different prediction models averaged together) — XGBoost + Random Forest — that learns when PSv2's trim signals are wrong and overrides them.

## The Problem

PSv2 trims exposure (reduces how much of your money is invested) when RSI + ROC + Z-score all flash overbought (signals suggesting the price has risen "too much, too fast"). This works on 78% of assets (daily) but bleeds heavily on **parabolic assets** (stocks/crypto that just keep skyrocketing) — BTC, TSLA, ETH — where overbought conditions persist for weeks/months and trimming means missing massive upside.

## The Solution

Train a binary classifier (a model that answers yes/no): at every PSv2 trim signal, predict whether price will **drop** (trim was correct) or **rise** (trim was harmful — should've stayed invested). Use the model's confidence score to override bad trims.

## Architecture

```
Price Data → PSv2 fires trim → ML evaluates 20 features → Confidence score
                                                              │
                    ┌─────────────────────────────────────────┤
                    │                                         │
              conf > 0.6                               conf < 0.4
           Trust the trim                          Override: stay 100%
          (execute PSv2)                          (ML says parabolic)
                                                         │
                                              0.4 ≤ conf ≤ 0.6
                                           Interpolate linearly
                                      (split the difference — partially
                                       trim, scaled between full and none)
```

Every time PSv2 wants to sell, the ML model asks: *"Is this stock actually about to drop, or is it just running hot and will keep going up?"*

| Confidence | What happens |
|:-----------|:-------------|
| **Above 0.6** | "Price will probably drop" → **trust PSv2's sell signal**, trim position |
| **Below 0.4** | "Price will keep running" → **ignore PSv2**, stay fully invested |
| **0.4 to 0.6** | Uncertain → **split the difference**, partially trim |

## 20 Features (6 Groups)

The model looks at 20 measurements about the stock every time PSv2 fires a sell signal.

**A. Trigger indicators** — the same signals PSv2 uses:
- RSI(14) — Relative Strength Index (a 0-100 score of how overbought/oversold a stock is over 14 bars)
- ROC(21) — Rate of Change (the % price change over 21 bars)
- Z-score(50) — how many standard deviations the price is from its 50-bar average (i.e. how "abnormal" the current price is)

**B. Momentum persistence** — key for detecting parabolics (runaway stocks):
- `rsi_above_70_streak` / `rsi_above_75_streak` — how many bars in a row RSI has stayed above 70 or 75 (overbought streaks)
- `roc_above_10_streak` — how many bars in a row the stock has had >10% momentum
- `rsi_slope_10` — is RSI accelerating or decelerating (speeding up or slowing down)?

**C. Trend strength:**
- ADX(14) — Average Directional Index (a 0-100 score measuring how strong the current trend is, regardless of direction)
- Directional spread (+DI - -DI) — how much stronger the upward movement is vs downward
- % above SMA(200) — how far price is above/below the 200-bar simple moving average (a classic "big picture" trend gauge)
- EMA(50) slope — slope of the 50-bar exponential moving average (is the medium-term trend tilting up or down?)

**D. Volatility regime** (how wild the price swings are):
- ATR ratio vs 63-bar avg — current Average True Range (typical bar size) compared to its 63-bar average (is volatility expanding or contracting?)
- Bollinger Band width — how spread out the volatility bands are (wider = more volatile)
- Realized vol(20) — actual measured price swings over 20 bars

**E. Volume patterns** (is money flowing in or out?):
- OBV slope — On-Balance Volume trend (are buyers or sellers accumulating over time?)
- Chaikin Money Flow (CMF) — combines price and volume to show buying/selling pressure over 20 bars
- Volume ratio vs 50-bar avg — is trading activity unusually high or low right now?

**F. Divergences** (when indicators disagree with price — often a warning sign):
- MACD histogram — measures the gap between two moving averages (positive = bullish momentum)
- MACD divergence — price is making new highs but MACD is declining (a classic warning that momentum is fading even though price looks strong)
- Price-RSI divergence — price is rising but RSI is falling (another fading-momentum signal)

All features are **timeframe-adaptive** via `bpd^0.4` scaling (bars-per-day raised to the 0.4 power) — so the same logic auto-scales for both daily and hourly charts without manual tuning (same as PSv2).

## Training

### What training means

"Training" = feeding the model historical examples so it learns patterns. Each example is:
- **Input**: the 20 measurements at a moment PSv2 fired a sell signal
- **Label**: what actually happened next — did the price **drop** (trim was correct, label = 1) or **rise** (trim was wrong, label = 0)?

The model finds patterns in those 20 numbers that predict the correct label. After seeing enough examples, it can predict on new, unseen sell signals.

### Cross-asset pooling

All 41 assets' trim signals are pooled into **one big dataset** (~2,580 trim signals on daily). The model learns general patterns across stocks, crypto, ETFs — not just one ticker. More examples = more robust learning.

### Walk-forward expanding window (no lookahead)

This is the anti-cheating mechanism. Instead of training on all data at once (which would peek at the future), it does this:

```
Fold 1:  [===== Train (504 bars / ~2yr) =====][== Test (126 bars / ~6mo) ==]
Fold 2:  [=========== Train (expanded) ===========][== Test (next 6mo) ==]
Fold 3:  [================= Train (expanded) =================][== Test ==]
  ...repeat, expanding train set each fold, never peeking at future data...
```

- Min train: 504 bars (2yr equivalent)
- Test window: 126 bars (6mo)
- Expand training set each fold, never peek at future data
- Daily produces 16 folds, hourly produces 2 folds

### Ensemble

Average probabilities from two different model types (harder to overfit when models disagree):
- **XGBoost**: 100 trees, depth 4, min_child_weight 10, L1+L2 regularization (a fast algorithm that builds small decision trees one after another, each fixing the mistakes of the last)
- **Random Forest**: 200 trees, depth 5, min_samples_leaf 20 (builds many independent decision trees and averages their votes)

### Anti-overfit safeguards

Overfitting = the model memorizes training data instead of learning real patterns. Protections:
- **Shallow trees** (max depth 4-5 — each decision path is short, can't memorize complex noise)
- **High minimum samples per leaf** (10-20 examples needed to form a rule — can't create rules from flukes)
- **L1 + L2 regularization** (mathematical penalty that shrinks model complexity — like a tax on overfitting)
- **Ensemble averaging** (two different model types must agree)
- **Walk-forward validation** (never trained on future data)
- **Conservative thresholds** (only overrides when confidence is strong — below 0.4 or above 0.6)

### Cold start

For the first 504 bars (~2 years), there aren't enough examples to train the model. During this period, it runs vanilla PSv2 with no ML override. ML only kicks in once it has enough data.

### Training time

XGBoost (100 trees) + Random Forest (200 trees), trained on ~2,580 samples with 20 features, across ~16 walk-forward folds — roughly **30 seconds to a few minutes** on a modern laptop. Small dataset by ML standards. The `joblib` dependency supports model caching (save trained models to disk so you don't retrain every run).

## Results

### Daily (10yr, 41 assets)

| Strategy | Beats B&H | Median Alpha |
|:---------|:---------:|:------------:|
| ML Peak Shaver | **34/41 (83%)** | **+5.8%** |
| Peak Shaver v2 | 31/41 (76%) | +5.5% |
| Peak Shaver v1 | 28/41 (68%) | +4.0% |
| Best binary strat | 8/41 (20%) | ~-96% |

**Key recoveries** (ML vs B&H):
- TSLA: +4,416% vs +3,375% B&H — **+1,041% alpha** (PSv2 lost -2,166%)
- ETH: +831% vs +512% B&H — **+319% alpha** (PSv2 lost -383%)
- SLV: +567% vs +431% B&H — **+136% alpha** (PSv2 lost -36%)
- BTC: +12,417% vs +15,369% B&H — gap shrunk from -12,406% to **-2,952%**

**No degradation on winners**: SPY, XLK, JPM, DIA all still beat B&H.

### Hourly (2yr, 41 assets)

| Strategy | Beats B&H | Median Alpha |
|:---------|:---------:|:------------:|
| ML Peak Shaver | **24/41 (59%)** | **+0.2%** |
| Peak Shaver v1 | 21/41 (51%) | +0.1% |
| Peak Shaver v2 | 18/41 (44%) | +0.0% |

ML is the only strategy producing positive avg alpha on hourly data.

### Walk-Forward OOS Accuracy

- Daily: **55.9%** (1,967 samples, 16 folds)
- Hourly: **57.0%** (149 samples, 2 folds)

Both better than coin flip; edge is small but consistent and amplified by asymmetric position sizing (the wins from staying invested during a parabolic run are much bigger than the losses from trimming slightly late — so even a small accuracy edge compounds into meaningful alpha).

### Top Feature Importances (Daily)

| Feature | Importance |
|:--------|:---------:|
| sma_200_distance | 0.075 |
| obv_slope_20 | 0.074 |
| atr_14_ratio | 0.073 |
| cmf_20 | 0.065 |
| macd_histogram | 0.058 |
| ema_50_slope | 0.056 |
| roc_21 | 0.056 |
| bb_width | 0.055 |
| roc_above_10_streak | 0.055 |
| adx_14 | 0.053 |

Features are well-distributed (no single feature dominates), with trend distance, volume flow, and volatility regime ranking highest — consistent with the parabolic detection thesis.

## Files

| File | Description |
|:-----|:------------|
| `ml_peak_shaver.py` | All ML logic: features, labels, training, strategy, evaluation |
| `trading_bot.py` | Integration: menu options, lazy ML imports, single-asset ML mode |

## Usage

```python
# Standalone evaluation (all assets)
python3 ml_peak_shaver.py

# Via interactive menu
python3 trading_bot.py
# Select "ML Peak Shaver: Train + Evaluate on ALL daily datasets"

# Programmatic
from ml_peak_shaver import train_ml_models, strategy_ml_peak_shaver
models = train_ml_models()  # trains on all daily assets
positions, indicators = strategy_ml_peak_shaver(df, models)
```

## Requirements

```
pip install xgboost scikit-learn joblib
```

Falls back gracefully to vanilla PSv2 if ML deps not installed.
