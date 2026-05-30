# Daily Backtest Results — Enhanced Peak Shaver (Hackathon)

**Data: ~10yr daily bars (2016 to 2026) from Yahoo Finance** | **Transaction Cost:** 0.05% (5bps) | **Next-day execution** | **Assets:** 41

## Strategy

| Code | Name | Type | Description |
|:-----|:-----|:-----|:------------|
| **EPS** | **Enhanced Peak Shaver** | **Discrete {-1,0,1}** | **Long default, flat at overbought/bearish/vol, short at Z>3 blow-offs** |

## Index (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| DIA | Dow Jones ETF | +283.8% **(W)** | 1.02 | -24.5% | 77 | +263.9% | 0.83 | EPS |
| IWM | Russell 2000 ETF | +152.4% | 0.55 | -41.1% | 104 | +196.6% **(W)** | 0.59 | B&H |
| QQQ | Nasdaq 100 ETF | +545.2% **(W)** | 1.10 | -22.8% | 127 | +533.8% | 0.95 | EPS |
| SPY | S&P 500 ETF | +297.3% **(W)** | 1.01 | -34.5% | 70 | +317.6% | 0.89 | EPS |
| **Beats B&H** | | | **3/4** | | | | | |

## Stock (8 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| AAPL | Apple | +449.4% | 0.84 | -46.2% | 165 | +1105.8% **(W)** | 1.01 | B&H |
| AMZN | Amazon | +627.6% **(W)** | 0.84 | -55.7% | 173 | +651.1% | 0.79 | EPS |
| JNJ | Johnson & Johnson | +96.9% | 0.52 | -28.0% | 110 | +203.2% **(W)** | 0.70 | B&H |
| JPM | JPMorgan | +377.9% | 0.77 | -44.1% | 126 | +593.9% **(W)** | 0.85 | B&H |
| MSFT | Microsoft | +735.0% **(W)** | 1.04 | -50.0% | 137 | +757.5% | 0.94 | EPS |
| TSLA | Tesla | +275.0% | 0.51 | -70.7% | 179 | +3375.5% **(W)** | 0.90 | B&H |
| WMT | Walmart | +657.6% **(W)** | 1.19 | -23.9% | 130 | +574.5% | 0.99 | EPS |
| XOM | ExxonMobil | +433.3% **(W)** | 0.79 | -41.7% | 120 | +176.4% | 0.51 | EPS |
| **Beats B&H** | | | **4/8** | | | | | |

## Sector (10 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| XLB | Materials | +193.6% **(W)** | 0.68 | -35.2% | 86 | +211.5% | 0.66 | EPS |
| XLE | Energy | +179.3% **(W)** | 0.52 | -50.5% | 129 | +182.8% | 0.50 | EPS |
| XLF | Financials | +286.8% **(W)** | 0.79 | -30.5% | 98 | +265.3% | 0.70 | EPS |
| XLI | Industrials | +271.5% **(W)** | 0.82 | -38.1% | 100 | +305.5% | 0.81 | EPS |
| XLK | Technology | +551.3% **(W)** | 1.02 | -42.9% | 142 | +665.4% | 0.96 | EPS |
| XLP | Consumer Staples | +123.7% **(W)** | 0.70 | -16.5% | 72 | +124.7% | 0.63 | EPS |
| XLRE | Real Estate | +127.9% **(W)** | 0.57 | -32.5% | 101 | +111.1% | 0.47 | EPS |
| XLU | Utilities | +212.8% **(W)** | 0.77 | -39.3% | 84 | +172.7% | 0.62 | EPS |
| XLV | Healthcare | +147.9% **(W)** | 0.70 | -18.8% | 79 | +177.0% | 0.70 | EPS |
| XLY | Consumer Disc | +190.0% | 0.67 | -45.0% | 117 | +252.8% **(W)** | 0.69 | B&H |
| **Beats B&H** | | | **9/10** | | | | | |

## Country (6 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| EEM | Emerging Mkts | +116.3% | 0.52 | -43.6% | 102 | +151.1% **(W)** | 0.56 | B&H |
| EFA | EAFE | +79.2% | 0.45 | -43.7% | 78 | +159.5% **(W)** | 0.65 | B&H |
| EWG | Germany | +45.2% | 0.29 | -53.9% | 95 | +134.0% **(W)** | 0.51 | B&H |
| EWJ | Japan | +109.5% | 0.54 | -33.3% | 69 | +154.0% **(W)** | 0.63 | B&H |
| EWU | UK | +20.1% | 0.19 | -54.5% | 66 | +135.1% **(W)** | 0.55 | B&H |
| FXI | China | +58.0% **(W)** | 0.31 | -49.0% | 102 | +57.7% | 0.30 | EPS |
| **Beats B&H** | | | **1/6** | | | | | |

## Fixed Income (3 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| IEF | 7-10Y Treasury | +7.8% | 0.15 | -19.5% | 78 | +9.8% **(W)** | 0.17 | B&H |
| SHY | 1-3Y Treasury | +13.1% | 0.86 | -6.1% | 47 | +18.1% **(W)** | 1.08 | B&H |
| TLT | 20+Y Treasury | +3.4% **(W)** | 0.09 | -32.7% | 88 | -10.4% | 0.00 | EPS |
| **Beats B&H** | | | **1/3** | | | | | |

## Commodity (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| GLD | Gold | +198.0% | 0.89 | -23.7% | 90 | +305.8% **(W)** | 0.98 | B&H |
| SLV | Silver | +64.1% | 0.33 | -53.8% | 148 | +431.0% **(W)** | 0.70 | B&H |
| UNG | Nat Gas | -90.0% | -0.24 | -95.4% | 149 | -88.6% **(W)** | -0.12 | B&H |
| USO | Oil | +100.2% **(W)** | 0.38 | -71.9% | 140 | +13.4% | 0.23 | EPS |
| **Beats B&H** | | | **1/4** | | | | | |

## Currency (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| FXB | British Pound | -5.4% | -0.01 | -28.1% | 60 | +2.2% **(W)** | 0.07 | B&H |
| FXE | Euro | +8.0% **(W)** | 0.14 | -28.6% | 53 | +5.9% | 0.12 | EPS |
| FXY | Yen | -38.9% | -0.51 | -47.2% | 75 | -30.9% **(W)** | -0.34 | B&H |
| UUP | US Dollar | +12.1% | 0.21 | -16.9% | 63 | +28.4% **(W)** | 0.39 | B&H |
| **Beats B&H** | | | **1/4** | | | | | |

## Crypto (2 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| BTC_USD | Bitcoin | +2.8% | 0.23 | -89.0% | 285 | +15369.1% **(W)** | 0.90 | B&H |
| ETH_USD | Ethereum | +332.6% | 0.51 | -94.2% | 256 | +512.3% **(W)** | 0.57 | B&H |
| **Beats B&H** | | | **0/2** | | | | | |

## Summary

**Beats Buy & Hold (Sharpe): 20/41 (49%)**

| Metric | EPS | B&H |
|:-------|----:|----:|
| Avg Sharpe | 0.555 | 0.601 |
| Median Sharpe | 0.546 | 0.646 |
| Avg Trades | 111 | 0 |
