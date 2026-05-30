"""
Strategy Comparison — runs all strategies on all datasets,
outputs strategy_comparison.md with full breakdown.
Uses test.py eval logic: next-day execution, 5bps costs, Sharpe primary.
"""

import pandas as pd
import numpy as np
import os
import sys
import time
import importlib.util
import json

TRADING_DAYS = 252
TRANSACTION_COST = 0.0005

STRATEGY_FILES = {
    "PS v1":        "submissions/peak_shaver_v1.py",
    "PS v2":        "submissions/peak_shaver_v2.py",
    "Hack Sharpe":  "submissions/hackathon_sharpe.py",
    "Enh PS":       "submissions/enhanced_peak_shaver.py",
    "ML v2":        "submissions/ml_peak_shaver_v2.py",
    "ML v3":        "submissions/ml_peak_shaver_v3.py",
    "ML Pre":       "submissions/strategy.py",
}

HACKATHON_DATA = {
    "SPY": "data/spy.csv",
    "QQQ": "data/qqq.csv",
}

DAILY_DIR = "../test_data/daily"
HOURLY_DIR = "../test_data/hourly"


def load_data(filepath):
    """Load OHLCV data, handling multi-ticker, yfinance multi-header, and plain CSVs."""
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"

    # Check for multi-ticker format (columns like Close_SPY, Open_QQQ)
    if any("_" in col for col in df.columns):
        new_cols = []
        is_multi = True
        for col in df.columns:
            parts = col.rsplit("_", 1)
            if len(parts) == 2:
                new_cols.append((parts[1], parts[0]))
            else:
                is_multi = False
                break
        if is_multi:
            df.columns = pd.MultiIndex.from_tuples(new_cols, names=["Ticker", "OHLCV"])
            tickers = list(df.columns.get_level_values(0).unique())
            df = df[tickers[0]].copy()
            df.columns.name = None

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        # Try yfinance multi-row header
        probe = pd.read_csv(filepath, nrows=5, header=None)
        if probe.iloc[0, 0] == "Price":
            df = pd.read_csv(filepath, header=[0, 1], index_col=0, parse_dates=True)
            df.columns = df.columns.get_level_values(0)
            df.index.name = "Date"

    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns in {filepath}")
    return df.ffill().dropna()


def load_strategy(path):
    spec = importlib.util.spec_from_file_location("strategy", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def backtest(data, signals):
    returns = data["Close"].pct_change()
    shifted = signals.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    r, pos = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = pos.diff().abs().fillna(0) * TRANSACTION_COST
    return pos * r - costs


def calc_metrics(returns, bars_per_year=252):
    if len(returns) == 0:
        return None
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


def bh_metrics(data, bars_per_year=252):
    returns = data["Close"].pct_change().dropna()
    return calc_metrics(returns, bars_per_year)


def count_trades(signals):
    return int(signals.diff().abs().fillna(0).gt(0).sum())


def run_dataset(datasets, strategies, bars_per_year=252, label=""):
    """Run all strategies on all datasets. Returns dict of results."""
    results = {}

    for ticker, data in datasets.items():
        results[ticker] = {}
        bh = bh_metrics(data, bars_per_year)
        results[ticker]["Buy & Hold"] = {**bh, "trades": 0, "time": 0}

        for strat_name, mod in strategies.items():
            try:
                t0 = time.perf_counter()
                signals = mod.generate_signals(data)
                elapsed = time.perf_counter() - t0

                signals = signals.astype(float)
                assert signals.index.equals(data.index)
                assert not signals.isna().any()
                assert np.isfinite(signals).all()

                strat_returns = backtest(data, signals)
                m = calc_metrics(strat_returns, bars_per_year)
                m["trades"] = count_trades(signals)
                m["time"] = elapsed
                results[ticker][strat_name] = m
            except Exception as e:
                print(f"  ERROR {strat_name} on {ticker}: {e}")
                results[ticker][strat_name] = None

    return results


def format_results_table(results, strat_names):
    """Format results as markdown table rows."""
    lines = []
    cols = ["Asset"]
    for s in strat_names:
        cols.extend([f"{s} Sharpe", f"{s} Return"])
    cols.extend(["B&H Sharpe", "B&H Return", "Best Strategy"])
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    for ticker in sorted(results.keys()):
        row = [ticker]
        best_sharpe = -999
        best_name = "B&H"

        bh = results[ticker].get("Buy & Hold")
        if bh:
            bh_sh = bh["sharpe"]
            best_sharpe = bh_sh
        else:
            bh_sh = 0

        for s in strat_names:
            m = results[ticker].get(s)
            if m:
                row.extend([f"{m['sharpe']:.2f}", f"{m['total_return']:+.1%}"])
                if m["sharpe"] > best_sharpe:
                    best_sharpe = m["sharpe"]
                    best_name = s
            else:
                row.extend(["ERR", "ERR"])

        row.extend([f"{bh_sh:.2f}", f"{bh['total_return']:+.1%}" if bh else "ERR", best_name])
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def format_summary_table(all_results, strat_names, label):
    """Aggregate stats across all tickers."""
    lines = []
    lines.append(f"| Strategy | Avg Sharpe | Med Sharpe | Avg Return | Beats B&H | Avg Trades |")
    lines.append(f"|----------|-----------|-----------|-----------|-----------|-----------|")

    bh_sharpes = {}
    for ticker, strats in all_results.items():
        bh = strats.get("Buy & Hold")
        if bh:
            bh_sharpes[ticker] = bh["sharpe"]

    for s in strat_names + ["Buy & Hold"]:
        sharpes = []
        returns = []
        trades = []
        beats = 0
        for ticker, strats in all_results.items():
            m = strats.get(s)
            if m:
                sharpes.append(m["sharpe"])
                returns.append(m["total_return"])
                trades.append(m.get("trades", 0))
                if s != "Buy & Hold" and ticker in bh_sharpes and m["sharpe"] > bh_sharpes[ticker]:
                    beats += 1

        if not sharpes:
            continue

        n = len(all_results)
        beats_str = f"{beats}/{n}" if s != "Buy & Hold" else "—"
        lines.append(
            f"| **{s}** | {np.mean(sharpes):.3f} | {np.median(sharpes):.3f} "
            f"| {np.mean(returns):+.1%} | {beats_str} | {np.mean(trades):.0f} |"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load strategies (non-ML first, ML separately since they're slow)
    print("Loading strategies...")
    non_ml_names = ["PS v1", "PS v2", "Hack Sharpe", "Enh PS", "ML Pre"]
    ml_names = ["ML v2", "ML v3"]
    all_strat_names = non_ml_names + ml_names

    strategies = {}
    for name, path in STRATEGY_FILES.items():
        try:
            strategies[name] = load_strategy(path)
            print(f"  Loaded: {name}")
        except Exception as e:
            print(f"  SKIP {name}: {e}")

    md_lines = []
    md_lines.append("# Strategy Comparison — Full Breakdown")
    md_lines.append("")
    md_lines.append("All strategies evaluated with **test.py logic**: next-day execution, 5bps transaction costs.")
    md_lines.append("Primary ranking: **Sharpe Ratio**.")
    md_lines.append("")

    # ── 1. Hackathon Data (SPY + QQQ) ──
    print("\n=== Hackathon Data (SPY + QQQ) ===")
    hack_data = {}
    for ticker, path in HACKATHON_DATA.items():
        if os.path.exists(path):
            hack_data[ticker] = load_data(path)
            print(f"  Loaded {ticker}: {len(hack_data[ticker])} bars")

    if hack_data:
        hack_results = run_dataset(hack_data, strategies, 252, "hackathon")
        md_lines.append("## 1. Hackathon Data (SPY + QQQ, ~10yr daily)")
        md_lines.append("")
        avail = [s for s in all_strat_names if s in strategies]
        md_lines.append(format_results_table(hack_results, avail))
        md_lines.append("")
        md_lines.append("### Summary")
        md_lines.append("")
        md_lines.append(format_summary_table(hack_results, avail, "hackathon"))
        md_lines.append("")

        for ticker in hack_data:
            print(f"\n  {ticker}:")
            for s in avail + ["Buy & Hold"]:
                m = hack_results[ticker].get(s)
                if m:
                    print(f"    {s:15s}  Sharpe={m['sharpe']:6.2f}  Return={m['total_return']:+8.1%}  Trades={m.get('trades',0):4d}")

    # ── 2. Daily Test Data (41 assets) ──
    print("\n=== Daily Test Data (41 assets) ===")
    daily_data = {}
    if os.path.exists(DAILY_DIR):
        for f in sorted(os.listdir(DAILY_DIR)):
            if f.endswith(".csv"):
                ticker = f.replace(".csv", "")
                try:
                    daily_data[ticker] = load_data(os.path.join(DAILY_DIR, f))
                except Exception:
                    pass
        print(f"  Loaded {len(daily_data)} assets")

    if daily_data:
        non_ml_strats = {k: v for k, v in strategies.items() if k in non_ml_names}
        ml_strats = {k: v for k, v in strategies.items() if k in ml_names}

        print("  Running non-ML strategies...")
        daily_results = run_dataset(daily_data, non_ml_strats, 252, "daily")

        ml_tickers = ["SPY", "QQQ", "XOM", "AAPL", "GLD"]
        ml_daily_data = {t: daily_data[t] for t in ml_tickers if t in daily_data}
        if ml_strats and ml_daily_data:
            print(f"  Running ML strategies on {list(ml_daily_data.keys())}...")
            ml_daily_results = run_dataset(ml_daily_data, ml_strats, 252, "daily_ml")
            for ticker in ml_daily_results:
                if ticker in daily_results:
                    daily_results[ticker].update(ml_daily_results[ticker])

        md_lines.append("## 2. Daily Test Data (~10yr, 41 assets)")
        md_lines.append("")
        md_lines.append(format_results_table(daily_results, [s for s in all_strat_names if s in strategies]))
        md_lines.append("")
        md_lines.append("### Summary")
        md_lines.append("")
        md_lines.append(format_summary_table(daily_results, [s for s in all_strat_names if s in strategies], "daily"))
        md_lines.append("")
        md_lines.append(f"*ML strategies only run on {', '.join(ml_tickers)} due to training time.*")
        md_lines.append("")

        for s in [s for s in all_strat_names if s in strategies] + ["Buy & Hold"]:
            sharpes = [daily_results[t][s]["sharpe"] for t in daily_results if daily_results[t].get(s)]
            if sharpes:
                print(f"  {s:15s}  Avg Sharpe={np.mean(sharpes):.3f}  Med={np.median(sharpes):.3f}")

    # ── 3. Hourly Test Data (41 assets) ──
    print("\n=== Hourly Test Data (41 assets) ===")
    hourly_data = {}
    if os.path.exists(HOURLY_DIR):
        for f in sorted(os.listdir(HOURLY_DIR)):
            if f.endswith(".csv"):
                ticker = f.replace(".csv", "")
                try:
                    hourly_data[ticker] = load_data(os.path.join(HOURLY_DIR, f))
                except Exception:
                    pass
        print(f"  Loaded {len(hourly_data)} assets")

    if hourly_data:
        non_ml_strats = {k: v for k, v in strategies.items() if k in non_ml_names}
        ml_strats = {k: v for k, v in strategies.items() if k in ml_names}
        bars_per_year = 252 * 7

        print("  Running non-ML strategies...")
        hourly_results = run_dataset(hourly_data, non_ml_strats, bars_per_year, "hourly")

        ml_hourly_data = {t: hourly_data[t] for t in ml_tickers if t in hourly_data}
        if ml_strats and ml_hourly_data:
            print(f"  Running ML strategies on {list(ml_hourly_data.keys())}...")
            ml_hourly_results = run_dataset(ml_hourly_data, ml_strats, bars_per_year, "hourly_ml")
            for ticker in ml_hourly_results:
                if ticker in hourly_results:
                    hourly_results[ticker].update(ml_hourly_results[ticker])

        md_lines.append("## 3. Hourly Test Data (~2yr, 41 assets)")
        md_lines.append("")
        md_lines.append(format_results_table(hourly_results, [s for s in all_strat_names if s in strategies]))
        md_lines.append("")
        md_lines.append("### Summary")
        md_lines.append("")
        md_lines.append(format_summary_table(hourly_results, [s for s in all_strat_names if s in strategies], "hourly"))
        md_lines.append("")
        md_lines.append(f"*ML strategies only run on {', '.join(ml_tickers)} due to training time.*")
        md_lines.append("")

        for s in [s for s in all_strat_names if s in strategies] + ["Buy & Hold"]:
            sharpes = [hourly_results[t][s]["sharpe"] for t in hourly_results if hourly_results[t].get(s)]
            if sharpes:
                print(f"  {s:15s}  Avg Sharpe={np.mean(sharpes):.3f}  Med={np.median(sharpes):.3f}")

    # ── 4. Overall Winner ──
    md_lines.append("## 4. Overall Winner")
    md_lines.append("")
    md_lines.append("| Dataset | Best Strategy (Avg Sharpe) |")
    md_lines.append("|---------|--------------------------|")

    for label, res in [("Hackathon (SPY+QQQ)", hack_results if hack_data else {}),
                        ("Daily (41 assets)", daily_results if daily_data else {}),
                        ("Hourly (41 assets)", hourly_results if hourly_data else {})]:
        if not res:
            continue
        best_name, best_avg = "—", -999
        for s in [s for s in all_strat_names if s in strategies]:
            sharpes = [res[t][s]["sharpe"] for t in res if res[t].get(s)]
            if sharpes and np.mean(sharpes) > best_avg:
                best_avg = np.mean(sharpes)
                best_name = s
        bh_sharpes_list = [res[t]["Buy & Hold"]["sharpe"] for t in res if res[t].get("Buy & Hold")]
        if bh_sharpes_list and np.mean(bh_sharpes_list) > best_avg:
            best_avg = np.mean(bh_sharpes_list)
            best_name = "Buy & Hold"
        md_lines.append(f"| {label} | **{best_name}** ({best_avg:.3f}) |")

    md_lines.append("")

    with open("strategy_comparison.md", "w") as f:
        f.write("\n".join(md_lines))
    print(f"\nResults written to strategy_comparison.md")
