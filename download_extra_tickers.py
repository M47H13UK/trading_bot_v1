"""Download ~69 extra tickers (daily + hourly) for ML training."""
import pandas as pd
import yfinance as yf
from pathlib import Path

DAILY_DIR = Path(__file__).parent / "test_data" / "daily"
HOURLY_DIR = Path(__file__).parent / "test_data" / "hourly"

EXTRA_TICKERS = [
    # Tech mega-cap
    "GOOGL", "GOOG", "META", "NVDA", "NFLX", "AVGO", "CRM", "ADBE", "INTC", "AMD", "ORCL", "CSCO",
    # Blue chip / defensive
    "PG", "KO", "PEP", "MRK", "PFE", "ABT", "UNH", "LLY",
    # Consumer / retail
    "HD", "COST", "MCD", "NKE", "SBUX", "TGT", "LOW",
    # Financial
    "GS", "MS", "BAC", "C", "BRK-B", "AXP", "V", "MA",
    # Industrial / energy
    "CAT", "DE", "BA", "GE", "HON", "LMT", "RTX", "CVX", "COP", "SLB",
    # International ETF
    "EWZ", "EWT", "EWY", "INDA", "EWC", "EWA", "EWH", "EWS", "THD", "VGK",
    # Commodity ETF
    "PPLT", "DBA", "WEAT", "CORN", "URA",
    # Other popular
    "DIS", "T", "VZ", "CMCSA", "PYPL", "SQ", "UBER", "ABNB", "COIN",
]


def sanitize(t):
    return t.replace("-", "_").replace("^", "")


def download(ticker, period, interval, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{sanitize(ticker)}.csv"
    if path.exists():
        return True
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if data.empty:
            print(f"  SKIP {ticker} [{interval}]: no data")
            return False
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index.name = "Date"
        data.to_csv(path)
        print(f"  OK {ticker} [{interval}]: {len(data)} bars")
        return True
    except Exception as e:
        print(f"  ERR {ticker} [{interval}]: {e}")
        return False


if __name__ == "__main__":
    print(f"Downloading {len(EXTRA_TICKERS)} extra tickers...")

    print("\n--- Daily (10y) ---")
    ok_d = sum(download(t, "10y", "1d", DAILY_DIR) for t in EXTRA_TICKERS)
    print(f"Daily: {ok_d}/{len(EXTRA_TICKERS)} done")

    print("\n--- Hourly (2y) ---")
    ok_h = sum(download(t, "2y", "1h", HOURLY_DIR) for t in EXTRA_TICKERS)
    print(f"Hourly: {ok_h}/{len(EXTRA_TICKERS)} done")

    total_daily = len(list(DAILY_DIR.glob("*.csv")))
    total_hourly = len(list(HOURLY_DIR.glob("*.csv")))
    print(f"\nTotal: {total_daily} daily, {total_hourly} hourly files")
