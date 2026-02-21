# Hourly (2yr) Backtest Results — Peak Shaver Strategies

**Data: ~2yr hourly bars (2024 to 2026) from Yahoo Finance** | **Initial Capital:** $10,000 | **Commission:** 0.0% | **Assets:** 41

## Strategies

| Code | Name | Type | Description |
|:-----|:-----|:-----|:------------|
| **PSv1** | **Peak Shaver v1** | **Continuous** | **RSI>75 + ROC>11% -> 50%, RSI>85 -> 30%** |
| **PSv2** | **Peak Shaver v2** | **Continuous** | **v1 + Z-score>1.0 gate (Tier 1), Z>3.0 gate (Tier 2)** |
| **ML** | **ML Peak Shaver** | **Continuous** | **XGBoost+RF ensemble overrides bad PSv2 trims on parabolics** |

## Index (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| DIA | Dow Jones ETF | +28.2% **(L)**| +28.9% **(W)**| +28.9%| +28.9%| PSv2 |
| IWM | Russell 2000 ETF | +35.4% **(W)**| +34.3%| +34.3%| +33.9% **(L)**| PSv1 |
| QQQ | Nasdaq 100 ETF | +43.6% **(W)**| +43.6%| +43.6%| +43.6%| PSv1 |
| SPY | S&P 500 ETF | +39.1% **(L)**| +39.2% **(W)**| +39.2%| +39.2%| PSv2 |
| **Beats B&H** | | 1/4 | 1/4 | 1/4 | — | |

## Stock (8 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| AAPL | Apple | +46.4%| +46.9%| +47.4% **(W)**| +44.9% **(L)**| ML |
| AMZN | Amazon | +25.5%| +26.7% **(W)**| +26.6%| +25.1% **(L)**| PSv2 |
| JNJ | Johnson & Johnson | +53.8% **(W)**| +53.8%| +53.8%| +53.8%| PSv1 |
| JPM | JPMorgan Chase | +72.8% **(L)**| +73.5% **(W)**| +73.5%| +73.4%| PSv2 |
| MSFT | Microsoft | +0.9%| +1.0% **(W)**| -0.2%| -0.5% **(L)**| PSv2 |
| TSLA | Tesla | +64.2%| +57.8% **(L)**| +136.6% **(W)**| +109.9%| ML |
| WMT | Walmart | +111.3% **(L)**| +111.4%| +113.5% **(W)**| +111.9%| ML |
| XOM | Exxon Mobil | +41.4% **(W)**| +41.0% **(L)**| +41.2%| +41.3%| PSv1 |
| **Beats B&H** | | 4/8 | 4/8 | 6/8 | — | |

## Sector (10 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| XLB | Materials | +25.7% **(W)**| +24.8% **(L)**| +24.8%| +24.8%| PSv1 |
| XLE | Energy | +28.4% **(W)**| +28.1%| +28.1%| +27.8% **(L)**| PSv1 |
| XLF | Financials | +31.3% **(L)**| +33.0% **(W)**| +33.0%| +33.0%| PSv2 |
| XLI | Industrials | +49.7% **(L)**| +50.3% **(W)**| +50.3%| +50.3%| PSv2 |
| XLK | Technology | +41.2% **(L)**| +42.3% **(W)**| +42.3%| +42.1%| PSv2 |
| XLP | Consumer Staples | +18.2% **(L)**| +18.4% **(W)**| +18.4%| +18.3%| PSv2 |
| XLRE | Real Estate | +13.6% **(W)**| +13.6%| +13.6%| +13.2% **(L)**| PSv1 |
| XLU | Utilities | +50.2%| +50.3% **(W)**| +50.3%| +50.0% **(L)**| PSv2 |
| XLV | Healthcare | +8.6% **(L)**| +8.9% **(W)**| +8.9%| +8.6%| PSv2 |
| XLY | Consumer Discr. | +30.0% **(L)**| +31.6% **(W)**| +31.6%| +31.5%| PSv2 |
| **Beats B&H** | | 4/10 | 7/10 | 7/10 | — | |

## Global (6 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| EEM | Emerging Markets | +55.4% **(W)**| +54.8% **(L)**| +54.8%| +55.0%| PSv1 |
| EFA | MSCI Intl Developed | +35.7% **(L)**| +37.6% **(W)**| +37.6%| +37.6%| PSv2 |
| EWG | Germany ETF | +43.1% **(L)**| +49.6%| +49.6%| +49.7% **(W)**| B&H |
| EWJ | Japan ETF | +39.2% **(W)**| +35.1%| +35.1%| +34.8% **(L)**| PSv1 |
| EWU | UK ETF | +47.3% **(L)**| +47.4% **(W)**| +47.4%| +47.4%| PSv2 |
| FXI | China Large Cap | +59.4%| +58.7% **(L)**| +73.5% **(W)**| +64.7%| ML |
| **Beats B&H** | | 2/6 | 1/6 | 2/6 | — | |

## Commodity (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| GLD | Gold | +151.7%| +147.0% **(L)**| +155.5% **(W)**| +149.3%| ML |
| SLV | Silver | +252.4%| +250.6% **(L)**| +282.2% **(W)**| +264.1%| ML |
| UNG | Natural Gas | -22.5%| -22.3%| -19.2% **(W)**| -26.0% **(L)**| ML |
| USO | Crude Oil | +15.9%| +16.6% **(W)**| +15.7%| +11.5% **(L)**| PSv2 |
| **Beats B&H** | | 3/4 | 2/4 | 4/4 | — | |

## Crypto (2 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| BTC_USD | Bitcoin | +33.7% **(W)**| +33.4%| +33.6%| +32.4% **(L)**| PSv1 |
| ETH_USD | Ethereum | -38.1%| -38.4% **(L)**| -29.2% **(W)**| -32.5%| ML |
| **Beats B&H** | | 1/2 | 1/2 | 2/2 | — | |

## Bond (3 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| IEF | Treasury 7-10yr | +3.5% **(W)**| +3.4% **(L)**| +3.4%| +3.4%| PSv1 |
| SHY | Treasury 1-3yr | +1.8% **(W)**| +1.6% **(L)**| +1.6%| +1.6%| PSv1 |
| TLT | Treasury 20+yr | -2.7% **(W)**| -3.4%| -3.4%| -3.6% **(L)**| PSv1 |
| **Beats B&H** | | 3/3 | 1/3 | 1/3 | — | |

## Forex (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| FXB | British Pound | +6.9% **(W)**| +6.7% **(L)**| +6.7%| +6.7%| PSv1 |
| FXE | Euro | +9.0%| +9.5% **(W)**| +9.5%| +8.8% **(L)**| PSv2 |
| FXY | Japanese Yen | -3.4% **(W)**| -3.9% **(L)**| -3.9%| -3.9%| PSv1 |
| UUP | US Dollar Index | -3.4% **(W)**| -3.4%| -3.4%| -3.4%| PSv1 |
| **Beats B&H** | | 3/4 | 1/4 | 1/4 | — | |


---

## Grand Summary

| Metric | PSv1 | PSv2 | ML |
|:-------|------:|------:|------:|
| **Avg Return** | +37.7% | +37.6% | +41.1% |
| **Median Return** | +33.7% | +33.4% | +33.6% |
| **# Wins (Best)** | **11/41** | **13/41** | **6/41** |
| **Beats B&H** | **21/41** (51%) | **18/41** (44%) | **24/41** (59%) |
| Median Alpha | +0.1% | +0.0% | +0.2% |

### Recommendation

**Ranked by median total return (41 assets):**

| Rank | Strategy | Median Return | Avg Return | # Wins | Beats B&H |
|:-----|:---------|-------------:|----------:|:------:|:---------:|
| 1 | **PSv1** | +33.7% | +37.7% | 11/41 | 21/41 |
| 2 | **ML** | +33.6% | +41.1% | 6/41 | 24/41 |
| 3 | **PSv2** | +33.4% | +37.6% | 13/41 | 18/41 |
| — | B&H | +33.0% | +39.1% | 1/41 | — |

**Analysis:**

- Hourly data has shorter history and more noise — all three PS variants cluster within <0.3% of each other on median return.
- **PSv2** wins the most individual races (13/41), **PSv1** has the highest median (+33.7%), **ML** has the highest avg return (+41.1%) and highest beats-B&H rate (59%).
- ML's avg advantage comes from bigger wins on parabolics (TSLA +26.7%, SLV +18.1%, FXI +8.8%) while tying PSv2 on most other assets.
- ML is the only strategy with positive median alpha (+0.2%).

**For the hackathon:** Near-tie. **ML** has the highest avg return and consistency (59% beat B&H), **PSv1** has the highest median. Use ML if parabolic risk exists; use PSv1 if ML deps unavailable.

### ML Peak Shaver — Wins & Losses vs B&H

**Beats B&H on 24/41 assets**

| Asset | Category | ML | B&H | Alpha |
|:------|:---------|-----:|----:|------:|
| TSLA | Stock | +136.6% | +109.9% | **+26.7%** |
| SLV | Commodity | +282.2% | +264.1% | **+18.1%** |
| FXI | Global | +73.5% | +64.7% | **+8.8%** |
| UNG | Commodity | -19.2% | -26.0% | **+6.8%** |
| GLD | Commodity | +155.5% | +149.3% | **+6.2%** |
| USO | Commodity | +15.7% | +11.5% | **+4.2%** |
| ETH_USD | Crypto | -29.2% | -32.5% | **+3.3%** |
| AAPL | Stock | +47.4% | +44.9% | **+2.5%** |
| WMT | Stock | +113.5% | +111.9% | **+1.6%** |
| AMZN | Stock | +26.6% | +25.1% | **+1.5%** |
| BTC_USD | Crypto | +33.6% | +32.4% | **+1.2%** |
| FXE | Forex | +9.5% | +8.8% | **+0.7%** |
| IWM | Index | +34.3% | +33.9% | **+0.4%** |
| XLRE | Sector | +13.6% | +13.2% | **+0.4%** |
| MSFT | Stock | -0.2% | -0.5% | **+0.3%** |
| XLE | Sector | +28.1% | +27.8% | **+0.3%** |
| XLU | Sector | +50.3% | +50.0% | **+0.3%** |
| XLV | Sector | +8.9% | +8.6% | **+0.3%** |
| EWJ | Global | +35.1% | +34.8% | **+0.3%** |
| XLK | Sector | +42.3% | +42.1% | **+0.2%** |
| TLT | Bond | -3.4% | -3.6% | **+0.2%** |
| JPM | Stock | +73.5% | +73.4% | **+0.1%** |
| XLP | Sector | +18.4% | +18.3% | **+0.1%** |
| XLY | Sector | +31.6% | +31.5% | **+0.1%** |

**Loses to B&H on 17/41 assets**

| Asset | Category | ML | B&H | Gap |
|:------|:---------|-----:|----:|----:|
| EEM | Global | +54.8% | +55.0% | -0.2% |
| XOM | Stock | +41.2% | +41.3% | -0.1% |
| EWG | Global | +49.6% | +49.7% | -0.1% |
| DIA | Index | +28.9% | +28.9% | +0.0% |
| QQQ | Index | +43.6% | +43.6% | +0.0% |
| SPY | Index | +39.2% | +39.2% | +0.0% |
| JNJ | Stock | +53.8% | +53.8% | +0.0% |
| XLB | Sector | +24.8% | +24.8% | +0.0% |
| XLF | Sector | +33.0% | +33.0% | +0.0% |
| XLI | Sector | +50.3% | +50.3% | +0.0% |
| EFA | Global | +37.6% | +37.6% | +0.0% |
| EWU | Global | +47.4% | +47.4% | +0.0% |
| IEF | Bond | +3.4% | +3.4% | +0.0% |
| SHY | Bond | +1.6% | +1.6% | +0.0% |
| FXB | Forex | +6.7% | +6.7% | +0.0% |
| FXY | Forex | -3.9% | -3.9% | +0.0% |
| UUP | Forex | -3.4% | -3.4% | +0.0% |
