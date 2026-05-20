import yfinance as yf
from textblob import TextBlob
import pandas as pd 

def get_sentiment(ticker):
    stock = yf.Ticker(ticker)
    news = stock.news

    if not news:
        return  pd.DataFrame()
    
    results = []

    for article in news:
        content = article.get('content', {})
        title = content.get('title', '')

        if not title:
            continue

        blob = TextBlob(title)
        polarity =blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0.1:
            label = 'Positive'
        elif polarity < -0.1:
            label = 'Negative'
        else:
            label = 'Neutral'

        results.append({
            'Headline': title,
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'Sentiment': label
        })

    return pd.DataFrame(results)


def get_sentiment_summary(df):
    if df.empty:
        return 'No data',0.0
    
    avg_polarity = df['polarity'].mean()

    if avg_polarity > 0.1:
        overall_sentiment = 'Positive'
    elif avg_polarity < -0.1:
        overall_sentiment = 'Negative'
    else:      
        overall_sentiment = 'Neutral'

    counts = df['Sentiment'].value_counts()
    pos = counts.get('Positive', 0)
    neg = counts.get('Negative', 0)
    neu = counts.get('Neutral', 0)

    summary =f'{overall_sentiment}  | {pos} positive, {neg} negative, {neu} neutral'
    return summary, round(avg_polarity, 3)