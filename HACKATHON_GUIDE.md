# LEFS Quant Hackathon — Full Guide

## TL;DR

Write a `generate_signals(data)` function in `submissions/strategy.py` that returns a Series of `{-1, 0, 1}`. Push to a branch named after your team. Ranked primarily by **Sharpe Ratio**.

---

## File Structure

### Organizer-Provided (hackathon_repo/ `main` branch)

Only 3 files from the organizers:

```
hackathon_repo/
├── README.md              # Official rules & submission instructions
├── test.py                # EVALUATION SCRIPT — organizers run this to score you
└── utilities.py           # Downloads training data (SPY + QQQ 2015-2026)
```

### Our Custom Files (added by us in hackathon_repo/)

```
hackathon_repo/
├── validate.py            # Local backtester — tests on SPY/QQQ/XOM, compares vs B&H
├── tune.py                # Parameter sweep for peak shaver thresholds
├── tune_shorts.py         # Tests shorting variants across 41 daily assets
├── run_full_backtest.py   # Full 41-asset backtest suite, outputs markdown
├── data/                  # Training data (downloaded via utilities.py)
│   ├── spy.csv
│   └── qqq.csv
├── submissions/
│   └── strategy.py        # YOUR CODE GOES HERE
└── results/
    └── results.json       # Output from test.py (auto-generated)
```

### Test Data (test_data/)

```
test_data/
├── daily/                 # ~10yr daily OHLCV (2016-2026), 41 assets
│   ├── SPY.csv, QQQ.csv, AAPL.csv, ... (41 CSVs)
│   └── DATA_REFERENCE.md
├── hourly/                # ~2yr hourly OHLCV (2024-2026), 41 assets
│   ├── SPY.csv, QQQ.csv, AAPL.csv, ... (41 CSVs)
│   └── DATA_REFERENCE.md
└── BACKTEST_RESULTS/
    ├── DAILY.md           # Pre-hackathon Peak Shaver v2 results
    ├── HOURLY.md
    ├── DAILY_HACKATHON.md # Enhanced Peak Shaver results
    └── HOURLY_HACKATHON.md
```

### Other Directories

```
hackathon_ref/             # Clean copy of organizer's original 3 files (README, test.py, utilities.py)
old/                       # Archived pre-hackathon work (viz, screenshots, docs)
```

---

## File-by-File Explanation

### `test.py` — The Evaluation Script (MOST IMPORTANT)

This is what the organizers run to score your submission. Understanding it is critical.

**What it does:**
1. Loads a **hidden test CSV** (not SPY/QQQ — it's `data/exxonmobil_xom.csv` in the default, but they'll swap it for unseen data)
2. Dynamically imports your `submissions/strategy.py`
3. Calls `generate_signals(data)` and times it (must finish in <10s)
4. Validates output: must be a `pd.Series` of `{-1, 0, 1}`, same index as data, no NaNs
5. Backtests with **next-day execution** (signals shifted by 1 bar) and **5bps transaction costs**
6. Computes metrics and writes `results/results.json`

**Key constants:**
- `TRADING_DAYS = 252` — annualization factor
- `TRANSACTION_COST = 0.0005` — 5 basis points per trade (each position change)
- `MAX_SIGNAL_TIME_SEC = 10` — strategy timeout

**Backtest logic (exact):**
```python
returns = data["Close"].pct_change()
shifted = positions.shift(1)       # NEXT-DAY execution (no lookahead)
costs = shifted.diff().abs().fillna(0) * 0.0005  # cost on every position change
strategy_returns = shifted * returns - costs
```

**Metrics computed:**
| Metric | Formula |
|--------|---------|
| Total Return | `(1 + returns).prod() - 1` |
| Annual Return | Compounded annualized |
| **Sharpe Ratio** | `(mean / std) * sqrt(252)` — **primary ranking** |
| Max Drawdown | Worst peak-to-trough on equity curve |
| Calmar Ratio | Annual return / abs(max drawdown) |
| Win Rate | % of positive-return days |

### `utilities.py` — Data Downloader

Downloads SPY + QQQ (2015-2026) via yfinance, saves to `data/training_data_multi.csv`. Multi-ticker format with multi-level column headers.

**Run:**
```bash
cd hackathon_repo
python -c "from utilities import download_hackathon_data; download_hackathon_data()"
```

### `validate.py` — Local Backtester

Like `test.py` but runs on multiple tickers (SPY, QQQ, XOM) and shows comparison vs buy-and-hold. Good for quick local testing.

**Run:**
```bash
cd hackathon_repo
python validate.py
```

**Output:**
```
Ticker   Sharpe    Return    MaxDD   Trades |  BH Sharpe  BH Return
----------------------------------------------------------------------
SPY        0.65    +327.5%   -49.3%     142 |       0.58    +253.1%
QQQ        0.78    +512.0%   -42.1%     156 |       0.71    +480.2%
XOM        0.31     +88.4%   -55.2%     198 |       0.25     +62.1%
```

### `tune.py` — Parameter Sweeper

Sweeps combinations of thresholds (RSI, ROC, Z-score, vol, shorting, hold period) across SPY/QQQ/XOM. Reports Sharpe for each config.

**Run:**
```bash
cd hackathon_repo
python tune.py
```

### `tune_shorts.py` — Shorting Variant Tester

Tests whether shorting during bearish/vol/blowoff regimes helps or hurts across all 41 daily assets. Requires `test_data/daily/` to exist.

**Run:**
```bash
cd hackathon_repo
python tune_shorts.py
```

### `run_full_backtest.py` — Full 41-Asset Suite

Runs strategy on all 41 assets (daily + hourly), outputs markdown tables to `test_data/BACKTEST_RESULTS/`. Mirrors `test.py` eval logic exactly.

**Run:**
```bash
cd hackathon_repo
python run_full_backtest.py
```

### `submissions/strategy.py` — Your Strategy

The only file the organizers care about. Must export one function:

```python
def generate_signals(data: pd.DataFrame) -> pd.Series:
    # data has columns: Open, High, Low, Close, Volume
    # Return pd.Series with same index, values in {-1, 0, 1}
    #   1 = long, 0 = flat, -1 = short
```

---

## How Submissions Work

### Step-by-step

1. Write your strategy in `hackathon_repo/submissions/strategy.py`
2. Test locally: `python validate.py` (or `python test.py` with data in `data/`)
3. Create a branch named after your team:
   ```bash
   cd hackathon_repo
   git checkout -b your-team-name
   ```
4. Commit and push:
   ```bash
   git add submissions/strategy.py
   git commit -m "your-team-name submission"
   git push origin your-team-name
   ```
5. Organizers pull your branch, run `test.py` with hidden test data, rank by Sharpe

### Rules
- Signals must be `-1`, `0`, or `1` only (no fractional positions)
- No NaNs in output
- Signal index must match data index exactly
- Must run in <10 seconds
- Don't push to `main`

---

## Example: Completed `submissions/strategy.py`

Simplest possible valid submission (buy-and-hold):

```python
import pandas as pd

def generate_signals(data: pd.DataFrame) -> pd.Series:
    return pd.Series(1, index=data.index)  # always long
```

More realistic — SMA crossover:

```python
import pandas as pd

def generate_signals(data: pd.DataFrame) -> pd.Series:
    close = data["Close"]
    sma_fast = close.rolling(20).mean()
    sma_slow = close.rolling(50).mean()

    signals = pd.Series(0, index=data.index)
    signals[sma_fast > sma_slow] = 1     # long when uptrend
    signals[sma_fast < sma_slow] = -1    # short when downtrend
    signals.iloc[:50] = 0                # warmup period
    return signals.fillna(0).astype(int)
```

---

## Multiple Submissions

To submit multiple strategies (e.g., testing variants), use separate branches:

```
hackathon_repo/
└── submissions/
    └── strategy.py          # only this file matters per branch
```

### Workflow

```bash
# Strategy A — conservative
git checkout -b team-alpha-conservative
# edit submissions/strategy.py with conservative strategy
git add submissions/strategy.py
git commit -m "team-alpha conservative"
git push origin team-alpha-conservative

# Strategy B — aggressive
git checkout -b team-alpha-aggressive
# edit submissions/strategy.py with aggressive strategy
git add submissions/strategy.py
git commit -m "team-alpha aggressive"
git push origin team-alpha-aggressive
```

Each branch has its own `submissions/strategy.py`. The organizers evaluate whichever branch you tell them is your final submission (typically one per team — check with organizers if multiple are allowed).

### How it looks in git

```
main                          ← organizer's template (don't touch)
team-alpha-conservative       ← your branch with strategy A
team-alpha-aggressive         ← your branch with strategy B
```

---

## Data Format

All CSVs follow the same OHLCV format:

```csv
Date,Close,High,Low,Open,Volume
2015-01-02,170.59,171.79,169.55,171.38,121465900
2015-01-05,167.51,169.71,167.20,169.54,169632600
```

- Index: `Date` (datetime, parsed automatically)
- Columns: `Open`, `High`, `Low`, `Close`, `Volume`
- Daily data: ~2500 rows (10yr)
- Hourly data: ~3500 rows (2yr, market hours only)
- The hidden test data will have the same format but for a different/unknown ticker and date range

---

## Quick Reference

| Task | Command |
|------|---------|
| Download training data | `python -c "from utilities import download_hackathon_data; download_hackathon_data()"` |
| Test locally (3 tickers) | `python validate.py` |
| Run official eval | `python test.py` |
| Tune parameters | `python tune.py` |
| Test shorting variants | `python tune_shorts.py` |
| Full 41-asset backtest | `python run_full_backtest.py` |
| Submit | `git checkout -b team-name && git add . && git commit -m "submission" && git push origin team-name` |

All commands run from `hackathon_repo/`.
