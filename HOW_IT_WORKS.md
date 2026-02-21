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

**Result: Beats Buy & Hold on 28/41 assets (68%), wins outright on 23/41 (56%)**

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

# The Peak Shaver (Flagship Strategy)

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
  │ Beats B&H: 8/41 (20%)  │            │ Beats B&H: 28/41 (68%) │
  └─────────────────────────┘            └─────────────────────────┘
```

## How It Works — Two Signals

```
  Signal 1: RSI(14) > 75
  ───────────────────────
  Relative Strength Index measures how "overbought" the price action is.
  Above 75 = heavily overbought. Price has risen too fast relative to
  recent movement. Mean reversion is likely.

  RSI scale:
  0 ──────── 30 ──────── 50 ──────── 70 ── 75 ── 85 ── 100
  oversold     normal       neutral     overbought  EXTREME
                                         ▲           ▲
                                    trigger zone  deeper cut


  Signal 2: 21-day ROC > 11%
  ──────────────────────────
  Rate of Change measures percentage gain over last 21 trading days.
  Above 11% = the asset gained 11%+ in a single month. That's extreme.

  ROC scale:
  -20% ──── -10% ──── 0% ──── 5% ──── 11% ──── 20% ──── 30%+
   crash      bad     flat    normal   trigger   parabolic
                                        ▲
                                   threshold
```

## Decision Logic

```
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  IF RSI > 85:           position = 30%   (extreme peak)    │
  │  ELIF RSI > 75 AND                                         │
  │       ROC(21) > 11%:    position = 50%   (overbought peak) │
  │  ELSE:                  position = 100%  (normal)          │
  │                                                             │
  │  That's it. Three lines of logic.                          │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

Visualized over time:

```
  Position (%)

  100% │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
       │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
   50% │                     █                     █
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
  │  Wins: 28 assets  (avg alpha per win: +18.5%)     │
  │  Losses: 13 assets (dominated by crypto & TSLA)   │
  │  Median alpha: +4.1% (positive!)                   │
  │                                                    │
  │  Losers are overwhelmingly parabolic assets where  │
  │  momentum overwhelms mean reversion:               │
  │  BTC (-12,180%), TSLA (-2,125%), ETH (-398%)       │
  │  Without these 3, the rest lose by only -2% to -26%│
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
  Over 10 years on SPY: PeakShaver +321.8% vs B&H +317.6% (+4.1%)
  Small per-event alpha × many events = consistent edge.
  ═══════════════════════════════════════════════════════════════════
```

---

# The 5 Sub-Strategies (Alternatives)

These are included for comparison. Each uses a different approach.
None beat B&H consistently alone, but they provide different perspectives.

## 1. SMA(200) Trend — Faber Timing Model
Long when price > 200-day SMA. 3-day confirmation filter. ~75% invested.

## 2. Dual MA (50/200) — Golden/Death Cross
Long when SMA(50) > SMA(200) * 1.01. 1% band filter. ~70% invested.

## 3. Momentum Composite — Multi-Timeframe Vote
Invests when 2+ of 3 timeframes (1/3/12-month ROC) are positive. ~70% invested.

## 4. Crash Avoidance — Default Invested
Always in. Exits only when 3/4 crash signals fire. ~90-95% invested.

## 5. Volume Trend — Dual Confirmation
Price + OBV must both confirm. Exits when both break down. ~80% invested.

## Master Ensemble — Binary Committee Vote
Majority vote of all 5 sub-strategies. Enter at 3+, exit at <=1. Hysteresis.
Beats B&H on only 8/41 assets — the binary in/out problem persists.

---

# Technical Reference

## Indicators Used

| Indicator | Function | Used By |
|:----------|:---------|:--------|
| RSI(14) | Overbought/oversold oscillator, 0-100 | **Peak Shaver**, Crash Avoidance |
| ROC(21) | 21-day Rate of Change (1-month momentum) | **Peak Shaver**, Momentum Composite |
| SMA(N) | Simple Moving Average | SMA200 Trend, Dual MA, Crash Avoidance |
| EMA(N) | Exponential Moving Average | Volume Trend |
| ATR(14) | Average True Range (volatility) | Crash Avoidance |
| OBV | On-Balance Volume | Volume Trend |
| ROC(63/252) | 3/12-month Rate of Change | Momentum Composite |

## Backtester Modes

| Method | Used By | Position Range | Description |
|:-------|:--------|:--------------|:------------|
| `run()` | Binary strategies | 0% or 100% | All-in / all-out trades |
| `run_positions()` | **Peak Shaver** | 0% to 100% | Continuous sizing, rebalances on 5%+ drift |

## Constants

```python
COMMISSION = 0.0    # Per-trade fee (0 = no commission)
INITIAL_CAPITAL = 10_000
REBALANCE_THRESHOLD = 5%  # Only rebalance when drift exceeds 5%
```

## File Map

```
trading_bot_v1/
├── trading_bot.py              ← all code (single file)
├── backtest_results.png        ← chart output (single asset)
├── cross_asset_results.png     ← chart output (all 41 assets)
├── test_data/
│   ├── SPY.csv ... (41 CSVs)  ← 10yr Yahoo Finance data
│   └── BACKTEST_RESULTS.md     ← comprehensive results table
├── CLAUDE.md                   ← hackathon context
└── HOW_IT_WORKS.md             ← this file
```
