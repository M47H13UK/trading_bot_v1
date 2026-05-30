"""
Full backtest suite — runs strategy on all 41 assets (daily + hourly),
outputs markdown results to test_data/BACKTEST_RESULTS/.
Uses exact same eval logic as test.py: next-day execution, 5bps costs.
"""

import pandas as pd
import numpy as np
import os
import sys
import time
import importlib.util

TRADING_DAYS = 252
TRANSACTION_COST = 0.0005
DAILY_DIR = "../test_data/daily"
HOURLY_DIR = "../test_data/hourly"
OUT_DIR = "../test_data/BACKTEST_RESULTS"

# Load strategy
spec = importlib.util.spec_from_file_location("strategy", "submissions/strategy.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def load_data(filepath):
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns in {filepath}: {df.columns.tolist()}")
    return df.ffill().dropna()


def backtest(data, signals):
    returns = data["Close"].pct_change()
    shifted = signals.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    r, pos = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = pos.diff().abs().fillna(0) * TRANSACTION_COST
    return pos * r - costs


def calc_metrics(returns, bars_per_year=252):
    vol = np.std(returns)
    total = (1 + returns).prod() - 1
    annual = (1 + total) ** (bars_per_year / len(returns)) - 1
    equity = (1 + returns).cumprod()
    dd = ((equity - equity.cummax()) / equity.cummax()).min()
    sharpe = (np.mean(returns) / vol) * np.sqrt(bars_per_year) if vol > 1e-8 else 0.0
    calmar = annual / abs(dd) if dd < 0 else 0.0
    win_rate = (returns > 0).mean()
    return {
        "total_return": total,
        "annual_return": annual,
        "sharpe": sharpe,
        "max_drawdown": dd,
        "calmar": calmar,
        "win_rate": win_rate,
    }


def count_trades(signals):
    return int(signals.diff().abs().fillna(0).gt(0).sum())


# Asset categories
CATEGORIES = {
    "Index": ["DIA", "IWM", "QQQ", "SPY"],
    "Stock": ["AAPL", "AMZN", "JNJ", "JPM", "MSFT", "TSLA", "WMT", "XOM"],
    "Sector": ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"],
    "Country": ["EEM", "EFA", "EWG", "EWJ", "EWU", "FXI"],
    "Fixed Income": ["IEF", "SHY", "TLT"],
    "Commodity": ["GLD", "SLV", "UNG", "USO"],
    "Currency": ["FXB", "FXE", "FXY", "UUP"],
    "Crypto": ["BTC_USD", "ETH_USD"],
}

ASSET_NAMES = {
    "DIA": "Dow Jones ETF", "IWM": "Russell 2000 ETF", "QQQ": "Nasdaq 100 ETF", "SPY": "S&P 500 ETF",
    "AAPL": "Apple", "AMZN": "Amazon", "JNJ": "Johnson & Johnson", "JPM": "JPMorgan",
    "MSFT": "Microsoft", "TSLA": "Tesla", "WMT": "Walmart", "XOM": "ExxonMobil",
    "XLB": "Materials", "XLE": "Energy", "XLF": "Financials", "XLI": "Industrials",
    "XLK": "Technology", "XLP": "Consumer Staples", "XLRE": "Real Estate",
    "XLU": "Utilities", "XLV": "Healthcare", "XLY": "Consumer Disc",
    "EEM": "Emerging Mkts", "EFA": "EAFE", "EWG": "Germany", "EWJ": "Japan",
    "EWU": "UK", "FXI": "China",
    "IEF": "7-10Y Treasury", "SHY": "1-3Y Treasury", "TLT": "20+Y Treasury",
    "GLD": "Gold", "SLV": "Silver", "UNG": "Nat Gas", "USO": "Oil",
    "FXB": "British Pound", "FXE": "Euro", "FXY": "Yen", "UUP": "US Dollar",
    "BTC_USD": "Bitcoin", "ETH_USD": "Ethereum",
}


def run_suite(data_dir, bars_per_year, label):
    """Run strategy on all assets in a directory, return results dict."""
    files = sorted([f for f in os.listdir(data_dir) if f.endswith(".csv")])
    results = {}

    for f in files:
        ticker = f.replace(".csv", "")
        try:
            data = load_data(os.path.join(data_dir, f))
        except Exception as e:
            print(f"  SKIP {ticker}: {e}")
            continue

        t0 = time.perf_counter()
        signals = mod.generate_signals(data)
        elapsed = time.perf_counter() - t0

        # Validate — accept any finite float
        assert signals.index.equals(data.index), f"{ticker}: index mismatch"
        assert not signals.isna().any(), f"{ticker}: NaN"
        assert np.isfinite(signals).all(), f"{ticker}: non-finite values"
        signals = signals.astype(float)

        strat_returns = backtest(data, signals)
        bh_returns = data["Close"].pct_change().dropna()

        sm = calc_metrics(strat_returns, bars_per_year)
        bm = calc_metrics(bh_returns, bars_per_year)
        trades = count_trades(signals)

        results[ticker] = {
            "strat": sm,
            "bh": bm,
            "trades": trades,
            "time": elapsed,
            "bars": len(data),
            "signals": signals,
        }

    return results


def format_md(results, timeframe, bars_per_year):
    """Format results as markdown matching existing BACKTEST_RESULTS style."""
    period = "~10yr daily bars (2016 to 2026)" if timeframe == "daily" else "~2yr hourly bars (2024 to 2026)"

    lines = []
    lines.append(f"# {timeframe.title()} Backtest Results — ML Pre-trained (Continuous)")
    lines.append(f"")
    lines.append(f"**Data: {period} from Yahoo Finance** | **Transaction Cost:** 0.05% (5bps) | **Next-day execution** | **Assets:** {len(results)}")
    lines.append(f"")
    lines.append(f"## Strategy")
    lines.append(f"")
    lines.append(f"| Code | Name | Type | Description |")
    lines.append(f"|:-----|:-----|:-----|:------------|")
    lines.append(f"| **ML Pre** | **Pre-trained ML Ensemble** | **Continuous** | **XGB+RF ensemble, continuous position sizing [-2, 2]** |")
    lines.append(f"")

    total_beats = 0
    total_assets = len(results)

    for cat, tickers in CATEGORIES.items():
        cat_results = {t: results[t] for t in tickers if t in results}
        if not cat_results:
            continue

        lines.append(f"## {cat} ({len(cat_results)} assets)")
        lines.append(f"")
        lines.append(f"| Asset | Name | Strat Return | Strat Sharpe | MaxDD | Trades | B&H Return | B&H Sharpe | Best |")
        lines.append(f"|:------|:-----|----------:|-----------:|------:|-------:|----------:|-----------:|:-----|")

        cat_beats = 0
        for ticker in tickers:
            if ticker not in results:
                continue
            r = results[ticker]
            s_ret = r["strat"]["total_return"]
            s_sh = r["strat"]["sharpe"]
            s_dd = r["strat"]["max_drawdown"]
            b_ret = r["bh"]["total_return"]
            b_sh = r["bh"]["sharpe"]
            trades = r["trades"]
            name = ASSET_NAMES.get(ticker, ticker)

            best = "Strat" if s_sh > b_sh else "B&H"
            if s_sh > b_sh:
                cat_beats += 1
                total_beats += 1

            s_tag = " **(W)**" if s_sh >= b_sh else ""
            b_tag = " **(W)**" if b_sh > s_sh else ""

            lines.append(
                f"| {ticker} | {name} "
                f"| {s_ret:+.1%}{s_tag} | {s_sh:.2f} | {s_dd:.1%} | {trades} "
                f"| {b_ret:+.1%}{b_tag} | {b_sh:.2f} | {best} |"
            )

        lines.append(f"| **Beats B&H** | | | **{cat_beats}/{len(cat_results)}** | | | | | |")
        lines.append(f"")

    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"**Beats Buy & Hold (Sharpe): {total_beats}/{total_assets} ({100*total_beats/total_assets:.0f}%)**")
    lines.append(f"")

    sharpes = [r["strat"]["sharpe"] for r in results.values()]
    bh_sharpes = [r["bh"]["sharpe"] for r in results.values()]
    lines.append(f"| Metric | Strategy | B&H |")
    lines.append(f"|:-------|----:|----:|")
    lines.append(f"| Avg Sharpe | {np.mean(sharpes):.3f} | {np.mean(bh_sharpes):.3f} |")
    lines.append(f"| Median Sharpe | {np.median(sharpes):.3f} | {np.median(bh_sharpes):.3f} |")
    lines.append(f"| Avg Trades | {np.mean([r['trades'] for r in results.values()]):.0f} | 0 |")
    lines.append(f"")

    return "\n".join(lines)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    # Daily
    print("Running daily backtest (41 assets)...")
    daily = run_suite(DAILY_DIR, 252, "daily")
    md = format_md(daily, "daily", 252)
    with open(os.path.join(OUT_DIR, "DAILY_HACKATHON.md"), "w") as f:
        f.write(md)
    beats = sum(1 for r in daily.values() if r["strat"]["sharpe"] > r["bh"]["sharpe"])
    print(f"  Daily: {beats}/{len(daily)} beat B&H on Sharpe")

    # Hourly
    print("Running hourly backtest (41 assets)...")
    hourly = run_suite(HOURLY_DIR, 252 * 7, "hourly")
    md = format_md(hourly, "hourly", 252 * 7)
    with open(os.path.join(OUT_DIR, "HOURLY_HACKATHON.md"), "w") as f:
        f.write(md)
    beats = sum(1 for r in hourly.values() if r["strat"]["sharpe"] > r["bh"]["sharpe"])
    print(f"  Hourly: {beats}/{len(hourly)} beat B&H on Sharpe")

    print(f"\nResults written to {OUT_DIR}/")
