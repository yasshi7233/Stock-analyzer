import numpy as np
import pandas as pd
import pytest

from indicators import add_macd, add_rsi, add_sma


@pytest.fixture
def sample_df():
    """Generates deterministic sample price data for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Linear price trend with known properties
    prices = [100.0 + (i * 0.5) for i in range(100)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p + 1.0 for p in prices],
            "Low": [p - 1.0 for p in prices],
            "Close": prices,
            "Volume": [1000000] * 100,
        },
        index=dates,
    )


class TestIndicators:
    def test_add_sma_calculation(self, sample_df):
        result = add_sma(sample_df, window=20)
        assert "SMA_20" in result.columns
        # First 19 rows should be NaN for a 20-period SMA
        assert result["SMA_20"].iloc[:19].isna().all()
        # Row 20 should equal the mean of the first 20 close prices
        expected_20 = sample_df["Close"].iloc[:20].mean()
        assert np.isclose(result["SMA_20"].iloc[19], expected_20)

    def test_indicators_do_not_mutate_input(self, sample_df):
        original_cols = list(sample_df.columns)
        _ = add_sma(sample_df, 20)
        assert list(sample_df.columns) == original_cols

        _ = add_rsi(sample_df, 14)
        assert list(sample_df.columns) == original_cols

        _ = add_macd(sample_df)
        assert list(sample_df.columns) == original_cols

    def test_missing_close_column_raises_error(self):
        bad_df = pd.DataFrame({"Price": [10, 20, 30]})
        with pytest.raises(ValueError, match="Close"):
            add_sma(bad_df, 10)
        with pytest.raises(ValueError, match="Close"):
            add_rsi(bad_df, 14)
        with pytest.raises(ValueError, match="Close"):
            add_macd(bad_df)

    def test_non_numeric_close_column_raises_error(self):
        non_numeric_df = pd.DataFrame({"Close": ["abc", "def", "ghi"]})
        with pytest.raises(ValueError, match="valid numeric data"):
            add_sma(non_numeric_df, 2)

    def test_invalid_input_types_and_parameters(self, sample_df):
        with pytest.raises(TypeError):
            add_sma("not a dataframe", 20)
        with pytest.raises(ValueError):
            add_sma(sample_df, -5)
        with pytest.raises(ValueError):
            add_rsi(sample_df, 0)
        with pytest.raises(ValueError):
            add_macd(sample_df, fast=26, slow=12)
        with pytest.raises(ValueError, match="positive integers"):
            add_macd(sample_df, fast=0, slow=26, signal=9)

    def test_rsi_flat_prices(self):
        # Flat prices (zero gain and zero loss)
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        flat_df = pd.DataFrame({"Close": [100.0] * 30}, index=dates)
        result = add_rsi(flat_df, period=14)
        # Warmup period is NaN: diff() creates 1 NaN, min_periods=14 requires 14 differences -> index 0..13 are NaN
        assert result["RSI"].iloc[:14].isna().all()
        # After warmup (index 14+), flat prices should yield 50.0
        assert (result["RSI"].iloc[14:] == 50.0).all()

    def test_rsi_pure_uptrend(self):
        # Pure gain (zero loss) -> RSI should reach 100.0
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        uptrend_df = pd.DataFrame({"Close": [float(i + 1) for i in range(30)]}, index=dates)
        result = add_rsi(uptrend_df, period=14)
        assert (result["RSI"].iloc[14:] == 100.0).all()

    def test_rsi_pure_downtrend(self):
        # Pure loss (zero gain) -> RSI should reach 0.0
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        downtrend_df = pd.DataFrame({"Close": [float(100 - i) for i in range(30)]}, index=dates)
        result = add_rsi(downtrend_df, period=14)
        assert (result["RSI"].iloc[14:] == 0.0).all()

    def test_macd_columns_and_warmup(self, sample_df):
        result = add_macd(sample_df, fast=12, slow=26, signal=9)
        assert "MACD" in result.columns
        assert "MACD_Signal" in result.columns
        assert "MACD_Hist" in result.columns
        # MACD_Hist = MACD - MACD_Signal
        diff = result["MACD"] - result["MACD_Signal"]
        assert np.allclose(result["MACD_Hist"], diff)