# Test Data Reference

## Source

All data downloaded from **Yahoo Finance** via the [`yfinance`](https://github.com/ranaroussi/yfinance) Python library.

- **Yahoo Finance**: https://finance.yahoo.com/
- **yfinance docs**: https://github.com/ranaroussi/yfinance
- **License**: Yahoo Finance data is free for personal use. See [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html).

## How the Data Was Downloaded

**Requirements:**
```bash
pip install yfinance pandas
```

**Command used (inside `trading_bot.py`):**
```python
import yfinance as yf

data = yf.download("TICKER", period="10y", progress=False, auto_adjust=True)
data.index.name = "Date"
data.to_csv("test_data/TICKER.csv")
```

- `period="10y"` — requests 10 years of daily history
- `auto_adjust=True` — prices are split- and dividend-adjusted (no separate Adj Close column)
- Crypto tickers trade 7 days/week; equities trade business days only

**To re-download all data from scratch:**
```bash
rm test_data/*.csv
python3 trading_bot.py   # auto-downloads missing tickers on startup
```

**To download a single ticker manually:**
```python
python3 -c "
import yfinance as yf
data = yf.download('SPY', period='10y', progress=False, auto_adjust=True)
data.index.name = 'Date'
data.to_csv('test_data/SPY.csv')
"
```

## File Format

All CSV files have the same format:

```
Date,Close,High,Low,Open,Volume
2016-02-22,193.72,196.00,193.02,195.55,120843700
```

| Column   | Description |
|----------|-------------|
| `Date`   | Trading date (YYYY-MM-DD), used as row index |
| `Close`  | Adjusted closing price |
| `High`   | Adjusted daily high |
| `Low`    | Adjusted daily low |
| `Open`   | Adjusted daily open |
| `Volume` | Number of shares/units traded |

## Date Ranges

| Category | Date Range | Rows | Frequency |
|----------|-----------|------|-----------|
| Equities & ETFs | 2016-02-22 to 2026-02-20 | 2515 | Business days (Mon-Fri) |
| BTC-USD | 2016-02-21 to 2026-02-21 | 3653 | Every day (7 days/week) |
| ETH-USD | 2017-11-09 to 2026-02-21 | 3026 | Every day (ETH data starts Nov 2017) |

---

## Individual Stocks

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `AAPL.csv` | AAPL | Apple Inc. | US mega-cap tech company. Listed on NASDAQ. | [link](https://finance.yahoo.com/quote/AAPL/) |
| `AMZN.csv` | AMZN | Amazon.com Inc. | US e-commerce and cloud computing giant. Listed on NASDAQ. | [link](https://finance.yahoo.com/quote/AMZN/) |
| `JNJ.csv` | JNJ | Johnson & Johnson | US healthcare/pharmaceutical conglomerate. Listed on NYSE. | [link](https://finance.yahoo.com/quote/JNJ/) |
| `JPM.csv` | JPM | JPMorgan Chase & Co. | Largest US bank by assets. Listed on NYSE. | [link](https://finance.yahoo.com/quote/JPM/) |
| `MSFT.csv` | MSFT | Microsoft Corporation | US software and cloud computing company. Listed on NASDAQ. | [link](https://finance.yahoo.com/quote/MSFT/) |
| `TSLA.csv` | TSLA | Tesla Inc. | US electric vehicle and clean energy company. Listed on NASDAQ. | [link](https://finance.yahoo.com/quote/TSLA/) |
| `WMT.csv` | WMT | Walmart Inc. | World's largest retailer by revenue. Listed on NYSE. | [link](https://finance.yahoo.com/quote/WMT/) |
| `XOM.csv` | XOM | Exxon Mobil Corporation | US oil and gas supermajor. Listed on NYSE. | [link](https://finance.yahoo.com/quote/XOM/) |

## Cryptocurrencies

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `BTC_USD.csv` | BTC-USD | Bitcoin / US Dollar | Largest cryptocurrency by market cap. Trades 24/7. | [link](https://finance.yahoo.com/quote/BTC-USD/) |
| `ETH_USD.csv` | ETH-USD | Ethereum / US Dollar | Second-largest cryptocurrency. Data starts Nov 2017. | [link](https://finance.yahoo.com/quote/ETH-USD/) |

## US Equity Index ETFs

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `SPY.csv` | SPY | SPDR S&P 500 ETF Trust | Tracks the S&P 500 index (500 largest US companies). Most traded ETF in the world. | [link](https://finance.yahoo.com/quote/SPY/) |
| `QQQ.csv` | QQQ | Invesco QQQ Trust | Tracks the Nasdaq-100 index, heavily weighted toward US large-cap tech. | [link](https://finance.yahoo.com/quote/QQQ/) |
| `DIA.csv` | DIA | SPDR Dow Jones Industrial Average ETF | Tracks the Dow Jones Industrial Average (30 blue-chip US stocks). | [link](https://finance.yahoo.com/quote/DIA/) |
| `IWM.csv` | IWM | iShares Russell 2000 ETF | Tracks the Russell 2000 index of US small-cap stocks. | [link](https://finance.yahoo.com/quote/IWM/) |

## International Equity ETFs

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `EEM.csv` | EEM | iShares MSCI Emerging Markets ETF | Broad exposure to emerging markets (China, India, Brazil, etc.). | [link](https://finance.yahoo.com/quote/EEM/) |
| `EFA.csv` | EFA | iShares MSCI EAFE ETF | Developed markets outside US and Canada (Europe, Australasia, Far East). | [link](https://finance.yahoo.com/quote/EFA/) |
| `EWG.csv` | EWG | iShares MSCI Germany ETF | Large- and mid-cap German equities. Eurozone's largest economy. | [link](https://finance.yahoo.com/quote/EWG/) |
| `EWJ.csv` | EWJ | iShares MSCI Japan ETF | Large- and mid-cap Japanese equities. World's third-largest economy. | [link](https://finance.yahoo.com/quote/EWJ/) |
| `EWU.csv` | EWU | iShares MSCI United Kingdom ETF | Large- and mid-cap UK equities on the London Stock Exchange. | [link](https://finance.yahoo.com/quote/EWU/) |
| `FXI.csv` | FXI | iShares China Large-Cap ETF | 50 largest Chinese companies listed on the Hong Kong Stock Exchange. | [link](https://finance.yahoo.com/quote/FXI/) |

## Currency ETFs

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `FXB.csv` | FXB | Invesco CurrencyShares British Pound Trust | Tracks GBP vs USD. | [link](https://finance.yahoo.com/quote/FXB/) |
| `FXE.csv` | FXE | Invesco CurrencyShares Euro Trust | Tracks EUR vs USD. | [link](https://finance.yahoo.com/quote/FXE/) |
| `FXY.csv` | FXY | Invesco CurrencyShares Japanese Yen Trust | Tracks JPY vs USD. | [link](https://finance.yahoo.com/quote/FXY/) |
| `UUP.csv` | UUP | Invesco DB US Dollar Index Bullish Fund | Tracks the US Dollar Index (DXY) vs a basket of major currencies. | [link](https://finance.yahoo.com/quote/UUP/) |

## Bond / Fixed Income ETFs

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `SHY.csv` | SHY | iShares 1-3 Year Treasury Bond ETF | Short-duration US Treasuries. Low volatility, often used as cash proxy. | [link](https://finance.yahoo.com/quote/SHY/) |
| `IEF.csv` | IEF | iShares 7-10 Year Treasury Bond ETF | Intermediate-duration US Treasuries. Sensitive to interest rate changes. | [link](https://finance.yahoo.com/quote/IEF/) |
| `TLT.csv` | TLT | iShares 20+ Year Treasury Bond ETF | Long-duration US Treasuries. Highly rate-sensitive; often used as equity hedge. | [link](https://finance.yahoo.com/quote/TLT/) |

## Commodity ETFs

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `GLD.csv` | GLD | SPDR Gold Shares | Tracks the spot price of gold. Largest physically-backed gold ETF. | [link](https://finance.yahoo.com/quote/GLD/) |
| `SLV.csv` | SLV | iShares Silver Trust | Tracks the spot price of silver. Physically-backed silver ETF. | [link](https://finance.yahoo.com/quote/SLV/) |
| `USO.csv` | USO | United States Oil Fund | Tracks WTI crude oil futures. Subject to contango/backwardation effects. | [link](https://finance.yahoo.com/quote/USO/) |
| `UNG.csv` | UNG | United States Natural Gas Fund | Tracks natural gas futures. Subject to significant contango decay over time. | [link](https://finance.yahoo.com/quote/UNG/) |

## S&P 500 Sector ETFs (Select Sector SPDRs)

These ETFs each hold the stocks from one sector of the S&P 500, allowing targeted sector exposure.

| File | Ticker | Full Name | Description | Yahoo Finance Link |
|------|--------|-----------|-------------|--------------------|
| `XLB.csv` | XLB | Materials Select Sector SPDR Fund | Chemicals, metals, mining, and packaging companies. | [link](https://finance.yahoo.com/quote/XLB/) |
| `XLE.csv` | XLE | Energy Select Sector SPDR Fund | Oil, gas, and energy equipment companies. | [link](https://finance.yahoo.com/quote/XLE/) |
| `XLF.csv` | XLF | Financial Select Sector SPDR Fund | Banks, insurance, and diversified financial services. | [link](https://finance.yahoo.com/quote/XLF/) |
| `XLI.csv` | XLI | Industrial Select Sector SPDR Fund | Aerospace, defense, machinery, and transportation companies. | [link](https://finance.yahoo.com/quote/XLI/) |
| `XLK.csv` | XLK | Technology Select Sector SPDR Fund | Software, hardware, semiconductors, and IT services. | [link](https://finance.yahoo.com/quote/XLK/) |
| `XLP.csv` | XLP | Consumer Staples Select Sector SPDR Fund | Food, beverage, household products, and tobacco companies. | [link](https://finance.yahoo.com/quote/XLP/) |
| `XLRE.csv` | XLRE | Real Estate Select Sector SPDR Fund | REITs and real estate management/development companies. | [link](https://finance.yahoo.com/quote/XLRE/) |
| `XLU.csv` | XLU | Utilities Select Sector SPDR Fund | Electric, gas, and water utilities. | [link](https://finance.yahoo.com/quote/XLU/) |
| `XLV.csv` | XLV | Health Care Select Sector SPDR Fund | Pharma, biotech, medical devices, and healthcare providers. | [link](https://finance.yahoo.com/quote/XLV/) |
| `XLY.csv` | XLY | Consumer Discretionary Select Sector SPDR Fund | Retail, automotive, apparel, and leisure companies. | [link](https://finance.yahoo.com/quote/XLY/) |
