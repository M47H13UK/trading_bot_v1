// Main orchestrator — wires everything together
import { TICKERS, DEFAULT_TICKER, WARMUP } from './constants.js';
import { loadTicker } from './data-loader.js';
import { computeAll } from './indicators.js';
import { computeTargets, simulate } from './peak-shaver.js';
import { compute as computeMetrics } from './metrics.js';
import { ChartManager } from './chart-manager.js';
import { StepController } from './step-controller.js';

let rows = [];
let indicators = {};
let targets = [];
let simResult = {};
let chartManager;
let stepper;

// Populate ticker dropdown
function initTickers() {
  const sel = document.getElementById('ticker-select');
  TICKERS.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t; opt.textContent = t;
    if (t === DEFAULT_TICKER) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', () => loadAsset(sel.value));
}

// Load asset, compute everything, render
async function loadAsset(ticker) {
  const loading = document.getElementById('loading');
  loading.style.display = 'flex';

  try {
    rows = await loadTicker(ticker);
    indicators = computeAll(rows);
    targets = computeTargets(indicators);
    simResult = simulate(rows, indicators, targets);

    stepper.reset(rows.length);
    onStep(stepper.currentIndex);
    chartManager.scrollToEnd(WARMUP + 1);
  } catch (err) {
    console.error('Failed to load', ticker, err);
    alert(`Failed to load ${ticker}: ${err.message}`);
  } finally {
    loading.style.display = 'none';
  }
}

// Called on every step change
function onStep(index) {
  chartManager.setData(rows, indicators, simResult.trades, index);

  // Metrics up to current index
  const eqSlice = simResult.equity.slice(0, index + 1);
  const m = computeMetrics(eqSlice, rows, 0);

  document.getElementById('m-return').textContent = m.totalReturn + '%';
  document.getElementById('m-bnh').textContent = m.bnhReturn + '%';
  document.getElementById('m-alpha').textContent = (m.alpha >= 0 ? '+' : '') + m.alpha + '%';
  document.getElementById('m-sharpe').textContent = m.sharpe;
  document.getElementById('m-sortino').textContent = m.sortino;
  document.getElementById('m-dd').textContent = m.maxDrawdown + '%';
  document.getElementById('m-calmar').textContent = m.calmar;

  // Color alpha
  const alphaEl = document.getElementById('m-alpha');
  alphaEl.style.color = parseFloat(m.alpha) >= 0 ? '#26a69a' : '#ef5350';
}

// Trade click popup
function showTradePopup(trade) {
  const popup = document.getElementById('trade-popup');
  const content = document.getElementById('popup-content');

  const ctx = trade.context;
  content.innerHTML = `
    <h3 style="margin:0 0 8px">${trade.action} — ${trade.summary}</h3>
    <p style="margin:0 0 4px;color:#888">${trade.time} @ $${trade.price.toFixed(2)}</p>
    <hr style="border-color:#2a3a5c;margin:8px 0">
    <h4 style="margin:0 0 6px">Triggers</h4>
    <ul style="margin:0 0 8px;padding-left:18px">
      ${trade.triggers.map(t => `<li>${t}</li>`).join('')}
    </ul>
    <h4 style="margin:0 0 6px">Indicator Context</h4>
    <table class="ctx-table">
      <tr><td>RSI(14)</td><td>${v(ctx.rsi)}</td><td>ROC(21)</td><td>${v(ctx.roc)}%</td></tr>
      <tr><td>SMA(50)</td><td>${v(ctx.sma50)}</td><td>SMA(200)</td><td>${v(ctx.sma200)}</td></tr>
      <tr><td>EMA(50)</td><td>${v(ctx.ema50)}</td><td>ADX</td><td>${v(ctx.adx)}</td></tr>
      <tr><td>ATR</td><td>${v(ctx.atr)}</td><td>OBV</td><td>${v(ctx.obv)}</td></tr>
      <tr><td>BB Upper</td><td>${v(ctx.bbUpper)}</td><td>BB Lower</td><td>${v(ctx.bbLower)}</td></tr>
      <tr><td>MACD</td><td>${v(ctx.macdLine)}</td><td>Signal</td><td>${v(ctx.macdSignal)}</td></tr>
    </table>
  `;

  popup.style.display = 'flex';
}

function v(val) { return val != null ? val : '—'; }

// Init
document.addEventListener('DOMContentLoaded', () => {
  chartManager = new ChartManager();
  chartManager.init();
  chartManager.onTradeClick = showTradePopup;

  stepper = new StepController(onStep);
  initTickers();

  // Close popup
  document.getElementById('popup-close').addEventListener('click', () => {
    document.getElementById('trade-popup').style.display = 'none';
  });
  document.getElementById('trade-popup').addEventListener('click', (e) => {
    if (e.target.id === 'trade-popup') e.target.style.display = 'none';
  });

  loadAsset(DEFAULT_TICKER);
});
