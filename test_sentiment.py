from sentiment import get_sentiment, get_sentiment_summary

ticker='AAPL'
print(f'Fetching news for {ticker}...')

df= get_sentiment(ticker)

if df.empty:
    print('No news data available.')
else:
    print(f'Found {len(df)} headlines')
    print(df.to_string(index =False))
    print()
    summary, avg_pol = get_sentiment_summary(df)
    print(f'Summary: {summary}')
    print(f'Average polarity: {avg_pol}')