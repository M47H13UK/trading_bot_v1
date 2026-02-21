// All 8 strategies from trading_bot.py, ported to JS.
// Each produces a targets[] array (0.0-1.0) compatible with simulate().
import { REBALANCE_DRIFT, INITIAL_CAPITAL, COMMISSION } from './constants.js';

// ── Forward-fill helper (mimics pandas ffill) ──
function ffill(arr, defaultVal = 0) {
  const out = new Array(arr.length);
  out[0] = isNaN(arr[0]) ? defaultVal : arr[0];
  for (let i = 1; i < arr.length; i++) {
    out[i] = isNaN(arr[i]) ? out[i - 1] : arr[i];
  }
  return out;
}

// ═══════════════════════════════════════════════════════════════
// Strategy definitions
// ═══════════════════════════════════════════════════════════════

export const STRATEGIES = [
  {
    id: 'peak_shaver_v2',
    name: 'Peak Shaver v2',
    desc: 'Triple-confirmation overbought detection. RSI + ROC + Z-score gates. Beats B&H on 78% of assets.',
    rules: [
      { cond: 'RSI(14) > 85 AND Z(50) > 3.0', act: 'Reduce to 30%', tier: 2 },
      { cond: 'RSI(14) > 75 AND ROC(21) > 11% AND Z(50) > 1.0', act: 'Reduce to 40%', tier: 1 },
      { cond: 'Otherwise', act: '100% invested', tier: 0 },
    ],
    rebalanceNote: 'Rebalance when allocation drifts >5% from target.',
    compute(ind) {
      const len = ind.rsi14.length;
      const t = new Array(len).fill(1.0);
      for (let i = 0; i < len; i++) {
        const r = ind.rsi14[i], m = ind.roc21[i], z = ind.zscore50[i];
        if (isNaN(r)) continue;
        if (r > 85 && !isNaN(z) && z > 3.0) t[i] = 0.30;
        else if (r > 75 && !isNaN(m) && m > 11 && !isNaN(z) && z > 1.0) t[i] = 0.40;
      }
      return t;
    },
    activeRule(ind, i) {
      const r = ind.rsi14[i], m = ind.roc21[i], z = ind.zscore50[i];
      if (r > 85 && !isNaN(z) && z > 3.0) return 0;
      if (r > 75 && !isNaN(m) && m > 11 && !isNaN(z) && z > 1.0) return 1;
      return 2;
    },
    ruleValues(ind, i) {
      return `RSI=${nf(ind.rsi14[i])}, ROC=${nf(ind.roc21[i])}%, Z=${nf(ind.zscore50[i])}`;
    },
  },
  {
    id: 'peak_shaver_v1',
    name: 'Peak Shaver v1',
    desc: 'Dual-confirmation overbought detection. RSI + ROC only. Beats B&H on 68% of assets.',
    rules: [
      { cond: 'RSI(14) > 85', act: 'Reduce to 30%', tier: 2 },
      { cond: 'RSI(14) > 75 AND ROC(21) > 11%', act: 'Reduce to 50%', tier: 1 },
      { cond: 'Otherwise', act: '100% invested', tier: 0 },
    ],
    rebalanceNote: 'Rebalance when allocation drifts >5% from target.',
    compute(ind) {
      const len = ind.rsi14.length;
      const t = new Array(len).fill(1.0);
      for (let i = 0; i < len; i++) {
        const r = ind.rsi14[i], m = ind.roc21[i];
        if (isNaN(r)) continue;
        if (r > 85) t[i] = 0.30;
        else if (r > 75 && !isNaN(m) && m > 11) t[i] = 0.50;
      }
      return t;
    },
    activeRule(ind, i) {
      const r = ind.rsi14[i], m = ind.roc21[i];
      if (r > 85) return 0;
      if (r > 75 && !isNaN(m) && m > 11) return 1;
      return 2;
    },
    ruleValues(ind, i) {
      return `RSI=${nf(ind.rsi14[i])}, ROC=${nf(ind.roc21[i])}%`;
    },
  },
  {
    id: 'sma200_trend',
    name: 'SMA200 Trend',
    desc: 'Faber Timing Model. Long above SMA(200) with 3-day confirmation. ~75% invested.',
    rules: [
      { cond: 'Close > SMA(200) for 3 days', act: 'Enter (100%)', tier: 1 },
      { cond: 'Close < SMA(200) for 3 days', act: 'Exit (0%)', tier: 0 },
    ],
    rebalanceNote: '3-day filter reduces whipsaws around the moving average.',
    compute(ind, rows) {
      const c = rows.map(r => r.close);
      const s = ind.sma200;
      const len = c.length;
      const sig = new Array(len).fill(NaN);
      for (let i = 2; i < len; i++) {
        if (isNaN(s[i]) || isNaN(s[i - 1]) || isNaN(s[i - 2])) continue;
        if (c[i] > s[i] && c[i - 1] > s[i - 1] && c[i - 2] > s[i - 2]) sig[i] = 1;
        if (c[i] < s[i] && c[i - 1] < s[i - 1] && c[i - 2] < s[i - 2]) sig[i] = 0;
      }
      return ffill(sig, 0);
    },
    activeRule(ind, i, rows) {
      return rows[i].close > ind.sma200[i] ? 0 : 1;
    },
    ruleValues(ind, i, rows) {
      return `Close=${nf(rows[i].close)}, SMA200=${nf(ind.sma200[i])}`;
    },
  },
  {
    id: 'dual_ma',
    name: 'Dual MA Cross',
    desc: 'Golden/Death Cross. SMA(50) vs SMA(200) with 1% band filter. ~70% invested.',
    rules: [
      { cond: 'SMA(50) > SMA(200) × 1.01', act: 'Enter (100%)', tier: 1 },
      { cond: 'SMA(50) < SMA(200) × 0.99', act: 'Exit (0%)', tier: 0 },
    ],
    rebalanceNote: '1% band prevents whipsaws when MAs are close together.',
    compute(ind) {
      const len = ind.sma50.length;
      const sig = new Array(len).fill(NaN);
      for (let i = 0; i < len; i++) {
        const s50 = ind.sma50[i], s200 = ind.sma200[i];
        if (isNaN(s50) || isNaN(s200)) continue;
        if (s50 > s200 * 1.01) sig[i] = 1;
        if (s50 < s200 * 0.99) sig[i] = 0;
      }
      return ffill(sig, 0);
    },
    activeRule(ind, i) {
      const s50 = ind.sma50[i], s200 = ind.sma200[i];
      if (isNaN(s50) || isNaN(s200)) return 1;
      return s50 > s200 * 1.01 ? 0 : 1;
    },
    ruleValues(ind, i) {
      return `SMA50=${nf(ind.sma50[i])}, SMA200=${nf(ind.sma200[i])}`;
    },
  },
  {
    id: 'momentum_composite',
    name: 'Momentum Composite',
    desc: 'Multi-timeframe momentum vote. 1/3/12-month ROC. Invest when 2+ positive. ~70% invested.',
    rules: [
      { cond: '2+ of ROC(21), ROC(63), ROC(252) > 0', act: 'Enter (100%)', tier: 1 },
      { cond: 'All 3 ROC < 0', act: 'Exit (0%)', tier: 0 },
    ],
    rebalanceNote: 'Uses hysteresis: enter at 2+ bullish, exit at 0 bullish.',
    compute(ind) {
      const len = ind.roc21.length;
      const sig = new Array(len).fill(NaN);
      for (let i = 0; i < len; i++) {
        const m1 = ind.roc21[i], m3 = ind.roc63[i], m12 = ind.roc252[i];
        const bull = (m1 > 0 ? 1 : 0) + (m3 > 0 ? 1 : 0) + (m12 > 0 ? 1 : 0);
        if (bull >= 2) sig[i] = 1;
        else if (bull === 0) sig[i] = 0;
      }
      return ffill(sig, 0);
    },
    activeRule(ind, i) {
      const bull = (ind.roc21[i] > 0 ? 1 : 0) + (ind.roc63[i] > 0 ? 1 : 0) + (ind.roc252[i] > 0 ? 1 : 0);
      return bull >= 2 ? 0 : 1;
    },
    ruleValues(ind, i) {
      return `ROC21=${nf(ind.roc21[i])}%, ROC63=${nf(ind.roc63[i])}%, ROC252=${nf(ind.roc252[i])}%`;
    },
  },
  {
    id: 'crash_avoidance',
    name: 'Crash Avoidance',
    desc: 'Always invested. Exit only on confirmed crashes (4 signals). ~90-95% invested.',
    rules: [
      { cond: 'Crash score ≥ 0.75 (3+ of 4 signals)', act: 'Exit (0%)', tier: 0 },
      { cond: 'Crash score ≤ 0.25 (≤1 signal)', act: 'Re-enter (100%)', tier: 1 },
    ],
    rebalanceNote: 'Signals: below SMA200, death cross, ATR spike (2× avg), RSI < 35.',
    compute(ind, rows) {
      const c = rows.map(r => r.close);
      const len = c.length;
      const sig = new Array(len).fill(NaN);
      for (let i = 0; i < len; i++) {
        const belowTrend = c[i] < ind.sma200[i] ? 1 : 0;
        const deathCross = ind.sma50[i] < ind.sma200[i] ? 1 : 0;
        const atrAvg = ind.atr14_avg252[i];
        const volSpike = (!isNaN(atrAvg) && atrAvg > 0 && ind.atr14[i] > 2 * atrAvg) ? 1 : 0;
        const rsiWeak = (!isNaN(ind.rsi14[i]) && ind.rsi14[i] < 35) ? 1 : 0;
        const score = (belowTrend + deathCross + volSpike + rsiWeak) / 4;
        if (score >= 0.75) sig[i] = 0;
        else if (score <= 0.25) sig[i] = 1;
      }
      return ffill(sig, 1); // default: invested
    },
    activeRule(ind, i, rows) {
      const belowTrend = rows[i].close < ind.sma200[i] ? 1 : 0;
      const deathCross = ind.sma50[i] < ind.sma200[i] ? 1 : 0;
      const atrAvg = ind.atr14_avg252[i];
      const volSpike = (!isNaN(atrAvg) && atrAvg > 0 && ind.atr14[i] > 2 * atrAvg) ? 1 : 0;
      const rsiWeak = (!isNaN(ind.rsi14[i]) && ind.rsi14[i] < 35) ? 1 : 0;
      const score = (belowTrend + deathCross + volSpike + rsiWeak) / 4;
      return score >= 0.75 ? 0 : 1;
    },
    ruleValues(ind, i, rows) {
      const belowTrend = rows[i].close < ind.sma200[i] ? 1 : 0;
      const deathCross = ind.sma50[i] < ind.sma200[i] ? 1 : 0;
      const atrAvg = ind.atr14_avg252[i];
      const volSpike = (!isNaN(atrAvg) && atrAvg > 0 && ind.atr14[i] > 2 * atrAvg) ? 1 : 0;
      const rsiWeak = (!isNaN(ind.rsi14[i]) && ind.rsi14[i] < 35) ? 1 : 0;
      const score = (belowTrend + deathCross + volSpike + rsiWeak) / 4;
      return `Score=${score.toFixed(2)} (trend=${belowTrend}, DC=${deathCross}, vol=${volSpike}, RSI=${rsiWeak})`;
    },
  },
  {
    id: 'volume_trend',
    name: 'Volume Trend',
    desc: 'Price + volume confirmation. Exit when BOTH price and volume break down. ~80% invested.',
    rules: [
      { cond: 'Close > EMA(50) AND OBV > OBV_EMA(50)', act: 'Enter (100%)', tier: 1 },
      { cond: 'Close < EMA(50) AND OBV < OBV_EMA(50)', act: 'Exit (0%)', tier: 0 },
    ],
    rebalanceNote: 'Requires both price and volume to confirm direction.',
    compute(ind, rows) {
      const c = rows.map(r => r.close);
      const len = c.length;
      const sig = new Array(len).fill(NaN);
      for (let i = 0; i < len; i++) {
        const priceUp = c[i] > ind.ema50[i];
        const volUp = ind.obv[i] > ind.obvEma50[i];
        if (priceUp && volUp) sig[i] = 1;
        else if (!priceUp && !volUp) sig[i] = 0;
      }
      return ffill(sig, 0);
    },
    activeRule(ind, i, rows) {
      const priceUp = rows[i].close > ind.ema50[i];
      const volUp = ind.obv[i] > ind.obvEma50[i];
      return (priceUp && volUp) ? 0 : 1;
    },
    ruleValues(ind, i, rows) {
      return `Close=${nf(rows[i].close)}, EMA50=${nf(ind.ema50[i])}, OBV=${nf(ind.obv[i])}, OBV_EMA=${nf(ind.obvEma50[i])}`;
    },
  },
  {
    id: 'master_ensemble',
    name: 'Master Ensemble',
    desc: 'Majority vote of 5 strategies with long bias. Enter at 3+, exit at ≤1. ~85% invested.',
    rules: [
      { cond: 'Consensus ≥ 3 (of 5 strategies bullish)', act: 'Enter (100%)', tier: 1 },
      { cond: 'Consensus ≤ 1', act: 'Exit (0%)', tier: 0 },
    ],
    rebalanceNote: 'Combines: SMA200 Trend, Dual MA, Momentum, Crash Avoidance, Volume Trend.',
    compute(ind, rows) {
      // Compute sub-strategy positions
      const strats = STRATEGIES;
      const p1 = strats.find(s => s.id === 'sma200_trend').compute(ind, rows);
      const p2 = strats.find(s => s.id === 'dual_ma').compute(ind, rows);
      const p3 = strats.find(s => s.id === 'momentum_composite').compute(ind, rows);
      const p4 = strats.find(s => s.id === 'crash_avoidance').compute(ind, rows);
      const p5 = strats.find(s => s.id === 'volume_trend').compute(ind, rows);

      const len = rows.length;
      const targets = new Array(len).fill(0);
      let pos = 0;
      for (let i = 0; i < len; i++) {
        const consensus = p1[i] + p2[i] + p3[i] + p4[i] + p5[i];
        if (pos === 0 && consensus >= 3) pos = 1;
        else if (pos === 1 && consensus <= 1) pos = 0;
        targets[i] = pos;
      }
      return targets;
    },
    activeRule(ind, i, rows) {
      // Simplified — just check current consensus
      const strats = STRATEGIES;
      const p1 = strats.find(s => s.id === 'sma200_trend').compute(ind, rows);
      const p2 = strats.find(s => s.id === 'dual_ma').compute(ind, rows);
      const p3 = strats.find(s => s.id === 'momentum_composite').compute(ind, rows);
      const p4 = strats.find(s => s.id === 'crash_avoidance').compute(ind, rows);
      const p5 = strats.find(s => s.id === 'volume_trend').compute(ind, rows);
      const consensus = p1[i] + p2[i] + p3[i] + p4[i] + p5[i];
      return consensus >= 3 ? 0 : 1;
    },
    ruleValues(ind, i, rows) {
      const strats = STRATEGIES;
      const p1 = strats.find(s => s.id === 'sma200_trend').compute(ind, rows);
      const p2 = strats.find(s => s.id === 'dual_ma').compute(ind, rows);
      const p3 = strats.find(s => s.id === 'momentum_composite').compute(ind, rows);
      const p4 = strats.find(s => s.id === 'crash_avoidance').compute(ind, rows);
      const p5 = strats.find(s => s.id === 'volume_trend').compute(ind, rows);
      const c = p1[i] + p2[i] + p3[i] + p4[i] + p5[i];
      return `Consensus=${c}/5 (SMA200=${p1[i]}, DualMA=${p2[i]}, Mom=${p3[i]}, Crash=${p4[i]}, Vol=${p5[i]})`;
    },
  },
];

export const DEFAULT_STRATEGY = 'peak_shaver_v2';

export function getStrategy(id) {
  return STRATEGIES.find(s => s.id === id) || STRATEGIES[0];
}

// ── Simulate portfolio rebalancing (generic, works for all strategies) ──
export function simulate(rows, indicators, targets, strategy) {
  let cash = INITIAL_CAPITAL;
  let shares = 0;
  const equity = [];
  const trades = [];

  for (let i = 0; i < rows.length; i++) {
    const price = rows[i].close;
    const target = Math.max(0, Math.min(1, targets[i]));
    const portfolioValue = cash + shares * price;

    if (portfolioValue <= 0) { equity.push(0); continue; }

    const currentAlloc = (shares * price) / portfolioValue;

    if (Math.abs(currentAlloc - target) > REBALANCE_DRIFT) {
      const targetValue = portfolioValue * target;
      const targetShares = targetValue / price;
      const diff = targetShares - shares;

      if (diff > 0) {
        cash -= diff * price * (1 + COMMISSION);
        shares += diff;
        trades.push(makeTrade(i, rows[i], 'BUY', diff, currentAlloc, target, indicators, rows, strategy));
      } else if (diff < 0) {
        cash += Math.abs(diff) * price * (1 - COMMISSION);
        shares += diff;
        trades.push(makeTrade(i, rows[i], 'SELL', Math.abs(diff), currentAlloc, target, indicators, rows, strategy));
      }
    }

    equity.push(cash + shares * price);
  }

  return { equity, trades };
}

function makeTrade(index, row, action, sharesDelta, fromAlloc, toAlloc, ind, rows, strategy) {
  const activeIdx = strategy.activeRule(ind, index, rows);
  const activeRule = strategy.rules[activeIdx];
  const valStr = strategy.ruleValues(ind, index, rows);

  let summary;
  if (action === 'SELL') {
    summary = `${activeRule ? activeRule.cond : 'Drift'}: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
  } else {
    summary = `Re-enter: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
  }

  return {
    index,
    time: row.time,
    price: row.close,
    action,
    shares: sharesDelta,
    fromAlloc,
    toAlloc,
    summary,
    activeRuleIdx: activeIdx,
    ruleValues: valStr,
    context: {
      rsi: nfn(ind.rsi14[index]),
      roc: nfn(ind.roc21[index]),
      zscore: nfn(ind.zscore50 ? ind.zscore50[index] : NaN),
      sma50: nfn(ind.sma50[index]),
      sma200: nfn(ind.sma200[index]),
      ema50: nfn(ind.ema50[index]),
      adx: nfn(ind.adx14.adx[index]),
      atr: nfn(ind.atr14[index]),
      bbUpper: nfn(ind.bb.upper[index]),
      bbLower: nfn(ind.bb.lower[index]),
      macdLine: nfn(ind.macd.line[index]),
      macdSignal: nfn(ind.macd.signal[index]),
      obv: nfn(ind.obv[index]),
    },
  };
}

function fmt(alloc) { return (alloc * 100).toFixed(0) + '%'; }
function nf(v) { return v != null && !isNaN(v) ? (+v).toFixed(2) : '—'; }
function nfn(v) { return v != null && !isNaN(v) ? +(+v).toFixed(2) : null; }
