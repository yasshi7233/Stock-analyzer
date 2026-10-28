from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from fetch import display_summary, fetch_stock_data


@pytest.fixture
def sample_ohlcv_df():
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(10)],
            "High": [105.0 + i for i in range(10)],
            "Low": [95.0 + i for i in range(10)],
            "Close": [102.0 + i for i in range(10)],
            "Volume": [1000000 + (i * 1000) for i in range(10)],
        },
        index=dates,
    )


class TestFetchStockData:
    @patch("fetch.yf.Ticker")
    def test_fetch_stock_data_with_date_range(self, mock_ticker_cls, sample_ohlcv_df):
        mock_stock = MagicMock()
        mock_stock.history.return_value = sample_ohlcv_df.copy()
        mock_stock.fast_info.currency = "USD"
        mock_ticker_cls.return_value = mock_stock

        df, metadata = fetch_stock_data("  aapl  ", start="2023-01-01", end="2023-01-10")

        mock_ticker_cls.assert_called_once_with("AAPL")
        mock_stock.history.assert_called_once_with(start="2023-01-01", end="2023-01-10", auto_adjust=False)
        assert not df.empty
        assert len(df) == 10
        assert metadata["currency"] == "USD"
        assert metadata["symbol"] == "AAPL"

    @patch("fetch.yf.Ticker")
    def test_fetch_stock_data_with_period(self, mock_ticker_cls, sample_ohlcv_df):
        mock_stock = MagicMock()
        mock_stock.history.return_value = sample_ohlcv_df.copy()
        mock_stock.fast_info.currency = "INR"
        mock_ticker_cls.return_value = mock_stock

        df, metadata = fetch_stock_data("RELIANCE.NS", period="6mo")

        mock_stock.history.assert_called_once_with(period="6mo", auto_adjust=False)
        assert len(df) == 10
        assert metadata["currency"] == "INR"

    @patch("fetch.yf.download")
    @patch("fetch.yf.Ticker")
    def test_fetch_fallback_to_download_when_history_empty(
        self, mock_ticker_cls, mock_download, sample_ohlcv_df
    ):
        mock_stock = MagicMock()
        mock_stock.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_stock
        mock_download.return_value = sample_ohlcv_df.copy()

        df, metadata = fetch_stock_data("MSFT", period="1y")

        mock_download.assert_called_once()
        assert not df.empty
        assert len(df) == 10

    @patch("fetch.yf.download")
    @patch("fetch.yf.Ticker")
    def test_fetch_returns_empty_when_all_fail(self, mock_ticker_cls, mock_download):
        mock_stock = MagicMock()
        mock_stock.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_stock
        mock_download.return_value = pd.DataFrame()

        df, metadata = fetch_stock_data("NONEXISTENT")

        assert df.empty
        assert metadata["symbol"] == "NONEXISTENT"

    @patch("fetch.yf.Ticker")
    def test_fetch_missing_required_columns(self, mock_ticker_cls):
        mock_stock = MagicMock()
        # Missing 'Volume'
        mock_stock.history.return_value = pd.DataFrame(
            {"Open": [10.0], "High": [12.0], "Low": [9.0], "Close": [11.0]}
        )
        mock_ticker_cls.return_value = mock_stock

        df, metadata = fetch_stock_data("INCOMPLETE")
        assert df.empty

    @patch("fetch.yf.Ticker")
    def test_fetch_tz_localization(self, mock_ticker_cls):
        # Create timezone-aware index
        tz_dates = pd.date_range("2023-01-01", periods=5, freq="D", tz="America/New_York")
        tz_df = pd.DataFrame(
            {
                "Open": [100.0] * 5,
                "High": [105.0] * 5,
                "Low": [95.0] * 5,
                "Close": [102.0] * 5,
                "Volume": [1000] * 5,
            },
            index=tz_dates,
        )
        mock_stock = MagicMock()
        mock_stock.history.return_value = tz_df
        mock_ticker_cls.return_value = mock_stock

        df, _ = fetch_stock_data("TZTEST")
        assert df.index.tz is None

    @patch("fetch.yf.download")
    @patch("fetch.yf.Ticker")
    def test_fetch_multiindex_columns_flattening(
        self, mock_ticker_cls, mock_download, sample_ohlcv_df
    ):
        mock_stock = MagicMock()
        mock_stock.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_stock

        # Create multi-index columns like yf.download sometimes returns
        multi_cols = pd.MultiIndex.from_tuples(
            [(c, "AAPL") for c in ["Open", "High", "Low", "Close", "Volume"]]
        )
        multi_df = sample_ohlcv_df.copy()
        multi_df.columns = multi_cols
        mock_download.return_value = multi_df

        df, _ = fetch_stock_data("AAPL")
        assert not df.empty
        assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]

    @patch("fetch.yf.Ticker")
    def test_fetch_fallback_info_when_fast_info_missing(self, mock_ticker_cls, sample_ohlcv_df):
        mock_stock = MagicMock(spec=["history", "info"])
        mock_stock.history.return_value = sample_ohlcv_df.copy()
        mock_stock.info = {"currency": "EUR", "shortName": "Euro Stock"}
        mock_ticker_cls.return_value = mock_stock

        df, metadata = fetch_stock_data("EURO")
        assert metadata["currency"] == "EUR"
        assert metadata["shortName"] == "Euro Stock"


class TestDisplaySummary:
    def test_display_summary_with_data(self, sample_ohlcv_df, capsys):
        display_summary(sample_ohlcv_df, "AAPL", "USD")
        captured = capsys.readouterr().out
        assert "Summary for AAPL" in captured
        assert "Total trading days: 10" in captured
        assert "USD" in captured

    def test_display_summary_empty(self, capsys):
        display_summary(pd.DataFrame(), "AAPL")
        captured = capsys.readouterr().out
        assert "No data available for AAPL" in captured

