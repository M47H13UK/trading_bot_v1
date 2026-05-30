"""
Local backtester — mirrors test.py eval logic exactly.
Tests strategy on multiple tickers, compares vs buy-and-hold.
"""

import pandas as pd
import numpy as np
import os
import time
import importlib.util
import yfinance as yf

TRADING_DAYS = 252
TRANSACTION_COST = 0.0005


def download_ticker(ticker, start="2015-01-01", end="2026-02-21"):
    """Download single ticker OHLCV, save to data/."""
    os.makedirs("data", exist_ok=True)
    path = f"data/{ticker.lower()}.csv"
    if os.path.exists(path):
        return path
    df = yf.download(ticker, start=start, end=end)
    # Flatten multi-level columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.to_csv(path)
    print(f"  Downloaded {ticker} -> {path} ({len(df)} bars)")
    return path


def load_data(filepath):
    """Load OHLCV data, handling both multi-ticker and single-ticker CSVs."""
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"

    # Check for multi-ticker format (columns like Close_SPY, Open_QQQ)
    if any("_" in col for col in df.columns):
        # Try multi-ticker parse: split Col_Ticker
        new_cols = []
        is_multi = True
        for col in df.columns:
            parts = col.rsplit("_", 1)
            if len(parts) == 2:
                new_cols.append((parts[1], parts[0]))  # (ticker, ohlcv)
            else:
                is_multi = False
                break
        if is_multi:
            df.columns = pd.MultiIndex.from_tuples(new_cols, names=["Ticker", "OHLCV"])
            tickers = list(df.columns.get_level_values(0).unique())
            ticker = tickers[0]
            df = df[ticker].copy()
            df.columns.name = None

    # Handle yfinance's multi-row header format
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        # Try re-reading with multi-level header
        probe = pd.read_csv(filepath, nrows=5, header=None)
        if probe.iloc[0, 0] == "Price":
            df = pd.read_csv(filepath, header=[0, 1], index_col=0, parse_dates=True)
            df.columns = df.columns.get_level_values(0)
            df.index.name = "Date"

    return df.ffill().dropna()


def backtest(data, signals):
    returns = data["Close"].pct_change()
    shifted = signals.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    returns, shifted = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = shifted.diff().abs().fillna(0) * TRANSACTION_COST
    return shifted * returns - costs


def calc_metrics(returns):
    vol = np.std(returns)
    total = (1 + returns).prod() - 1
    annual = (1 + total) ** (TRADING_DAYS / len(returns)) - 1
    equity = (1 + returns).cumprod()
    dd = ((equity - equity.cummax()) / equity.cummax()).min()
    sharpe = (np.mean(returns) / vol) * np.sqrt(TRADING_DAYS) if vol > 1e-8 else 0.0
    calmar = annual / abs(dd) if dd < 0 else 0.0
    return {
        "total_return": total, "annual_return": annual, "sharpe": sharpe,
        "max_drawdown": dd, "calmar": calmar, "win_rate": (returns > 0).mean(),
    }


def bh_metrics(data):
    """Buy-and-hold benchmark metrics."""
    returns = data["Close"].pct_change().dropna()
    return calc_metrics(returns)


def count_trades(signals):
    """Count position changes (each costs transaction fees)."""
    return int(signals.diff().abs().fillna(0).gt(0).sum())


if __name__ == "__main__":
    # Download test tickers
    print("Downloading data...")
    tickers = ["SPY", "QQQ", "XOM"]
    paths = {t: download_ticker(t) for t in tickers}

    # Load strategy
    spec = importlib.util.spec_from_file_location("strategy", "submissions/strategy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    print(f"\n{'Ticker':<8} {'Sharpe':>8} {'Return':>10} {'MaxDD':>8} {'Trades':>8} | {'BH Sharpe':>10} {'BH Return':>10}")
    print("-" * 78)

    for ticker, path in paths.items():
        data = load_data(path)

        t0 = time.perf_counter()
        signals = mod.generate_signals(data)
        elapsed = time.perf_counter() - t0

        # Validate — accept any finite float
        assert signals.index.equals(data.index), f"{ticker}: index mismatch"
        assert not signals.isna().any(), f"{ticker}: NaN in signals"
        assert np.isfinite(signals).all(), f"{ticker}: non-finite signal values"

        signals = signals.astype(float)
        strat_returns = backtest(data, signals)
        sm = calc_metrics(strat_returns)
        bm = bh_metrics(data)
        trades = count_trades(signals)

        print(f"{ticker:<8} {sm['sharpe']:>8.2f} {sm['total_return']:>9.1%} {sm['max_drawdown']:>8.1%} {trades:>8} | {bm['sharpe']:>10.2f} {bm['total_return']:>9.1%}")

    print(f"\nSignal time: {elapsed:.4f}s (limit: 10s)")
    print(f"Signal range: [{signals.min():.2f}, {signals.max():.2f}]")
