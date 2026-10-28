from datetime import date, timedelta
import pandas as pd
import pytest


def clean_ticker_input(ticker: str) -> str:
    """Helper representing the ticker cleaning logic."""
    if not ticker or not isinstance(ticker, str):
        return ""
    return ticker.strip().upper()


def validate_date_range(start_date: date, end_date: date) -> tuple[bool, str]:
    """Helper representing the date range validation logic."""
    if start_date >= end_date:
        return False, "Start date must be before end date."
    return True, ""


class TestAppLogic:
    def test_ticker_cleaning(self):
        assert clean_ticker_input("  aapl  ") == "AAPL"
        assert clean_ticker_input("msft") == "MSFT"
        assert clean_ticker_input("  reliance.ns  ") == "RELIANCE.NS"
        assert clean_ticker_input("") == ""
        assert clean_ticker_input(None) == ""

    def test_date_range_validation(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        valid, _ = validate_date_range(yesterday, today)
        assert valid is True

        invalid_same, msg = validate_date_range(today, today)
        assert invalid_same is False
        assert "Start date must be before end date." in msg

        invalid_reversed, msg = validate_date_range(tomorrow, today)
        assert invalid_reversed is False
        assert "Start date must be before end date." in msg
