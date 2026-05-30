"""
Peak Shaver | Quantitative Trading Terminal
============================================
Bloomberg/TradingView-style dark terminal for hackathon demo.
Imports strategies from trading_bot.py + ml_peak_shaver_v2.py.

Run:  streamlit run dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path

# --- Import from existing codebase ---
from trading_bot import (
    DEFAULT_TICKERS, TICKER_INFO, TEST_DATA_DIR, HOURLY_DATA_DIR, COMMISSION,
    load_csv_data, _sanitize_ticker, _detect_bars_per_day,
    rsi, roc, zscore, sma, ema, bollinger_bands, macd_indicator, atr, adx, obv, cmf,
    detect_regime, strategy_peak_shaver_v1, strategy_peak_shaver,
    Backtester,
)

try:
    from ml_peak_shaver_v2 import (
        ML_AVAILABLE, build_features, train_ml_models,
        strategy_ml_peak_shaver, _load_all_assets,
    )
except ImportError:
    ML_AVAILABLE = False

# =============================================================================
# PAGE CONFIG + CSS
# =============================================================================

st.set_page_config(
    page_title="Peak Shaver Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
    /* Main background */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0a0a0f;
        color: #c9d1d9;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e2d3d;
    }
    /* Header bar */
    .terminal-header {
        background: linear-gradient(90deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        border: 1px solid #1e2d3d;
        border-radius: 6px;
        padding: 12px 24px;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .terminal-header .title {
        color: #58a6ff;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 2px;
    }
    .terminal-header .status {
        color: #8b949e;
        font-size: 12px;
        letter-spacing: 1px;
    }
    .terminal-header .live-dot {
        display: inline-block;
        width: 8px; height: 8px;
        background: #3fb950;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #1e2d3d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        color: #e6edf3 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stMetricDelta"] > div {
        font-family: 'JetBrains Mono', monospace !important;
    }
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: #0d1117;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #1e2d3d;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b949e;
        border-radius: 6px;
        padding: 8px 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #161b22 !important;
        color: #58a6ff !important;
        border: 1px solid #1e2d3d;
    }
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid #1e2d3d;
        border-radius: 8px;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #161b22;
        border: 1px solid #1e2d3d;
        border-radius: 6px;
        color: #8b949e;
    }
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ═══ Skeleton Loading: hide stale data, show grey placeholders ═══ */

    /* Kill default Streamlit fade */
    [data-stale="true"] {
        opacity: 1 !important;
    }

    /* ── Charts: overlay dark skeleton with grid lines + shimmer ── */
    [data-stale="true"] [data-testid="stPlotlyChart"] {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
    }
    [data-stale="true"] [data-testid="stPlotlyChart"]::before {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 900;
        border-radius: 8px;
        border: 1px solid #1e2d3d;
        background:
            /* faint horizontal grid lines */
            repeating-linear-gradient(
                to bottom,
                transparent 0px, transparent 47px,
                #1a2332 47px, #1a2332 48px
            ),
            /* faint vertical grid lines */
            repeating-linear-gradient(
                to right,
                transparent 0px, transparent 119px,
                #1a2332 119px, #1a2332 120px
            ),
            #0d1117;
    }
    [data-stale="true"] [data-testid="stPlotlyChart"]::after {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 901;
        border-radius: 8px;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(30, 45, 61, 0.45) 45%,
            rgba(45, 65, 85, 0.5) 50%,
            rgba(30, 45, 61, 0.45) 55%,
            transparent 100%
        );
        background-size: 200% 100%;
        animation: skel-shimmer 1.8s ease-in-out infinite;
        pointer-events: none;
    }

    /* ── Metric cards: blank out numbers, show grey bars ── */
    [data-stale="true"] [data-testid="stMetricValue"] > div {
        color: transparent !important;
        background: #1e2d3d !important;
        border-radius: 4px;
        animation: skel-pulse 1.8s ease-in-out infinite;
    }
    [data-stale="true"] [data-testid="stMetricDelta"] > div {
        color: transparent !important;
        background: #161b22 !important;
        border-radius: 4px;
        animation: skel-pulse 1.8s ease-in-out infinite 0.2s;
    }

    /* ── Dataframes: overlay skeleton ── */
    [data-stale="true"] [data-testid="stDataFrame"] {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
    }
    [data-stale="true"] [data-testid="stDataFrame"]::before {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 900;
        border-radius: 8px;
        border: 1px solid #1e2d3d;
        background:
            repeating-linear-gradient(
                to bottom,
                transparent 0px, transparent 35px,
                #1a2332 35px, #1a2332 36px
            ),
            #0d1117;
    }
    [data-stale="true"] [data-testid="stDataFrame"]::after {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 901;
        border-radius: 8px;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(30, 45, 61, 0.45) 45%,
            rgba(45, 65, 85, 0.5) 50%,
            rgba(30, 45, 61, 0.45) 55%,
            transparent 100%
        );
        background-size: 200% 100%;
        animation: skel-shimmer 1.8s ease-in-out infinite;
        pointer-events: none;
    }

    /* ── Markdown headings: subtle pulse ── */
    [data-stale="true"] [data-testid="stMarkdown"] h4,
    [data-stale="true"] [data-testid="stMarkdown"] h3 {
        color: transparent !important;
        background: #1e2d3d;
        border-radius: 4px;
        display: inline-block;
        min-width: 180px;
        animation: skel-pulse 1.8s ease-in-out infinite;
    }

    @keyframes skel-shimmer {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    @keyframes skel-pulse {
        0%, 100% { opacity: 0.35; }
        50%      { opacity: 0.7; }
    }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# Plotly dark template
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0d1117",
    font=dict(family="JetBrains Mono, Consolas, monospace", color="#c9d1d9", size=11),
    margin=dict(l=60, r=20, t=40, b=40),
)


def dark_chart(fig, **kwargs):
    """Render Plotly chart with dark terminal axis/legend defaults."""
    fig.update_xaxes(gridcolor="#1e2d3d", zerolinecolor="#1e2d3d")
    fig.update_yaxes(gridcolor="#1e2d3d", zerolinecolor="#1e2d3d")
    fig.update_layout(legend=dict(bgcolor="rgba(13,17,23,0.8)", bordercolor="#1e2d3d", borderwidth=1))
    st.plotly_chart(fig, **kwargs)

COLORS = {
    "blue": "#58a6ff", "green": "#3fb950", "red": "#f85149",
    "yellow": "#d29922", "purple": "#bc8cff", "orange": "#f0883e",
    "cyan": "#39d2c0", "gray": "#484f58", "white": "#e6edf3",
}


# =============================================================================
# DATA LOADING (cached)
# =============================================================================

@st.cache_data(show_spinner=False)
def load_asset(stem, timeframe):
    """Load a single asset CSV."""
    data_dir = HOURLY_DATA_DIR if timeframe == "Hourly" else TEST_DATA_DIR
    filepath = data_dir / f"{stem}.csv"
    if not filepath.exists():
        return None
    return load_csv_data(str(filepath))


@st.cache_data(show_spinner=False)
def get_available_assets(timeframe):
    """List available assets for a timeframe."""
    data_dir = HOURLY_DATA_DIR if timeframe == "Hourly" else TEST_DATA_DIR
    if not data_dir.exists():
        return []
    assets = []
    for f in sorted(data_dir.glob("*.csv")):
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        assets.append((stem, name, category))
    return assets


# =============================================================================
# CUSTOM STRATEGY (live parameter tuning)
# =============================================================================

def strategy_peak_shaver_custom(df, rsi_period=14, roc_period=21, z_window=50,
                                 rsi_t1=75, roc_t1=11, z_t1=1.0,
                                 rsi_t2=85, z_t2=3.0,
                                 trim_t1=0.40, trim_t2=0.30):
    """Peak Shaver with custom parameters from sidebar sliders."""
    bpd = _detect_bars_per_day(df)
    close = df["Close"]
    scale = max(1.0, bpd ** 0.4)

    rsi_val = rsi(close, max(rsi_period, int(rsi_period * scale)))
    mom_1m = roc(close, max(roc_period, int(roc_period * scale)))
    z = zscore(close, max(z_window, int(z_window * scale)))

    position = pd.Series(1.0, index=df.index)
    position[(rsi_val > rsi_t1) & (mom_1m > roc_t1) & (z > z_t1)] = trim_t1
    position[(rsi_val > rsi_t2) & (z > z_t2)] = trim_t2

    return position, {"position": position, "rsi": rsi_val, "mom_1m": mom_1m, "zscore": z}


# =============================================================================
# BACKTEST RUNNER (cached)
# =============================================================================

@st.cache_data(show_spinner=False)
def _run_backtest_cached(df_hash, df, strategy_name, initial_capital, commission,
                         rsi_period, roc_period, z_window,
                         rsi_t1, roc_t1, z_t1, rsi_t2, z_t2, trim_t1, trim_t2):
    """Cached backtest for non-ML strategies."""
    bt = Backtester(df, initial_capital=initial_capital, commission=commission)

    if strategy_name == "PSv1":
        positions, indicators = strategy_peak_shaver_v1(df)
        result = bt.run_positions(positions, strategy_name="Peak Shaver v1")
    elif strategy_name == "Custom":
        positions, indicators = strategy_peak_shaver_custom(
            df, rsi_period, roc_period, z_window,
            rsi_t1, roc_t1, z_t1, rsi_t2, z_t2, trim_t1, trim_t2,
        )
        result = bt.run_positions(positions, strategy_name="Custom PS")
    else:  # PSv2
        positions, indicators = strategy_peak_shaver(df)
        result = bt.run_positions(positions, strategy_name="Peak Shaver v2")

    result["positions"] = positions
    result["indicators"] = indicators
    return result


def run_backtest(df_hash, df, strategy_name, initial_capital=10000, commission=0.0,
                 rsi_period=14, roc_period=21, z_window=50,
                 rsi_t1=75, roc_t1=11.0, z_t1=1.0,
                 rsi_t2=85, z_t2=3.0, trim_t1=0.40, trim_t2=0.30):
    """Run backtest. ML runs uncached (session-state models), rest cached."""
    if strategy_name == "ML" and ML_AVAILABLE:
        models = st.session_state.get("ml_models")
        bt = Backtester(df, initial_capital=initial_capital, commission=commission)
        if models is None:
            positions, indicators = strategy_peak_shaver(df)
            result = bt.run_positions(positions, strategy_name="ML (untrained → PSv2)")
        else:
            positions, indicators = strategy_ml_peak_shaver(df, models)
            result = bt.run_positions(positions, strategy_name="ML Peak Shaver")
        result["positions"] = positions
        result["indicators"] = indicators
        return result

    return _run_backtest_cached(
        df_hash, df, strategy_name, initial_capital, commission,
        rsi_period, roc_period, z_window,
        rsi_t1, roc_t1, z_t1, rsi_t2, z_t2, trim_t1, trim_t2,
    )


@st.cache_data(show_spinner="Scanning all assets...")
def run_all_assets_scan(timeframe, initial_capital, commission):
    """Run PSv2 on all assets. Returns list of result dicts (without equity curves for caching)."""
    data_dir = HOURLY_DATA_DIR if timeframe == "Hourly" else TEST_DATA_DIR
    csv_files = sorted(Path(data_dir).glob("*.csv"))
    results = []
    for f in csv_files:
        stem = f.stem
        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        try:
            df = load_csv_data(str(f))
            if len(df) < 100:
                continue
            bt = Backtester(df, initial_capital=initial_capital, commission=commission)
            pos, _ = strategy_peak_shaver(df)
            r = bt.run_positions(pos, strategy_name=stem)
            results.append({
                "Asset": stem, "Name": name, "Category": category,
                "Return %": r["total_return_pct"],
                "B&H %": r["buy_and_hold_return_pct"],
                "Alpha %": round(r["total_return_pct"] - r["buy_and_hold_return_pct"], 2),
                "Sharpe": r["sharpe_ratio"],
                "Sortino": r["sortino_ratio"],
                "Max DD %": r["max_drawdown_pct"],
                "Calmar": r["calmar_ratio"],
                "Trades": r["num_trades"],
            })
        except Exception:
            pass
    return results


@st.cache_resource(show_spinner="Training ML models...")
def get_ml_models(timeframe):
    """Train ML models (cached per session)."""
    if not ML_AVAILABLE:
        return None
    data_dir = HOURLY_DATA_DIR if timeframe == "Hourly" else TEST_DATA_DIR
    return train_ml_models(data_dir)


# =============================================================================
# HELPER: hash dataframe for caching
# =============================================================================

def df_hash(df):
    """Quick hash for cache key."""
    return f"{len(df)}_{df.index[0]}_{df.index[-1]}_{df['Close'].iloc[-1]:.4f}"


# =============================================================================
# TERMINAL HEADER
# =============================================================================

def render_header():
    n_assets = len(get_available_assets("Daily"))
    ml_status = "ML READY" if ML_AVAILABLE else "ML N/A"
    st.markdown(f"""
    <div class="terminal-header">
        <div>
            <span class="title">PEAK SHAVER</span>
            <span style="color:#8b949e; font-size:14px; margin-left:8px;">|</span>
            <span style="color:#8b949e; font-size:14px; margin-left:8px;">Quantitative Trading Terminal</span>
        </div>
        <div class="status">
            <span class="live-dot"></span>LIVE
            <span style="margin-left:16px;">{ml_status}</span>
            <span style="margin-left:16px;">{n_assets} ASSETS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙ Controls")

        timeframe = st.radio("Timeframe", ["Daily", "Hourly"], horizontal=True,
                             help="Daily: 10yr history | Hourly: 2yr history")

        assets = get_available_assets(timeframe)
        if not assets:
            st.warning("No data found. Run `python trading_bot.py` first to download.")
            st.stop()

        # Group by category
        categories = sorted(set(a[2] for a in assets))
        options = []
        for cat in categories:
            for stem, name, c in assets:
                if c == cat:
                    options.append(f"[{cat}] {stem} — {name}")

        selected = st.selectbox("Asset", options, index=0,
                                help="Select asset to analyze")
        stem = selected.split("] ")[1].split(" —")[0].strip()

        strat_options = ["PSv2", "PSv1", "Custom"]
        if ML_AVAILABLE:
            strat_options.insert(2, "ML")
        strategy = st.radio("Strategy", strat_options,
                            horizontal=True,
                            help="PSv1: dual-confirm | PSv2: triple-confirm | ML: ensemble-adjusted | Custom: live tuning")

        compare = st.checkbox("Compare all strategies + B&H",
                              help="Overlay PSv1, PSv2, and B&H on charts")

        # ML: auto-train if not yet trained
        if strategy == "ML" and st.session_state.get("ml_models") is None:
            if st.button("Train ML Models", type="primary", key="train_ml_sidebar"):
                st.session_state["ml_models"] = get_ml_models(timeframe)
                st.session_state["ml_trained"] = True
                st.rerun()
            else:
                st.caption("ML selected — train models first to see ML positions.")

        # Custom parameters
        params = {}
        if strategy == "Custom":
            with st.expander("Parameters", expanded=True):
                params["rsi_period"] = st.slider("RSI Period", 5, 30, 14)
                params["roc_period"] = st.slider("ROC Period", 5, 50, 21)
                params["z_window"] = st.slider("Z-Score Window", 20, 100, 50)
                st.markdown("**Tier 1 Thresholds**")
                params["rsi_t1"] = st.slider("RSI T1", 50, 90, 75)
                params["roc_t1"] = st.slider("ROC T1 %", 0.0, 30.0, 11.0, 0.5)
                params["z_t1"] = st.slider("Z-Score T1", 0.0, 3.0, 1.0, 0.1)
                params["trim_t1"] = st.slider("Trim T1", 0.0, 1.0, 0.40, 0.05)
                st.markdown("**Tier 2 Thresholds**")
                params["rsi_t2"] = st.slider("RSI T2", 60, 99, 85)
                params["z_t2"] = st.slider("Z-Score T2", 1.0, 5.0, 3.0, 0.1)
                params["trim_t2"] = st.slider("Trim T2", 0.0, 1.0, 0.30, 0.05)

        with st.expander("Backtest Settings"):
            initial_capital = st.number_input("Initial Capital $", 1000, 1_000_000, 10_000, 1000)
            commission_pct = st.number_input("Commission %", 0.0, 1.0, 0.0, 0.01)

        return {
            "timeframe": timeframe,
            "stem": stem,
            "strategy": strategy,
            "compare": compare,
            "params": params,
            "initial_capital": initial_capital,
            "commission": commission_pct / 100,
        }


# =============================================================================
# TAB 1: SINGLE ASSET ANALYSIS
# =============================================================================

def render_tab_single(cfg):
    df = load_asset(cfg["stem"], cfg["timeframe"])
    if df is None:
        st.error(f"Could not load {cfg['stem']}")
        return

    name, category = TICKER_INFO.get(cfg["stem"], (cfg["stem"], "Other"))
    h = df_hash(df)

    # Run primary strategy
    result = run_backtest(
        h, df, cfg["strategy"], cfg["initial_capital"], cfg["commission"],
        **cfg["params"],
    )

    # B&H reference values
    bnh_ret = result["buy_and_hold_return_pct"]

    # ---- KPI Row ----
    cols = st.columns(6)
    cols[0].metric("Total Return", f"{result['total_return_pct']:+.2f}%",
                   delta=f"{result['total_return_pct'] - bnh_ret:+.2f}% vs B&H")
    cols[1].metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
    cols[2].metric("Sortino Ratio", f"{result['sortino_ratio']:.2f}")
    cols[3].metric("Max Drawdown", f"{result['max_drawdown_pct']:.2f}%")
    cols[4].metric("Calmar Ratio", f"{result['calmar_ratio']:.2f}")
    cols[5].metric("Trades", f"{result['num_trades']}")

    # ---- Main 5-Row Chart ----
    close = df["Close"]
    regime = detect_regime(df)

    # Indicators
    sma_50 = sma(close, 50)
    sma_200 = sma(close, 200)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close)
    rsi_val = rsi(close, 14)
    macd_line, signal_line, macd_hist = macd_indicator(close)

    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        row_heights=[0.40, 0.10, 0.15, 0.15, 0.15],
        vertical_spacing=0.02,
        subplot_titles=["", "Position Size", "RSI (14)", "MACD", "Volume"],
    )

    # Row 1: Candlestick + overlays
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC", increasing_line_color=COLORS["green"],
        decreasing_line_color=COLORS["red"],
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=sma_50, name="SMA 50",
                             line=dict(color=COLORS["yellow"], width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sma_200, name="SMA 200",
                             line=dict(color=COLORS["purple"], width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_upper, name="BB Upper",
                             line=dict(color=COLORS["gray"], width=0.5), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_lower, name="BB Lower",
                             line=dict(color=COLORS["gray"], width=0.5),
                             fill="tonexty", fillcolor="rgba(88,166,255,0.05)",
                             showlegend=False), row=1, col=1)

    # Regime vrects
    prev_r, start_i = None, 0
    regime_colors = {1: "rgba(63,185,80,0.08)", -1: "rgba(248,81,73,0.08)", 0: "rgba(0,0,0,0)"}
    for i in range(len(regime)):
        r = regime.iloc[i]
        if r != prev_r and prev_r is not None and prev_r != 0:
            fig.add_vrect(x0=regime.index[start_i], x1=regime.index[i-1],
                          fillcolor=regime_colors.get(prev_r, "rgba(0,0,0,0)"),
                          layer="below", line_width=0, row=1, col=1)
            start_i = i
        elif r != prev_r:
            start_i = i
        prev_r = r

    # Trade markers from trade log
    tlog = result["trade_log"]
    if not tlog.empty:
        buys = tlog[tlog["action"] == "BUY"]
        sells = tlog[tlog["action"].isin(["SELL", "TRAIL_STOP", "CIRCUIT_BREAK"])]
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys["date"], y=buys["price"], mode="markers", name="Buy",
                marker=dict(symbol="triangle-up", size=10, color=COLORS["green"]),
            ), row=1, col=1)
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells["date"], y=sells["price"], mode="markers", name="Sell",
                marker=dict(symbol="triangle-down", size=10, color=COLORS["red"]),
            ), row=1, col=1)

    # Row 2: Position size
    positions = result["positions"]
    fig.add_trace(go.Scatter(
        x=df.index, y=positions * 100, fill="tozeroy", name="Position %",
        line=dict(color=COLORS["cyan"], width=1),
        fillcolor="rgba(57,210,192,0.2)",
    ), row=2, col=1)

    # Row 3: RSI
    fig.add_trace(go.Scatter(x=df.index, y=rsi_val, name="RSI",
                             line=dict(color=COLORS["purple"], width=1)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"], line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"], line_width=0.8, row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", line_width=0, row=3, col=1)

    # Row 4: MACD
    colors_macd = [COLORS["green"] if v >= 0 else COLORS["red"] for v in macd_hist]
    fig.add_trace(go.Bar(x=df.index, y=macd_hist, name="MACD Hist",
                         marker_color=colors_macd, opacity=0.5), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_line, name="MACD",
                             line=dict(color=COLORS["blue"], width=1)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=signal_line, name="Signal",
                             line=dict(color=COLORS["orange"], width=1)), row=4, col=1)

    # Row 5: Volume
    vol_colors = [COLORS["green"] if close.iloc[i] >= close.iloc[max(0, i-1)]
                  else COLORS["red"] for i in range(len(close))]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                         marker_color=vol_colors, opacity=0.6), row=5, col=1)

    fig.update_layout(
        height=900, **PLOTLY_LAYOUT,
        title=dict(text=f"{cfg['stem']} — {name} [{category}]", font=dict(size=16, color=COLORS["blue"])),
        xaxis_rangeslider_visible=False,
        showlegend=True,
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(range=[0, 105], row=3, col=1)

    dark_chart(fig, use_container_width=True)

    # ---- Equity Curve + Drawdown ----
    st.markdown("---")
    col_eq, col_dd = st.columns(2)

    with col_eq:
        fig_eq = go.Figure()
        # Strategy equity
        eq = result["equity_curve"]
        fig_eq.add_trace(go.Scatter(
            x=eq.index, y=eq, name=result["strategy_name"],
            line=dict(color=COLORS["blue"], width=2),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.1)",
        ))
        # B&H equity
        bnh_eq = cfg["initial_capital"] * (close / close.iloc[0])
        fig_eq.add_trace(go.Scatter(
            x=bnh_eq.index, y=bnh_eq, name="Buy & Hold",
            line=dict(color=COLORS["gray"], width=1.5, dash="dash"),
        ))

        # Compare mode
        if cfg["compare"] and cfg["strategy"] != "PSv1":
            r_v1 = run_backtest(h, df, "PSv1", cfg["initial_capital"], cfg["commission"])
            fig_eq.add_trace(go.Scatter(
                x=r_v1["equity_curve"].index, y=r_v1["equity_curve"], name="PSv1",
                line=dict(color=COLORS["yellow"], width=1, dash="dot"),
            ))
        if cfg["compare"] and cfg["strategy"] != "PSv2":
            r_v2 = run_backtest(h, df, "PSv2", cfg["initial_capital"], cfg["commission"])
            fig_eq.add_trace(go.Scatter(
                x=r_v2["equity_curve"].index, y=r_v2["equity_curve"], name="PSv2",
                line=dict(color=COLORS["green"], width=1, dash="dot"),
            ))

        fig_eq.update_layout(
            height=350, **PLOTLY_LAYOUT,
            title=dict(text="Equity Curve", font=dict(size=14, color=COLORS["white"])),
        )
        dark_chart(fig_eq, use_container_width=True)

    with col_dd:
        fig_dd = go.Figure()
        dd = result["drawdown"]
        fig_dd.add_trace(go.Scatter(
            x=dd.index, y=dd * 100, name=result["strategy_name"],
            fill="tozeroy", line=dict(color=COLORS["red"], width=1),
            fillcolor="rgba(248,81,73,0.2)",
        ))

        if cfg["compare"] and cfg["strategy"] != "PSv1":
            dd_v1 = run_backtest(h, df, "PSv1", cfg["initial_capital"], cfg["commission"])["drawdown"]
            fig_dd.add_trace(go.Scatter(
                x=dd_v1.index, y=dd_v1 * 100, name="PSv1",
                line=dict(color=COLORS["yellow"], width=1, dash="dot"),
            ))
        if cfg["compare"] and cfg["strategy"] != "PSv2":
            dd_v2 = run_backtest(h, df, "PSv2", cfg["initial_capital"], cfg["commission"])["drawdown"]
            fig_dd.add_trace(go.Scatter(
                x=dd_v2.index, y=dd_v2 * 100, name="PSv2",
                line=dict(color=COLORS["green"], width=1, dash="dot"),
            ))

        # B&H drawdown
        bnh_dd = (bnh_eq / bnh_eq.cummax() - 1) * 100
        fig_dd.add_trace(go.Scatter(
            x=bnh_dd.index, y=bnh_dd, name="B&H",
            line=dict(color=COLORS["gray"], width=1, dash="dash"),
        ))

        fig_dd.update_layout(
            height=350, **PLOTLY_LAYOUT,
            title=dict(text="Drawdown", font=dict(size=14, color=COLORS["white"])),
            yaxis_title="Drawdown %",
        )
        dark_chart(fig_dd, use_container_width=True)


# =============================================================================
# TAB 2: CROSS-ASSET SCANNER
# =============================================================================

def render_tab_scanner(cfg):
    results = run_all_assets_scan(cfg["timeframe"], cfg["initial_capital"], cfg["commission"])

    if not results:
        st.warning("No results. Ensure data is downloaded.")
        return

    rdf = pd.DataFrame(results)

    # Summary bar
    beats = (rdf["Return %"] > rdf["B&H %"]).sum()
    total = len(rdf)
    avg_alpha = rdf["Alpha %"].mean()
    avg_sharpe = rdf["Sharpe"].mean()

    cols = st.columns(4)
    cols[0].metric("Assets Tested", total)
    cols[1].metric("Beat Rate", f"{beats}/{total} ({beats/total*100:.0f}%)")
    cols[2].metric("Avg Alpha", f"{avg_alpha:+.2f}%")
    cols[3].metric("Avg Sharpe", f"{avg_sharpe:.2f}")

    # Heatmap
    st.markdown("#### Performance Heatmap")
    metric_cols = ["Return %", "Alpha %", "Sharpe", "Sortino", "Max DD %", "Calmar"]
    heatmap_data = rdf.set_index("Asset")[metric_cols]

    # Normalize each column to 0-1 for heatmap
    normalized = heatmap_data.copy()
    for col in metric_cols:
        mn, mx = normalized[col].min(), normalized[col].max()
        if mx != mn:
            normalized[col] = (normalized[col] - mn) / (mx - mn)
        else:
            normalized[col] = 0.5

    fig_hm = go.Figure(go.Heatmap(
        z=normalized.values,
        x=metric_cols,
        y=[f"[{rdf.iloc[i]['Category']}] {rdf.iloc[i]['Asset']}" for i in range(len(rdf))],
        text=heatmap_data.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=9),
        colorscale="RdYlGn",
        showscale=False,
    ))
    fig_hm.update_layout(
        height=max(400, len(rdf) * 22), **PLOTLY_LAYOUT,
        yaxis=dict(autorange="reversed"),
    )
    dark_chart(fig_hm, use_container_width=True)

    # Category bar chart
    st.markdown("#### Average Return by Category")
    cat_stats = rdf.groupby("Category").agg(
        avg_return=("Return %", "mean"),
        avg_bnh=("B&H %", "mean"),
        avg_alpha=("Alpha %", "mean"),
        count=("Asset", "count"),
    ).reset_index()

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        x=cat_stats["Category"], y=cat_stats["avg_return"],
        name="Strategy", marker_color=COLORS["blue"], opacity=0.8,
    ))
    fig_cat.add_trace(go.Bar(
        x=cat_stats["Category"], y=cat_stats["avg_bnh"],
        name="Buy & Hold", marker_color=COLORS["gray"], opacity=0.6,
    ))
    fig_cat.update_layout(
        height=350, **PLOTLY_LAYOUT, barmode="group",
        title=dict(text="Avg Return: Strategy vs B&H by Category", font=dict(size=14)),
        yaxis_title="Return %",
    )
    dark_chart(fig_cat, use_container_width=True)

    # Full results table
    st.markdown("#### Full Results")

    def highlight_row(row):
        if row["Alpha %"] > 0:
            return ["background-color: rgba(63,185,80,0.15)"] * len(row)
        elif row["Alpha %"] < 0:
            return ["background-color: rgba(248,81,73,0.1)"] * len(row)
        return [""] * len(row)

    st.dataframe(
        rdf.sort_values("Alpha %", ascending=False).style.apply(highlight_row, axis=1).format({
            "Return %": "{:+.2f}", "B&H %": "{:+.2f}", "Alpha %": "{:+.2f}",
            "Sharpe": "{:.2f}", "Sortino": "{:.2f}", "Max DD %": "{:.2f}", "Calmar": "{:.2f}",
        }),
        use_container_width=True, height=600,
    )


# =============================================================================
# TAB 3: ML INTELLIGENCE
# =============================================================================

def render_tab_ml(cfg):
    if not ML_AVAILABLE:
        st.warning("ML not available. Install: `pip install xgboost scikit-learn`")
        return

    st.markdown("#### ML Model Training")
    if st.button("Train ML Models", type="primary", key="train_ml_tab"):
        st.session_state["ml_models"] = get_ml_models(cfg["timeframe"])
        st.session_state["ml_trained"] = True

    if not st.session_state.get("ml_trained"):
        st.info("Click 'Train ML Models' to train the ensemble on all assets.")
        return

    models = st.session_state.get("ml_models")
    if models is None:
        st.error("Training failed.")
        return

    # Load current asset
    df = load_asset(cfg["stem"], cfg["timeframe"])
    if df is None:
        st.error("Could not load asset.")
        return

    name, category = TICKER_INFO.get(cfg["stem"], (cfg["stem"], "Other"))
    h = df_hash(df)

    # Run PSv2 and ML
    bt = Backtester(df, initial_capital=cfg["initial_capital"], commission=cfg["commission"])
    ps_pos, _ = strategy_peak_shaver(df)
    ps_result = bt.run_positions(ps_pos, strategy_name="Peak Shaver v2")

    ml_pos, ml_indicators = strategy_ml_peak_shaver(df, models, asset_category=category)
    ml_result = bt.run_positions(ml_pos, strategy_name="ML Peak Shaver")

    # Metric comparison
    st.markdown("#### PSv2 vs ML Peak Shaver")
    cols = st.columns(6)
    metrics = [
        ("Return %", "total_return_pct"), ("Sharpe", "sharpe_ratio"),
        ("Sortino", "sortino_ratio"), ("Max DD %", "max_drawdown_pct"),
        ("Calmar", "calmar_ratio"), ("Trades", "num_trades"),
    ]
    for i, (label, key) in enumerate(metrics):
        ps_v = ps_result[key]
        ml_v = ml_result[key]
        delta = ml_v - ps_v
        fmt = f"{ml_v:+.2f}" if isinstance(ml_v, float) else str(ml_v)
        delta_fmt = f"{delta:+.2f}" if isinstance(delta, float) else str(int(delta))
        cols[i].metric(f"ML {label}", fmt, delta=f"{delta_fmt} vs PSv2")

    # Feature importance
    st.markdown("#### Feature Importance (Top 15)")
    features = build_features(df, asset_category=category)
    xgb_model = models[0]
    feat_names = models[3]
    importances = pd.Series(xgb_model.feature_importances_, index=feat_names).sort_values(ascending=True)
    top15 = importances.tail(15)

    fig_fi = go.Figure(go.Bar(
        x=top15.values, y=top15.index, orientation="h",
        marker_color=COLORS["cyan"], opacity=0.8,
    ))
    fig_fi.update_layout(
        height=400, **PLOTLY_LAYOUT,
        title=dict(text="XGBoost Feature Importance", font=dict(size=14)),
        xaxis_title="Importance",
    )
    dark_chart(fig_fi, use_container_width=True)

    # Position overlay: PSv2 vs ML
    st.markdown("#### Position Overlay: PSv2 vs ML")
    fig_po = go.Figure()
    fig_po.add_trace(go.Scatter(
        x=df.index, y=ps_pos * 100, name="PSv2 Position",
        line=dict(color=COLORS["yellow"], width=1),
    ))
    fig_po.add_trace(go.Scatter(
        x=df.index, y=ml_pos * 100, name="ML Position",
        line=dict(color=COLORS["cyan"], width=2),
    ))

    # Highlight overrides
    overrides = (ml_pos != ps_pos) & (ps_pos < 1.0)
    if overrides.any():
        override_idx = df.index[overrides]
        fig_po.add_trace(go.Scatter(
            x=override_idx, y=ml_pos[overrides] * 100, mode="markers",
            name="ML Override", marker=dict(color=COLORS["orange"], size=5, symbol="diamond"),
        ))

    fig_po.update_layout(
        height=300, **PLOTLY_LAYOUT,
        title=dict(text=f"{cfg['stem']} — Position Size Comparison", font=dict(size=14)),
        yaxis_title="Position %", yaxis_range=[0, 110],
    )
    dark_chart(fig_po, use_container_width=True)

    # Equity comparison
    st.markdown("#### Equity Comparison")
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=ps_result["equity_curve"].index, y=ps_result["equity_curve"],
        name="PSv2", line=dict(color=COLORS["yellow"], width=1.5),
    ))
    fig_eq.add_trace(go.Scatter(
        x=ml_result["equity_curve"].index, y=ml_result["equity_curve"],
        name="ML Peak Shaver", line=dict(color=COLORS["cyan"], width=2),
    ))
    bnh_eq = cfg["initial_capital"] * (df["Close"] / df["Close"].iloc[0])
    fig_eq.add_trace(go.Scatter(
        x=bnh_eq.index, y=bnh_eq, name="B&H",
        line=dict(color=COLORS["gray"], width=1, dash="dash"),
    ))
    fig_eq.update_layout(
        height=350, **PLOTLY_LAYOUT,
        title=dict(text="Equity Curves", font=dict(size=14)),
        yaxis_title="Portfolio Value ($)",
    )
    dark_chart(fig_eq, use_container_width=True)


# =============================================================================
# TAB 4: PORTFOLIO BUILDER
# =============================================================================

def render_tab_portfolio(cfg):
    assets = get_available_assets(cfg["timeframe"])
    asset_options = [f"{stem} — {name}" for stem, name, cat in assets]

    # Default picks
    default_stems = ["SPY", "QQQ", "AAPL", "GLD", "BTC_USD"]
    default_indices = []
    for ds in default_stems:
        for i, (stem, name, cat) in enumerate(assets):
            if stem == ds:
                default_indices.append(i)
                break

    selected = st.multiselect(
        "Select Portfolio Assets",
        asset_options,
        default=[asset_options[i] for i in default_indices] if default_indices else asset_options[:5],
        help="Equal-weight portfolio of selected assets",
    )

    if len(selected) < 2:
        st.info("Select at least 2 assets.")
        return

    stems = [s.split(" —")[0].strip() for s in selected]

    # Load data and run backtests
    portfolio_eq = None
    bnh_eq = None
    returns_dict = {}
    asset_results = []

    for stem in stems:
        df = load_asset(stem, cfg["timeframe"])
        if df is None:
            continue

        name, category = TICKER_INFO.get(stem, (stem, "Other"))
        bt = Backtester(df, initial_capital=cfg["initial_capital"], commission=cfg["commission"])
        pos, _ = strategy_peak_shaver(df)
        r = bt.run_positions(pos, strategy_name=stem)

        # Normalize to starting capital
        eq_norm = r["equity_curve"] / cfg["initial_capital"]
        bnh_norm = df["Close"] / df["Close"].iloc[0]

        if portfolio_eq is None:
            portfolio_eq = eq_norm
            bnh_eq = bnh_norm
        else:
            # Align dates and sum (equal weight)
            portfolio_eq = portfolio_eq.add(eq_norm, fill_value=0)
            bnh_eq = bnh_eq.add(bnh_norm, fill_value=0)

        returns_dict[stem] = df["Close"].pct_change().dropna()
        asset_results.append({"Asset": stem, "Name": name, **{
            k: r[k] for k in ["total_return_pct", "sharpe_ratio", "sortino_ratio",
                               "max_drawdown_pct", "calmar_ratio"]
        }})

    if portfolio_eq is None:
        st.warning("No valid data.")
        return

    # Average for equal weight
    n = len(stems)
    portfolio_eq = portfolio_eq / n * cfg["initial_capital"]
    bnh_eq = bnh_eq / n * cfg["initial_capital"]

    # Portfolio metrics
    port_ret = (portfolio_eq.iloc[-1] / cfg["initial_capital"] - 1) * 100
    bnh_ret = (bnh_eq.iloc[-1] / cfg["initial_capital"] - 1) * 100
    port_daily = portfolio_eq.pct_change().dropna()
    port_sharpe = (port_daily.mean() / port_daily.std()) * np.sqrt(252) if port_daily.std() > 0 else 0
    port_dd = (portfolio_eq / portfolio_eq.cummax() - 1).min() * 100

    cols = st.columns(4)
    cols[0].metric("Portfolio Return", f"{port_ret:+.2f}%", delta=f"{port_ret - bnh_ret:+.2f}% vs B&H")
    cols[1].metric("B&H Return", f"{bnh_ret:+.2f}%")
    cols[2].metric("Portfolio Sharpe", f"{port_sharpe:.2f}")
    cols[3].metric("Portfolio Max DD", f"{port_dd:.2f}%")

    # Combined equity curve
    st.markdown("#### Portfolio Equity Curve")
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=portfolio_eq.index, y=portfolio_eq, name="Strategy Portfolio",
        line=dict(color=COLORS["blue"], width=2),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.1)",
    ))
    fig_eq.add_trace(go.Scatter(
        x=bnh_eq.index, y=bnh_eq, name="B&H Portfolio",
        line=dict(color=COLORS["gray"], width=1.5, dash="dash"),
    ))
    fig_eq.update_layout(
        height=400, **PLOTLY_LAYOUT,
        title=dict(text=f"Equal-Weight Portfolio ({n} assets)", font=dict(size=14)),
        yaxis_title="Portfolio Value ($)",
    )
    dark_chart(fig_eq, use_container_width=True)

    # Correlation heatmap
    col_corr, col_table = st.columns(2)

    with col_corr:
        st.markdown("#### Return Correlations")
        if returns_dict:
            ret_df = pd.DataFrame(returns_dict).dropna()
            corr = ret_df.corr()
            fig_corr = go.Figure(go.Heatmap(
                z=corr.values, x=corr.columns, y=corr.index,
                text=corr.values.round(2), texttemplate="%{text}",
                colorscale="RdBu_r", zmid=0, showscale=True,
                textfont=dict(size=10),
            ))
            fig_corr.update_layout(
                height=400, **PLOTLY_LAYOUT,
                title=dict(text="Pairwise Correlation", font=dict(size=14)),
            )
            dark_chart(fig_corr, use_container_width=True)

    with col_table:
        st.markdown("#### Asset Metrics")
        if asset_results:
            adf = pd.DataFrame(asset_results)
            adf.columns = ["Asset", "Name", "Return %", "Sharpe", "Sortino", "Max DD %", "Calmar"]
            st.dataframe(adf.sort_values("Sharpe", ascending=False), use_container_width=True, height=400)


# =============================================================================
# MAIN
# =============================================================================

def main():
    render_header()
    cfg = render_sidebar()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Single Asset",
        "🔍 Cross-Asset Scanner",
        "🤖 ML Intelligence",
        "📦 Portfolio Builder",
    ])

    with tab1:
        render_tab_single(cfg)

    with tab2:
        render_tab_scanner(cfg)

    with tab3:
        render_tab_ml(cfg)

    with tab4:
        render_tab_portfolio(cfg)


if __name__ == "__main__":
    main()
