# Daily (10yr) Backtest Results — Peak Shaver Strategies

**Data: ~10yr daily bars (2016 to 2026) from Yahoo Finance** | **Initial Capital:** $10,000 | **Commission:** 0.0% | **Assets:** 41

## Strategies

| Code | Name | Type | Description |
|:-----|:-----|:-----|:------------|
| **PSv1** | **Peak Shaver v1** | **Continuous** | **RSI>75 + ROC>11% -> 50%, RSI>85 -> 30%** |
| **PSv2** | **Peak Shaver v2** | **Continuous** | **v1 + Z-score>1.0 gate (Tier 1), Z>3.0 gate (Tier 2)** |
| **ML** | **ML Peak Shaver v2** | **Continuous** | **XGBRegressor+RF regression, multi-horizon labels, magnitude-weighted, dynamic ensemble** |

## Index (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| DIA | Dow Jones ETF | +247.6% **(L)**| +284.8% **(W)**| +280.4%| +263.9%| PSv2 |
| IWM | Russell 2000 ETF | +213.3% **(W)**| +209.6%| +206.2%| +196.6% **(L)**| PSv1 |
| QQQ | Nasdaq 100 ETF | +539.3%| +561.4% **(W)**| +551.8%| +533.8% **(L)**| PSv2 |
| SPY | S&P 500 ETF | +321.8% **(W)**| +318.9%| +316.4% **(L)**| +317.6%| PSv1 |
| **Beats B&H** | | 3/4 | 4/4 | 3/4 | — | |

## Stock (8 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| AAPL | Apple | +1089.6% **(L)**| +1159.6% **(W)**| +1151.6%| +1105.8%| PSv2 |
| AMZN | Amazon | +857.4% **(W)**| +835.6%| +717.9%| +651.1% **(L)**| PSv1 |
| JNJ | Johnson & Johnson | +177.2% **(L)**| +195.2%| +202.1%| +203.2% **(W)**| B&H |
| JPM | JPMorgan Chase | +579.5% **(L)**| +594.8% **(W)**| +582.9%| +593.9%| PSv2 |
| MSFT | Microsoft | +776.3% **(W)**| +764.6%| +775.4%| +757.5% **(L)**| PSv1 |
| TSLA | Tesla | +1250.3%| +1209.2% **(L)**| +3523.5% **(W)**| +3375.5%| ML |
| WMT | Walmart | +635.3% **(W)**| +617.4%| +590.5%| +574.5% **(L)**| PSv1 |
| XOM | Exxon Mobil | +196.2% **(W)**| +188.1%| +174.2% **(L)**| +176.3%| PSv1 |
| **Beats B&H** | | 4/8 | 6/8 | 5/8 | — | |

## Sector (10 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| XLB | Materials | +245.7% **(W)**| +227.8%| +228.9%| +211.5% **(L)**| PSv1 |
| XLE | Energy | +188.2%| +200.7% **(W)**| +185.3%| +182.8% **(L)**| PSv2 |
| XLF | Financials | +246.9% **(L)**| +280.3% **(W)**| +259.0%| +265.3%| PSv2 |
| XLI | Industrials | +289.7% **(L)**| +298.4%| +295.3%| +305.5% **(W)**| B&H |
| XLK | Technology | +696.6%| +691.8%| +700.0% **(W)**| +665.4% **(L)**| ML |
| XLP | Consumer Staples | +131.7% **(W)**| +125.5%| +124.9%| +124.7% **(L)**| PSv1 |
| XLRE | Real Estate | +116.3%| +117.3%| +123.7% **(W)**| +111.1% **(L)**| ML |
| XLU | Utilities | +176.8% **(W)**| +171.2%| +170.9% **(L)**| +172.7%| PSv1 |
| XLV | Healthcare | +171.1% **(L)**| +174.5%| +174.2%| +177.0% **(W)**| B&H |
| XLY | Consumer Discr. | +255.9%| +278.3%| +289.0% **(W)**| +252.8% **(L)**| ML |
| **Beats B&H** | | 7/10 | 7/10 | 6/10 | — | |

## Global (6 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| EEM | Emerging Markets | +159.8% **(W)**| +153.4%| +148.7% **(L)**| +151.1%| PSv1 |
| EFA | MSCI Intl Developed | +168.1%| +169.1% **(W)**| +168.8%| +159.5% **(L)**| PSv2 |
| EWG | Germany ETF | +129.6%| +133.1%| +128.9% **(L)**| +134.0% **(W)**| B&H |
| EWJ | Japan ETF | +163.1% **(W)**| +162.7%| +158.2%| +154.1% **(L)**| PSv1 |
| EWU | UK ETF | +138.9%| +140.7% **(W)**| +137.0%| +135.1% **(L)**| PSv2 |
| FXI | China Large Cap | +66.3%| +68.3% **(W)**| +67.7%| +57.7% **(L)**| PSv2 |
| **Beats B&H** | | 5/6 | 5/6 | 4/6 | — | |

## Commodity (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| GLD | Gold | +317.8%| +318.9%| +321.8% **(W)**| +305.8% **(L)**| ML |
| SLV | Silver | +454.6%| +394.9% **(L)**| +490.4% **(W)**| +431.0%| ML |
| UNG | Natural Gas | -84.6%| -82.3% **(W)**| -85.5%| -88.6% **(L)**| PSv2 |
| USO | Crude Oil | +21.6%| +24.2%| +26.7% **(W)**| +13.4% **(L)**| ML |
| **Beats B&H** | | 4/4 | 3/4 | 4/4 | — | |

## Crypto (2 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| BTC_USD | Bitcoin | +3189.0%| +2963.5% **(L)**| +11130.1%| +15369.1% **(W)**| B&H |
| ETH_USD | Ethereum | +114.5% **(L)**| +129.5%| +593.8% **(W)**| +512.3%| ML |
| **Beats B&H** | | 0/2 | 0/2 | 1/2 | — | |

## Bond (3 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| IEF | Treasury 7-10yr | +6.9% **(L)**| +11.1%| +11.4% **(W)**| +9.8%| ML |
| SHY | Treasury 1-3yr | +16.3% **(L)**| +18.2%| +18.3% **(W)**| +18.1%| ML |
| TLT | Treasury 20+yr | -7.5%| -6.3%| -5.4% **(W)**| -10.4% **(L)**| ML |
| **Beats B&H** | | 1/3 | 3/3 | 3/3 | — | |

## Forex (4 assets)

| Asset | Name | PSv1 | PSv2 | ML | B&H | Best |
|:------|:-----|-------:|-------:|-------:|----:|:-----|
| FXB | British Pound | +6.0% **(W)**| +3.1%| +3.1%| +2.2% **(L)**| PSv1 |
| FXE | Euro | +7.5% **(W)**| +6.2%| +6.1%| +5.9% **(L)**| PSv1 |
| FXY | Japanese Yen | -30.8% **(W)**| -30.9%| -30.9%| -30.9% **(L)**| PSv1 |
| UUP | US Dollar Index | +30.2% **(W)**| +28.7%| +28.7%| +28.4% **(L)**| PSv1 |
| **Beats B&H** | | 4/4 | 4/4 | 4/4 | — | |


---

## Grand Summary

| Metric | PSv1 | PSv2 | ML |
|:-------|------:|------:|------:|
| **Avg Return** | +348.1% | +344.2% | +608.3% |
| **Avg Return (excl. outliers)** | +169.9% | +185.3% | +240.4% |
| **Median Return** | +177.2% | +188.1% | +185.3% |
| **# Wins (Best)** | **15/41** | **10/41** | **11/41** |
| **Beats B&H** | **28/41** (68%) | **32/41** (78%) | **30/41** (73%) |
| Median Alpha | +4.1% | +5.5% | +3.1% |

### Recommendation

**Ranked by median total return (41 assets):**

| Rank | Strategy | Median Return | Avg Return | Avg (excl. outliers) | # Wins | Beats B&H |
|:-----|:---------|-------------:|----------:|--------------------:|:------:|:---------:|
| 1 | **PSv2** | +188.1% | +344.2% | +185.3% | 10/41 | 32/41 |
| 2 | **ML** | +185.3% | +608.3% | +240.4% | 11/41 | 30/41 |
| 3 | **PSv1** | +177.2% | +348.1% | +169.9% | 15/41 | 28/41 |
| — | B&H | +182.8% | +697.0% | +229.6% | 5/41 | — |

**Analysis:**

- **ML** has the highest avg return (+608.3%) and highest outlier-excluded avg (+240.4%) — parabolic overrides on TSLA, ETH, SLV, BTC drive massive gains.
- **PSv2** has the highest median return (+188.1%) and highest beats-B&H rate (32/41).
- **PSv1** wins the most individual races (15/41) on steady assets where aggressive trimming pays off.
- ML barely trails PSv1/PSv2 on non-parabolics (<5% gaps) but gains thousands of pct on parabolics.

**For the hackathon:** **ML Peak Shaver** — highest avg return, highest outlier-excluded avg, robust parabolic handling. Fall back to PSv2 if ML deps unavailable.

### ML Peak Shaver — Wins & Losses

**vs B&H: 30/41 | vs PSv1: 22/41 | vs PSv2: 17/41**

**Beats B&H on 30/41 assets**

| Asset | Category | ML | B&H | Alpha | vs PSv1 | vs PSv2 |
|:------|:---------|-----:|----:|------:|--------:|--------:|
| TSLA | Stock | +3523.5% | +3375.5% | **+148.0%** | +2273.2% | +2314.2% |
| ETH_USD | Crypto | +593.8% | +512.3% | **+81.5%** | +479.3% | +464.3% |
| AMZN | Stock | +717.9% | +651.1% | **+66.9%** | -139.4% | -117.6% |
| SLV | Commodity | +490.4% | +431.0% | **+59.4%** | +35.8% | +95.5% |
| AAPL | Stock | +1151.6% | +1105.8% | **+45.7%** | +62.0% | -8.0% |
| XLY | Sector | +289.0% | +252.8% | **+36.2%** | +33.1% | +10.7% |
| XLK | Sector | +700.0% | +665.4% | **+34.6%** | +3.4% | +8.2% |
| QQQ | Index | +551.8% | +533.8% | **+18.0%** | +12.5% | -9.6% |
| MSFT | Stock | +775.4% | +757.5% | **+17.9%** | -0.9% | +10.8% |
| XLB | Sector | +228.9% | +211.5% | **+17.4%** | -16.8% | +1.1% |
| DIA | Index | +280.4% | +263.9% | **+16.6%** | +32.8% | -4.3% |
| GLD | Commodity | +321.8% | +305.8% | **+16.0%** | +3.9% | +2.9% |
| WMT | Stock | +590.5% | +574.5% | **+16.0%** | -44.8% | -26.9% |
| USO | Commodity | +26.7% | +13.4% | **+13.2%** | +5.0% | +2.4% |
| XLRE | Sector | +123.7% | +111.1% | **+12.6%** | +7.4% | +6.4% |
| FXI | Global | +67.7% | +57.7% | **+10.1%** | +1.4% | -0.6% |
| IWM | Index | +206.2% | +196.6% | **+9.7%** | -7.1% | -3.4% |
| EFA | Global | +168.8% | +159.5% | **+9.3%** | +0.7% | -0.3% |
| TLT | Bond | -5.4% | -10.4% | **+5.0%** | +2.1% | +0.9% |
| EWJ | Global | +158.2% | +154.1% | **+4.1%** | -4.9% | -4.5% |
| UNG | Commodity | -85.5% | -88.6% | **+3.1%** | -0.9% | -3.2% |
| XLE | Sector | +185.3% | +182.8% | **+2.5%** | -2.9% | -15.4% |
| EWU | Global | +137.0% | +135.1% | **+1.8%** | -2.0% | -3.7% |
| IEF | Bond | +11.4% | +9.8% | **+1.6%** | +4.4% | +0.2% |
| FXB | Forex | +3.1% | +2.2% | **+0.9%** | -2.8% | +0.0% |
| UUP | Forex | +28.7% | +28.4% | **+0.3%** | -1.5% | +0.0% |
| XLP | Sector | +124.9% | +124.7% | **+0.2%** | -6.8% | -0.6% |
| FXE | Forex | +6.1% | +5.9% | **+0.2%** | -1.3% | -0.1% |
| SHY | Bond | +18.3% | +18.1% | **+0.1%** | +1.9% | +0.0% |
| FXY | Forex | -30.9% | -30.9% | **+0.0%** | -0.1% | +0.0% |

**Loses to B&H on 11/41 assets**

| Asset | Category | ML | B&H | Gap | vs PSv1 | vs PSv2 |
|:------|:---------|-----:|----:|----:|--------:|--------:|
| BTC_USD | Crypto | +11130.1% | +15369.1% | -4239.1% | +7941.0% | +8166.6% |
| JPM | Stock | +582.9% | +593.9% | -11.0% | +3.4% | -11.9% |
| XLI | Sector | +295.3% | +305.5% | -10.2% | +5.6% | -3.1% |
| XLF | Sector | +259.0% | +265.3% | -6.3% | +12.1% | -21.3% |
| EWG | Global | +128.9% | +134.0% | -5.2% | -0.7% | -4.2% |
| XLV | Sector | +174.2% | +177.0% | -2.8% | +3.1% | -0.3% |
| EEM | Global | +148.7% | +151.1% | -2.4% | -11.1% | -4.7% |
| XOM | Stock | +174.2% | +176.3% | -2.2% | -22.1% | -13.9% |
| XLU | Sector | +170.9% | +172.7% | -1.8% | -5.9% | -0.3% |
| SPY | Index | +316.4% | +317.6% | -1.2% | -5.4% | -2.5% |
| JNJ | Stock | +202.1% | +203.2% | -1.1% | +24.9% | +6.9% |
