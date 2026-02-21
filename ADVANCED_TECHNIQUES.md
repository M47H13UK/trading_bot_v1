# Advanced Techniques — Beyond Long-Only

Reference doc for hackathon (Feb 22, 2026). Current bot is long-only, 0-100% position, no derivatives. This covers what's possible if rules allow more.

---

## 1. Current Limitations

Our Peak Shaver:
- **Long-only**: can hold 0% to 100%, never short
- **No leverage**: max exposure = 1x capital
- **Position range**: 100% default, reduces to 50% (RSI>75 + ROC>11%) or 30% (RSI>85)
- **Alpha ceiling**: at best, we avoid some downside — can't profit from drops

Result: beats B&H on 28/41 assets (68%), but alpha is modest (median +4.1%). The big losses come from parabolic assets (BTC -12,180%, TSLA -2,125%) where shaving peaks costs us continuation gains.

---

## 2. Leverage — Amplifying Alpha

### The Idea

If Peak Shaver generates +4.1% median alpha at 1x, leverage multiplies it:
- **2x leverage**: median alpha becomes ~+8.2%
- **3x leverage**: median alpha becomes ~+12.3%

### How It Works with Peak Shaver

```
Current (1x):
  Normal:     100% invested  (1.0x exposure)
  Overbought: 50% invested   (0.5x exposure)
  Extreme:    30% invested    (0.3x exposure)

With 2x leverage:
  Normal:     200% invested  (2.0x exposure)
  Overbought: 100% invested  (1.0x exposure)  ← B&H equivalent
  Extreme:    60% invested   (0.6x exposure)
```

At 2x, our "reduced" position during peaks is still 100% — we're not missing rallies, just deleveraging. This is far safer than 2x B&H which stays at 2x through crashes.

### Concrete Example: SPY

```
SPY 10yr backtest:
  B&H (1x):          +317.6%
  Peak Shaver (1x):  +321.8%  (alpha: +4.1%)

  B&H (2x):          ~+635%   (but 2x drawdowns too)
  Peak Shaver (2x):  ~+644%   (alpha: ~+8%, with reduced drawdowns)
                                deleverages at peaks → less max drawdown
```

### Kelly Criterion for Sizing

Kelly formula determines optimal leverage based on win rate and payoff ratio:

```
f* = (p * b - q) / b

Where:
  p = win probability (Peak Shaver beats B&H 68% of time)
  q = 1 - p = 0.32
  b = avg win / avg loss (varies by asset)

For SPY-like assets: Kelly suggests ~1.5-2.0x is optimal
For crypto: Kelly suggests <1x (high variance destroys leveraged positions)
```

**Key rule**: never go full Kelly — use half-Kelly (0.75-1.0x) to survive variance.

### Risks

- **Margin calls**: 2x means 50% drop wipes you out. Must have stop-losses
- **Funding costs**: borrowing costs ~5-8% annualized, eats into alpha
- **Volatility drag**: leveraged positions lose more to daily rebalancing in choppy markets
- **Liquidation**: in crypto/futures, forced liquidation can happen intraday

---

## 3. Shorting — Profiting from Peaks

### The Idea

Currently when RSI>75 + ROC>11%, we reduce to 50%. What if instead we go **short**?

```
Current Peak Shaver:
  Peak detected → reduce from 100% to 50%
  Pullback of -4% → saved 2% vs B&H (half the loss avoided)

Short Peak Shaver:
  Peak detected → flip from +100% to -50% (short)
  Pullback of -4% → gained 2% from short PLUS saved 4% on long
  Total alpha: +6% per event (3x the current alpha)
```

### Position Spectrum

```
Without shorting:    0% ─────────────── 50% ──────────── 100%
                     cash              reduced           full long
                     (not possible     (overbought)      (default)
                      in current bot)

With shorting:      -100% ──── -50% ──── 0% ──── 50% ──── 100%
                    full short  partial   flat    partial   full long
                               short     cash    long
```

### Market-Neutral Strategy

Go long one asset, short a correlated one. Profit from the spread, not direction.

```
Example: Long XLK (Tech), Short SPY (S&P 500)
  - If tech outperforms: long gains > short losses → profit
  - If tech underperforms: short gains > long losses → profit
  - Market direction doesn't matter, only relative performance
```

Peak Shaver backtests show XLK (+696.6%) massively outperforms SPY (+321.8%). A pairs trade would've captured that spread with lower drawdowns.

### Risks

- **Unlimited loss potential**: a short can lose >100% if price goes to infinity
- **Short squeeze**: forced covering in illiquid markets
- **Borrowing fees**: hard-to-borrow stocks cost 5-50%+ annually
- **Uptick rules**: some markets restrict shorting on downticks

---

## 4. Combined: Leveraged Long-Short

### Full Range Deployment

```
Position spectrum: -1x ──────── 0x ──────── +1x ──────── +2x

Peak Shaver with full toolkit:
  RSI < 30 (oversold):        +2.0x  (leveraged long — buying the dip)
  RSI 30-75 (normal):         +1.5x  (moderate leverage)
  RSI > 75, ROC > 11%:        -0.5x  (short — profiting from pullback)
  RSI > 85:                   -1.0x  (full short — extreme overbought)
```

### Impact on Our Backtest Numbers

```
SPY example — estimated with leverage + shorting:

  Strategy             Return    Max Drawdown
  ─────────────────────────────────────────────
  B&H (1x)             +317%       -34%
  Peak Shaver (1x)     +321%       -30%  (current)
  Peak Shaver (2x L)   ~+644%      -45%  (leveraged only)
  Peak Shaver (L+S)    ~+800%      -35%  (leverage + shorting)
                                          short positions hedge
                                          during drawdowns
```

The short leg acts as a natural hedge: when markets drop, our short profits offset long losses. Max drawdown actually improves vs pure leverage.

### Why This Is Powerful

1. **Alpha on both sides**: profit from peaks (short) AND dips (leveraged long)
2. **Reduced drawdowns**: short positions hedge during market drops
3. **Higher Sharpe ratio**: more return per unit risk
4. **Capital efficiency**: same capital generates returns from both directions

---

## 5. Other Real-Life Techniques

### Options

- **Protective puts**: buy puts when RSI>75 instead of reducing position. Keeps upside if rally continues, limits downside
- **Covered calls**: sell calls at peak signals — collect premium, cap upside (which we expect to be limited anyway)
- **Straddles**: buy both calls and puts before high-volatility events. Profit from big moves in either direction
- **Cost**: options premium is the drag. Works best when volatility is underpriced

### Statistical Arbitrage / Pairs Trading

- Cointegrated pairs (e.g., XOM/CVX, MSFT/AAPL) mean-revert relative to each other
- Z-score of spread triggers entries: long the underperformer, short the overperformer
- Market-neutral: no directional exposure, pure alpha
- Our backtest data shows many sector ETFs track closely — good candidates

### ML/RL-Based Signal Generation

- **Random forests / gradient boosting**: combine RSI, ROC, volume, volatility into a single prediction
- **LSTM/transformer**: capture temporal patterns in price sequences
- **Reinforcement learning**: agent learns optimal position sizing directly from reward (return)
- **Risk**: overfitting. 10 years of daily data = ~2,500 samples. Not much for deep learning

### Sentiment Analysis

- **News NLP**: parse headlines for bullish/bearish keywords, event detection
- **Social media**: Reddit/Twitter sentiment as contrarian or momentum signal
- **Earnings surprises**: pre-position around earnings using whisper numbers
- **Latency**: by the time sentiment is quantifiable, the move may be priced in

### High-Frequency / Order Flow

- **Order book imbalance**: bid/ask volume ratio predicts short-term direction
- **VWAP/TWAP**: execution algorithms that minimize market impact
- **Tick data**: sub-second patterns in trade flow
- **Not relevant for hackathon** — requires low-latency infrastructure and tick data

### Portfolio Optimization

- **Mean-variance (Markowitz)**: optimal allocation across multiple assets given expected returns and covariance
- **Risk parity**: weight assets by inverse volatility — equal risk contribution
- **Black-Litterman**: combine market equilibrium with our Peak Shaver views
- **Relevant if hackathon provides multiple assets** — optimize allocation, not just per-asset signals

### Alternative Data

- **Satellite imagery**: parking lot counts, shipping traffic, crop health
- **Credit card transaction data**: real-time revenue estimates
- **Patent filings, job postings**: leading indicators of company direction
- **Not hackathon-relevant** — requires expensive data subscriptions

---

## 6. Questions to Ask at Hackathon

### Trading Mechanics
1. Is shorting allowed? If yes, any position limits (e.g., max -100%)?
2. Is leverage allowed? If yes, max leverage ratio?
3. Are there position size limits (min/max % per trade)?
4. Can we hold fractional positions (e.g., 50% invested) or only binary in/out?
5. Is there a margin system or just a leverage multiplier?

### Data & Assets
6. What data is provided — OHLCV? Tick data? Fundamentals?
7. Single asset or multiple assets to trade?
8. If multiple, can we go long one and short another (pairs)?
9. Can we use external data (APIs, web scraping) or only provided data?
10. What timeframe — daily bars? Intraday?

### Evaluation Criteria
11. What's the primary metric — total return, Sharpe, or something else?
12. Are there risk constraints (max drawdown limit, VaR)?
13. Is there a penalty for high turnover or excessive trading?
14. Is risk-adjusted return weighted (Sharpe, Sortino, Calmar)?
15. Are there any baseline benchmarks we're compared against (B&H, index)?

### Execution Rules
16. What commission/fee per trade?
17. Is slippage modeled?
18. How often can we rebalance — every bar? Daily? Weekly?
19. Is there a minimum holding period?
20. Do we start with a fixed capital amount?

### Technical
21. What programming languages/libraries are allowed?
22. Is there a compute time limit for backtests?
23. What's the submission format — code file, CSV of trades, or live API?
24. Can we use pre-trained ML models or must everything train on provided data?
25. Is there internet access during the hackathon?
