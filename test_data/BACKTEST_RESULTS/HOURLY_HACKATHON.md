# Hourly Backtest Results — Enhanced Peak Shaver (Hackathon)

**Data: ~2yr hourly bars (2024 to 2026) from Yahoo Finance** | **Transaction Cost:** 0.05% (5bps) | **Next-day execution** | **Assets:** 41

## Strategy

| Code | Name | Type | Description |
|:-----|:-----|:-----|:------------|
| **EPS** | **Enhanced Peak Shaver** | **Discrete {-1,0,1}** | **Long default, flat at overbought/bearish/vol, short at Z>3 blow-offs** |

## Index (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| DIA | Dow Jones ETF | +29.6% **(W)** | 1.05 | -11.6% | 104 | +28.9% | 0.95 | EPS |
| IWM | Russell 2000 ETF | +2.7% | 0.17 | -25.3% | 143 | +33.9% **(W)** | 0.77 | B&H |
| QQQ | Nasdaq 100 ETF | +18.6% | 0.58 | -19.4% | 140 | +43.6% **(W)** | 1.00 | B&H |
| SPY | S&P 500 ETF | +10.8% | 0.44 | -22.7% | 99 | +39.2% **(W)** | 1.13 | B&H |
| **Beats B&H** | | | **1/4** | | | | | |

## Stock (8 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| AAPL | Apple | +13.6% | 0.39 | -29.3% | 128 | +44.9% **(W)** | 0.82 | B&H |
| AMZN | Amazon | -37.9% | -0.64 | -47.7% | 140 | +25.1% **(W)** | 0.51 | B&H |
| JNJ | Johnson & Johnson | +35.3% | 1.00 | -19.6% | 127 | +53.8% **(W)** | 1.32 | B&H |
| JPM | JPMorgan | +29.6% | 0.68 | -21.0% | 119 | +73.4% **(W)** | 1.22 | B&H |
| MSFT | Microsoft | -6.4% | -0.03 | -29.5% | 191 | -0.5% **(W)** | 0.12 | B&H |
| TSLA | Tesla | -37.5% | -0.18 | -64.3% | 196 | +109.9% **(W)** | 0.92 | B&H |
| WMT | Walmart | +51.7% | 1.15 | -16.7% | 122 | +111.9% **(W)** | 1.84 | B&H |
| XOM | ExxonMobil | +13.1% | 0.40 | -30.1% | 144 | +41.3% **(W)** | 0.88 | B&H |
| **Beats B&H** | | | **0/8** | | | | | |

## Sector (10 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| XLB | Materials | +10.2% | 0.40 | -25.4% | 146 | +24.8% **(W)** | 0.74 | B&H |
| XLE | Energy | -9.7% | -0.15 | -37.0% | 130 | +27.8% **(W)** | 0.67 | B&H |
| XLF | Financials | +22.1% | 0.71 | -16.2% | 108 | +33.0% **(W)** | 0.91 | B&H |
| XLI | Industrials | +27.5% | 0.87 | -21.0% | 115 | +50.3% **(W)** | 1.31 | B&H |
| XLK | Technology | +36.1% | 0.85 | -22.5% | 152 | +42.1% **(W)** | 0.85 | B&H |
| XLP | Consumer Staples | -5.8% | -0.21 | -22.8% | 141 | +18.3% **(W)** | 0.77 | B&H |
| XLRE | Real Estate | +1.9% | 0.14 | -24.6% | 112 | +13.2% **(W)** | 0.46 | B&H |
| XLU | Utilities | +35.7% | 1.05 | -13.5% | 102 | +50.0% **(W)** | 1.33 | B&H |
| XLV | Healthcare | +19.8% **(W)** | 0.75 | -16.8% | 147 | +8.6% | 0.36 | EPS |
| XLY | Consumer Disc | +7.6% | 0.29 | -25.0% | 138 | +31.5% **(W)** | 0.75 | B&H |
| **Beats B&H** | | | **1/10** | | | | | |

## Country (6 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| EEM | Emerging Mkts | +50.0% | 1.43 | -15.9% | 136 | +55.0% **(W)** | 1.44 | B&H |
| EFA | EAFE | +12.8% | 0.55 | -18.5% | 125 | +37.6% **(W)** | 1.17 | B&H |
| EWG | Germany | +27.0% | 0.89 | -15.1% | 135 | +49.7% **(W)** | 1.29 | B&H |
| EWJ | Japan | +3.1% | 0.18 | -28.1% | 123 | +34.8% **(W)** | 0.86 | B&H |
| EWU | UK | +19.6% | 0.77 | -21.2% | 104 | +47.4% **(W)** | 1.45 | B&H |
| FXI | China | +33.5% | 0.72 | -22.6% | 192 | +64.7% **(W)** | 1.07 | B&H |
| **Beats B&H** | | | **0/6** | | | | | |

## Fixed Income (3 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| IEF | 7-10Y Treasury | -3.8% | -0.32 | -9.3% | 128 | +3.4% **(W)** | 0.31 | B&H |
| SHY | 1-3Y Treasury | -7.4% | -2.28 | -7.8% | 113 | +1.6% **(W)** | 0.44 | B&H |
| TLT | 20+Y Treasury | -2.7% **(W)** | -0.06 | -13.8% | 160 | -3.6% | -0.08 | EPS |
| **Beats B&H** | | | **1/3** | | | | | |

## Commodity (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| GLD | Gold | +132.3% **(W)** | 2.41 | -11.3% | 142 | +149.3% | 2.39 | EPS |
| SLV | Silver | +100.2% | 1.15 | -33.5% | 168 | +264.1% **(W)** | 1.76 | B&H |
| UNG | Nat Gas | -30.4% | -0.11 | -63.4% | 284 | -26.0% **(W)** | 0.04 | B&H |
| USO | Oil | -9.2% | -0.03 | -41.4% | 197 | +11.5% **(W)** | 0.33 | B&H |
| **Beats B&H** | | | **1/4** | | | | | |

## Currency (4 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| FXB | British Pound | -4.8% | -0.36 | -13.4% | 119 | +6.7% **(W)** | 0.55 | B&H |
| FXE | Euro | -7.5% | -0.57 | -11.6% | 159 | +8.8% **(W)** | 0.63 | B&H |
| FXY | Yen | -25.1% | -1.48 | -27.3% | 220 | -3.9% **(W)** | -0.14 | B&H |
| UUP | US Dollar | -14.6% | -1.04 | -18.4% | 156 | -3.4% **(W)** | -0.19 | B&H |
| **Beats B&H** | | | **0/4** | | | | | |

## Crypto (2 assets)

| Asset | Name | EPS Return | EPS Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |
|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|
| BTC_USD | Bitcoin | +117.7% **(W)** | 0.49 | -33.2% | 904 | +32.4% | 0.24 | EPS |
| ETH_USD | Ethereum | -80.0% | -0.43 | -87.5% | 948 | -32.5% **(W)** | 0.03 | B&H |
| **Beats B&H** | | | **1/2** | | | | | |

## Summary

**Beats Buy & Hold (Sharpe): 5/41 (12%)**

| Metric | EPS | B&H |
|:-------|----:|----:|
| Avg Sharpe | 0.283 | 0.810 |
| Median Sharpe | 0.396 | 0.819 |
| Avg Trades | 182 | 0 |
