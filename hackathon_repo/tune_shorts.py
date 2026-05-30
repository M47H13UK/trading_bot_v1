"""Tune shorting variants — can we profit from going -1 during bearish/vol regimes?"""

import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, "submissions")
import strategy as s

TRADING_DAYS = 252
TRANSACTION_COST = 0.0005
DATA_DIR = "../test_data/daily"


def load_data(filepath):
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"
    return df.ffill().dropna()


def backtest_signals(data, signals):
    returns = data["Close"].pct_change()
    shifted = signals.shift(1)
    aligned = pd.concat([returns, shifted], axis=1).dropna()
    r, pos = aligned.iloc[:, 0], aligned.iloc[:, 1]
    costs = pos.diff().abs().fillna(0) * TRANSACTION_COST
    strat_r = pos * r - costs
    vol = np.std(strat_r)
    sharpe = (np.mean(strat_r) / vol) * np.sqrt(TRADING_DAYS) if vol > 1e-8 else 0.0
    total = (1 + strat_r).prod() - 1
    trades = int(pos.diff().abs().fillna(0).gt(0).sum())
    return sharpe, total, trades


def make_signals(data, short_bear=False, short_vol=False, short_blowoff=True,
                 vol_thresh=1.5, rsi_thresh=70, roc_thresh=8, z_thresh=0.8):
    close = data["Close"]
    n = len(data)
    rsi_val = s.rsi(close, 14)
    roc_val = s.roc(close, 21)
    z = s.zscore(close, 50)
    adx_val, plus_di, minus_di = s.adx(data, 14)
    atr_val = s.atr(data, 14)
    atr_63 = atr_val.rolling(63).mean()
    sma_200 = s.sma(close, 200)

    signal = pd.Series(1, index=data.index)

    # Peak shaver
    signal[(rsi_val > rsi_thresh) & (roc_val > roc_thresh) & (z > z_thresh)] = 0

    # Blow-off shorts
    if short_blowoff:
        signal[(rsi_val > 85) & (z > 3.0)] = -1

    # Bearish regime
    bearish = (adx_val > 25) & (minus_di > plus_di) & (close < sma_200)
    signal[bearish] = -1 if short_bear else 0

    # Vol spike
    vol_ratio = atr_val / atr_63.replace(0, np.nan)
    vol_mask = vol_ratio > vol_thresh
    if short_vol:
        signal[vol_mask & (signal >= 0)] = -1
    else:
        signal[vol_mask & (signal == 1)] = 0

    # Oversold recovery
    signal[(rsi_val < 30) & (z < -1.5)] = 1

    signal.iloc[:200] = 1

    # Hysteresis
    values = signal.values.copy()
    last_change_idx = -3
    for i in range(1, n):
        if values[i] != values[i - 1]:
            if i - last_change_idx >= 3:
                last_change_idx = i
            else:
                values[i] = values[i - 1]
    return pd.Series(values, index=data.index).fillna(1).astype(int)


# Load all daily data
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
datasets = {}
for f in files:
    try:
        datasets[f.replace(".csv", "")] = load_data(os.path.join(DATA_DIR, f))
    except Exception:
        pass

configs = [
    ("flat_only(cur)", {"short_bear": False, "short_vol": False, "short_blowoff": False}),
    ("blowoff_short", {"short_bear": False, "short_vol": False, "short_blowoff": True}),
    ("bear_short", {"short_bear": True, "short_vol": False, "short_blowoff": False}),
    ("vol_short", {"short_bear": False, "short_vol": True, "short_blowoff": False}),
    ("bear+blow", {"short_bear": True, "short_vol": False, "short_blowoff": True}),
    ("bear+vol", {"short_bear": True, "short_vol": True, "short_blowoff": False}),
    ("all_shorts", {"short_bear": True, "short_vol": True, "short_blowoff": True}),
    ("bear+vol+blow", {"short_bear": True, "short_vol": True, "short_blowoff": True}),
]

print(f"{'Config':<18} {'AvgSharpe':>10} {'MedSharpe':>10} {'Beats BH':>10} {'AvgTrades':>10}")
print("-" * 62)

# Precompute B&H sharpes
bh_sharpes = {}
for ticker, data in datasets.items():
    r = data["Close"].pct_change().dropna()
    vol = np.std(r)
    bh_sharpes[ticker] = (np.mean(r) / vol) * np.sqrt(TRADING_DAYS) if vol > 1e-8 else 0.0

for name, kwargs in configs:
    sharpes = []
    trades_list = []
    beats = 0
    for ticker, data in datasets.items():
        sig = make_signals(data, **kwargs)
        sh, tot, tr = backtest_signals(data, sig)
        sharpes.append(sh)
        trades_list.append(tr)
        if sh > bh_sharpes[ticker]:
            beats += 1
    print(f"{name:<18} {np.mean(sharpes):>10.3f} {np.median(sharpes):>10.3f} {beats:>7}/{len(datasets):<3} {np.mean(trades_list):>10.0f}")
