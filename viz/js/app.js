// Main orchestrator — wires everything together
import { ASSET_CATEGORIES, ASSET_INFO, DEFAULT_TICKER, WARMUP } from './constants.js';
import { loadTicker } from './data-loader.js';
import { computeAll } from './indicators.js';
import { STRATEGIES, DEFAULT_STRATEGY, getStrategy, simulate } from './strategies.js';
import { compute as computeMetrics } from './metrics.js';
import { ChartManager } from './chart-manager.js';
import { StepController } from './step-controller.js';

let rows = [];
let indicators = {};
let targets = [];
let simResult = {};
let chartManager;
let stepper;
let currentTicker = DEFAULT_TICKER;
let currentStrategyId = DEFAULT_STRATEGY;
let prevStepIndex = -1;

// ── Asset Picker Modal ──
function initAssetPicker() {
  const btn = document.getElementById('asset-btn');
  const modal = document.getElementById('asset-modal');
  const grid = document.getElementById('asset-grid');

  btn.textContent = DEFAULT_TICKER;

  for (const [category, tickers] of Object.entries(ASSET_CATEGORIES)) {
    const section = document.createElement('div');
    section.className = 'asset-category';
    section.innerHTML = `<div class="asset-cat-label">${category}</div>`;
    const items = document.createElement('div');
    items.className = 'asset-items';
    for (const t of tickers) {
      const chip = document.createElement('button');
      chip.className = 'asset-chip';
      chip.dataset.ticker = t;
      if (t === DEFAULT_TICKER) chip.classList.add('active');

      // Ticker label + info on hover
      const info = ASSET_INFO[t];
      chip.textContent = t;
      if (info) {
        chip.title = `${info.name} — ${info.desc}`;
        chip.innerHTML = `<span class="chip-ticker">${t}</span><span class="chip-name">${info.name}</span>`;
      }

      chip.addEventListener('click', () => {
        grid.querySelectorAll('.asset-chip.active').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        btn.textContent = t;
        currentTicker = t;
        modal.style.display = 'none';
        loadAsset(t);
      });
      items.appendChild(chip);
    }
    section.appendChild(items);
    grid.appendChild(section);
  }

  btn.addEventListener('click', () => {
    modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
  });
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.style.display = 'none';
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modal.style.display = 'none';
      document.getElementById('strategy-modal').style.display = 'none';
    }
  });
}

// ── Strategy Picker Modal ──
function initStrategyPicker() {
  const btn = document.getElementById('strategy-btn');
  const modal = document.getElementById('strategy-modal');
  const grid = document.getElementById('strategy-grid');

  const defaultStrat = getStrategy(DEFAULT_STRATEGY);
  btn.textContent = defaultStrat.name;

  for (const s of STRATEGIES) {
    const card = document.createElement('button');
    card.className = 'strategy-card';
    if (s.id === DEFAULT_STRATEGY) card.classList.add('active');
    card.dataset.id = s.id;
    card.innerHTML = `
      <div class="strat-name">${s.name}</div>
      <div class="strat-desc">${s.desc}</div>
    `;
    card.addEventListener('click', () => {
      grid.querySelectorAll('.strategy-card.active').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      btn.textContent = s.name;
      currentStrategyId = s.id;
      modal.style.display = 'none';
      recomputeStrategy();
    });
    grid.appendChild(card);
  }

  btn.addEventListener('click', () => {
    modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
  });
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.style.display = 'none';
  });
}

// Recompute strategy without reloading data
function recomputeStrategy() {
  const strategy = getStrategy(currentStrategyId);
  targets = strategy.compute(indicators, rows);
  simResult = simulate(rows, indicators, targets, strategy);
  prevStepIndex = -1;
  onStep(stepper.currentIndex);
}

// Load asset, compute everything, render
async function loadAsset(ticker) {
  const loading = document.getElementById('loading');
  loading.style.display = 'flex';

  try {
    rows = await loadTicker(ticker);
    indicators = computeAll(rows);
    const strategy = getStrategy(currentStrategyId);
    targets = strategy.compute(indicators, rows);
    simResult = simulate(rows, indicators, targets, strategy);

    prevStepIndex = -1;
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
  if (index === prevStepIndex + 1 && prevStepIndex >= 0) {
    chartManager.appendBar(rows, indicators, simResult.trades, index);
  } else {
    chartManager.setData(rows, indicators, simResult.trades, index);
  }
  prevStepIndex = index;

  const eqSlice = simResult.equity.slice(0, index + 1);
  const m = computeMetrics(eqSlice, rows, 0);

  document.getElementById('m-return').textContent = m.totalReturn + '%';
  document.getElementById('m-bnh').textContent = m.bnhReturn + '%';
  document.getElementById('m-alpha').textContent = (m.alpha >= 0 ? '+' : '') + m.alpha + '%';
  document.getElementById('m-sharpe').textContent = m.sharpe;
  document.getElementById('m-sortino').textContent = m.sortino;
  document.getElementById('m-dd').textContent = m.maxDrawdown + '%';
  document.getElementById('m-calmar').textContent = m.calmar;

  const alphaEl = document.getElementById('m-alpha');
  alphaEl.style.color = parseFloat(m.alpha) >= 0 ? '#26a69a' : '#ef5350';

  updateDuration(index);
}

function updateDuration(index) {
  const startDate = parseDate(rows[WARMUP].time);
  const endDate = parseDate(rows[index].time);

  let years = endDate.getFullYear() - startDate.getFullYear();
  let months = endDate.getMonth() - startDate.getMonth();
  let days = endDate.getDate() - startDate.getDate();
  if (days < 0) { months--; days += new Date(endDate.getFullYear(), endDate.getMonth(), 0).getDate(); }
  if (months < 0) { years--; months += 12; }

  const parts = [];
  if (years > 0) parts.push(years + 'y');
  if (months > 0) parts.push(months + 'm');
  parts.push(days + 'd');
  document.getElementById('m-duration').textContent = parts.join(' ');
}

function parseDate(str) {
  const [y, m, d] = str.split('-').map(Number);
  return new Date(y, m - 1, d);
}

// ── Trade Reasoning Popup ──
function showTradePopup(trade) {
  const popup = document.getElementById('trade-popup');
  const content = document.getElementById('popup-content');
  const strategy = getStrategy(currentStrategyId);
  const ctx = trade.context;
  const actionColor = trade.action === 'SELL' ? '#ef5350' : '#26a69a';

  // Build rules section with active rule highlighted
  const rulesHtml = strategy.rules.map((r, idx) => {
    const isActive = idx === trade.activeRuleIdx;
    return `<div class="rule ${isActive ? 'rule-active' : ''}">
      <span class="rule-cond">${r.cond}</span>
      <span class="rule-arrow">→</span>
      <span class="rule-act">${r.act}</span>
    </div>`;
  }).join('');

  content.innerHTML = `
    <h3 style="margin:0 0 8px;color:${actionColor}">${trade.action} — ${trade.summary}</h3>
    <p style="margin:0 0 4px;color:#888">${trade.time} @ $${trade.price.toFixed(2)} · ${trade.shares.toFixed(2)} shares</p>
    <hr style="border-color:#2a3a5c;margin:8px 0">

    <h4 style="margin:0 0 6px">Current Values</h4>
    <p style="margin:0 0 12px;font-size:12px;color:#a68dff;font-family:monospace">${trade.ruleValues}</p>

    <h4 style="margin:0 0 6px">${strategy.name} Rules</h4>
    <div class="rules-box">
      ${rulesHtml}
      <div class="rule-note">${strategy.rebalanceNote}</div>
    </div>

    <h4 style="margin:8px 0 6px">Indicator Context</h4>
    <table class="ctx-table">
      <tr><td>RSI(14)</td><td>${v(ctx.rsi)}</td><td>ROC(21)</td><td>${v(ctx.roc)}%</td></tr>
      <tr><td>Z-score(50)</td><td>${v(ctx.zscore)}</td><td>ADX</td><td>${v(ctx.adx)}</td></tr>
      <tr><td>SMA(50)</td><td>${v(ctx.sma50)}</td><td>SMA(200)</td><td>${v(ctx.sma200)}</td></tr>
      <tr><td>EMA(50)</td><td>${v(ctx.ema50)}</td><td>ATR</td><td>${v(ctx.atr)}</td></tr>
      <tr><td>BB Upper</td><td>${v(ctx.bbUpper)}</td><td>BB Lower</td><td>${v(ctx.bbLower)}</td></tr>
      <tr><td>MACD</td><td>${v(ctx.macdLine)}</td><td>Signal</td><td>${v(ctx.macdSignal)}</td></tr>
      <tr><td>OBV</td><td>${v(ctx.obv)}</td><td></td><td></td></tr>
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
  initAssetPicker();
  initStrategyPicker();

  document.getElementById('popup-close').addEventListener('click', () => {
    document.getElementById('trade-popup').style.display = 'none';
  });
  document.getElementById('trade-popup').addEventListener('click', (e) => {
    if (e.target.id === 'trade-popup') e.target.style.display = 'none';
  });

  loadAsset(DEFAULT_TICKER);
});
