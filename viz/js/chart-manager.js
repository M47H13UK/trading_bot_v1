// Multi-pane Lightweight Charts wrapper with sync
import { COLORS } from './constants.js';

const COMMON = {
  layout: { background: { color: COLORS.panelBg }, textColor: COLORS.text },
  grid: { vertLines: { color: COLORS.grid }, horzLines: { color: COLORS.grid } },
  crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  timeScale: { borderColor: COLORS.border, timeVisible: false },
  rightPriceScale: { borderColor: COLORS.border },
};

export class ChartManager {
  constructor() {
    this.charts = {};   // { price, rsi, macd, volume }
    this.series = {};
    this.tradeMarkers = [];
    this.onTradeClick = null;
  }

  init() {
    this.createPriceChart();
    this.createRsiChart();
    this.createMacdChart();
    this.createVolumeChart();
    this.syncTimeScales();
    this.syncCrosshairs();
    window.addEventListener('resize', () => this.resize());
  }

  createPriceChart() {
    const el = document.getElementById('chart-price');
    const chart = LightweightCharts.createChart(el, { ...COMMON, height: el.clientHeight });
    const candles = chart.addCandlestickSeries({
      upColor: COLORS.up, downColor: COLORS.down,
      borderUpColor: COLORS.up, borderDownColor: COLORS.down,
      wickUpColor: COLORS.up, wickDownColor: COLORS.down,
    });
    const sma50 = chart.addLineSeries({ color: COLORS.sma50, lineWidth: 1, title: 'SMA50' });
    const sma200 = chart.addLineSeries({ color: COLORS.sma200, lineWidth: 1, title: 'SMA200' });
    const ema50 = chart.addLineSeries({ color: COLORS.ema50, lineWidth: 1, title: 'EMA50' });
    const bbUp = chart.addLineSeries({ color: COLORS.bbUpper, lineWidth: 1, lineStyle: 2, title: 'BB+' });
    const bbLow = chart.addLineSeries({ color: COLORS.bbLower, lineWidth: 1, lineStyle: 2, title: 'BB-' });
    const bbMid = chart.addLineSeries({ color: COLORS.bbMiddle, lineWidth: 1, lineStyle: 1, title: 'BBm' });

    this.charts.price = chart;
    this.series.candles = candles;
    this.series.sma50 = sma50;
    this.series.sma200 = sma200;
    this.series.ema50 = ema50;
    this.series.bbUp = bbUp;
    this.series.bbLow = bbLow;
    this.series.bbMid = bbMid;

    // Click handler for trade markers
    chart.subscribeClick((param) => {
      if (!param.time || !this.onTradeClick) return;
      const trade = this.tradeMarkers.find(t => t.time === param.time);
      if (trade) this.onTradeClick(trade);
    });
  }

  createRsiChart() {
    const el = document.getElementById('chart-rsi');
    const chart = LightweightCharts.createChart(el, {
      ...COMMON, height: el.clientHeight,
      rightPriceScale: { ...COMMON.rightPriceScale, scaleMargins: { top: 0.05, bottom: 0.05 } },
    });
    const line = chart.addLineSeries({ color: COLORS.rsiLine, lineWidth: 2, title: 'RSI(14)' });

    // Horizontal threshold lines via baseline series workaround — use line + priceLines
    line.createPriceLine({ price: 85, color: COLORS.rsiHigh, lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
    line.createPriceLine({ price: 75, color: COLORS.rsiMid, lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
    line.createPriceLine({ price: 30, color: COLORS.rsiLow, lineWidth: 1, lineStyle: 2, axisLabelVisible: false });

    this.charts.rsi = chart;
    this.series.rsi = line;
  }

  createMacdChart() {
    const el = document.getElementById('chart-macd');
    const chart = LightweightCharts.createChart(el, { ...COMMON, height: el.clientHeight });

    const hist = chart.addHistogramSeries({
      priceFormat: { type: 'price', precision: 4, minMove: 0.0001 },
      title: 'MACD Hist',
    });
    const line = chart.addLineSeries({ color: COLORS.macdLine, lineWidth: 1, title: 'MACD' });
    const sig = chart.addLineSeries({ color: COLORS.macdSignal, lineWidth: 1, title: 'Signal' });

    this.charts.macd = chart;
    this.series.macdHist = hist;
    this.series.macdLine = line;
    this.series.macdSignal = sig;
  }

  createVolumeChart() {
    const el = document.getElementById('chart-volume');
    const chart = LightweightCharts.createChart(el, {
      ...COMMON, height: el.clientHeight,
      rightPriceScale: { ...COMMON.rightPriceScale, scaleMargins: { top: 0.1, bottom: 0 } },
    });
    const vol = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      title: 'Volume',
    });

    this.charts.volume = chart;
    this.series.volume = vol;
  }

  syncTimeScales() {
    const keys = Object.keys(this.charts);
    keys.forEach(k1 => {
      this.charts[k1].timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (!range) return;
        keys.forEach(k2 => {
          if (k1 !== k2) this.charts[k2].timeScale().setVisibleLogicalRange(range);
        });
      });
    });
  }

  syncCrosshairs() {
    const keys = Object.keys(this.charts);
    keys.forEach(k1 => {
      this.charts[k1].subscribeCrosshairMove(param => {
        if (!param.time) return;
        keys.forEach(k2 => {
          if (k1 !== k2) {
            this.charts[k2].setCrosshairPosition(
              undefined,  // price — let each chart determine its own
              param.time,
              this.getFirstSeries(k2)
            );
          }
        });
      });
    });
  }

  getFirstSeries(chartKey) {
    switch (chartKey) {
      case 'price': return this.series.candles;
      case 'rsi': return this.series.rsi;
      case 'macd': return this.series.macdLine;
      case 'volume': return this.series.volume;
    }
  }

  // Set data for all panes up to endIndex
  setData(rows, indicators, trades, endIndex) {
    const slice = rows.slice(0, endIndex + 1);
    const times = slice.map(r => r.time);

    // Price candles
    this.series.candles.setData(slice.map(r => ({
      time: r.time, open: r.open, high: r.high, low: r.low, close: r.close,
    })));

    // Overlays
    this.setLineData(this.series.sma50, times, indicators.sma50, endIndex);
    this.setLineData(this.series.sma200, times, indicators.sma200, endIndex);
    this.setLineData(this.series.ema50, times, indicators.ema50, endIndex);
    this.setLineData(this.series.bbUp, times, indicators.bb.upper, endIndex);
    this.setLineData(this.series.bbLow, times, indicators.bb.lower, endIndex);
    this.setLineData(this.series.bbMid, times, indicators.bb.middle, endIndex);

    // Trade markers on candles
    const visible = trades.filter(t => t.index <= endIndex);
    this.tradeMarkers = visible;
    const markers = visible.map(t => ({
      time: t.time,
      position: t.action === 'BUY' ? 'belowBar' : 'aboveBar',
      color: t.action === 'BUY' ? COLORS.buy : COLORS.sell,
      shape: t.action === 'BUY' ? 'arrowUp' : 'arrowDown',
      text: t.action === 'BUY' ? 'B' : 'S',
    }));
    this.series.candles.setMarkers(markers);

    // RSI
    this.setLineData(this.series.rsi, times, indicators.rsi14, endIndex);

    // MACD
    const macdHistData = [];
    for (let i = 0; i <= endIndex; i++) {
      const v = indicators.macd.histogram[i];
      if (!isNaN(v)) {
        macdHistData.push({
          time: rows[i].time, value: v,
          color: v >= 0 ? COLORS.macdHistUp : COLORS.macdHistDown,
        });
      }
    }
    this.series.macdHist.setData(macdHistData);
    this.setLineData(this.series.macdLine, times, indicators.macd.line, endIndex);
    this.setLineData(this.series.macdSignal, times, indicators.macd.signal, endIndex);

    // Volume
    this.series.volume.setData(slice.map(r => ({
      time: r.time, value: r.volume,
      color: r.close >= r.open ? COLORS.up + '88' : COLORS.down + '88',
    })));
  }

  setLineData(series, times, values, endIndex) {
    const data = [];
    for (let i = 0; i <= endIndex; i++) {
      if (!isNaN(values[i])) data.push({ time: times[i], value: values[i] });
    }
    series.setData(data);
  }

  resize() {
    for (const key of Object.keys(this.charts)) {
      const el = document.getElementById(`chart-${key}`);
      this.charts[key].resize(el.clientWidth, el.clientHeight);
    }
  }

  // Scroll to show last N candles
  scrollToEnd(totalBars) {
    const range = { from: Math.max(0, totalBars - 80), to: totalBars };
    for (const chart of Object.values(this.charts)) {
      chart.timeScale().setVisibleLogicalRange(range);
    }
  }
}
