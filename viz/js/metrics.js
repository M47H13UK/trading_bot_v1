// Running performance metrics (mirrors trading_bot.py lines 738-779)
import { INITIAL_CAPITAL } from './constants.js';

export function compute(equity, rows, startIdx) {
  if (equity.length < 2) return blank();

  const finalVal = equity[equity.length - 1];
  const totalReturn = (finalVal / INITIAL_CAPITAL - 1) * 100;

  const startPrice = rows[startIdx].close;
  const endPrice = rows[startIdx + equity.length - 1].close;
  const bnhReturn = ((endPrice / startPrice) - 1) * 100;
  const alpha = totalReturn - bnhReturn;

  // Daily returns
  const dailyRet = [];
  for (let i = 1; i < equity.length; i++) {
    if (equity[i - 1] > 0) dailyRet.push(equity[i] / equity[i - 1] - 1);
  }

  const sharpe = sharpeRatio(dailyRet);
  const sortino = sortinoRatio(dailyRet);
  const maxDd = maxDrawdown(equity);

  const years = equity.length / 252;
  const annualReturn = (Math.pow(finalVal / INITIAL_CAPITAL, 1 / Math.max(years, 0.1)) - 1) * 100;
  const calmar = maxDd !== 0 ? annualReturn / Math.abs(maxDd) : 0;

  return {
    totalReturn: totalReturn.toFixed(2),
    bnhReturn: bnhReturn.toFixed(2),
    alpha: alpha.toFixed(2),
    sharpe: sharpe.toFixed(2),
    sortino: sortino.toFixed(2),
    maxDrawdown: maxDd.toFixed(2),
    calmar: calmar.toFixed(2),
    finalValue: finalVal.toFixed(0),
  };
}

function sharpeRatio(rets) {
  if (rets.length < 2) return 0;
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const std = Math.sqrt(rets.reduce((s, r) => s + (r - mean) ** 2, 0) / (rets.length - 1));
  return std > 0 ? (mean / std) * Math.sqrt(252) : 0;
}

function sortinoRatio(rets) {
  if (rets.length < 2) return 0;
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const down = rets.filter(r => r < 0);
  if (down.length === 0) return 0;
  const downStd = Math.sqrt(down.reduce((s, r) => s + r * r, 0) / down.length);
  return downStd > 0 ? (mean / downStd) * Math.sqrt(252) : 0;
}

function maxDrawdown(equity) {
  let peak = equity[0];
  let maxDd = 0;
  for (let i = 1; i < equity.length; i++) {
    if (equity[i] > peak) peak = equity[i];
    const dd = (equity[i] / peak - 1) * 100;
    if (dd < maxDd) maxDd = dd;
  }
  return maxDd;
}

function blank() {
  return { totalReturn: '0.00', bnhReturn: '0.00', alpha: '0.00',
    sharpe: '0.00', sortino: '0.00', maxDrawdown: '0.00',
    calmar: '0.00', finalValue: '0' };
}
