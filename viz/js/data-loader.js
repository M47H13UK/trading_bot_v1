// CSV loader using PapaParse — fetches from ../test_data/{TICKER}.csv
const cache = {};

export async function loadTicker(ticker) {
  if (cache[ticker]) return cache[ticker];

  const url = `../test_data/daily/${ticker}.csv`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to fetch ${url}: ${resp.status}`);
  const text = await resp.text();

  const parsed = Papa.parse(text.trim(), { header: true, skipEmptyLines: true });
  if (parsed.errors.length) console.warn('CSV parse warnings:', parsed.errors);

  const rows = parsed.data.map(r => ({
    time: r.Date,                     // YYYY-MM-DD string — Lightweight Charts handles it
    open: +r.Open,
    high: +r.High,
    low: +r.Low,
    close: +r.Close,
    volume: +r.Volume,
  })).filter(r => !isNaN(r.close) && r.time);

  // Sort chronologically
  rows.sort((a, b) => (a.time < b.time ? -1 : 1));

  cache[ticker] = rows;
  return rows;
}
