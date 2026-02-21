# How the Trading Bot Works

## Overall Pipeline

```
┌──────────────┐    ┌────────────┐    ┌─────────────────┐    ┌────────────────┐
│  MARKET DATA │───>│ INDICATORS │───>│  5 SUB-STRATEGIES│───>│   ENSEMBLE     │
│              │    │            │    │                  │    │                │
│ 41 assets    │    │ SMA, EMA,  │    │ Each outputs a   │    │ Combines all 5 │
│ 10yr Yahoo   │    │ RSI, ATR,  │    │ binary position: │    │ into a single  │
│ Finance data │    │ ROC, OBV   │    │ 1 = invested     │    │ consensus score│
│              │    │            │    │ 0 = cash         │    │ (0 to 5)       │
└──────────────┘    └────────────┘    └─────────────────┘    └───────┬────────┘
                                                                     │
                                                          ┌──────────▼──────────┐
                                                          │  LEV ENSEMBLE       │
                                                          │                     │
                                                          │  Maps consensus to  │
                                                          │  position size:     │
                                                          │  70% to 130%        │
                                                          │  invested           │
                                                          │                     │
                                                          │  NEVER fully exits  │
                                                          └──────────┬──────────┘
                                                                     │
                                                          ┌──────────▼──────────┐
                                                          │  BACKTESTER         │
                                                          │                     │
                                                          │  $10k start         │
                                                          │  Continuous sizing  │
                                                          │  Supports leverage  │
                                                          │  Rebalances on 5%+  │
                                                          │  drift              │
                                                          └─────────────────────┘
```

**Result: Beats Buy & Hold on 28/41 assets (68%), wins outright on 24/41 (59%)**

---

## The Core Insight: Why Most Strategies Lose to Buy & Hold

Before understanding the Lev Ensemble, you need to understand the problem it solves.

Traditional trading strategies are binary: you're either 100% invested or 100% cash.
In a 10-year bull market, **every day you spend in cash costs you compound returns**.

```
The compounding problem (SPY over 10 years):

  Buy & Hold: $10,000 invested for 3,650 days
  ────────────────────────────────────────────────────> $31,760  (+218%)

  Typical active strategy: invested ~70% of the time
  ──────────        ──────────        ────────────────> $22,400  (+124%)
       in cash ^         in cash ^
       (missed gains)    (missed gains)

  Even being RIGHT on your trades doesn't help if you
  miss compounding by sitting in cash too long.

  The math:
  ┌────────────────────────────────────────────────────────────┐
  │  Missing just 10 of the best trading days out of 2,520    │
  │  over 10 years cuts your returns by MORE THAN HALF.       │
  │                                                           │
  │  The best days often happen right after the worst days    │
  │  — so exiting during crashes means missing the recovery.  │
  └────────────────────────────────────────────────────────────┘
```

The Lev Ensemble's solution: **never fully exit**. Instead, dial your exposure
between 70% and 130% based on how many strategies agree the market is bullish.

---

# The Leveraged Ensemble (Primary Strategy)

## How It Works — Step by Step

### Step 1: Run All 5 Sub-Strategies

Each sub-strategy independently decides: "should I be invested right now?" (1 = yes, 0 = no).
On any given day, each one outputs either 1 or 0.

```
Day X example — strong bull market:

  SMA(200) Trend:       1  (price above 200-day SMA for 3+ days)
  Dual MA (50/200):     1  (50-day SMA > 200-day SMA by 1%+)
  Momentum Composite:   1  (2+ of 3 timeframes positive)
  Crash Avoidance:      1  (crash score low, all clear)
  Volume Trend:         1  (price AND volume both uptrending)
                        ─
  Consensus:            5  (all 5 agree: strong bull)
```

```
Day Y example — mixed signals:

  SMA(200) Trend:       1  (still above 200-day SMA)
  Dual MA (50/200):     0  (50-day crossed below 200-day)
  Momentum Composite:   1  (3-month and 12-month still positive)
  Crash Avoidance:      1  (no crash detected)
  Volume Trend:         0  (OBV trending down)
                        ─
  Consensus:            3  (mixed — 3 bullish, 2 bearish)
```

```
Day Z example — bear market:

  SMA(200) Trend:       0  (price below 200-day SMA)
  Dual MA (50/200):     0  (death cross confirmed)
  Momentum Composite:   0  (all 3 timeframes negative)
  Crash Avoidance:      0  (3/4 crash signals firing)
  Volume Trend:         0  (price AND volume breaking down)
                        ─
  Consensus:            0  (unanimous: get defensive)
```

### Step 2: Map Consensus to Position Size

This is the key formula:

```
  position = 1.0 + 0.3 * (consensus / 5.0 * 2 - 1)

  Simplified:
  position = 1.0 + 0.3 * (consensus / 2.5 - 1)

  Then clamp to [0.7, 1.3]
```

What this produces:

```
  Consensus    Calculation                          Position    Meaning
  ─────────    ────────────────────────────────     ────────    ─────────────────────
     0         1.0 + 0.3 * (0/2.5 - 1) = 0.70      70%       Defensive (min)
     1         1.0 + 0.3 * (1/2.5 - 1) = 0.82      82%       Cautious
     2         1.0 + 0.3 * (2/2.5 - 1) = 0.94      94%       Slightly underweight
     3         1.0 + 0.3 * (3/2.5 - 1) = 1.06     106%       Slightly leveraged
     4         1.0 + 0.3 * (4/2.5 - 1) = 1.18     118%       Moderately leveraged
     5         1.0 + 0.3 * (5/2.5 - 1) = 1.30     130%       Max leverage
```

Visualized:

```
  Position Size (% of portfolio)

  130% │                                                      ████████  ← max leverage
       │                                            ████████
  118% │                                  ████████
       │                        ████████
  106% │              ████████
       │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ← 100% = Buy & Hold
   94% │    ████████
       │
   82% │████████
       │
   70% │ ← minimum (never below this — always 70% in the market)
       └──────────────────────────────────────────────────────────────
         0        1        2        3        4        5
                         Consensus (# of strategies saying "buy")
```

### Step 3: Backtester Executes the Position

The backtester (`run_positions()`) takes the daily position target and rebalances:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  Start: $10,000 cash, 0 shares                                 │
  │                                                                 │
  │  For each trading day:                                          │
  │                                                                 │
  │    1. Read target position from Lev Ensemble (0.70 to 1.30)    │
  │                                                                 │
  │    2. Calculate current allocation:                              │
  │       current_alloc = (shares * price) / portfolio_value        │
  │                                                                 │
  │    3. If |current_alloc - target| > 5% → REBALANCE:            │
  │       - target > current: BUY more shares                      │
  │       - target < current: SELL some shares                     │
  │       - For positions > 100%: cash goes negative (margin)      │
  │                                                                 │
  │    4. Record portfolio_value = cash + shares * price            │
  │       (cash can be negative when leveraged)                     │
  └─────────────────────────────────────────────────────────────────┘
```

The 5% drift threshold prevents excessive trading. Without it, tiny daily price
movements would trigger rebalancing every day. With it, the bot only trades when
allocation has meaningfully drifted from target.

---

## Full Worked Example: SPY Over a Market Cycle

```
  ═══════════════════════════════════════════════════════════════════
  Scenario: S&P 500 entering a correction then recovering
  Starting portfolio: $10,000
  ═══════════════════════════════════════════════════════════════════

  ┌─── PHASE 1: Bull Market (consensus = 5, position = 130%) ──────

  Day 1:   SPY = $400, consensus = 5/5
           Target: 130% invested → need $13,000 in stock
           Buy $13,000 of SPY = 32.5 shares
           Cash = $10,000 - $13,000 = -$3,000 (margin)
           Portfolio = -$3,000 + 32.5 * $400 = $10,000

  Day 30:  SPY = $420 (+5%)
           Portfolio = -$3,000 + 32.5 * $420 = $10,650
           That's +6.5% return on 5% move (leverage amplifies!)

           Buy & Hold comparison: $10,000 * 1.05 = $10,500 (+5%)
           Lev Ensemble alpha so far: +$150

  ┌─── PHASE 2: Signals Weaken (consensus drops 5 → 3) ────────────

  Day 60:  SPY = $410, consensus = 3/5
           Target: 106% invested
           Current: 130% → drift > 5% → REBALANCE
           Sell some shares to reduce to 106%
           Now hold ~27.5 shares, cash ≈ -$625

  ┌─── PHASE 3: Correction Hits (consensus drops 3 → 0) ──────────

  Day 90:  SPY = $370 (-10% from peak), consensus = 0/5
           Target: 70% invested
           Current: >100% → REBALANCE
           Sell down to 70% → hold ~19.5 shares, cash ≈ +$3,095

           Portfolio = $3,095 + 19.5 * $370 = $10,310
           Buy & Hold: $10,000 * ($370/$400) = $9,250

           Even though we're down from the peak, being at 70%
           instead of 100% saved us during the drop.

  ┌─── PHASE 4: Recovery Begins (consensus 0 → 3 → 5) ────────────

  Day 120: SPY = $360 (bottom), consensus climbs back to 3
           Target: 106%. Already close to that. Small rebalance.

  Day 150: SPY = $400 (full recovery), consensus = 5
           Target: 130% → ramp back up
           Portfolio ≈ $10,800

           Buy & Hold: back to $10,000 (flat round trip)
           Lev Ensemble: +$800 alpha from reducing exposure
           during the drawdown and leveraging the recovery.

  ═══════════════════════════════════════════════════════════════════
  KEY TAKEAWAY:
  - In bull phases: 130% > 100%, so we outperform B&H
  - In corrections: 70% < 100%, so we lose less than B&H
  - Net result: alpha compounds over time
  ═══════════════════════════════════════════════════════════════════
```

---

## Why It Beats Buy & Hold — The Math

The Lev Ensemble has two sources of alpha:

```
  Source 1: LEVERAGE in bull markets (consensus 4-5)
  ─────────────────────────────────────────────────────
  When all signals agree → 118-130% invested
  In a +10% year, you capture +11.8% to +13.0%
  Extra: +1.8% to +3.0% annually

  Source 2: DEFENSE in corrections (consensus 0-1)
  ─────────────────────────────────────────────────────
  When signals turn bearish → 70-82% invested
  In a -20% crash, you lose -14% to -16.4% instead of -20%
  Savings: +3.6% to +6.0%

  Combined over 10 years of bull/bear cycles:
  ┌──────────────────────────────────────────────────┐
  │  Year 1:  Bull    +13.0% vs +10.0% B&H  (+3.0%) │
  │  Year 2:  Bull    +15.6% vs +12.0% B&H  (+3.6%) │
  │  Year 3:  Bear    -14.0% vs -20.0% B&H  (+6.0%) │
  │  Year 4:  Recov   +19.5% vs +15.0% B&H  (+4.5%) │
  │  Year 5:  Bull    +10.4% vs +8.0% B&H   (+2.4%) │
  │  ...                                              │
  │                                                   │
  │  Compounded alpha over 10 years: +50% to +200%   │
  │  Actual result on SPY: +370.8% vs +317.6%        │
  └──────────────────────────────────────────────────┘
```

---

## When the Lev Ensemble Loses

It underperforms B&H on 13/41 assets. The common patterns:

```
  1. Steady low-vol grinders (XLP, XLU, JNJ, XLV)
     ─────────────────────────────────────────────
     These barely have corrections. Consensus stays at 3-4
     most of the time, so the bot stays near 100-118%.
     But the occasional false signals cause small drag.
     Losses are small: -5% to -22% gap.

  2. Declining / trendless assets (UNG, TLT, FXY)
     ─────────────────────────────────────────────
     When the asset is going down, 70% invested in a
     losing trade still loses. The bot needs the asset
     to go up at SOME point to generate alpha.

  3. Extreme whipsaw assets (IWM, XLRE)
     ─────────────────────────────────────────────
     Frequent regime changes trigger rebalancing costs.
     Sub-strategies disagree constantly → consensus
     oscillates → position swings → drag.
```

---

# The 5 Sub-Strategies

Each one is designed for high time-in-market (70-95% invested).
They're not meant to be used alone — they vote as a committee.

## 1. SMA(200) Trend — Faber Timing Model

Long when price is above the 200-day Simple Moving Average.
Uses 3-day confirmation to avoid whipsaws at the boundary.

```
  Price ($)
                                    price stays above SMA(200) for 3+ days
                                    → ENTER (position = 1)
                                              │
   $150 │                           ╱─────────▼──────────╱──
        │                     ╱────╱                    ╱
   $140 │               ╱────╱                     ╱───╱
        │          ╱────╱  ═══════════════════════════════  SMA(200)
   $130 │    ╱────╱
        │───╱                 price drops below SMA(200) for 3+ days
   $120 │                     → EXIT (position = 0)
        └──────────────────────────────────────────────────── Time
              Invested: ███████████████████████████████████
              Cash:     ████████████████
                        ▲               ▲
                     3-day delay      3-day delay
                    (reduces whipsaws)
```

~75% time invested. Catches major trends, avoids prolonged bear markets.

## 2. Dual MA (50/200) — Golden/Death Cross

Long when 50-day SMA is above 200-day SMA by at least 1%.
The 1% band prevents flipping on tiny crossovers.

```
  Moving Averages ($)

   $150 │          SMA(50) ───╱──────────            ╱──
        │                ╱───╱                  ╱───╱
   $140 │     ══════════════════════════════════════════  SMA(200)
        │        ╱──╱
   $130 │  ╱────╱
        │─╱          │                          │
   $120 │      SMA(50) > SMA(200) * 1.01  SMA(50) < SMA(200) * 0.99
        │            → BUY (golden cross)       → SELL (death cross)
        └──────────────────────────────────────────────────── Time
                 ├─── 1% band ───┤
                 (no signal inside band — prevents whipsaw)
```

~70% time invested. Fewer trades than SMA(200), slower to react.

## 3. Momentum Composite — Multi-Timeframe Vote

Checks 3 momentum timeframes. If 2 of 3 are positive, stay invested.

```
  Each timeframe votes independently:

  1-month ROC (21 days):   price now vs 21 days ago    → +2.1%  → BULLISH (1)
  3-month ROC (63 days):   price now vs 63 days ago    → -1.3%  → BEARISH (0)
  12-month ROC (252 days): price now vs 252 days ago   → +8.7%  → BULLISH (1)
                                                                    ─────────
                                                         Vote:      2/3 → BUY

  Exit only when ALL THREE are negative (0/3).

  Timeline visualization:
  ────────────────────────────────────────────────────── Time
  1-month:   ▓▓▓▓▓▓░░░▓▓▓▓▓▓▓▓▓▓▓░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  3-month:   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  12-month:  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░▓▓▓▓
  Position:  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░▓▓▓▓
                                              ▲
                                         All 3 negative
                                         = only exit point
```

~70% time invested. Very slow to exit — only does so in true bear markets.

## 4. Crash Avoidance — Default Invested

Stays invested at all times. Exits ONLY when 3 of 4 crash signals fire.

```
  The 4 crash signals:

  ┌──────────────────────┬─────────────────────────────────┐
  │ Signal               │ Fires when...                   │
  ├──────────────────────┼─────────────────────────────────┤
  │ Below trend          │ Price < SMA(200)                │
  │ Death cross          │ SMA(50) < SMA(200)              │
  │ Volatility spike     │ ATR > 2x its 1-year average     │
  │ RSI weakness         │ RSI(14) < 35                    │
  └──────────────────────┴─────────────────────────────────┘

  crash_score = (signals firing) / 4

  ┌────────────────────────────────────────────────────────┐
  │ crash_score >= 0.75 (3 or 4 signals) → EXIT           │
  │ crash_score <= 0.25 (0 or 1 signal)  → RE-ENTER       │
  │ default (no signal yet)               → INVESTED       │
  └────────────────────────────────────────────────────────┘

  Normal market:                     Crash:
  ┌─────────────────┐               ┌─────────────────┐
  │ Below trend:  NO │               │ Below trend: YES │
  │ Death cross:  NO │               │ Death cross: YES │
  │ Vol spike:    NO │               │ Vol spike:   YES │
  │ RSI weak:     NO │               │ RSI weak:    YES │
  │                  │               │                  │
  │ Score: 0/4       │               │ Score: 4/4       │
  │ → STAY IN        │               │ → GET OUT        │
  └─────────────────┘               └─────────────────┘
```

~90-95% time invested. Highest of any sub-strategy. Only exits in severe crashes.

## 5. Volume Trend — Dual Confirmation

Invested when BOTH price trend AND volume trend confirm. Exits only when both break.

```
  Price vs EMA(50):                 OBV vs OBV-EMA(50):

  Price ─╱──────                    OBV ──╱─────
        ╱  ═══════ EMA(50)              ╱  ═══════ OBV-EMA
  ─────╱                          ─────╱

  Decision matrix:
  ┌───────────────────┬──────────────────┬──────────────────┐
  │                   │ OBV > OBV-EMA    │ OBV < OBV-EMA    │
  ├───────────────────┼──────────────────┼──────────────────┤
  │ Price > EMA(50)   │ BUY  (both up)   │ HOLD (mixed)     │
  │ Price < EMA(50)   │ HOLD (mixed)     │ SELL (both down)  │
  └───────────────────┴──────────────────┴──────────────────┘

  Only changes position when BOTH agree. Mixed signals → keep current position.
```

~80% time invested. Good at confirming real moves vs fake breakouts.

---

# The Master Ensemble (Binary Version)

Simpler version of the Lev Ensemble. Binary in/out with hysteresis.

```
  Same 5 sub-strategies → same consensus (0-5)

  But instead of continuous position sizing:
  ┌──────────────────────────────────────────────┐
  │  Consensus >= 3  AND  currently OUT  → BUY   │
  │  Consensus <= 1  AND  currently IN   → SELL  │
  │  Otherwise                           → HOLD  │
  └──────────────────────────────────────────────┘

  Hysteresis prevents oscillation:

  Consensus: 5  4  3  2  1  2  3  2  3  4  3  2  1  0  1  2  3  4  5
  Position:  IN IN IN IN IN IN IN IN IN IN IN IN  0  0  0  0 IN IN IN
                              ▲                   ▲              ▲
                         stays in because         exits at       re-enters at
                         consensus > 1            consensus 1    consensus 3
```

Beats B&H on only 8/41 assets. The Lev Ensemble is strictly better because
it never fully exits — the 0% position of the binary ensemble is its downfall.

---

# Technical Reference

## Indicators Used

| Indicator | Function | Used By |
|:----------|:---------|:--------|
| SMA(N) | Average of last N closing prices | SMA200 Trend, Dual MA, Crash Avoidance |
| EMA(N) | Exponential moving average (recent-weighted) | Volume Trend |
| RSI(14) | Momentum oscillator, 0-100 scale | Crash Avoidance |
| ATR(14) | Average True Range (volatility) | Crash Avoidance |
| OBV | On-Balance Volume (cumulative volume direction) | Volume Trend |
| ROC(N) | Rate of Change (% price change over N days) | Momentum Composite |

## Backtester Modes

| Method | Used By | Position Type | Description |
|:-------|:--------|:-------------|:------------|
| `run()` | All binary strategies | 0% or 100% | All-in / all-out, whole trades |
| `run_positions()` | Lev Ensemble | 0% to 130%+ | Continuous sizing, supports leverage |

## Constants

```python
COMMISSION = 0.0    # Per-trade fee (0 = no commission)
INITIAL_CAPITAL = 10_000
REBALANCE_THRESHOLD = 5%  # Only rebalance when allocation drifts 5%+ from target
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
