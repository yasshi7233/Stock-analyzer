from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from sentiment import (
    NEGATIVE_THRESHOLD,
    POSITIVE_THRESHOLD,
    classify_polarity,
    get_sentiment,
    get_sentiment_summary,
)


class TestSentiment:
    def test_classify_polarity_thresholds(self):
        assert classify_polarity(0.5) == "Positive"
        assert classify_polarity(0.101) == "Positive"
        assert classify_polarity(0.1) == "Neutral"
        assert classify_polarity(0.0) == "Neutral"
        assert classify_polarity(-0.1) == "Neutral"
        assert classify_polarity(-0.101) == "Negative"
        assert classify_polarity(-0.8) == "Negative"

    def test_get_sentiment_summary_empty(self):
        summary, avg = get_sentiment_summary(pd.DataFrame())
        assert summary == "No data"
        assert avg is None

        summary, avg = get_sentiment_summary(None)
        assert summary == "No data"
        assert avg is None

    def test_get_sentiment_summary_valid(self):
        df = pd.DataFrame(
            {
                "Headline": ["H1", "H2", "H3"],
                "polarity": [0.6, -0.4, 0.0],
                "subjectivity": [0.5, 0.5, 0.1],
                "Sentiment": ["Positive", "Negative", "Neutral"],
            }
        )
        summary, avg = get_sentiment_summary(df)
        assert "0.067" in str(avg) or round(avg, 2) == 0.07
        assert "1 positive, 1 negative, 1 neutral" in summary

    @patch("sentiment.yf.Ticker")
    def test_get_sentiment_parses_new_and_old_structures(self, mock_ticker):
        # Mock Yahoo news response covering both modern format (nested content) and older format
        mock_instance = MagicMock()
        mock_instance.news = [
            {"content": {"title": "Great outstanding record profits and excellent growth"}},
            {"title": "Terrible loss and painful bankruptcy lawsuit"},
            {"content": {"title": "Company holds annual shareholder meeting"}},
            {"content": {}},  # missing title
            "invalid_entry",  # malformed entry
        ]
        mock_ticker.return_value = mock_instance

        df = get_sentiment("TEST")
        assert len(df) == 3
        assert list(df.columns) == ["Headline", "polarity", "subjectivity", "Sentiment"]
        assert df["Sentiment"].iloc[0] == "Positive"
        assert df["Sentiment"].iloc[1] == "Negative"
        assert df["Sentiment"].iloc[2] == "Neutral"

    @patch("sentiment.yf.Ticker")
    def test_get_sentiment_network_failure(self, mock_ticker):
        mock_ticker.side_effect = ConnectionError("Network unreachable")
        df = get_sentiment("FAIL")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_sentiment_invalid_ticker(self):
        assert get_sentiment("").empty
        assert get_sentiment(None).empty