"""Quick parameter sweep to find optimal thresholds, especially for XOM."""

import pandas as pd
import numpy as np
import importlib.util
import itertools

# Load strategy module functions
spec = importlib.util.spec_from_file_location("strategy", "submissions/strategy.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TRADING_DAYS = 252
TRANSACTION_COST = 0.0005


def load_data(filepath):
    probe = pd.read_csv(filepath, nrows=5, header=None)
    if probe.iloc[0, 0] == "Price":
        df = pd.read_csv(filepath, header=[0, 1], index_col=0, parse_dates=True)
        df.columns = df.columns.get_level_values(0)
    else:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"
    return df.ffill().dropna()


def backtest_signals(data, signals):
    returns = data["Close"].pct_change()
    shifted = signals.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    r, s = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = s.diff().abs().fillna(0) * TRANSACTION_COST
    strat_r = s * r - costs
    vol = np.std(strat_r)
    sharpe = (np.mean(strat_r) / vol) * np.sqrt(TRADING_DAYS) if vol > 1e-8 else 0.0
    total = (1 + strat_r).prod() - 1
    trades = int(s.diff().abs().fillna(0).gt(0).sum())
    return sharpe, total, trades


def make_signals(data, rsi_thresh=75, roc_thresh=11, z_thresh=1.0,
                 blowoff_rsi=85, blowoff_z=3.0, enable_short=True,
                 adx_thresh=25, vol_thresh=2.5, oversold_rsi=30, oversold_z=-1.5,
                 min_hold=3):
    close = data["Close"]
    n = len(data)
    rsi_val = mod.rsi(close, 14)
    roc_val = mod.roc(close, 21)
    z = mod.zscore(close, 50)
    adx_val, plus_di, minus_di = mod.adx(data, 14)
    atr_val = mod.atr(data, 14)
    atr_63 = atr_val.rolling(63).mean()
    sma_200 = mod.sma(close, 200)

    signal = pd.Series(1, index=data.index)

    # Peak shaver
    overbought = (rsi_val > rsi_thresh) & (roc_val > roc_thresh) & (z > z_thresh)
    signal[overbought] = 0

    # Blow-off shorts
    if enable_short:
        blowoff = (rsi_val > blowoff_rsi) & (z > blowoff_z)
        signal[blowoff] = -1

    # Bearish regime
    bearish = (adx_val > adx_thresh) & (minus_di > plus_di) & (close < sma_200)
    signal[bearish] = 0

    # Vol spike
    vol_ratio = atr_val / atr_63.replace(0, np.nan)
    signal[(vol_ratio > vol_thresh) & (signal == 1)] = 0

    # Oversold recovery
    signal[(rsi_val < oversold_rsi) & (z < oversold_z)] = 1

    # Warmup
    signal.iloc[:200] = 1

    # Hysteresis
    values = signal.values.copy()
    last_change_idx = -min_hold
    for i in range(1, n):
        if values[i] != values[i - 1]:
            if i - last_change_idx >= min_hold:
                last_change_idx = i
            else:
                values[i] = values[i - 1]
    signal = pd.Series(values, index=data.index).fillna(1).astype(int)
    return signal


# Load data
tickers = {"SPY": "data/spy.csv", "QQQ": "data/qqq.csv", "XOM": "data/xom.csv"}
datasets = {t: load_data(p) for t, p in tickers.items()}

# Parameter grid
configs = [
    # Round 3: final combos
    ("vol1.5+noshort", {"vol_thresh": 1.5, "enable_short": False}),
    ("vol1.5+tpeak", {"vol_thresh": 1.5, "rsi_thresh": 70, "roc_thresh": 8, "z_thresh": 0.8}),
    ("tpeak+noshort", {"vol_thresh": 1.5, "rsi_thresh": 70, "roc_thresh": 8, "z_thresh": 0.8, "enable_short": False}),
    ("tpeak+ns+h5", {"vol_thresh": 1.5, "rsi_thresh": 70, "roc_thresh": 8, "z_thresh": 0.8, "enable_short": False, "min_hold": 5}),
    ("tpeak+ns+h4", {"vol_thresh": 1.5, "rsi_thresh": 70, "roc_thresh": 8, "z_thresh": 0.8, "enable_short": False, "min_hold": 4}),
    ("v1.5+rsi72+r9", {"vol_thresh": 1.5, "rsi_thresh": 72, "roc_thresh": 9, "z_thresh": 0.9, "enable_short": False}),
    ("v1.5+rsi68+r7", {"vol_thresh": 1.5, "rsi_thresh": 68, "roc_thresh": 7, "z_thresh": 0.7, "enable_short": False}),
]

print(f"{'Config':<20} {'SPY':>8} {'QQQ':>8} {'XOM':>8} {'Avg':>8} | {'SPY tr':>6} {'QQQ tr':>6} {'XOM tr':>6}")
print("-" * 88)

for name, kwargs in configs:
    sharpes = {}
    trade_counts = {}
    for t, data in datasets.items():
        sig = make_signals(data, **kwargs)
        sh, tot, tr = backtest_signals(data, sig)
        sharpes[t] = sh
        trade_counts[t] = tr
    avg = np.mean(list(sharpes.values()))
    print(f"{name:<20} {sharpes['SPY']:>8.2f} {sharpes['QQQ']:>8.2f} {sharpes['XOM']:>8.2f} {avg:>8.2f} | {trade_counts['SPY']:>6} {trade_counts['QQQ']:>6} {trade_counts['XOM']:>6}")
