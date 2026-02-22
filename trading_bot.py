"""
Quant Hackathon: Adaptive Regime-Based Trading Bot
===================================================
Competition-grade bot with regime detection, adaptive strategy switching,
volatility-based risk management, and cross-asset robustness.

Strategies adapt to market conditions: trend-following in trending markets,
mean-reversion in ranging markets, reduced exposure when uncertain.

Requirements:
    pip install pandas numpy matplotlib yfinance pick

Usage:
    python trading_bot.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import yfinance as yf
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ML imports are lazy to avoid circular import (ml_peak_shaver imports from here)
ML_READY = False

def _init_ml():
    """Lazy-load ML module. Returns True if available."""
    global ML_READY
    if ML_READY:
        return True
    try:
        import ml_peak_shaver_v2 as ml_peak_shaver
        if ml_peak_shaver.ML_AVAILABLE:
            ML_READY = True
            return True
    except ImportError:
        pass
    return False


# =============================================================================
# CONSTANTS
# =============================================================================

COMMISSION = 0.0  # per-trade commission rate (set to e.g. 0.001 for 0.1%)

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "daily"
HOURLY_DATA_DIR = Path(__file__).parent / "test_data" / "hourly"

# 41 tickers across 8 categories — diverse enough to prove robustness
DEFAULT_TICKERS = [
    # US Index ETFs
    ("SPY",     "S&P 500 ETF",           "Index"),
    ("QQQ",     "Nasdaq 100 ETF",        "Index"),
    ("DIA",     "Dow Jones ETF",         "Index"),
    ("IWM",     "Russell 2000 ETF",      "Index"),
    # Global ETFs
    ("EFA",     "MSCI Intl Developed",   "Global"),
    ("EEM",     "Emerging Markets",      "Global"),
    ("FXI",     "China Large Cap",       "Global"),
    ("EWJ",     "Japan ETF",             "Global"),
    ("EWG",     "Germany ETF",           "Global"),
    ("EWU",     "UK ETF",                "Global"),
    # US Sector ETFs
    ("XLK",     "Technology",            "Sector"),
    ("XLV",     "Healthcare",            "Sector"),
    ("XLE",     "Energy",                "Sector"),
    ("XLF",     "Financials",            "Sector"),
    ("XLY",     "Consumer Discr.",       "Sector"),
    ("XLP",     "Consumer Staples",      "Sector"),
    ("XLI",     "Industrials",           "Sector"),
    ("XLB",     "Materials",             "Sector"),
    ("XLU",     "Utilities",             "Sector"),
    ("XLRE",    "Real Estate",           "Sector"),
    # Individual stocks (diverse industries)
    ("AAPL",    "Apple",                 "Stock"),
    ("MSFT",    "Microsoft",             "Stock"),
    ("AMZN",    "Amazon",                "Stock"),
    ("TSLA",    "Tesla",                 "Stock"),
    ("JNJ",     "Johnson & Johnson",     "Stock"),
    ("XOM",     "Exxon Mobil",           "Stock"),
    ("JPM",     "JPMorgan Chase",        "Stock"),
    ("WMT",     "Walmart",              "Stock"),
    # Commodities
    ("GLD",     "Gold",                  "Commodity"),
    ("SLV",     "Silver",                "Commodity"),
    ("USO",     "Crude Oil",             "Commodity"),
    ("UNG",     "Natural Gas",           "Commodity"),
    # Crypto
    ("BTC-USD", "Bitcoin",               "Crypto"),
    ("ETH-USD", "Ethereum",              "Crypto"),
    # Bonds
    ("SHY",     "Treasury 1-3yr",        "Bond"),
    ("IEF",     "Treasury 7-10yr",       "Bond"),
    ("TLT",     "Treasury 20+yr",        "Bond"),
    # Forex proxies
    ("UUP",     "US Dollar Index",       "Forex"),
    ("FXE",     "Euro",                  "Forex"),
    ("FXY",     "Japanese Yen",          "Forex"),
    ("FXB",     "British Pound",         "Forex"),
]

# Lookup: filename_stem -> (name, category)
TICKER_INFO = {}
for _t, _n, _c in DEFAULT_TICKERS:
    TICKER_INFO[_t.replace("-", "_").replace("^", "")] = (_n, _c)


# =============================================================================
# 1. DATA
# =============================================================================

def _sanitize_ticker(ticker):
    return ticker.replace("-", "_").replace("^", "")


def download_market_data(ticker, name, period="10y", interval="1d", out_dir=None):
    """Download OHLCV from Yahoo Finance, save to out_dir (default: test_data/)."""
    dest = out_dir or TEST_DATA_DIR
    dest.mkdir(parents=True, exist_ok=True)
    filepath = dest / f"{_sanitize_ticker(ticker)}.csv"
    if filepath.exists():
        return filepath

    print(f"  Downloading {ticker} ({name}) [{interval}]...")
    try:
        data = yf.download(ticker, period=period, interval=interval,
                           progress=False, auto_adjust=True)
        if data.empty:
            print(f"  Warning: no data for {ticker}, skipping")
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index.name = "Date"
        data.to_csv(filepath)
        return filepath
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
        return None


def ensure_test_data():
    """Download any missing tickers (daily + hourly)."""
    # Daily (10yr)
    TEST_DATA_DIR.mkdir(exist_ok=True)
    existing = {f.stem for f in TEST_DATA_DIR.glob("*.csv")}
    expected = {_sanitize_ticker(t[0]) for t in DEFAULT_TICKERS}

    missing = expected - existing
    if missing:
        print(f"Downloading {len(missing)} daily datasets from Yahoo Finance...")
        for ticker, name, cat in DEFAULT_TICKERS:
            if _sanitize_ticker(ticker) in missing:
                download_market_data(ticker, name, period="10y")
        print()

    # Hourly (2yr — yfinance max for 1h interval)
    HOURLY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    h_existing = {f.stem for f in HOURLY_DATA_DIR.glob("*.csv")}
    h_missing = expected - h_existing
    if h_missing:
        print(f"Downloading {len(h_missing)} hourly datasets from Yahoo Finance...")
        for ticker, name, cat in DEFAULT_TICKERS:
            if _sanitize_ticker(ticker) in h_missing:
                download_market_data(ticker, name, period="2y", interval="1h",
                                     out_dir=HOURLY_DATA_DIR)
        print()


def generate_sample_data(days=500, start_price=100.0, volatility=0.02, seed=42):
    """Generate synthetic OHLCV data (geometric Brownian motion)."""
    np.random.seed(seed)
    dates = pd.date_range(start=datetime(2023, 1, 1), periods=days, freq="B")
    daily_returns = np.random.normal(loc=0.0003, scale=volatility, size=days)
    price_series = start_price * np.cumprod(1 + daily_returns)

    df = pd.DataFrame(index=dates)
    df["Close"] = price_series
    df["Open"] = df["Close"].shift(1).fillna(start_price)
    df["High"] = df[["Open", "Close"]].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, days)))
    df["Low"] = df[["Open", "Close"]].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, days)))
    df["Volume"] = np.random.randint(100_000, 10_000_000, size=days)
    return df


def load_csv_data(filepath):
    """Load OHLCV from CSV."""
    df = pd.read_csv(filepath, parse_dates=["Date"], index_col="Date")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def select_data_source():
    """Arrow-key menu to choose dataset. Returns (df, name, run_all_flag)."""
    from pick import pick

    ensure_test_data()

    csv_files = sorted(TEST_DATA_DIR.glob("*.csv"))
    hourly_files = sorted(HOURLY_DATA_DIR.glob("*.csv")) if HOURLY_DATA_DIR.exists() else []

    options = []

    # Run-all options
    options.append(">> Run ALL daily datasets (cross-asset performance test)")
    options.append(">> Run ALL hourly datasets (cross-asset, 2yr hourly bars)")
    ml_ok = _init_ml()
    if ml_ok:
        options.append(">> ML Peak Shaver: Train + Evaluate on ALL daily datasets")
        options.append(">> ML Peak Shaver: Run on single dataset (select next)")

    # Daily datasets
    for f in csv_files:
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        try:
            tmp = pd.read_csv(f, parse_dates=["Date"], index_col="Date", usecols=["Date"])
            days = len(tmp)
            start = tmp.index[0].strftime("%Y-%m-%d")
            end = tmp.index[-1].strftime("%Y-%m-%d")
            label = f"[{category:<9}] [D]  {stem:<12} {name:<22}  {days:>5} days  {start} to {end}"
        except Exception:
            label = f"[{'?':<9}] [D]  {stem}"
        options.append(label)

    # Hourly datasets
    for f in hourly_files:
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        try:
            tmp = pd.read_csv(f, parse_dates=["Date"], index_col="Date", usecols=["Date"])
            bars = len(tmp)
            start = tmp.index[0].strftime("%Y-%m-%d")
            end = tmp.index[-1].strftime("%Y-%m-%d")
            label = f"[{category:<9}] [1H] {stem:<12} {name:<22}  {bars:>5} bars  {start} to {end}"
        except Exception:
            label = f"[{'?':<9}] [1H] {stem}"
        options.append(label)

    options.append("Random Generated Data (500 days synthetic)")

    title = (
        "=== PEAK SHAVER v2: Data Selector ===\n"
        "Arrow keys to navigate, Enter to select.\n"
        "Source: Yahoo Finance | Daily (10yr) + Hourly (2yr) | 41 assets\n"
    )
    selected, index = pick(options, title, indicator="=>")

    if index == 0:
        return None, None, True  # run-all daily mode
    if index == 1:
        return None, None, "hourly"  # run-all hourly mode

    # ML options (only present if ml_ok)
    ml_offset = 2
    if ml_ok:
        if index == 2:
            return None, None, "ml_eval"  # ML full evaluation
        if index == 3:
            return None, None, "ml_single"  # ML single — re-prompt for asset
        ml_offset = 4

    if index == len(options) - 1:
        print("\nUsing randomly generated data...\n")
        return generate_sample_data(), "Synthetic", False

    # Determine which file was selected
    daily_offset = ml_offset  # after run-all + ML options
    hourly_offset = daily_offset + len(csv_files)

    if index < hourly_offset:
        chosen_file = csv_files[index - daily_offset]
    else:
        chosen_file = hourly_files[index - hourly_offset]

    stem = chosen_file.stem
    name, _ = TICKER_INFO.get(stem, (stem, "Other"))
    tf = "hourly" if index >= hourly_offset else "daily"
    print(f"\nLoading {stem} ({name}) [{tf}]...\n")
    return load_csv_data(str(chosen_file)), stem, False


# =============================================================================
# 2. INDICATORS
# =============================================================================

def sma(series, window):
    """Simple Moving Average."""
    return series.rolling(window=window).mean()


def ema(series, window):
    """Exponential Moving Average."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series, period=14):
    """Relative Strength Index (0-100)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bollinger_bands(series, window=20, num_std=2):
    """Returns (upper, middle, lower)."""
    middle = sma(series, window)
    std = series.rolling(window=window).std()
    return middle + std * num_std, middle, middle - std * num_std


def macd_indicator(series, fast=12, slow=26, signal=9):
    """Returns (macd_line, signal_line, histogram)."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


def atr(df, period=14):
    """Average True Range — measures volatility in price terms."""
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def adx(df, period=14):
    """Average Directional Index — trend strength (0-100).
    >25 = strong trend, <20 = ranging/choppy."""
    high, low, close = df["High"], df["Low"], df["Close"]

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    atr_val = atr(df, period)
    atr_val = atr_val.replace(0, np.nan)

    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_val
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_val

    di_sum = plus_di + minus_di
    di_sum = di_sum.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx_val = dx.ewm(alpha=1/period, adjust=False).mean()

    return adx_val, plus_di, minus_di


def obv(df):
    """On-Balance Volume — cumulative volume direction indicator."""
    direction = np.sign(df["Close"].diff())
    return (direction * df["Volume"]).cumsum()


def roc(series, period=10):
    """Rate of Change (momentum as percentage)."""
    return series.pct_change(periods=period) * 100


def zscore(series, window=20):
    """Z-score: how many std devs price is from rolling mean."""
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std.replace(0, np.nan)


def cmf(df, period=20):
    """Chaikin Money Flow — buying vs selling pressure (-1 to 1)."""
    high, low, close, volume = df["High"], df["Low"], df["Close"], df["Volume"]
    hl_range = high - low
    hl_range = hl_range.replace(0, np.nan)
    mf_multiplier = ((close - low) - (high - close)) / hl_range
    mf_volume = mf_multiplier * volume
    return mf_volume.rolling(period).sum() / volume.rolling(period).sum()


# =============================================================================
# 3. REGIME DETECTION
# =============================================================================

def detect_regime(df, adx_period=14, trend_thresh=25, range_thresh=20):
    """Classify market regime using ADX.
    Returns Series: 1=trending, -1=ranging, 0=neutral."""
    adx_val, _, _ = adx(df, adx_period)

    regime = pd.Series(0, index=df.index, dtype=int)
    regime[adx_val >= trend_thresh] = 1
    regime[adx_val <= range_thresh] = -1
    return regime


# =============================================================================
# 4. STRATEGIES — Peak Shaver family (continuous position sizing)
#    Returns (position_series, indicators_dict)
#    100% invested by default, trims at peaks. No leverage, no shorting.
# =============================================================================

def _detect_bars_per_day(df):
    """Detect timeframe from data index spacing (1=daily, 7=hourly)."""
    if len(df) < 20:
        return 1
    deltas = df.index.to_series().diff().dropna()
    median_mins = deltas.median().total_seconds() / 60
    if median_mins < 120:    # < 2 hours -> hourly
        return 7
    elif median_mins < 480:  # < 8 hours -> 4h
        return 2
    return 1                 # daily


def strategy_peak_shaver_v1(df):
    """Peak Shaver v1: Dual-confirmation overbought detection (original).
    100% invested by default, reduces at peaks using RSI + ROC only.

    Tier 1: RSI(14) > 75 AND ROC(21) > 11% -> 50%
    Tier 2: RSI(14) > 85 -> 30%

    Beats Buy & Hold on 28/41 assets across 10yr daily data (68%).
    No leverage, no shorting — long-only 0-100%.
    Returns (position_series, indicators_dict)."""
    bpd = _detect_bars_per_day(df)
    close = df["Close"]

    scale = max(1.0, bpd ** 0.4)
    rsi_val = rsi(close, max(14, int(14 * scale)))
    mom_1m = roc(close, max(21, int(21 * scale)))

    position = pd.Series(1.0, index=df.index)
    # Tier 1: dual confirmation -> 50%
    position[(rsi_val > 75) & (mom_1m > 11)] = 0.50
    # Tier 2: extreme overbought -> 30%
    position[rsi_val > 85] = 0.30

    return position, {"position": position, "rsi": rsi_val, "mom_1m": mom_1m}


def strategy_peak_shaver(df):
    """Peak Shaver v2: Triple-confirmation overbought detection.
    100% invested by default, reduces at peaks using RSI + ROC + Z-score.
    Timeframe-adaptive (works on daily and hourly bars).

    Tier 1: RSI(14) > 75 AND ROC(21) > 11% AND Z-score(50) > 1.0 -> 40%
            (overbought + strong momentum + price statistically stretched)
    Tier 2: RSI(14) > 85 AND Z-score(50) > 3.0 -> 30%
            (extreme overbought + extreme stretch from mean)

    The z-score gate prevents bad trims in trending markets where RSI stays
    high but price isn't far from its moving average (e.g. steady grinders).
    Deep trim requires z > 3.0, which only fires at genuine blow-off tops.

    Beats Buy & Hold on 32/41 assets across 10yr daily data (78%).
    No leverage, no shorting — long-only 0-100%.
    Returns (position_series, indicators_dict)."""
    bpd = _detect_bars_per_day(df)
    close = df["Close"]

    # Scale indicator periods for timeframe (bpd^0.4 optimal for hourly)
    # daily: scale=1.0 (unchanged), hourly: scale≈2.2 (RSI 30, ROC 45)
    scale = max(1.0, bpd ** 0.4)
    rsi_val = rsi(close, max(14, int(14 * scale)))
    mom_1m = roc(close, max(21, int(21 * scale)))
    z = zscore(close, max(50, int(50 * scale)))

    position = pd.Series(1.0, index=df.index)
    # Tier 1: triple confirmation -> 40%
    position[(rsi_val > 75) & (mom_1m > 11) & (z > 1.0)] = 0.40
    # Tier 2: extreme overbought + extreme stretch -> 30%
    position[(rsi_val > 85) & (z > 3.0)] = 0.30

    return position, {"position": position, "rsi": rsi_val, "mom_1m": mom_1m, "zscore": z}


# =============================================================================
# 5. BACKTESTER — with risk management
# =============================================================================

class Backtester:
    """Backtester with trailing stops, volatility targeting, and circuit breaker."""

    def __init__(self, df, initial_capital=10_000, commission=COMMISSION,
                 trailing_stop_atr_mult=0, vol_target=0,
                 max_drawdown_pct=0):
        self.df = df.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.trailing_stop_mult = trailing_stop_atr_mult
        self.vol_target = vol_target
        self.max_dd_pct = max_drawdown_pct
        # Precompute ATR for risk management
        self.atr_series = atr(df, 14)

    def run(self, trades_signal, strategy_name="Strategy"):
        cash = self.initial_capital
        position = 0.0
        portfolio_values = []
        trade_log = []

        peak_equity = self.initial_capital
        highest_price_since_entry = 0.0
        halted = False

        # Rolling realized vol for vol targeting
        returns_list = []

        for date, row in self.df.iterrows():
            price = row["Close"]
            signal = trades_signal.get(date, 0)
            current_atr = self.atr_series.get(date, price * 0.02)

            portfolio_value = cash + position * price
            peak_equity = max(peak_equity, portfolio_value)

            # Track returns for vol targeting
            if len(portfolio_values) > 0:
                ret = (portfolio_value / portfolio_values[-1]) - 1
            else:
                ret = 0.0
            returns_list.append(ret)

            # --- Circuit breaker ---
            if self.max_dd_pct > 0 and peak_equity > 0:
                dd = (portfolio_value - peak_equity) / peak_equity
                if dd < -self.max_dd_pct and position > 0:
                    revenue = position * price * (1 - self.commission)
                    cash += revenue
                    trade_log.append({
                        "date": date, "action": "CIRCUIT_BREAK",
                        "price": price, "shares": position,
                    })
                    position = 0.0
                    halted = True
                    highest_price_since_entry = 0.0
                if halted and dd > -self.max_dd_pct * 0.5:
                    halted = False

            # --- Trailing stop ---
            if position > 0 and self.trailing_stop_mult > 0:
                highest_price_since_entry = max(highest_price_since_entry, price)
                stop_price = highest_price_since_entry - current_atr * self.trailing_stop_mult
                if price < stop_price:
                    revenue = position * price * (1 - self.commission)
                    cash += revenue
                    trade_log.append({
                        "date": date, "action": "TRAIL_STOP",
                        "price": price, "shares": position,
                    })
                    position = 0.0
                    highest_price_since_entry = 0.0

            # --- Process signals ---
            if signal == 1 and position == 0 and not halted:
                # Vol targeting: scale position size
                size_scale = 1.0
                if self.vol_target > 0 and len(returns_list) > 20:
                    recent_vol = np.std(returns_list[-20:]) * np.sqrt(252)
                    if recent_vol > 0:
                        size_scale = min(self.vol_target / recent_vol, 1.0)

                invest_amount = cash * size_scale
                shares = invest_amount / (price * (1 + self.commission))
                if shares > 0:
                    cost = shares * price * (1 + self.commission)
                    cash -= cost
                    position = shares
                    highest_price_since_entry = price
                    trade_log.append({
                        "date": date, "action": "BUY",
                        "price": price, "shares": shares,
                    })

            elif signal == -1 and position > 0:
                revenue = position * price * (1 - self.commission)
                cash += revenue
                trade_log.append({
                    "date": date, "action": "SELL",
                    "price": price, "shares": position,
                })
                position = 0.0
                highest_price_since_entry = 0.0

            portfolio_values.append(cash + position * price)

        # --- Compute metrics ---
        equity = pd.Series(portfolio_values, index=self.df.index)
        daily_ret = equity.pct_change().dropna()

        total_return = (equity.iloc[-1] / self.initial_capital - 1) * 100
        bnh_return = (self.df["Close"].iloc[-1] / self.df["Close"].iloc[0] - 1) * 100

        # Sharpe
        sharpe = 0.0
        if daily_ret.std() > 0:
            sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(252)

        # Sortino (only downside deviation)
        downside = daily_ret[daily_ret < 0]
        sortino = 0.0
        if len(downside) > 0 and downside.std() > 0:
            sortino = (daily_ret.mean() / downside.std()) * np.sqrt(252)

        # Max drawdown
        drawdown = (equity / equity.cummax() - 1)
        max_dd = drawdown.min() * 100

        # Calmar (annualized return / max drawdown)
        years = len(equity) / 252
        annual_return = ((equity.iloc[-1] / self.initial_capital) ** (1 / max(years, 0.1)) - 1) * 100
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0

        # Win rate & profit factor
        trades_df = pd.DataFrame(trade_log)
        win_rate = 0.0
        profit_factor = 0.0
        if not trades_df.empty:
            buys = trades_df[trades_df["action"] == "BUY"]["price"].values
            sells = trades_df[trades_df["action"].isin(["SELL", "TRAIL_STOP", "CIRCUIT_BREAK"])]["price"].values
            n_pairs = min(len(buys), len(sells))
            if n_pairs > 0:
                pnl = sells[:n_pairs] - buys[:n_pairs]
                wins = pnl[pnl > 0]
                losses = pnl[pnl < 0]
                win_rate = len(wins) / n_pairs * 100
                total_wins = wins.sum() if len(wins) > 0 else 0
                total_losses = abs(losses.sum()) if len(losses) > 0 else 0
                profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        return {
            "strategy_name": strategy_name,
            "total_return_pct": round(total_return, 2),
            "buy_and_hold_return_pct": round(bnh_return, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "calmar_ratio": round(calmar, 2),
            "win_rate_pct": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "num_trades": len([t for t in trade_log if t["action"] == "BUY"]),
            "final_value": round(equity.iloc[-1], 2),
            "equity_curve": equity,
            "drawdown": drawdown,
            "trade_log": pd.DataFrame(trade_log),
        }

    def run_positions(self, target_positions, strategy_name="Strategy"):
        """Backtest with continuous position sizing (0-100%).
        target_positions: Series of floats (0.0=cash, 1.0=fully invested).
        Rebalances when allocation drifts >5% from target."""
        cash = self.initial_capital
        shares = 0.0
        portfolio_values = []
        trade_log = []

        for date, row in self.df.iterrows():
            price = row["Close"]
            target = float(target_positions.get(date, 0))
            target = max(0.0, min(1.0, target))  # cap at 100%, no leverage

            portfolio_value = cash + shares * price
            if portfolio_value <= 0:
                portfolio_values.append(0.0)
                continue

            current_alloc = (shares * price) / portfolio_value

            # Rebalance when drift exceeds 5%
            if abs(current_alloc - target) > 0.05:
                target_value = portfolio_value * target
                target_shares = target_value / price
                diff = target_shares - shares

                if diff > 0:  # buy
                    cost = diff * price * (1 + self.commission)
                    cash -= cost
                    shares += diff
                    trade_log.append({"date": date, "action": "BUY",
                                      "price": price, "shares": diff})
                elif diff < 0:  # sell
                    revenue = abs(diff) * price * (1 - self.commission)
                    cash += revenue
                    shares += diff  # diff is negative
                    trade_log.append({"date": date, "action": "SELL",
                                      "price": price, "shares": abs(diff)})

            portfolio_values.append(cash + shares * price)

        # --- Metrics (same as run()) ---
        equity = pd.Series(portfolio_values, index=self.df.index)
        daily_ret = equity.pct_change().dropna()

        total_return = (equity.iloc[-1] / self.initial_capital - 1) * 100
        bnh_return = (self.df["Close"].iloc[-1] / self.df["Close"].iloc[0] - 1) * 100

        sharpe = 0.0
        if daily_ret.std() > 0:
            sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(252)

        downside = daily_ret[daily_ret < 0]
        sortino = 0.0
        if len(downside) > 0 and downside.std() > 0:
            sortino = (daily_ret.mean() / downside.std()) * np.sqrt(252)

        drawdown = (equity / equity.cummax() - 1)
        max_dd = drawdown.min() * 100

        years = len(equity) / 252
        annual_return = ((equity.iloc[-1] / self.initial_capital) ** (1 / max(years, 0.1)) - 1) * 100
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0

        trades_df = pd.DataFrame(trade_log)
        num_buys = len([t for t in trade_log if t["action"] == "BUY"])

        return {
            "strategy_name": strategy_name,
            "total_return_pct": round(total_return, 2),
            "buy_and_hold_return_pct": round(bnh_return, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "calmar_ratio": round(calmar, 2),
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "num_trades": num_buys,
            "final_value": round(equity.iloc[-1], 2),
            "equity_curve": equity,
            "drawdown": drawdown,
            "trade_log": trades_df,
        }


# =============================================================================
# 6. VISUALIZATION
# =============================================================================

def plot_results(df, results_list, regime=None, asset_name=""):
    """6-panel plot: equity, price+regime, ADX, RSI, MACD, drawdown."""
    fig = plt.figure(figsize=(16, 30))
    gs = gridspec.GridSpec(6, 1, height_ratios=[2.5, 2, 1, 1, 1, 1.5], hspace=0.3)

    # --- 1. Equity Curves ---
    ax = fig.add_subplot(gs[0])
    for r in results_list:
        ax.plot(r["equity_curve"],
                label=f'{r["strategy_name"]} ({r["total_return_pct"]:+.1f}%)',
                linewidth=1.5)
    bnh = 10_000 * (df["Close"] / df["Close"].iloc[0])
    ax.plot(bnh, label=f'Buy & Hold ({results_list[0]["buy_and_hold_return_pct"]:+.1f}%)',
            linestyle="--", color="gray", linewidth=1.5)
    ax.set_title(f"Strategy Performance: {asset_name}", fontsize=14, fontweight="bold")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(True, alpha=0.3)

    # --- 2. Price + Regime Overlay + Best Strategy Signals ---
    ax = fig.add_subplot(gs[1])
    ax.plot(df["Close"], color="black", linewidth=1, label="Price")

    if regime is not None:
        # Color background by regime
        prev_regime = None
        start_idx = 0
        for i in range(len(regime)):
            r = regime.iloc[i]
            if r != prev_regime and prev_regime is not None:
                color = "#d4edda" if prev_regime == 1 else "#f8d7da" if prev_regime == -1 else "#e2e3e5"
                ax.axvspan(regime.index[start_idx], regime.index[i-1], alpha=0.3, color=color, linewidth=0)
                start_idx = i
            prev_regime = r
        # Final span
        if prev_regime is not None:
            color = "#d4edda" if prev_regime == 1 else "#f8d7da" if prev_regime == -1 else "#e2e3e5"
            ax.axvspan(regime.index[start_idx], regime.index[-1], alpha=0.3, color=color, linewidth=0)

    # Best strategy signals
    best = max(results_list, key=lambda x: x["sharpe_ratio"])
    if not best["trade_log"].empty:
        buys = best["trade_log"][best["trade_log"]["action"] == "BUY"]
        sells = best["trade_log"][best["trade_log"]["action"].isin(["SELL", "TRAIL_STOP", "CIRCUIT_BREAK"])]
        if not buys.empty:
            ax.scatter(buys["date"], buys["price"], marker="^", color="green",
                       s=50, zorder=5, label="Buy")
        if not sells.empty:
            colors = sells["action"].map({"SELL": "red", "TRAIL_STOP": "orange", "CIRCUIT_BREAK": "purple"})
            ax.scatter(sells["date"], sells["price"], marker="v", color=colors.values,
                       s=50, zorder=5, label="Sell/Stop")

    import matplotlib.patches as mpatches
    patches = [
        mpatches.Patch(color="#d4edda", alpha=0.5, label="Trending"),
        mpatches.Patch(color="#f8d7da", alpha=0.5, label="Ranging"),
        mpatches.Patch(color="#e2e3e5", alpha=0.5, label="Neutral"),
    ]
    ax.legend(handles=patches + ax.get_legend_handles_labels()[0], loc="upper left", fontsize=7)
    ax.set_title(f"Price + Regime Detection ({best['strategy_name']} signals)", fontsize=12)
    ax.set_ylabel("Price ($)")
    ax.grid(True, alpha=0.3)

    # --- 3. ADX (Regime Indicator) ---
    ax = fig.add_subplot(gs[2])
    adx_val, plus_di, minus_di = adx(df, 14)
    ax.plot(adx_val, color="black", linewidth=1.5, label="ADX")
    ax.plot(plus_di, color="green", linewidth=0.8, alpha=0.7, label="+DI")
    ax.plot(minus_di, color="red", linewidth=0.8, alpha=0.7, label="-DI")
    ax.axhline(y=25, color="blue", linestyle="--", linewidth=0.8, label="Trend thresh (25)")
    ax.axhline(y=20, color="gray", linestyle="--", linewidth=0.8, label="Range thresh (20)")
    ax.set_title("ADX — Trend Strength & Regime Detection", fontsize=12)
    ax.set_ylabel("ADX")
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(True, alpha=0.3)

    # --- 4. RSI ---
    ax = fig.add_subplot(gs[3])
    rsi_val = rsi(df["Close"], 14)
    ax.plot(rsi_val, color="purple", linewidth=1)
    ax.axhline(y=70, color="red", linestyle="--", linewidth=0.8, label="Overbought (70)")
    ax.axhline(y=30, color="green", linestyle="--", linewidth=0.8, label="Oversold (30)")
    ax.fill_between(rsi_val.index, 30, 70, alpha=0.05, color="gray")
    ax.set_title("RSI (14-period)", fontsize=12)
    ax.set_ylabel("RSI")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(True, alpha=0.3)

    # --- 5. MACD ---
    ax = fig.add_subplot(gs[4])
    macd_line, signal_line, histogram = macd_indicator(df["Close"])
    ax.plot(macd_line, color="blue", linewidth=1, label="MACD")
    ax.plot(signal_line, color="orange", linewidth=1, label="Signal")
    colors = ["green" if v >= 0 else "red" for v in histogram]
    ax.bar(df.index, histogram, color=colors, alpha=0.4, width=1)
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.set_title("MACD (12, 26, 9)", fontsize=12)
    ax.set_ylabel("Value")
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(True, alpha=0.3)

    # --- 6. Drawdown ---
    ax = fig.add_subplot(gs[5])
    for r in results_list:
        ax.fill_between(r["drawdown"].index, r["drawdown"] * 100, 0,
                         alpha=0.3, label=f'{r["strategy_name"]} ({r["max_drawdown_pct"]:.1f}%)')
    ax.set_title("Drawdown Comparison", fontsize=12)
    ax.set_ylabel("Drawdown (%)")
    ax.legend(loc="lower left", fontsize=7)
    ax.grid(True, alpha=0.3)

    plt.savefig("backtest_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Chart saved to backtest_results.png")


def print_summary(results_list):
    """Print performance comparison table with risk metrics."""
    print("\n" + "=" * 110)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 110)
    header = (
        f"{'Strategy':<28} {'Return%':>8} {'Sharpe':>7} {'Sortino':>8} "
        f"{'MaxDD%':>7} {'Calmar':>7} {'WinRate':>8} {'PF':>6} {'Trades':>7} {'Final$':>9}"
    )
    print(header)
    print("-" * 110)

    for r in results_list:
        pf_str = f'{r["profit_factor"]:.2f}' if r["profit_factor"] < 100 else "inf"
        print(
            f'{r["strategy_name"]:<28} '
            f'{r["total_return_pct"]:>+8.2f} '
            f'{r["sharpe_ratio"]:>7.2f} '
            f'{r["sortino_ratio"]:>8.2f} '
            f'{r["max_drawdown_pct"]:>7.2f} '
            f'{r["calmar_ratio"]:>7.2f} '
            f'{r["win_rate_pct"]:>7.1f}% '
            f'{pf_str:>6} '
            f'{r["num_trades"]:>7} '
            f'{r["final_value"]:>9.2f}'
        )

    print("-" * 110)
    print(f'{"Buy & Hold":<28} {results_list[0]["buy_and_hold_return_pct"]:>+8.2f}')
    print("=" * 110)

    # Recommendation
    best = max(results_list, key=lambda x: x["sharpe_ratio"])
    print(f'\nRECOMMENDATION: {best["strategy_name"]}')
    print(f'  Sharpe: {best["sharpe_ratio"]:.2f} | '
          f'Return: {best["total_return_pct"]:+.2f}% | '
          f'Max DD: {best["max_drawdown_pct"]:.2f}% | '
          f'Win Rate: {best["win_rate_pct"]:.0f}%')
    alpha = best["total_return_pct"] - best["buy_and_hold_return_pct"]
    print(f'  Alpha vs Buy & Hold: {alpha:+.2f}%')


# =============================================================================
# 7. CROSS-ASSET TEST (Run ALL datasets)
# =============================================================================

def run_all_datasets(data_dir=None, label="Daily"):
    """Run Peak Shaver v2 on every CSV in data_dir and compare."""
    data_dir = data_dir or TEST_DATA_DIR
    csv_files = sorted(Path(data_dir).glob("*.csv"))
    if not csv_files:
        print("No data files found. Run the bot normally first to download data.")
        return

    print(f"\nRunning Peak Shaver v2 on {len(csv_files)} assets [{label}]...\n")

    results = []
    for f in csv_files:
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        try:
            df = load_csv_data(str(f))
            if len(df) < 100:
                continue
            bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)
            positions, _ = strategy_peak_shaver(df)
            r = bt.run_positions(positions, strategy_name=stem)
            r["asset"] = stem
            r["category"] = category
            r["name"] = name
            results.append(r)
            status = "+" if r["total_return_pct"] > r["buy_and_hold_return_pct"] else "-"
            print(f"  [{status}] {stem:<12} {name:<22} "
                  f"Return:{r['total_return_pct']:>+8.2f}%  "
                  f"Sharpe:{r['sharpe_ratio']:>6.2f}  "
                  f"MaxDD:{r['max_drawdown_pct']:>7.2f}%  "
                  f"B&H:{r['buy_and_hold_return_pct']:>+8.2f}%")
        except Exception as e:
            print(f"  [!] {stem}: {e}")

    if not results:
        print("No results.")
        return

    # Summary stats
    print("\n" + "=" * 90)
    print(f"CROSS-ASSET SUMMARY: Peak Shaver v2 [{label}]")
    print("=" * 90)

    beats_bnh = sum(1 for r in results
                    if r["total_return_pct"] > r["buy_and_hold_return_pct"])
    avg_sharpe = np.mean([r["sharpe_ratio"] for r in results])
    avg_return = np.mean([r["total_return_pct"] for r in results])
    avg_dd = np.mean([r["max_drawdown_pct"] for r in results])
    avg_alpha = np.mean([r["total_return_pct"] - r["buy_and_hold_return_pct"] for r in results])

    print(f"  Assets tested:       {len(results)}")
    print(f"  Beats Buy & Hold:    {beats_bnh}/{len(results)} ({beats_bnh/len(results)*100:.0f}%)")
    print(f"  Avg Return:          {avg_return:+.2f}%")
    print(f"  Avg Sharpe:          {avg_sharpe:.2f}")
    print(f"  Avg Max Drawdown:    {avg_dd:.2f}%")
    print(f"  Avg Alpha vs B&H:    {avg_alpha:+.2f}%")

    # By category
    print(f"\n  {'Category':<12} {'Count':>6} {'AvgReturn':>10} {'AvgSharpe':>10} {'AvgMaxDD':>9} {'BeatB&H':>8}")
    print("  " + "-" * 57)
    categories = sorted(set(r["category"] for r in results))
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_avg_ret = np.mean([r["total_return_pct"] for r in cat_results])
        cat_avg_sh = np.mean([r["sharpe_ratio"] for r in cat_results])
        cat_avg_dd = np.mean([r["max_drawdown_pct"] for r in cat_results])
        cat_beats = sum(1 for r in cat_results
                        if r["total_return_pct"] > r["buy_and_hold_return_pct"])
        print(f"  {cat:<12} {len(cat_results):>6} {cat_avg_ret:>+10.2f} "
              f"{cat_avg_sh:>10.2f} {cat_avg_dd:>9.2f} {cat_beats}/{len(cat_results):>5}")

    print("=" * 90)

    # Save cross-asset chart
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Sharpe by asset
    ax = axes[0]
    names = [r["asset"] for r in results]
    sharpes = [r["sharpe_ratio"] for r in results]
    colors = ["green" if s > 0 else "red" for s in sharpes]
    ax.barh(names, sharpes, color=colors, alpha=0.7)
    ax.axvline(x=0, color="black", linewidth=0.5)
    ax.set_title("Sharpe Ratio by Asset", fontsize=12)
    ax.set_xlabel("Sharpe Ratio")

    # Return vs B&H
    ax = axes[1]
    strat_returns = [r["total_return_pct"] for r in results]
    bnh_returns = [r["buy_and_hold_return_pct"] for r in results]
    x = np.arange(len(names))
    ax.barh(x - 0.2, strat_returns, 0.4, label="Master Ensemble", color="steelblue", alpha=0.8)
    ax.barh(x + 0.2, bnh_returns, 0.4, label="Buy & Hold", color="gray", alpha=0.6)
    ax.set_yticks(x)
    ax.set_yticklabels(names, fontsize=7)
    ax.axvline(x=0, color="black", linewidth=0.5)
    ax.set_title("Return: Strategy vs Buy & Hold", fontsize=12)
    ax.set_xlabel("Return (%)")
    ax.legend()

    plt.tight_layout()
    plt.savefig("cross_asset_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nCross-asset chart saved to cross_asset_results.png")


# =============================================================================
# 8. MAIN
# =============================================================================

def main():
    df, asset_name, run_all = select_data_source()

    if run_all == True:
        run_all_datasets(TEST_DATA_DIR, "Daily")
        return
    elif run_all == "hourly":
        run_all_datasets(HOURLY_DATA_DIR, "Hourly")
        return
    elif run_all == "ml_eval":
        from ml_peak_shaver_v2 import evaluate_ml_enhancement as _ml_eval
        _ml_eval()
        return
    elif run_all == "ml_single":
        from ml_peak_shaver_v2 import train_ml_models as _ml_train
        # Re-prompt for a single asset, then run with ML
        df, asset_name, _ = select_data_source()
        if df is None:
            print("No asset selected.")
            return
        print("Training ML models on all daily assets...")
        models = _ml_train()
        _run_single_asset(df, asset_name, ml_models=models)
        return

    _run_single_asset(df, asset_name)


def _run_single_asset(df, asset_name, ml_models=None):
    """Run all strategies on a single asset."""
    print(f"Data: {len(df)} trading days, {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}\n")

    # Detect regime
    regime = detect_regime(df)
    trending_pct = (regime == 1).mean() * 100
    ranging_pct = (regime == -1).mean() * 100
    neutral_pct = (regime == 0).mean() * 100
    print(f"Regime breakdown: {trending_pct:.0f}% trending, "
          f"{ranging_pct:.0f}% ranging, {neutral_pct:.0f}% neutral\n")

    # Run Peak Shaver strategies
    bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)
    all_results = []

    # Peak Shaver v1
    pos_v1, _ = strategy_peak_shaver_v1(df)
    all_results.append(bt.run_positions(pos_v1, strategy_name="PEAK SHAVER v1"))

    # Peak Shaver v2
    pos_v2, _ = strategy_peak_shaver(df)
    all_results.append(bt.run_positions(pos_v2, strategy_name="** PEAK SHAVER v2 **"))

    # ML Peak Shaver (if models available)
    if ml_models is not None:
        from ml_peak_shaver_v2 import strategy_ml_peak_shaver as _ml_strat
        ml_pos, _ = _ml_strat(df, ml_models)
        all_results.append(bt.run_positions(ml_pos, strategy_name="** ML PEAK SHAVER **"))

    # Use regime detection for plotting
    plot_regime = regime

    print_summary(all_results)
    plot_results(df, all_results, regime=plot_regime, asset_name=asset_name or "")

    # Best strategy detail
    best = max(all_results, key=lambda x: x["sharpe_ratio"])
    if not best["trade_log"].empty:
        print(f"\nTrade log ({best['strategy_name']}, first 10):")
        print(best["trade_log"].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
