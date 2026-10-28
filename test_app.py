from datetime import date, datetime, timedelta
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import streamlit as st
import app
from validation import clean_ticker_input, validate_date_range


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """Ensures Streamlit caches do not leak between test runs."""
    st.cache_data.clear()
    app.cached_fetch_data.clear()
    app.cached_sentiment_data.clear()
    yield
    st.cache_data.clear()
    app.cached_fetch_data.clear()
    app.cached_sentiment_data.clear()


class TestValidationLogic:
    """Unit tests for the centralized validation module."""

    def test_clean_ticker_input_valid(self):
        assert clean_ticker_input("  aapl  ") == "AAPL"
        assert clean_ticker_input("msft") == "MSFT"
        assert clean_ticker_input("  reliance.ns  ") == "RELIANCE.NS"
        assert clean_ticker_input("brk.a") == "BRK.A"

    def test_clean_ticker_input_invalid_and_empty(self):
        assert clean_ticker_input("") == ""
        assert clean_ticker_input("   ") == ""
        assert clean_ticker_input(None) == ""
        assert clean_ticker_input(123) == ""
        assert clean_ticker_input(["AAPL"]) == ""
        assert clean_ticker_input({}) == ""

    def test_validate_date_range_valid_date_objects(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        valid, msg = validate_date_range(yesterday, today)
        assert valid is True
        assert msg == ""

    def test_validate_date_range_valid_iso_strings(self):
        valid, msg = validate_date_range("2023-01-01", "2023-12-31")
        assert valid is True
        assert msg == ""

    def test_validate_date_range_datetime_objects(self):
        dt_start = datetime(2023, 1, 1, 10, 0)
        dt_end = datetime(2023, 1, 2, 10, 0)
        valid, msg = validate_date_range(dt_start, dt_end)
        assert valid is True
        assert msg == ""

    def test_validate_date_range_same_dates(self):
        today = date.today()
        valid, msg = validate_date_range(today, today)
        assert valid is False
        assert "Start date must be before end date." in msg

    def test_validate_date_range_inverted_dates(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        valid, msg = validate_date_range(tomorrow, today)
        assert valid is False
        assert "Start date must be before end date." in msg

    def test_validate_date_range_empty_or_none(self):
        valid, msg = validate_date_range(None, date.today())
        assert valid is False
        assert "Start date and end date must not be empty." in msg

        valid, msg = validate_date_range(date.today(), None)
        assert valid is False
        assert "Start date and end date must not be empty." in msg

    def test_validate_date_range_malformed_string(self):
        valid, msg = validate_date_range("not-a-date", "2023-12-31")
        assert valid is False
        assert "Invalid start date format" in msg

        valid, msg = validate_date_range("2023-01-01", "invalid-end")
        assert valid is False
        assert "Invalid end date format" in msg

    def test_validate_date_range_invalid_types(self):
        valid, msg = validate_date_range(12345, 67890)
        assert valid is False
        assert "Start date and end date must be valid date objects." in msg


@pytest.fixture
def sample_market_data():
    dates = pd.date_range("2023-01-01", periods=120, freq="D")
    df = pd.DataFrame(
        {
            "Open": 100.0,
            "High": 105.0,
            "Low": 95.0,
            "Close": 100.0 + np.arange(120) * 0.5,
            "Volume": 1000000,
        },
        index=dates,
    )
    meta = {"currency": "USD", "symbol": "AAPL", "shortName": "Apple Inc."}
    return df, meta


class TestStreamlitAppUI:
    """Integration tests for Streamlit app interactions and session state persistence."""

    def test_app_initial_state(self):
        at = AppTest.from_file("app.py", default_timeout=15)
        at.run()
        assert len(at.exception) == 0
        assert len(at.info) >= 1
        assert "analysis_data" in at.session_state
        assert at.session_state["analysis_data"] is None

    def test_app_run_analysis_and_session_state_persistence(self, sample_market_data):
        df, meta = sample_market_data
        with patch("fetch.fetch_stock_data", return_value=(df, meta)), patch(
            "sentiment.get_sentiment", return_value=pd.DataFrame()
        ):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()

            # Click Run Analysis
            at.sidebar.button[0].click().run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"] is not None
            assert at.session_state["analysis_data"]["ticker"] == "AAPL"

            # Display controls change (toggle RSI off) must not erase analysis
            at.sidebar.checkbox[1].uncheck().run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"] is not None
            assert at.session_state["analysis_data"]["ticker"] == "AAPL"

            # Display controls change (toggle SMA off) must not erase analysis
            at.sidebar.checkbox[0].uncheck().run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"] is not None

    def test_app_ticker_change_prevents_stale_results(self, sample_market_data):
        df, meta = sample_market_data
        with patch("fetch.fetch_stock_data", return_value=(df, meta)), patch(
            "sentiment.get_sentiment", return_value=pd.DataFrame()
        ):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert at.session_state["analysis_data"] is not None

            # Change ticker input without clicking Run Analysis
            at.sidebar.text_input[0].input("MSFT").run()
            assert len(at.exception) == 0
            assert len(at.warning) >= 1
            assert any("MSFT" in w.value for w in at.warning)
            # Stale AAPL tabs/chart headers should not be shown
            subheaders = [s.value for s in at.subheader]
            assert "AAPL Price and Technical Indicators" not in subheaders

    def test_app_failed_fetch_clears_state(self):
        with patch("fetch.fetch_stock_data", side_effect=ConnectionError("Offline")):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert len(at.error) >= 1
            assert any("Unable to connect" in e.value for e in at.error)
            assert at.session_state["analysis_data"] is None

    def test_app_empty_market_data_clears_state(self):
        with patch("fetch.fetch_stock_data", return_value=(pd.DataFrame(), {})):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert len(at.error) >= 1
            assert any("No price data found" in e.value for e in at.error)
            assert at.session_state["analysis_data"] is None

    def test_app_run_analysis_with_sentiment_data(self, sample_market_data):
        df, meta = sample_market_data
        sentiment_df = pd.DataFrame(
            {
                "Headline": ["Positive news about company", "Negative lawsuit filed", "Neutral earnings update"],
                "polarity": [0.6, -0.5, 0.0],
                "subjectivity": [0.5, 0.4, 0.1],
                "Sentiment": ["Positive", "Negative", "Neutral"],
            }
        )
        with patch("fetch.fetch_stock_data", return_value=(df, meta)), patch(
            "sentiment.get_sentiment", return_value=sentiment_df
        ):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"] is not None
            # Check sentiment summary banner was rendered (Neutral average triggers warning badge)
            assert any("Overall Sentiment" in w.value for w in at.warning)

    def test_app_invalid_date_stops_analysis(self):
        at = AppTest.from_file("app.py", default_timeout=15)
        at.run()
        # Set start date to today and end date to yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)
        at.sidebar.date_input[1].set_value(today)      # Start date
        at.sidebar.date_input[0].set_value(yesterday)  # End date
        at.sidebar.button[0].click().run()
        assert len(at.error) >= 1
        assert any("invalid date range" in e.value for e in at.error)
        assert at.session_state["analysis_data"] is None

    def test_app_empty_ticker_stops_analysis(self):
        at = AppTest.from_file("app.py", default_timeout=15)
        at.run()
        at.sidebar.text_input[0].input("   ")
        at.sidebar.button[0].click().run()
        assert len(at.error) >= 1
        assert any("valid stock ticker" in e.value for e in at.error)
        assert at.session_state["analysis_data"] is None

    def test_app_initial_capital_recalculation(self, sample_market_data):
        df, meta = sample_market_data
        with patch("fetch.fetch_stock_data", return_value=(df, meta)), patch(
            "sentiment.get_sentiment", return_value=pd.DataFrame()
        ):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert at.session_state["analysis_data"]["initial_capital"] == 100000.0

            # Change capital to 50000
            at.sidebar.number_input[0].set_value(50000.0).run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"]["initial_capital"] == 50000.0
            assert at.session_state["analysis_data"]["metrics"]["initial_capital"] == 50000.0

    def test_app_backtest_error_handling(self):
        # Short data (20 days) where SMA-50 cannot warm up
        short_dates = pd.date_range("2023-01-01", periods=20, freq="D")
        short_df = pd.DataFrame(
            {"Open": 100.0, "High": 105.0, "Low": 95.0, "Close": 100.0, "Volume": 1000},
            index=short_dates,
        )
        meta = {"currency": "USD", "symbol": "SHORT", "shortName": "Short Co."}
        with patch("fetch.fetch_stock_data", return_value=(short_df, meta)), patch(
            "sentiment.get_sentiment", return_value=pd.DataFrame()
        ):
            at = AppTest.from_file("app.py", default_timeout=15)
            at.run()
            at.sidebar.button[0].click().run()
            assert len(at.exception) == 0
            assert at.session_state["analysis_data"] is not None
            assert at.session_state["analysis_data"]["bt_error"] is not None
            assert any("Backtest cannot be completed" in w.value for w in at.warning)
