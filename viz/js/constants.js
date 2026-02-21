// Asset categories for the picker modal
export const ASSET_CATEGORIES = {
  'Indexes': ['SPY', 'QQQ', 'DIA', 'IWM'],
  'Stocks': ['AAPL', 'AMZN', 'JNJ', 'JPM', 'MSFT', 'TSLA', 'WMT', 'XOM'],
  'Crypto': ['BTC_USD', 'ETH_USD'],
  'Commodities': ['GLD', 'SLV', 'UNG', 'USO'],
  'Bonds': ['TLT', 'IEF', 'SHY'],
  'Sectors': ['XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY'],
  'International': ['EEM', 'EFA', 'EWG', 'EWJ', 'EWU', 'FXI'],
  'Currency': ['FXB', 'FXE', 'FXY', 'UUP'],
};

// Flat list for backwards compat
export const TICKERS = Object.values(ASSET_CATEGORIES).flat();

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

// Asset descriptions — full name + one-liner
export const ASSET_INFO = {
  SPY:     { name: 'S&P 500 ETF',              desc: 'Tracks 500 largest US companies' },
  QQQ:     { name: 'Nasdaq 100 ETF',           desc: 'Tech-heavy large-cap index' },
  DIA:     { name: 'Dow Jones ETF',            desc: '30 blue-chip US stocks' },
  IWM:     { name: 'Russell 2000 ETF',         desc: 'Small-cap US stocks' },
  AAPL:    { name: 'Apple Inc',                desc: 'Consumer electronics & services' },
  AMZN:    { name: 'Amazon.com',               desc: 'E-commerce & cloud (AWS)' },
  JNJ:     { name: 'Johnson & Johnson',        desc: 'Pharma & consumer health' },
  JPM:     { name: 'JPMorgan Chase',           desc: 'Largest US bank' },
  MSFT:    { name: 'Microsoft',                desc: 'Software, cloud (Azure), AI' },
  TSLA:    { name: 'Tesla Inc',                desc: 'Electric vehicles & energy' },
  WMT:     { name: 'Walmart',                  desc: 'Retail giant' },
  XOM:     { name: 'ExxonMobil',               desc: 'Oil & gas major' },
  BTC_USD: { name: 'Bitcoin',                  desc: 'Largest cryptocurrency' },
  ETH_USD: { name: 'Ethereum',                 desc: 'Smart contract platform' },
  GLD:     { name: 'Gold ETF',                 desc: 'Tracks gold spot price' },
  SLV:     { name: 'Silver ETF',               desc: 'Tracks silver spot price' },
  UNG:     { name: 'Natural Gas ETF',          desc: 'Tracks natgas futures' },
  USO:     { name: 'Crude Oil ETF',            desc: 'Tracks WTI crude oil' },
  TLT:     { name: '20+ Year Treasury ETF',    desc: 'Long-term US government bonds' },
  IEF:     { name: '7-10 Year Treasury ETF',   desc: 'Medium-term US bonds' },
  SHY:     { name: '1-3 Year Treasury ETF',    desc: 'Short-term US bonds' },
  XLB:     { name: 'Materials Sector',         desc: 'Chemicals, mining, packaging' },
  XLE:     { name: 'Energy Sector',            desc: 'Oil, gas, energy equipment' },
  XLF:     { name: 'Financials Sector',        desc: 'Banks, insurance, capital markets' },
  XLI:     { name: 'Industrials Sector',       desc: 'Aerospace, defense, transport' },
  XLK:     { name: 'Technology Sector',        desc: 'Software, hardware, semiconductors' },
  XLP:     { name: 'Consumer Staples',         desc: 'Food, beverage, household products' },
  XLRE:    { name: 'Real Estate Sector',       desc: 'REITs & real estate services' },
  XLU:     { name: 'Utilities Sector',         desc: 'Electric, gas, water utilities' },
  XLV:     { name: 'Healthcare Sector',        desc: 'Pharma, biotech, medical devices' },
  XLY:     { name: 'Consumer Discretionary',   desc: 'Retail, auto, leisure' },
  EEM:     { name: 'Emerging Markets ETF',     desc: 'China, India, Brazil, Taiwan stocks' },
  EFA:     { name: 'Developed Markets ETF',    desc: 'Europe, Japan, Australia ex-US' },
  EWG:     { name: 'Germany ETF',              desc: 'Tracks DAX / German equities' },
  EWJ:     { name: 'Japan ETF',                desc: 'Tracks Nikkei / Japanese equities' },
  EWU:     { name: 'United Kingdom ETF',       desc: 'Tracks FTSE / UK equities' },
  FXI:     { name: 'China Large-Cap ETF',      desc: 'Top 50 Chinese companies' },
  FXB:     { name: 'British Pound ETF',        desc: 'GBP/USD currency exposure' },
  FXE:     { name: 'Euro ETF',                 desc: 'EUR/USD currency exposure' },
  FXY:     { name: 'Japanese Yen ETF',         desc: 'JPY/USD currency exposure' },
  UUP:     { name: 'US Dollar Index ETF',      desc: 'Dollar strength vs basket' },
};

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
