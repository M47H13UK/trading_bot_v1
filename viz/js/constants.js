// Ticker list from test_data/
export const TICKERS = [
  'AAPL','AMZN','BTC_USD','DIA','EEM','EFA','ETH_USD','EWG','EWJ','EWU',
  'FXB','FXE','FXI','FXY','GLD','IEF','IWM','JNJ','JPM','MSFT',
  'QQQ','SHY','SLV','SPY','TLT','TSLA','UNG','USO','UUP','WMT',
  'XLB','XLE','XLF','XLI','XLK','XLP','XLRE','XLU','XLV','XLY','XOM'
];

export const DEFAULT_TICKER = 'SPY';

// Peak Shaver thresholds
export const RSI_EXTREME = 85;
export const RSI_HIGH = 75;
export const ROC_THRESHOLD = 11; // %
export const REBALANCE_DRIFT = 0.05; // 5%

// Indicator periods
export const RSI_PERIOD = 14;
export const ROC_PERIOD = 21;
export const SMA_SHORT = 50;
export const SMA_LONG = 200;
export const EMA_PERIOD = 50;
export const BB_WINDOW = 20;
export const BB_STD = 2;
export const MACD_FAST = 12;
export const MACD_SLOW = 26;
export const MACD_SIGNAL = 9;
export const ATR_PERIOD = 14;
export const ADX_PERIOD = 14;

// Backtest
export const INITIAL_CAPITAL = 10_000;
export const COMMISSION = 0.0;

// Chart warmup — need 200 candles for SMA(200)
export const WARMUP = 200;

// Colors
export const COLORS = {
  bg: '#1a1a2e',
  panelBg: '#16213e',
  text: '#e0e0e0',
  textDim: '#888',
  grid: '#1e2d4a',
  border: '#2a3a5c',
  // Candles
  up: '#26a69a',
  down: '#ef5350',
  // Indicators
  sma50: '#ff9800',
  sma200: '#2196f3',
  ema50: '#e040fb',
  bbUpper: '#78909c',
  bbLower: '#78909c',
  bbMiddle: '#546e7a',
  // RSI
  rsiLine: '#7c4dff',
  rsiHigh: '#ef5350',
  rsiMid: '#ff9800',
  rsiLow: '#26a69a',
  // MACD
  macdLine: '#2196f3',
  macdSignal: '#ff9800',
  macdHistUp: '#26a69a',
  macdHistDown: '#ef5350',
  // Markers
  buy: '#26a69a',
  sell: '#ef5350',
};
