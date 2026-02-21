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

`trading_bot.py` — Peak Shaver v2 (flagship):
- **Triple confirmation**: RSI(14) + ROC(21) + Z-score(50) overbought detection
- 100% invested by default, trims to 40% at peaks, 30% at extreme blow-offs
- Timeframe-adaptive: auto-scales indicator periods for daily/hourly bars
- **Daily (10yr, 41 assets): beats B&H 32/41 (78%)**
- **Hourly (2yr, 41 assets): beats B&H 20/41 (49%)**
- No leverage, no shorting — long-only 0-100%
- Also includes 6 comparison strategies (SMA, Dual MA, Momentum, Crash Avoidance, Volume Trend, Ensemble)

Swap `generate_sample_data()` for `load_csv_data("their_file.csv")` when data is provided.
