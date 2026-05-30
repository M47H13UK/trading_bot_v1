"""Generate complete backtest results markdown with ML v3 included."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from trading_bot import (
    strategy_peak_shaver_v1, strategy_peak_shaver,
    Backtester, TICKER_INFO, COMMISSION, TEST_DATA_DIR, HOURLY_DATA_DIR,
)
from ml_peak_shaver_v2 import (
    _load_all_assets, train_ml_models, strategy_ml_peak_shaver,
)
from ml_peak_shaver_v3 import train_v3, strategy_ml_v3

# Category grouping order
CAT_ORDER = ["Index", "Stock", "Sector", "Global", "Commodity", "Crypto", "Bond", "Forex"]
CAT_LABELS = {
    "Index": "Index", "Stock": "Stock", "Sector": "Sector", "Global": "Global",
    "Commodity": "Commodity", "Crypto": "Crypto", "Bond": "Bond", "Forex": "Forex",
}


def run_dataset(data_dir, label, timeframe_desc):
    """Run all strategies on all assets, return list of result dicts."""
    print(f"\n{'='*80}", flush=True)
    print(f"  RUNNING {label} BACKTEST", flush=True)
    print(f"{'='*80}", flush=True)

    # Train ML models
    print(f"\n--- Training ML v2 ({label}) ---", flush=True)
    v2_models = train_ml_models(data_dir)

    print(f"\n--- Training ML v3 ({label}) ---", flush=True)
    v3_models = train_v3(data_dir)

    assets = _load_all_assets(data_dir)
    results = []
    curves = {}  # equity/drawdown curves for the representative asset (charts)

    for stem, name, category, df in assets:
        bt = Backtester(df, initial_capital=10_000, commission=COMMISSION)

        # PSv1
        pos1, _ = strategy_peak_shaver_v1(df)
        r1 = bt.run_positions(pos1, strategy_name="PSv1")

        # PSv2
        pos2, _ = strategy_peak_shaver(df)
        r2 = bt.run_positions(pos2, strategy_name="PSv2")

        # ML v2
        if v2_models:
            ml2_pos, _ = strategy_ml_peak_shaver(df, v2_models, asset_category=category)
        else:
            ml2_pos = pos2
        r_ml2 = bt.run_positions(ml2_pos, strategy_name="ML v2")

        # ML v3
        if v3_models:
            ml3_pos, _ = strategy_ml_v3(df, v3_models, asset_category=category,
                                         exit_percentile=30)
        else:
            ml3_pos = pos2
        r_ml3 = bt.run_positions(ml3_pos, strategy_name="ML v3")

        bnh = r1["buy_and_hold_return_pct"]

        row = {
            "asset": stem, "name": name, "category": category,
            "psv1": r1["total_return_pct"],
            "psv2": r2["total_return_pct"],
            "ml2": r_ml2["total_return_pct"],
            "ml3": r_ml3["total_return_pct"],
            "bnh": bnh,
        }
        # Determine best
        strats = {"PSv1": row["psv1"], "PSv2": row["psv2"],
                  "ML": row["ml2"], "MLv3": row["ml3"], "B&H": row["bnh"]}
        row["best"] = max(strats, key=strats.get)
        # Determine worst
        row["worst_key"] = min(strats, key=strats.get)
        results.append(row)

        # Capture curves for the representative asset (used by README charts)
        if stem == "SPY":
            bnh_curve = 10_000 * (df["Close"] / df["Close"].iloc[0])
            curves = {
                "index": df.index,
                "B&H": bnh_curve,
                "PSv2": r2["equity_curve"],
                "MLv2": r_ml2["equity_curve"],
                "MLv3": r_ml3["equity_curve"],
                "dd_PSv2": r2["drawdown"],
                "dd_MLv3": r_ml3["drawdown"],
            }

        status = "+" if row["ml3"] > row["ml2"] else "-"
        print(f"  [{status}] {stem:<12} PSv1:{row['psv1']:>+8.1f}  PSv2:{row['psv2']:>+8.1f}  "
              f"MLv2:{row['ml2']:>+8.1f}  MLv3:{row['ml3']:>+8.1f}  B&H:{bnh:>+8.1f}", flush=True)

    return results, curves


def fmt_cell(val, is_best, is_worst):
    """Format a table cell with (W) and (L) markers."""
    s = f"+{val:.1f}%" if val >= 0 else f"{val:.1f}%"
    if is_best:
        s += " **(W)**"
    elif is_worst:
        s += " **(L)**"
    return s


def generate_markdown(results, label, timeframe_desc, n_assets):
    """Generate full markdown string from results."""
    lines = []
    lines.append(f"# {label} Backtest Results — Peak Shaver Strategies")
    lines.append("")
    lines.append(f"**Data: {timeframe_desc}** | **Initial Capital:** $10,000 | **Commission:** 0.0% | **Assets:** {n_assets}")
    lines.append("")
    lines.append("## Strategies")
    lines.append("")
    lines.append("| Code | Name | Type | Description |")
    lines.append("|:-----|:-----|:-----|:------------|")
    lines.append("| **PSv1** | **Peak Shaver v1** | **Continuous** | **RSI>75 + ROC>11% -> 50%, RSI>85 -> 30%** |")
    lines.append("| **PSv2** | **Peak Shaver v2** | **Continuous** | **v1 + Z-score>1.0 gate (Tier 1), Z>3.0 gate (Tier 2)** |")
    lines.append("| **ML** | **ML Peak Shaver v2** | **Continuous** | **XGBRegressor+RF regression, multi-horizon labels, magnitude-weighted, dynamic ensemble** |")
    lines.append("| **MLv3** | **ML v3 Return Maximizer** | **Continuous** | **Every-bar return prediction, binary position sizing (100%/0%), 37 features, bullish bias** |")
    lines.append("")

    # Group by category
    for cat in CAT_ORDER:
        cat_rows = [r for r in results if r["category"] == cat]
        if not cat_rows:
            continue

        cat_label = CAT_LABELS.get(cat, cat)
        lines.append(f"## {cat_label} ({len(cat_rows)} assets)")
        lines.append("")
        lines.append("| Asset | Name | PSv1 | PSv2 | ML | MLv3 | B&H | Best |")
        lines.append("|:------|:-----|-------:|-------:|-------:|-------:|----:|:-----|")

        beats_bnh = {"psv1": 0, "psv2": 0, "ml2": 0, "ml3": 0}
        for r in cat_rows:
            strats = {"PSv1": r["psv1"], "PSv2": r["psv2"],
                      "ML": r["ml2"], "MLv3": r["ml3"], "B&H": r["bnh"]}
            best_key = max(strats, key=strats.get)
            worst_key = min(strats, key=strats.get)

            c_psv1 = fmt_cell(r["psv1"], best_key == "PSv1", worst_key == "PSv1")
            c_psv2 = fmt_cell(r["psv2"], best_key == "PSv2", worst_key == "PSv2")
            c_ml2 = fmt_cell(r["ml2"], best_key == "ML", worst_key == "ML")
            c_ml3 = fmt_cell(r["ml3"], best_key == "MLv3", worst_key == "MLv3")
            c_bnh = fmt_cell(r["bnh"], best_key == "B&H", worst_key == "B&H")

            lines.append(f"| {r['asset']} | {r['name']} | {c_psv1}| {c_psv2}| {c_ml2}| {c_ml3}| {c_bnh}| {best_key} |")

            for key, col in [("psv1", "psv1"), ("psv2", "psv2"), ("ml2", "ml2"), ("ml3", "ml3")]:
                if r[col] > r["bnh"]:
                    beats_bnh[key] += 1

        n = len(cat_rows)
        lines.append(f"| **Beats B&H** | | {beats_bnh['psv1']}/{n} | {beats_bnh['psv2']}/{n} | {beats_bnh['ml2']}/{n} | {beats_bnh['ml3']}/{n} | — | |")
        lines.append("")

    # Grand summary
    lines.append("---")
    lines.append("")
    lines.append("## Grand Summary")
    lines.append("")

    rdf = pd.DataFrame(results)
    n = len(rdf)

    def calc_stats(col):
        avg = rdf[col].mean()
        # Exclude outliers: clip to 5th-95th for avg_excl
        lo, hi = rdf[col].quantile(0.05), rdf[col].quantile(0.95)
        avg_excl = rdf[col].clip(lo, hi).mean()
        med = rdf[col].median()
        beats = (rdf[col] > rdf["bnh"]).sum() if col != "bnh" else None
        # Count wins
        cols = ["psv1", "psv2", "ml2", "ml3", "bnh"]
        wins = sum(1 for _, row in rdf.iterrows()
                   if row[col] == max(row[c] for c in cols))
        return avg, avg_excl, med, beats, wins

    lines.append("| Metric | PSv1 | PSv2 | ML | MLv3 |")
    lines.append("|:-------|------:|------:|------:|------:|")

    stats = {}
    for col, label in [("psv1", "PSv1"), ("psv2", "PSv2"), ("ml2", "ML"), ("ml3", "MLv3")]:
        stats[col] = calc_stats(col)
    bnh_stats = calc_stats("bnh")

    lines.append(f"| **Avg Return** | +{stats['psv1'][0]:.1f}% | +{stats['psv2'][0]:.1f}% | +{stats['ml2'][0]:.1f}% | +{stats['ml3'][0]:.1f}% |")
    lines.append(f"| **Avg Return (excl. outliers)** | +{stats['psv1'][1]:.1f}% | +{stats['psv2'][1]:.1f}% | +{stats['ml2'][1]:.1f}% | +{stats['ml3'][1]:.1f}% |")
    lines.append(f"| **Median Return** | +{stats['psv1'][2]:.1f}% | +{stats['psv2'][2]:.1f}% | +{stats['ml2'][2]:.1f}% | +{stats['ml3'][2]:.1f}% |")
    lines.append(f"| **# Wins (Best)** | **{stats['psv1'][4]}/{n}** | **{stats['psv2'][4]}/{n}** | **{stats['ml2'][4]}/{n}** | **{stats['ml3'][4]}/{n}** |")
    lines.append(f"| **Beats B&H** | **{stats['psv1'][3]}/{n}** ({stats['psv1'][3]/n*100:.0f}%) | **{stats['psv2'][3]}/{n}** ({stats['psv2'][3]/n*100:.0f}%) | **{stats['ml2'][3]}/{n}** ({stats['ml2'][3]/n*100:.0f}%) | **{stats['ml3'][3]}/{n}** ({stats['ml3'][3]/n*100:.0f}%) |")

    # Median alpha
    for col in ["psv1", "psv2", "ml2", "ml3"]:
        alpha = (rdf[col] - rdf["bnh"]).median()
        stats[col] = (*stats[col], alpha)
    lines.append(f"| Median Alpha | {stats['psv1'][5]:+.1f}% | {stats['psv2'][5]:+.1f}% | {stats['ml2'][5]:+.1f}% | {stats['ml3'][5]:+.1f}% |")

    # Recommendation
    lines.append("")
    lines.append("### Recommendation")
    lines.append("")
    lines.append(f"**Ranked by average total return ({n} assets):**")
    lines.append("")
    lines.append("| Rank | Strategy | Median Return | Avg Return | Avg (excl. outliers) | # Wins | Beats B&H |")
    lines.append("|:-----|:---------|-------------:|----------:|--------------------:|:------:|:---------:|")

    ranking = sorted(
        [("PSv1", stats["psv1"]), ("PSv2", stats["psv2"]),
         ("ML", stats["ml2"]), ("MLv3", stats["ml3"])],
        key=lambda x: x[1][0], reverse=True
    )
    for rank, (name, s) in enumerate(ranking, 1):
        lines.append(f"| {rank} | **{name}** | +{s[2]:.1f}% | +{s[0]:.1f}% | +{s[1]:.1f}% | {s[4]}/{n} | {s[3]}/{n} |")
    lines.append(f"| — | B&H | +{bnh_stats[2]:.1f}% | +{bnh_stats[0]:.1f}% | +{bnh_stats[1]:.1f}% | {bnh_stats[4]}/{n} | — |")

    # MLv3 wins/losses detail
    lines.append("")
    lines.append("### ML v3 Return Maximizer — Wins & Losses")
    lines.append("")

    v3_beats_bnh = (rdf["ml3"] > rdf["bnh"]).sum()
    v3_beats_v2 = (rdf["ml3"] > rdf["ml2"]).sum()
    v3_beats_psv2 = (rdf["ml3"] > rdf["psv2"]).sum()
    lines.append(f"**vs B&H: {v3_beats_bnh}/{n} | vs ML v2: {v3_beats_v2}/{n} | vs PSv2: {v3_beats_psv2}/{n}**")
    lines.append("")

    # Wins table (sorted by alpha desc)
    winners = rdf[rdf["ml3"] > rdf["bnh"]].copy()
    winners["alpha"] = winners["ml3"] - winners["bnh"]
    winners = winners.sort_values("alpha", ascending=False)

    lines.append(f"**Beats B&H on {len(winners)}/{n} assets**")
    lines.append("")
    lines.append("| Asset | Category | MLv3 | B&H | Alpha | vs ML v2 | vs PSv2 |")
    lines.append("|:------|:---------|-----:|----:|------:|--------:|--------:|")
    for _, r in winners.iterrows():
        lines.append(f"| {r['asset']} | {r['category']} | +{r['ml3']:.1f}% | +{r['bnh']:.1f}% | **+{r['alpha']:.1f}%** | {r['ml3']-r['ml2']:+.1f}% | {r['ml3']-r['psv2']:+.1f}% |")

    # Losses table
    losers = rdf[rdf["ml3"] <= rdf["bnh"]].copy()
    losers["gap"] = losers["ml3"] - losers["bnh"]
    losers = losers.sort_values("gap", ascending=True)

    lines.append("")
    lines.append(f"**Loses to B&H on {len(losers)}/{n} assets**")
    lines.append("")
    lines.append("| Asset | Category | MLv3 | B&H | Gap | vs ML v2 | vs PSv2 |")
    lines.append("|:------|:---------|-----:|----:|----:|--------:|--------:|")
    for _, r in losers.iterrows():
        lines.append(f"| {r['asset']} | {r['category']} | +{r['ml3']:.1f}% | +{r['bnh']:.1f}% | {r['gap']:+.1f}% | {r['ml3']-r['ml2']:+.1f}% | {r['ml3']-r['psv2']:+.1f}% |")

    return "\n".join(lines) + "\n"


STRAT_COLORS = {
    "B&H": "#7f8c8d", "PSv1": "#3498db", "PSv2": "#2980b9",
    "MLv2": "#e67e22", "MLv3": "#27ae60",
}


def save_single_asset_chart(curves, out_path, asset="SPY"):
    """Equity curves + drawdown for one asset across the strategy lineage."""
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1], "hspace": 0.25})

    for label in ["B&H", "PSv2", "MLv2", "MLv3"]:
        series = curves[label]
        ret = (series.iloc[-1] / series.iloc[0] - 1) * 100
        style = "--" if label == "B&H" else "-"
        lw = 1.6 if label == "B&H" else 2.0
        ax1.plot(curves["index"], series.values, style, linewidth=lw,
                 color=STRAT_COLORS[label], label=f"{label}  ({ret:+.0f}%)")
    ax1.set_title(f"{asset}: Strategy Lineage vs Buy & Hold  (daily, 10yr, $10k start, 0% commission)",
                  fontsize=13, fontweight="bold")
    ax1.set_ylabel("Portfolio Value ($)")
    ax1.legend(loc="upper left", frameon=False)
    ax1.grid(True, alpha=0.25)

    ax2.fill_between(curves["index"], curves["dd_PSv2"] * 100, 0,
                     color=STRAT_COLORS["PSv2"], alpha=0.35, label="PSv2")
    ax2.fill_between(curves["index"], curves["dd_MLv3"] * 100, 0,
                     color=STRAT_COLORS["MLv3"], alpha=0.35, label="MLv3")
    ax2.set_title("Drawdown", fontsize=11)
    ax2.set_ylabel("Drawdown (%)")
    ax2.legend(loc="lower left", frameon=False, fontsize=8)
    ax2.grid(True, alpha=0.25)

    plt.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"Wrote {out_path}", flush=True)


def save_cross_asset_chart(results, out_path):
    """Beat-rate and median return per strategy across all benchmark assets."""
    n = len(results)
    rdf = pd.DataFrame(results)
    strat_cols = [("psv1", "PSv1"), ("psv2", "PSv2"), ("ml2", "MLv2"), ("ml3", "MLv3")]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

    # Panel 1: beats Buy & Hold
    labels = [lbl for _, lbl in strat_cols]
    beats = [(rdf[c] > rdf["bnh"]).sum() for c, _ in strat_cols]
    colors = [STRAT_COLORS[lbl] for lbl in labels]
    bars = ax1.bar(labels, beats, color=colors, alpha=0.9)
    ax1.axhline(n / 2, color="#c0392b", linestyle="--", linewidth=1, label="50% (coin flip)")
    ax1.set_ylim(0, n)
    ax1.set_ylabel(f"Assets beating Buy & Hold (of {n})")
    ax1.set_title(f"How often each strategy beats Buy & Hold", fontsize=12, fontweight="bold")
    for b, v in zip(bars, beats):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v}/{n}\n({v/n*100:.0f}%)",
                 ha="center", va="bottom", fontsize=9)
    ax1.legend(frameon=False, fontsize=8)

    # Panel 2: median return per strategy vs B&H
    med = [rdf[c].median() for c, _ in strat_cols] + [rdf["bnh"].median()]
    med_labels = labels + ["B&H"]
    med_colors = colors + [STRAT_COLORS["B&H"]]
    bars2 = ax2.bar(med_labels, med, color=med_colors, alpha=0.9)
    ax2.set_ylabel("Median total return (%)")
    ax2.set_title("Median return across all benchmark assets", fontsize=12, fontweight="bold")
    for b, v in zip(bars2, med):
        ax2.text(b.get_x() + b.get_width() / 2, v + 2, f"+{v:.0f}%",
                 ha="center", va="bottom", fontsize=9)
    ax2.grid(True, axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"Wrote {out_path}", flush=True)


def main():
    root = Path(__file__).parent
    out_dir = root / "test_data" / "BACKTEST_RESULTS"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Daily
    daily_results, daily_curves = run_dataset(TEST_DATA_DIR, "Daily (10yr)", "~10yr daily bars (2016 to 2026) from Yahoo Finance")
    daily_md = generate_markdown(daily_results, "Daily (10yr)", "~10yr daily bars (2016 to 2026) from Yahoo Finance", len(daily_results))
    (out_dir / "DAILY.md").write_text(daily_md)
    print(f"\nWrote {out_dir / 'DAILY.md'}", flush=True)

    # README charts — generated from the same daily run for consistency
    save_cross_asset_chart(daily_results, root / "cross_asset_results.png")
    if daily_curves:
        save_single_asset_chart(daily_curves, root / "backtest_results.png")

    # Hourly
    hourly_results, _ = run_dataset(HOURLY_DATA_DIR, "Hourly (2yr)", "~2yr hourly bars (2024 to 2026) from Yahoo Finance")
    hourly_md = generate_markdown(hourly_results, "Hourly (2yr)", "~2yr hourly bars (2024 to 2026) from Yahoo Finance", len(hourly_results))
    (out_dir / "HOURLY.md").write_text(hourly_md)
    print(f"\nWrote {out_dir / 'HOURLY.md'}", flush=True)

    print("\nDone!", flush=True)


if __name__ == "__main__":
    main()
