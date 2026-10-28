import pandas as pd
from textblob import TextBlob
import yfinance as yf

# Shared sentiment classification thresholds
POSITIVE_THRESHOLD = 0.1
NEGATIVE_THRESHOLD = -0.1


def classify_polarity(polarity: float) -> str:
    """Classifies a polarity score into 'Positive', 'Negative', or 'Neutral'

    using standard shared thresholds.
    """
    if polarity > POSITIVE_THRESHOLD:
        return "Positive"
    elif polarity < NEGATIVE_THRESHOLD:
        return "Negative"
    return "Neutral"


def get_sentiment(ticker: str) -> pd.DataFrame:
    """Fetches latest news headlines for a ticker from Yahoo Finance

    and computes sentiment polarity and subjectivity using TextBlob.

    Returns:
        DataFrame with columns: Headline, polarity, subjectivity, Sentiment.
        Returns an empty DataFrame if no news is available or on network/API failure.
    """
    if not ticker or not isinstance(ticker, str):
        return pd.DataFrame()

    try:
        stock = yf.Ticker(ticker.strip().upper())
        news = getattr(stock, "news", None)
    except Exception:
        # Fallback gracefully on network or unexpected Yahoo Finance issues
        return pd.DataFrame()

    if not news or not isinstance(news, list):
        return pd.DataFrame()

    results = []
    for article in news:
        if not isinstance(article, dict):
            continue

        # Yahoo Finance news structure has evolved across versions:
        # 1. Old structure: article.get('title')
        # 2. Newer structure: article.get('content', {}).get('title')
        title = ""
        content = article.get("content")
        if isinstance(content, dict):
            title = content.get("title", "")
        if not title:
            title = article.get("title", "")

        if not isinstance(title, str) or not title.strip():
            continue

        clean_title = title.strip()
        try:
            blob = TextBlob(clean_title)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
        except Exception:
            polarity = 0.0
            subjectivity = 0.0

        label = classify_polarity(polarity)
        results.append(
            {
                "Headline": clean_title,
                "polarity": round(float(polarity), 3),
                "subjectivity": round(float(subjectivity), 3),
                "Sentiment": label,
            }
        )

    return pd.DataFrame(results)


def get_sentiment_summary(df: pd.DataFrame):
    """Calculates overall sentiment summary string and average polarity.

    Returns:
        tuple (summary_text, avg_polarity)
        Returns ("No data", None) if dataframe is empty.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return "No data", None

    if "polarity" not in df.columns or "Sentiment" not in df.columns:
        return "No data", None

    avg_polarity = float(df["polarity"].mean())
    overall_sentiment = classify_polarity(avg_polarity)

    counts = df["Sentiment"].value_counts()
    pos = int(counts.get("Positive", 0))
    neg = int(counts.get("Negative", 0))
    neu = int(counts.get("Neutral", 0))

    summary = f"{overall_sentiment} | {pos} positive, {neg} negative, {neu} neutral"
    return summary, round(avg_polarity, 3)