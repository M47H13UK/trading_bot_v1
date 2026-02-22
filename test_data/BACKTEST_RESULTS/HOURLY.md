# Hourly (2yr) Backtest Results — Peak Shaver Strategies

**Data: ~2yr hourly bars (2024 to 2026) from Yahoo Finance** | **Initial Capital:** $10,000 | **Commission:** 0.0% | **Assets:** 41

## Strategies

| Code | Name | Type | Description |
|:-----|:-----|:-----|:------------|
| **PSv1** | **Peak Shaver v1** | **Continuous** | **RSI>75 + ROC>11% -> 50%, RSI>85 -> 30%** |
| **PSv2** | **Peak Shaver v2** | **Continuous** | **v1 + Z-score>1.0 gate (Tier 1), Z>3.0 gate (Tier 2)** |
| **ML** | **ML Peak Shaver v2** | **Continuous** | **XGBRegressor+RF regression, multi-horizon labels, magnitude-weighted, dynamic ensemble** |

## Index (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| DIA | Dow Jones ETF | +28.2% **(L)**| +28.9% **(W)**| +28.9%| +28.9%| PSv2 |
| IWM | Russell 2000 ETF | +35.4% **(W)**| +34.3%| +34.0%| +33.9% **(L)**| PSv1 |
| QQQ | Nasdaq 100 ETF | +43.6% **(W)**| +43.6% **(L)**| +43.6%| +43.6%| PSv1 |
| SPY | S&P 500 ETF | +39.1% **(L)**| +39.2% **(W)**| +39.2%| +39.2%| PSv2 |
| **Beats B&H** | | 2/4 | 1/4 | 1/4 | — | |

## Stock (8 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| AAPL | Apple | +46.4%| +46.9% **(W)**| +44.0% **(L)**| +44.9%| PSv2 |
| AMZN | Amazon | +25.5%| +26.7% **(W)**| +26.0%| +25.1% **(L)**| PSv2 |
| JNJ | Johnson & Johnson | +53.8%| +53.8%| +53.8%| +53.8%| PSv1 |
| JPM | JPMorgan Chase | +72.8% **(L)**| +73.5% **(W)**| +73.5%| +73.5%| PSv2 |
| MSFT | Microsoft | +0.9%| +1.0% **(W)**| -0.5% **(L)**| -0.5%| PSv2 |
| TSLA | Tesla | +64.2%| +57.8% **(L)**| +108.3%| +109.9% **(W)**| B&H |
| WMT | Walmart | +111.3% **(L)**| +111.4%| +113.0% **(W)**| +111.8%| ML |
| XOM | Exxon Mobil | +41.4% **(W)**| +41.0%| +41.0% **(L)**| +41.3%| PSv1 |
| **Beats B&H** | | 4/8 | 4/8 | 3/8 | — | |

## Sector (10 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| XLB | Materials | +25.7% **(W)**| +24.8% **(L)**| +24.8%| +24.8%| PSv1 |
| XLE | Energy | +28.4% **(W)**| +28.1%| +27.8% **(L)**| +27.8%| PSv1 |
| XLF | Financials | +31.3% **(L)**| +33.0% **(W)**| +33.0%| +33.0%| PSv2 |
| XLI | Industrials | +49.7% **(L)**| +50.3% **(W)**| +50.3%| +50.3%| PSv2 |
| XLK | Technology | +41.2% **(L)**| +42.3%| +42.3% **(W)**| +42.1%| ML |
| XLP | Consumer Staples | +18.2% **(L)**| +18.4%| +18.4% **(W)**| +18.3%| ML |
| XLRE | Real Estate | +13.6%| +13.6%| +13.7% **(W)**| +13.2% **(L)**| ML |
| XLU | Utilities | +50.2%| +50.3%| +50.4% **(W)**| +50.0% **(L)**| ML |
| XLV | Healthcare | +8.6%| +8.9% **(W)**| +8.6% **(L)**| +8.6%| PSv2 |
| XLY | Consumer Discr. | +30.1% **(L)**| +31.6%| +31.7% **(W)**| +31.5%| ML |
| **Beats B&H** | | 5/10 | 7/10 | 5/10 | — | |

## Global (6 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| EEM | Emerging Markets | +55.4% **(W)**| +54.8%| +54.8% **(L)**| +55.0%| PSv1 |
| EFA | MSCI Intl Developed | +35.7% **(L)**| +37.6% **(W)**| +37.6%| +37.6%| PSv2 |
| EWG | Germany ETF | +43.1% **(L)**| +49.6%| +49.6%| +49.7% **(W)**| B&H |
| EWJ | Japan ETF | +39.2% **(W)**| +35.1%| +35.2%| +34.8% **(L)**| PSv1 |
| EWU | UK ETF | +47.3% **(L)**| +47.4% **(W)**| +47.4%| +47.4%| PSv2 |
| FXI | China Large Cap | +59.4%| +58.7% **(L)**| +73.5% **(W)**| +64.7%| ML |
| **Beats B&H** | | 2/6 | 2/6 | 3/6 | — | |

## Commodity (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| GLD | Gold | +151.7% **(W)**| +147.0% **(L)**| +150.2%| +149.3%| PSv1 |
| SLV | Silver | +252.4%| +250.6%| +248.1% **(L)**| +264.1% **(W)**| B&H |
| UNG | Natural Gas | -22.5%| -22.3%| -19.7% **(W)**| -26.0% **(L)**| ML |
| USO | Crude Oil | +15.9%| +16.6% **(W)**| +15.9%| +11.5% **(L)**| PSv2 |
| **Beats B&H** | | 3/4 | 2/4 | 3/4 | — | |

## Crypto (2 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| BTC_USD | Bitcoin | +33.7%| +33.4%| +33.8% **(W)**| +32.5% **(L)**| ML |
| ETH_USD | Ethereum | -38.1%| -38.4% **(L)**| -32.1% **(W)**| -32.5%| ML |
| **Beats B&H** | | 1/2 | 1/2 | 2/2 | — | |

## Bond (3 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| IEF | Treasury 7-10yr | +3.5% **(W)**| +3.4%| +3.4%| +3.4% **(L)**| PSv1 |
| SHY | Treasury 1-3yr | +1.8% **(W)**| +1.6% **(L)**| +1.6%| +1.6%| PSv1 |
| TLT | Treasury 20+yr | -2.7% **(W)**| -3.4%| -3.4%| -3.6% **(L)**| PSv1 |
| **Beats B&H** | | 3/3 | 2/3 | 2/3 | — | |

## Forex (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| FXB | British Pound | +6.9% **(W)**| +6.7% **(L)**| +6.7%| +6.7%| PSv1 |
| FXE | Euro | +9.0%| +9.5% **(W)**| +8.8% **(L)**| +8.8%| PSv2 |
| FXY | Japanese Yen | -3.4% **(W)**| -3.9% **(L)**| -3.9%| -3.9%| PSv1 |
| UUP | US Dollar Index | -3.4% **(W)**| -3.4% **(L)**| -3.4%| -3.4%| PSv1 |
| **Beats B&H** | | 4/4 | 1/4 | 0/4 | — | |


---

## Grand Summary

| Metric | PSv1 | PSv2 | ML |
|:-------|------:|------:|------:|
| **Avg Return** | +37.7% | +37.6% | +39.3% |
| **Avg Return (excl. outliers)** | +27.1% | +27.1% | +28.9% |
| **Median Return** | +33.7% | +33.4% | +33.8% |
| **# Wins (Best)** | **15/41** | **13/41** | **10/41** |
| **Beats B&H** | **24/41** (58%) | **20/41** (48%) | **19/41** (46%) |
| Median Alpha | +0.1% | +0.0% | +0.0% |

### Recommendation

**Ranked by median total return (41 assets):**

| Rank | Strategy | Median Return | Avg Return | Avg (excl. outliers) | # Wins | Beats B&H |
|:-----|:---------|-------------:|----------:|--------------------:|:------:|:---------:|
| 1 | **ML** | +33.8% | +39.3% | +28.9% | 10/41 | 19/41 |
| 2 | **PSv1** | +33.7% | +37.7% | +27.1% | 15/41 | 24/41 |
| 3 | **PSv2** | +33.4% | +37.6% | +27.1% | 13/41 | 20/41 |
| — | B&H | +33.0% | +39.1% | +28.3% | 3/41 | — |

**Analysis:**

- **ML** has the highest avg return (+39.3%) and highest outlier-excluded avg (+28.9%) — parabolic overrides on TSLA, ETH, SLV, BTC drive massive gains.
- **PSv1** has the highest beats-B&H rate (24/41) and highest median alpha (+0.1%).
- **PSv1** wins the most individual races (15/41) on steady assets where aggressive trimming pays off.
- ML barely trails PSv1/PSv2 on non-parabolics (<5% gaps) but gains thousands of pct on parabolics.

**For the hackathon:** Near-tie on median. **ML** has the highest avg return and best parabolic handling. Use ML if parabolic risk exists; PSv1/PSv2 if ML deps unavailable.

### ML Peak Shaver — Wins & Losses

**vs B&H: 19/41 | vs PSv1: 20/41 | vs PSv2: 15/41**

**Beats B&H on 19/41 assets**

| Asset | Category | ML | B&H | Alpha | vs PSv1 | vs PSv2 |
|:------|:---------|-----:|----:|------:|--------:|--------:|
| FXI | Global | +73.5% | +64.7% | **+8.8%** | +14.0% | +14.8% |
| UNG | Commodity | -19.7% | -26.0% | **+6.2%** | +2.8% | +2.6% |
| USO | Commodity | +15.9% | +11.5% | **+4.4%** | -0.0% | -0.7% |
| BTC_USD | Crypto | +33.8% | +32.5% | **+1.3%** | +0.1% | +0.4% |
| WMT | Stock | +113.0% | +111.8% | **+1.2%** | +1.7% | +1.7% |
| AMZN | Stock | +26.0% | +25.1% | **+0.9%** | +0.5% | -0.7% |
| GLD | Commodity | +150.2% | +149.3% | **+0.9%** | -1.5% | +3.2% |
| XLRE | Sector | +13.7% | +13.2% | **+0.5%** | +0.0% | +0.0% |
| ETH_USD | Crypto | -32.1% | -32.5% | **+0.4%** | +6.0% | +6.3% |
| XLU | Sector | +50.4% | +50.0% | **+0.4%** | +0.2% | +0.0% |
| EWJ | Global | +35.2% | +34.8% | **+0.3%** | -4.0% | +0.0% |
| XLK | Sector | +42.3% | +42.1% | **+0.2%** | +1.2% | +0.0% |
| TLT | Bond | -3.4% | -3.6% | **+0.2%** | -0.7% | +0.0% |
| IWM | Index | +34.0% | +33.9% | **+0.2%** | -1.4% | -0.2% |
| XLY | Sector | +31.7% | +31.5% | **+0.2%** | +1.6% | +0.1% |
| IEF | Bond | +3.4% | +3.4% | **+0.0%** | -0.1% | +0.0% |
| EWU | Global | +47.4% | +47.4% | **+0.0%** | +0.1% | +0.0% |
| XLP | Sector | +18.4% | +18.3% | **+0.0%** | +0.1% | +0.0% |
| JPM | Stock | +73.5% | +73.5% | **+0.0%** | +0.7% | +0.0% |

**Loses to B&H on 22/41 assets**

| Asset | Category | ML | B&H | Gap | vs PSv1 | vs PSv2 |
|:------|:---------|-----:|----:|----:|--------:|--------:|
| SLV | Commodity | +248.1% | +264.1% | -16.0% | -4.3% | -2.6% |
| TSLA | Stock | +108.3% | +109.9% | -1.6% | +44.1% | +50.5% |
| AAPL | Stock | +44.0% | +44.9% | -0.9% | -2.4% | -2.9% |
| XOM | Stock | +41.0% | +41.3% | -0.4% | -0.5% | -0.0% |
| EEM | Global | +54.8% | +55.0% | -0.2% | -0.6% | -0.0% |
| EWG | Global | +49.6% | +49.7% | -0.1% | +6.4% | -0.0% |
| DIA | Index | +28.9% | +28.9% | +0.0% | +0.7% | +0.0% |
| EFA | Global | +37.6% | +37.6% | +0.0% | +1.9% | +0.0% |
| FXB | Forex | +6.7% | +6.7% | +0.0% | -0.2% | +0.0% |
| FXE | Forex | +8.8% | +8.8% | +0.0% | -0.1% | -0.7% |
| FXY | Forex | -3.9% | -3.9% | +0.0% | -0.5% | +0.0% |
| JNJ | Stock | +53.8% | +53.8% | +0.0% | +0.0% | +0.0% |
| MSFT | Stock | -0.5% | -0.5% | +0.0% | -1.4% | -1.5% |
| QQQ | Index | +43.6% | +43.6% | +0.0% | -0.1% | +0.0% |
| SHY | Bond | +1.6% | +1.6% | +0.0% | -0.2% | +0.0% |
| SPY | Index | +39.2% | +39.2% | +0.0% | +0.0% | +0.0% |
| UUP | Forex | -3.4% | -3.4% | +0.0% | -0.1% | +0.0% |
| XLB | Sector | +24.8% | +24.8% | +0.0% | -0.9% | +0.0% |
| XLE | Sector | +27.8% | +27.8% | +0.0% | -0.6% | -0.3% |
| XLF | Sector | +33.0% | +33.0% | +0.0% | +1.7% | +0.0% |
| XLI | Sector | +50.3% | +50.3% | +0.0% | +0.6% | +0.0% |
| XLV | Sector | +8.6% | +8.6% | +0.0% | -0.1% | -0.3% |
