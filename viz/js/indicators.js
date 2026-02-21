// JS port of trading_bot.py indicator functions (lines 221-321)
// All functions take plain arrays and return plain arrays.

export function sma(values, window) {
  const out = new Array(values.length).fill(NaN);
  for (let i = window - 1; i < values.length; i++) {
    let sum = 0;
    for (let j = i - window + 1; j <= i; j++) sum += values[j];
    out[i] = sum / window;
  }
  return out;
}

export function ema(values, span) {
  const out = new Array(values.length).fill(NaN);
  const k = 2 / (span + 1);
  out[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    out[i] = values[i] * k + out[i - 1] * (1 - k);
  }
  return out;
}

// RSI using SMA-based rolling mean (matches trading_bot.py)
export function rsi(values, period = 14) {
  const out = new Array(values.length).fill(NaN);
  const gains = new Array(values.length).fill(0);
  const losses = new Array(values.length).fill(0);

  for (let i = 1; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    gains[i] = d > 0 ? d : 0;
    losses[i] = d < 0 ? -d : 0;
  }

  for (let i = period; i < values.length; i++) {
    let avgGain = 0, avgLoss = 0;
    for (let j = i - period + 1; j <= i; j++) {
      avgGain += gains[j];
      avgLoss += losses[j];
    }
    avgGain /= period;
    avgLoss /= period;
    if (avgLoss === 0) { out[i] = 100; continue; }
    const rs = avgGain / avgLoss;
    out[i] = 100 - 100 / (1 + rs);
  }
  return out;
}

export function roc(values, period = 21) {
  const out = new Array(values.length).fill(NaN);
  for (let i = period; i < values.length; i++) {
    if (values[i - period] !== 0) {
      out[i] = ((values[i] - values[i - period]) / values[i - period]) * 100;
    }
  }
  return out;
}

export function zscore(values, window = 50) {
  const mean = sma(values, window);
  const out = new Array(values.length).fill(NaN);
  for (let i = window - 1; i < values.length; i++) {
    let sum2 = 0;
    for (let j = i - window + 1; j <= i; j++) {
      const d = values[j] - mean[i];
      sum2 += d * d;
    }
    const std = Math.sqrt(sum2 / (window - 1));
    out[i] = std > 0 ? (values[i] - mean[i]) / std : 0;
  }
  return out;
}

export function bollingerBands(values, window = 20, numStd = 2) {
  const mid = sma(values, window);
  const upper = new Array(values.length).fill(NaN);
  const lower = new Array(values.length).fill(NaN);

  for (let i = window - 1; i < values.length; i++) {
    let sum2 = 0;
    for (let j = i - window + 1; j <= i; j++) {
      const diff = values[j] - mid[i];
      sum2 += diff * diff;
    }
    const std = Math.sqrt(sum2 / (window - 1));
    upper[i] = mid[i] + std * numStd;
    lower[i] = mid[i] - std * numStd;
  }
  return { upper, middle: mid, lower };
}

export function macd(values, fast = 12, slow = 26, signal = 9) {
  const fastEma = ema(values, fast);
  const slowEma = ema(values, slow);
  const line = fastEma.map((f, i) => f - slowEma[i]);
  const sig = ema(line, signal);
  const hist = line.map((l, i) => l - sig[i]);
  return { line, signal: sig, histogram: hist };
}

// EWM with alpha=1/period, adjust=False (matches pandas)
function ewmAlpha(values, period) {
  const alpha = 1 / period;
  const out = new Array(values.length).fill(NaN);
  out[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    const v = isNaN(values[i]) ? 0 : values[i];
    out[i] = v * alpha + out[i - 1] * (1 - alpha);
  }
  return out;
}

export function atr(rows, period = 14) {
  const tr = new Array(rows.length).fill(0);
  tr[0] = rows[0].high - rows[0].low;
  for (let i = 1; i < rows.length; i++) {
    const hl = rows[i].high - rows[i].low;
    const hc = Math.abs(rows[i].high - rows[i - 1].close);
    const lc = Math.abs(rows[i].low - rows[i - 1].close);
    tr[i] = Math.max(hl, hc, lc);
  }
  return ewmAlpha(tr, period);
}

export function adx(rows, period = 14) {
  const len = rows.length;
  const plusDm = new Array(len).fill(0);
  const minusDm = new Array(len).fill(0);

  for (let i = 1; i < len; i++) {
    const upMove = rows[i].high - rows[i - 1].high;
    const downMove = rows[i - 1].low - rows[i].low;
    plusDm[i] = (upMove > downMove && upMove > 0) ? upMove : 0;
    minusDm[i] = (downMove > upMove && downMove > 0) ? downMove : 0;
  }

  const atrVal = atr(rows, period);
  const smoothPlusDm = ewmAlpha(plusDm, period);
  const smoothMinusDm = ewmAlpha(minusDm, period);

  const plusDi = new Array(len).fill(NaN);
  const minusDi = new Array(len).fill(NaN);
  const dx = new Array(len).fill(NaN);

  for (let i = 0; i < len; i++) {
    if (atrVal[i] && atrVal[i] !== 0) {
      plusDi[i] = 100 * smoothPlusDm[i] / atrVal[i];
      minusDi[i] = 100 * smoothMinusDm[i] / atrVal[i];
      const diSum = plusDi[i] + minusDi[i];
      dx[i] = diSum !== 0 ? 100 * Math.abs(plusDi[i] - minusDi[i]) / diSum : 0;
    }
  }

  const adxVal = ewmAlpha(dx.map(v => isNaN(v) ? 0 : v), period);
  return { adx: adxVal, plusDi, minusDi };
}

export function obv(rows) {
  const out = new Array(rows.length).fill(0);
  out[0] = 0;
  for (let i = 1; i < rows.length; i++) {
    const dir = Math.sign(rows[i].close - rows[i - 1].close);
    out[i] = out[i - 1] + dir * rows[i].volume;
  }
  return out;
}

// Compute all indicators for a dataset
export function computeAll(rows) {
  const closes = rows.map(r => r.close);
  const obvVals = obv(rows);
  return {
    sma50: sma(closes, 50),
    sma200: sma(closes, 200),
    ema50: ema(closes, 50),
    rsi14: rsi(closes, 14),
    roc21: roc(closes, 21),
    roc63: roc(closes, 63),
    roc252: roc(closes, 252),
    zscore50: zscore(closes, 50),
    bb: bollingerBands(closes, 20, 2),
    macd: macd(closes, 12, 26, 9),
    atr14: atr(rows, 14),
    atr14_avg252: sma(atr(rows, 14), 252),
    adx14: adx(rows, 14),
    obv: obvVals,
    obvEma50: ema(obvVals, 50),
  };
}
