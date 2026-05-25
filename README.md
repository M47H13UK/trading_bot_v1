# Adaptive Regime-Based Trading Bot

**🏆 1st place — Lancaster University Quant Hackathon (LEFS x FemTech, Feb 2026)**

A long-only adaptive trading system backtested across 41 assets and 10 years of daily data. Combines classical technical-indicator strategies with XGBoost/Random Forest models, evaluated under a unified backtester with continuous 0–100% position sizing.

![Backtest example](backtest_results.png)

---

## Headline Results

Tested on 41 assets across 8 categories (Index, Stock, Sector, Global, Commodity, Crypto, Bond, Forex). $10,000 initial capital, 0% commission, no leverage, no shorting.

| Strategy           | Type        | Daily (10y) | Hourly (2y) |
|:-------------------|:------------|:-----------:|:-----------:|
| Peak Shaver v1     | Rule-based  | 28/41 (68%) | 24/41 (59%) |
| **Peak Shaver v2** | Rule-based  | **32/41 (78%)** | 20/41 (49%) |
| ML Peak Shaver v2  | XGB + RF    | 30/41 (73%) | 19/41 (46%) |
| **ML v3 Return Maximizer** | XGB + RF | 26/41 (63%) | **30/41 (73%)** |

Win-rate = beats Buy & Hold on that asset. Full per-asset breakdown in [`test_data/BACKTEST_RESULTS/DAILY.md`](test_data/BACKTEST_RESULTS/DAILY.md) and [`HOURLY.md`](test_data/BACKTEST_RESULTS/HOURLY.md).

---

## Core Insight

Traditional active strategies are binary (100% invested or 100% cash). In a 10-year bull market, every day in cash compounds against you, and missing the 10 best days roughly halves total returns — and the best days cluster right after the worst, so exiting during a crash forfeits the recovery.

So we don't try to avoid crashes. We **shave peaks**: stay 100% invested by default, trim exposure only when multiple overbought signals fire simultaneously, and snap back to full exposure fast. Full reasoning in [HOW_IT_WORKS.md](HOW_IT_WORKS.md).

---

## Strategies

| Code      | Approach                                                                                |
|:----------|:----------------------------------------------------------------------------------------|
| SMA(200)  | Faber timing — long above 200-day SMA, 3-day confirmation                               |
| Dual MA   | 50/200 golden-cross / death-cross with 1% band filter                                   |
| Momentum  | Multi-timeframe (1/3/12-month) majority vote                                            |
| Crash Avoid | Stay invested; exit only on 3/4 crash signals                                         |
| Volume    | Price + OBV dual confirmation                                                           |
| Ensemble  | Majority vote across the five above                                                     |
| **PSv1**  | RSI(14)>75 + ROC(21)>11% → 50% exposure; RSI>85 → 30%                                  |
| **PSv2**  | PSv1 + Z-score(50)>1.0 and >3.0 tiered gates; timeframe-adaptive indicator periods     |
| **ML v2** | XGBRegressor + RandomForest, multi-horizon labels, magnitude-weighted, dynamic ensemble |
| **ML v3** | Every-bar return prediction, binary 100%/0% sizing, 37 features, bullish-bias threshold |

---

## Quick Start

```bash
pip install -r requirements.txt
```

**Interactive CLI** (run any strategy on any asset):
```bash
python trading_bot.py
```

**Streamlit terminal dashboard** (Bloomberg/TradingView-style demo):
```bash
streamlit run dashboard.py
```

**Browser visualizer** (lightweight-charts, step-through bar-by-bar):
```bash
open viz/index.html
```

**Full cross-asset backtest** (regenerates `BACKTEST_RESULTS/*.md`):
```bash
python run_full_backtest.py
```

---

## Project Structure

```
trading_bot.py              # Core: indicators, strategies, backtester, CLI
ml_peak_shaver_v2.py        # ML strategy v2 — XGB + RF, multi-horizon labels
ml_peak_shaver_v3.py        # ML strategy v3 — every-bar return prediction
dashboard.py                # Streamlit terminal-style demo
run_full_backtest.py        # Regenerates the BACKTEST_RESULTS markdown
viz/                        # Browser visualizer (lightweight-charts + vanilla JS)
test_data/
  daily/                    # 41 assets × ~10y daily OHLCV (CSV cache)
  hourly/                   # 41 assets × ~2y hourly OHLCV
  BACKTEST_RESULTS/         # Per-asset results tables (daily + hourly)
  DATA_REFERENCE.md         # Data source documentation
HOW_IT_WORKS.md             # Core technical breakdown
ML_PS_Explanation.md        # ML strategy deep-dive
ADVANCED_TECHNIQUES.md      # Discarded approaches and why
requirements.txt
```

---

## Tech Stack

`Python 3.10+` · `pandas` · `numpy` · `yfinance` · `xgboost` · `scikit-learn` · `matplotlib` · `streamlit` · `plotly` · `lightweight-charts` (browser viz)

---

## License

MIT — see [LICENSE](LICENSE).
