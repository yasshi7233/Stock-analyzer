import pandas as pd
import yfinance as yf


def fetch_stock_data(ticker: str, period: str = "1y", start=None, end=None) -> tuple[pd.DataFrame, dict]:
    """Fetches historical OHLCV data and ticker info from Yahoo Finance.

    Parameters:
        ticker: Cleaned ticker symbol (e.g. 'AAPL', 'RELIANCE.NS').
        period: Valid yfinance period string (e.g. '1y', '5y') if start/end not used.
        start: Optional start date (string or date object).
        end: Optional end date (string or date object).

    Returns:
        tuple (df, metadata)
        - df: Cleaned DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        - metadata: dict with keys 'currency', 'shortName', 'symbol'
    """
    clean_ticker = ticker.strip().upper()
    stock = yf.Ticker(clean_ticker)

    if start is not None and end is not None:
        df = stock.history(start=start, end=end, auto_adjust=False)
    else:
        df = stock.history(period=period, auto_adjust=False)

    if df.empty:
        # Fallback to yf.download in case history returns empty
        df = yf.download(clean_ticker, start=start, end=end, progress=False, auto_adjust=False)

    metadata = {"currency": "USD", "shortName": clean_ticker, "symbol": clean_ticker}

    try:
        # fast_info is significantly faster than stock.info
        fast_info = getattr(stock, "fast_info", None)
        if fast_info:
            metadata["currency"] = getattr(fast_info, "currency", "USD") or "USD"
        elif hasattr(stock, "info") and stock.info:
            metadata["currency"] = stock.info.get("currency", "USD") or "USD"
            metadata["shortName"] = stock.info.get("shortName", clean_ticker)
    except Exception:
        pass

    if df.empty:
        return pd.DataFrame(), metadata

    # Handle MultiIndex columns if returned by yf.download
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    available_cols = [c for c in required_cols if c in df.columns]
    if len(available_cols) < len(required_cols):
        return pd.DataFrame(), metadata

    df = df[required_cols].copy()
    # Normalize index to DatetimeIndex without timezone for clean plotting
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    df.dropna(subset=["Close"], inplace=True)
    return df, metadata


def display_summary(df: pd.DataFrame, ticker: str, currency: str = "USD"):
    """Displays a console summary of the stock data."""
    if df.empty:
        print(f"No data available for {ticker}")
        return

    print(f"--- Summary for {ticker} ---")
    print(f"Total trading days: {len(df)}")
    print(f"Latest closing price: {currency} {df['Close'].iloc[-1]:.2f}")
    print(f"Average daily volume: {int(df['Volume'].mean()):,}")
    print(df.head())


if __name__ == "__main__":
    user_ticker = input("Enter the stock ticker symbol (e.g., AAPL): ").strip().upper()
    if user_ticker:
        data, meta = fetch_stock_data(user_ticker)
        if not data.empty:
            display_summary(data, user_ticker, meta.get("currency", "USD"))
        else:
            print(f"No data could be retrieved for ticker '{user_ticker}'.")