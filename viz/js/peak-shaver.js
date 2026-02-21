// Peak Shaver strategy logic + rebalance simulation (trading_bot.py lines 507-522, 696-779)
import {
  RSI_EXTREME, RSI_HIGH, ROC_THRESHOLD, REBALANCE_DRIFT,
  INITIAL_CAPITAL, COMMISSION
} from './constants.js';

// Compute target positions from indicators
export function computeTargets(indicators) {
  const len = indicators.rsi14.length;
  const targets = new Array(len).fill(1.0);

  for (let i = 0; i < len; i++) {
    const r = indicators.rsi14[i];
    const m = indicators.roc21[i];
    if (isNaN(r)) continue;

    // RSI > 85 takes priority (more extreme)
    if (r > RSI_EXTREME) {
      targets[i] = 0.30;
    } else if (r > RSI_HIGH && !isNaN(m) && m > ROC_THRESHOLD) {
      targets[i] = 0.50;
    }
  }
  return targets;
}

// Simulate portfolio rebalancing — returns trades[] with reasoning
export function simulate(rows, indicators, targets) {
  let cash = INITIAL_CAPITAL;
  let shares = 0;
  const equity = [];
  const trades = [];

  for (let i = 0; i < rows.length; i++) {
    const price = rows[i].close;
    const target = Math.max(0, Math.min(1, targets[i]));
    const portfolioValue = cash + shares * price;

    if (portfolioValue <= 0) {
      equity.push(0);
      continue;
    }

    const currentAlloc = (shares * price) / portfolioValue;

    if (Math.abs(currentAlloc - target) > REBALANCE_DRIFT) {
      const targetValue = portfolioValue * target;
      const targetShares = targetValue / price;
      const diff = targetShares - shares;

      if (diff > 0) { // buy
        const cost = diff * price * (1 + COMMISSION);
        cash -= cost;
        shares += diff;
        trades.push(makeTrade(i, rows[i], 'BUY', diff, currentAlloc, target, indicators));
      } else if (diff < 0) { // sell
        const revenue = Math.abs(diff) * price * (1 - COMMISSION);
        cash += revenue;
        shares += diff;
        trades.push(makeTrade(i, rows[i], 'SELL', Math.abs(diff), currentAlloc, target, indicators));
      }
    }

    equity.push(cash + shares * price);
  }

  return { equity, trades };
}

function makeTrade(index, row, action, sharesDelta, fromAlloc, toAlloc, ind) {
  const r = ind.rsi14[index];
  const m = ind.roc21[index];

  // Determine reasoning
  let summary;
  const triggers = [];

  if (action === 'SELL') {
    if (r > RSI_EXTREME) {
      summary = `Extreme Overbought Trim: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
      triggers.push(`RSI(14) = ${r.toFixed(1)} > ${RSI_EXTREME} ✓`);
    } else if (r > RSI_HIGH && m > ROC_THRESHOLD) {
      summary = `Overbought Peak Trim: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
      triggers.push(`RSI(14) = ${r.toFixed(1)} > ${RSI_HIGH} ✓`);
      triggers.push(`ROC(21) = ${m.toFixed(1)}% > ${ROC_THRESHOLD}% ✓`);
    } else {
      summary = `Rebalance Sell: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
      triggers.push('Drift rebalance (allocation drifted >5% from target)');
    }
  } else {
    summary = `Re-enter: ${fmt(fromAlloc)}→${fmt(toAlloc)}`;
    if (!isNaN(r)) triggers.push(`RSI(14) = ${r.toFixed(1)} (cooled off)`);
    if (!isNaN(m)) triggers.push(`ROC(21) = ${m.toFixed(1)}%`);
    triggers.push('Target returned to 100% — buying back');
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
    triggers,
    context: {
      rsi: isNaN(r) ? null : +r.toFixed(2),
      roc: isNaN(m) ? null : +m.toFixed(2),
      sma50: nanSafe(ind.sma50[index]),
      sma200: nanSafe(ind.sma200[index]),
      ema50: nanSafe(ind.ema50[index]),
      adx: nanSafe(ind.adx14.adx[index]),
      atr: nanSafe(ind.atr14[index]),
      bbUpper: nanSafe(ind.bb.upper[index]),
      bbLower: nanSafe(ind.bb.lower[index]),
      macdLine: nanSafe(ind.macd.line[index]),
      macdSignal: nanSafe(ind.macd.signal[index]),
      obv: nanSafe(ind.obv[index]),
    },
  };
}

function fmt(alloc) { return (alloc * 100).toFixed(0) + '%'; }
function nanSafe(v) { return (v == null || isNaN(v)) ? null : +v.toFixed(2); }
