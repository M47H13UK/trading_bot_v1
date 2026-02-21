# Quant Hackathon - Lancaster University

**Date**: Sun Feb 22, 2026, 10am-6pm (8 hours)
**Venue**: InfoLab Skylounge
**Organizers**: LEFS x FemTech x one other society

## Goal

Build a trading bot that yields the best returns. Compete against other teams.

## What We Know

- No public rules/dataset info found. Format details not confirmed by organizers.
- **Assumption**: they provide a CSV with historical OHLCV data and we backtest strategies against it. Judging likely on returns, possibly risk-adjusted (Sharpe, drawdown).
- Prize: winning team joins Lancaster's Hackathon Competition Squad.

## Current Approach

`trading_bot.py` — template with:
- CSV loader + synthetic data generator
- Indicators: SMA, EMA, RSI, Bollinger Bands, MACD
- 5 strategies: SMA Crossover, RSI, Bollinger Bands, MACD, Combined Ensemble
- Backtester with commission, Sharpe, max drawdown, equity curves
- Visualization comparing all strategies vs Buy & Hold

Swap `generate_sample_data()` for `load_csv_data("their_file.csv")` when data is provided.
