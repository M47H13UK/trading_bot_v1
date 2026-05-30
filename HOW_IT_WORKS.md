# How the Trading Bot Works

## Overall Pipeline

```
┌──────────────┐    ┌────────────┐    ┌──────────────────┐    ┌────────────────┐
│  MARKET DATA │───>│ INDICATORS │───>│  PEAK SHAVER     │    │  BACKTESTER    │
│              │    │            │    │  (flagship)       │───>│                │
│ OHLCV data   │    │ RSI(14)    │    │                  │    │ $10k start     │
│ daily bars   │    │ ROC(21)    │    │ 100% invested    │    │ Continuous     │
│              │    │            │    │ default, reduce  │    │ position sizing│
│              │    │            │    │ at overbought    │    │ 0% to 100%     │
│              │    │            │    │ peaks only       │    │ No leverage    │
└──────────────┘    └────────────┘    └──────────────────┘    └────────────────┘
```

**Result: Beats Buy & Hold on 32/41 assets (78%) daily, 20/41 (49%) hourly**

---

## The Core Insight: Why It's Hard to Beat Buy & Hold

Traditional trading strategies are binary: either 100% invested or 100% cash.
In a 10-year bull market, **every day in cash costs compound returns**.

```
The compounding problem (SPY over 10 years):

  Buy & Hold: $10,000 invested for 3,650 days
  ────────────────────────────────────────────────────> $31,760  (+218%)

  Typical active strategy: invested ~70% of the time
  ──────────        ──────────        ────────────────> $22,400  (+124%)
       in cash ^         in cash ^
       (missed gains)    (missed gains)

  ┌────────────────────────────────────────────────────────────┐
  │  Missing just 10 of the best trading days out of 2,520    │
  │  over 10 years cuts your returns by MORE THAN HALF.       │
  │                                                           │
  │  The best days often happen right after the worst days    │
  │  — so exiting during crashes means missing the recovery.  │
  └────────────────────────────────────────────────────────────┘
```

Without leverage, you can AT BEST match B&H (100% invested). Any time below
100% is pure drag. The ONLY way to beat B&H is to reduce exposure right
before drops and be back at 100% before rallies.

**Our approach: don't try to avoid crashes. Instead, shave peaks.**

---

# The Peak Shaver v2 (Flagship Strategy)

## The Idea

Instead of trying to predict crashes (which adds drag from false signals),
exploit a simple statistical fact: **overbought peaks tend to mean-revert**.

When RSI is extreme AND momentum is extreme, the asset is likely to pull back.
By reducing position at these peaks, we capture small but consistent alpha.

```
  The key difference from crash-avoidance strategies:

  Crash avoidance:                        Peak Shaver:
  ┌─────────────────────────┐            ┌─────────────────────────┐
  │ "Get out when it's bad" │            │ "Take some off at peaks"│
  │                         │            │                         │
  │ Problem: you're OUT     │            │ Advantage: 95%+ of time │
  │ during the recovery.    │            │ at 100%. Minimal drag.  │
  │ Cash drag kills alpha.  │            │ Small alpha x many days │
  │                         │            │ = consistent edge.      │
  │ Beats B&H: 8/41 (20%)  │            │ Beats B&H: 32/41 (78%) │
  └─────────────────────────┘            └─────────────────────────┘
```

## How It Works — Three Signals (Triple Confirmation)

v2 adds Z-score as a third confirmation signal. This filters out bad trims
where RSI is overbought but price isn't statistically stretched from its mean.

```
  Signal 1: RSI(14) > 75
  ───────────────────────
  Relative Strength Index measures how "overbought" the price action is.
  Above 75 = heavily overbought.

  Signal 2: 21-day ROC > 11%
  ──────────────────────────
  Rate of Change measures percentage gain over last 21 trading days.
  Above 11% = gained 11%+ in a single month.

  Signal 3: Z-score(50) > 1.0  [NEW in v2]
  ─────────────────────────────────────────
  Z-score measures how many standard deviations the price is above its
  50-day moving average. > 1.0 = price is statistically stretched.
  This prevents trimming during steady trends where RSI stays high
  but price isn't far from its trend line (e.g., JNJ, DIA, JPM).

  For deep trim (Tier 2): Z-score > 3.0 required — only at genuine
  blow-off tops (3+ std devs above mean).
```

## Decision Logic

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  IF RSI > 85 AND Z-score > 3.0:                                 │
  │      position = 30%    (extreme overbought + extreme stretch)    │
  │  ELIF RSI > 75 AND ROC(21) > 11% AND Z-score > 1.0:            │
  │      position = 40%    (overbought + momentum + stretched)       │
  │  ELSE:                                                           │
  │      position = 100%   (normal — fully invested)                 │
  │                                                                  │
  │  Timeframe-adaptive: periods auto-scale for hourly/daily bars.   │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘
```

Visualized over time:

```
  Position (%)

  100% │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
       │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
   40% │                     █                     █
       │                     █                     █
   30% │
       └────────────────────────────────────────────────────────────── Time
                             ▲                     ▲
                          RSI>75 &              RSI>75 &
                          ROC>11%               ROC>11%
                          (peak shave)          (peak shave)

  Typical: ~95-97% of trading days at 100%. Only 3-5% of days reduced.
```

## Why It Beats Buy & Hold

```
  The math behind peak shaving:

  1. Asset rallies 11%+ in 21 days with RSI > 75
  2. Strategy reduces to 50%
  3. Common outcomes:

     Scenario A (60% of the time): Price pulls back 2-5%
     ─────────────────────────────────────────────────────
     B&H loses the full pullback.
     Peak Shaver loses only half (50% position).
     Alpha: +1% to +2.5% per event.

     Scenario B (40% of the time): Price keeps rallying
     ─────────────────────────────────────────────────────
     B&H captures the full rally.
     Peak Shaver captures only half.
     Loss: variable, depends on continuation.

  Because mean reversion happens MORE OFTEN than continuation at
  RSI > 75 extremes, the net expectation is positive.

  Across 41 assets, 10 years each:
  ┌───────────────────────────────────────────────────┐
  │  Wins: 32 assets  (78% beat rate)                  │
  │  Losses: 9 assets (dominated by crypto & TSLA)     │
  │  Median alpha: +5.5% (positive!)                   │
  │                                                    │
  │  v2 improvement: Z-score filter prevented bad      │
  │  trims on AAPL, DIA, IEF, JPM, SHY, XLF.          │
  │  (+6 gained, -2 lost vs v1)                        │
  │                                                    │
  │  Remaining losers: parabolic assets where           │
  │  momentum overwhelms mean reversion:               │
  │  BTC (-12,406%), TSLA (-2,166%), ETH (-383%)       │
  └───────────────────────────────────────────────────┘
```

## When It Loses

```
  1. Parabolic rallies (crypto, meme stocks)
     ────────────────────────────────────────
     BTC went from $4k to $100k+. RSI stayed above 75 for
     extended periods. Peak shaving at 50% during these
     sustained rallies means missing massive gains.
     These assets defy normal mean-reversion statistics.

  2. Very steady grinders (JNJ, bonds)
     ────────────────────────────────────────
     Rarely trigger RSI > 75, so peak shaving barely activates.
     When it does, the pullback might not come (steady trends).
     Losses are small: -2% to -26%.

  3. Assets that NEVER pull back
     ────────────────────────────────────────
     Some stocks rally in a straight line (TSLA 2020).
     Peak shaving reduces position, but the rally continues.
     The 50% position means capturing only half the gain.
```

---

# Worked Example: SPY Over a Market Cycle

```
  ═══════════════════════════════════════════════════════════════════
  Scenario: S&P 500, $10,000 starting capital
  ═══════════════════════════════════════════════════════════════════

  ┌─── PHASE 1: Normal Bull Market ─────────────────────────────────

  Day 1-100:  SPY climbs steadily from $400 to $440 (+10%)
              RSI oscillates 50-65, ROC stays < 11%
              Position: 100% → MATCHES Buy & Hold exactly
              Both portfolios: ~$11,000

  ┌─── PHASE 2: Euphoric Rally ─────────────────────────────────────

  Day 100-120: SPY surges from $440 to $495 (+12.5% in 20 days)
               RSI hits 78, ROC = 12.3% → BOTH SIGNALS TRIGGER
               Position drops from 100% to 50%

               Day 120: Portfolio = $5,250 cash + $5,250 in SPY
               Buy & Hold: $12,375

  ┌─── PHASE 3: Mean Reversion (the payoff) ─────────────────────────

  Day 121-135: SPY pulls back from $495 to $475 (-4%)
               RSI drops to 55, ROC drops → position back to 100%

               Peak Shaver at day 121: $5,250 + $5,250 = $10,500 in SPY
               Loss on SPY portion: -4% of $5,250 = -$210
               Peak Shaver value: ~$12,165

               Buy & Hold: $12,375 * 0.96 = $11,880

               Alpha from this ONE event: +$285 (+2.3%)

  ┌─── PHASE 4: Back to Normal ─────────────────────────────────────

  Day 135+:    RSI < 75, position = 100%
               Back to matching B&H, but starting from a higher base.

  ═══════════════════════════════════════════════════════════════════
  Over 10 years on SPY: PeakShaver v2 +318.9% vs B&H +317.6% (+1.3%)
  Small per-event alpha × many events = consistent edge.
  ═══════════════════════════════════════════════════════════════════
```

---

# Related Strategies in This Repo

Peak Shaver has two rule-based tiers, plus ML and competition variants:

| Strategy | Code | What it does |
|:---------|:-----|:-------------|
| Peak Shaver v1 | `strategy_peak_shaver_v1` | RSI + ROC trim only |
| **Peak Shaver v2** | `strategy_peak_shaver` | v1 + the Z-score gate described above |
| ML Peak Shaver v2/v3 | `ml_peak_shaver_v2.py`, `ml_peak_shaver_v3.py` | Learn *when* to override the rule-based trims — see [ML_PS_Explanation.md](ML_PS_Explanation.md) |
| Hackathon Sharpe | `strategy_hackathon_sharpe` | Discrete `{-1, 0, 1}` variant for the competition's next-day, 5bps backtest |

> **Note:** earlier binary in/out strategies (SMA-200, Dual-MA, Momentum, Crash-Avoidance, Volume-Trend, Ensemble) were removed. Each beat Buy & Hold on far fewer assets (the best, the Ensemble, only ~8/41) because time spent in cash is pure drag — the core insight at the top of this doc.

---

# Technical Reference

## Indicators Used

| Indicator | Function | Used By |
|:----------|:---------|:--------|
| RSI(14) | Overbought/oversold oscillator, 0-100 | **Peak Shaver v2**, Hackathon Sharpe, ML features |
| ROC(21) | 21-day Rate of Change (1-month momentum) | **Peak Shaver v2**, ML features |
| Z-score(50) | Std devs above 50-day mean (statistical stretch) | **Peak Shaver v2**, Hackathon Sharpe, ML features |
| ADX(14) | Trend strength / regime | Hackathon Sharpe, ML features |
| SMA / EMA | Moving averages (trend, slopes) | Hackathon Sharpe, ML features |
| ATR(14) | Average True Range (volatility) | Hackathon Sharpe, ML features |
| OBV / CMF | Volume-flow indicators | ML features |
| MACD, Bollinger, etc. | Momentum / volatility bands | ML features (36–37 total) |

## Backtester Modes

| Method | Used By | Position Range | Description |
|:-------|:--------|:--------------|:------------|
| `run_positions()` | **Peak Shaver v1/v2, ML v2/v3** | 0% to 100% | Continuous sizing, rebalances on 5%+ drift, 0% commission |
| `backtest_hackathon()` | Hackathon Sharpe | -1 / 0 / +1 | Discrete signals, next-day execution, 5bps cost (mirrors the competition eval) |

## Constants

```python
COMMISSION = 0.0    # Per-trade fee (0 = no commission)
INITIAL_CAPITAL = 10_000
REBALANCE_THRESHOLD = 5%  # Only rebalance when drift exceeds 5%
```

## File Map

```
trading_bot_v1/
├── trading_bot.py              ← rule-based Peak Shaver v1/v2 + Hackathon Sharpe + backtester
├── ml_peak_shaver_v2.py        ← ML Peak Shaver v2 (XGB+RF ensemble)
├── ml_peak_shaver_v3.py        ← ML v3 Return Maximizer
├── run_full_backtest.py        ← regenerates the results tables + charts below
├── backtest_results.png        ← SPY strategy-lineage chart
├── cross_asset_results.png     ← cross-asset beat-rate + return chart
├── test_data/
│   ├── daily/                  ← 10yr daily Yahoo Finance data (41 benchmark + extra training tickers)
│   ├── hourly/                 ← 2yr hourly data (same tickers)
│   └── BACKTEST_RESULTS/       ← DAILY.md + HOURLY.md results tables
├── HOW_IT_WORKS.md             ← this file (rule-based Peak Shaver)
└── ML_PS_Explanation.md        ← ML v2/v3 deep dive
```

> Full project layout (including the hackathon submission) is in the top-level [README.md](README.md).
