import pandas as pd
import numpy as np


def _validate_close_series(df: pd.DataFrame) -> pd.Series:
    """Validates that df is a DataFrame and contains 'Close' column.

    Returns the 'Close' series as float type.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column.")
    close_series = pd.to_numeric(df["Close"], errors="coerce")
    if close_series.dropna().empty:
        raise ValueError("DataFrame 'Close' column has no valid numeric data.")
    return close_series


def add_sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Adds a Simple Moving Average (SMA) column without mutating the input DataFrame.

    Parameters:
        df: pandas DataFrame containing at least a 'Close' column.
        window: Integer window period for the SMA (must be >= 1).

    Returns:
        A new DataFrame with column SMA_{window} added.
    """
    if not isinstance(window, int) or window < 1:
        raise ValueError(f"Window must be a positive integer, got: {window}")

    close_series = _validate_close_series(df)
    out = df.copy()
    out[f"SMA_{window}"] = close_series.rolling(window=window).mean()
    return out


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Adds the Relative Strength Index (RSI) using Wilder's smoothing method

    without mutating the input DataFrame.

    Parameters:
        df: pandas DataFrame containing at least a 'Close' column.
        period: RSI lookback period (default 14, must be >= 1).

    Returns:
        A new DataFrame with column 'RSI' added.
    """
    if not isinstance(period, int) or period < 1:
        raise ValueError(f"Period must be a positive integer, got: {period}")

    close_series = _validate_close_series(df)
    out = df.copy()

    delta = close_series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    # Wilder's Smoothing: alpha = 1 / period (equivalent to com = period - 1)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    # Safe RSI calculation:
    # 1. When avg_loss == 0 and avg_gain == 0 (e.g. flat prices): RSI = 50.0
    # 2. When avg_loss == 0 and avg_gain > 0: RSI = 100.0
    # 3. When avg_gain == 0 and avg_loss > 0: RSI = 0.0
    # 4. Otherwise: RS = avg_gain / avg_loss, RSI = 100 - (100 / (1 + RS))
    rsi = pd.Series(np.nan, index=df.index, dtype=float)

    both_zero = (avg_gain == 0.0) & (avg_loss == 0.0)
    zero_loss = (avg_loss == 0.0) & (avg_gain > 0.0)
    zero_gain = (avg_gain == 0.0) & (avg_loss > 0.0)
    standard = (avg_loss > 0.0) & (avg_gain > 0.0)

    rsi[both_zero] = 50.0
    rsi[zero_loss] = 100.0
    rsi[zero_gain] = 0.0

    rs = avg_gain[standard] / avg_loss[standard]
    rsi[standard] = 100.0 - (100.0 / (1.0 + rs))

    # Any index before min_periods remains NaN
    out["RSI"] = rsi
    return out


def add_macd(
    df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Adds MACD, MACD_Signal, and MACD_Hist columns without mutating the input DataFrame.

    Parameters:
        df: pandas DataFrame containing at least a 'Close' column.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal EMA period (default 9).

    Returns:
        A new DataFrame with MACD, MACD_Signal, and MACD_Hist added.
    """
    if fast <= 0 or slow <= 0 or signal <= 0:
        raise ValueError("MACD parameters (fast, slow, signal) must be positive integers.")
    if fast >= slow:
        raise ValueError(f"Fast period ({fast}) must be less than slow period ({slow}).")

    close_series = _validate_close_series(df)
    out = df.copy()

    ema_fast = close_series.ewm(span=fast, adjust=False).mean()
    ema_slow = close_series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line

    out["MACD"] = macd_line
    out["MACD_Signal"] = signal_line
    out["MACD_Hist"] = macd_hist
    return out