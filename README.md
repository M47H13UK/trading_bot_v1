# Adaptive Regime-Based Trading Bot

Built for the **Lancaster University Quant Hackathon** (LEFS x FemTech, Feb 2026).

## What It Does

Backtests 7 trading strategies across 41 assets (indices, sectors, stocks, commodities, crypto, bonds, forex) using ~10 years of daily data from Yahoo Finance.

**Flagship strategy — Peak Shaver:** stays 100% invested by default, reduces to 50% exposure only at overbought peaks (RSI > 75 + ROC > 11%). Beats Buy & Hold on 23/41 assets outright.

### All Strategies

| Strategy | Approach |
|:---------|:---------|
| SMA(200) Trend | Faber timing — long above 200-day SMA, 3-day confirmation |
| Dual MA (50/200) | Golden/death cross with 1% band filter |
| Momentum Composite | Multi-timeframe momentum (1/3/12-month) majority vote |
| Crash Avoidance | Always invested, exit only on 3/4 crash signals |
| Volume Trend | Price + OBV dual confirmation |
| Master Ensemble | Majority vote across 5 strategies |
| **Peak Shaver** | **Flagship** — shaves peaks instead of avoiding crashes |

## Quick Start

```bash
pip install pandas numpy matplotlib yfinance pick
python trading_bot.py
```

Interactive menu lets you:
- Run single-asset backtest
- Run full cross-asset test (41 assets)
- View results and charts

## Results

Tested on 41 assets across 8 categories with $10k initial capital and 0% commission:

| Category | Peak Shaver Avg | B&H Avg | Peak Shaver Wins |
|:---------|----------------:|--------:|-----------------:|
| Index (4) | +330.5% | +328.0% | 3/4 |
| Sector (10) | +251.9% | +246.9% | 7/10 |
| Stock (8) | +695.2% | +929.7% | 4/8 |
| Overall (41) | — | — | 23/41 |

## Project Structure

```
trading_bot.py          # Main bot — strategies, backtester, visualization
HOW_IT_WORKS.md         # Detailed technical explanation
test_data/              # Cached Yahoo Finance CSVs (41 assets, ~10yr each)
  BACKTEST_RESULTS.md   # Full results table
  DATA_REFERENCE.md     # Data source documentation
backtest_results.png    # Single-asset backtest chart
cross_asset_results.png # Cross-asset comparison chart
```

## How It Works

See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for the full technical breakdown — covers the core insight (why it's hard to beat B&H without leverage), the Peak Shaver approach, and regime detection logic.
