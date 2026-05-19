import pandas as pd
from indicators import add_sma, add_rsi, add_macd

df = pd.read_csv('AAPL_stock_data.csv', index_col=0,parse_dates=True)

df =add_sma(df,20)
df =add_sma(df,50)
df =add_rsi(df)
df =add_macd(df)
print(df[['Close','SMA_20','SMA_50','RSI','MACD','MACD_Signal']].tail(10))

df.to_csv('AAPL_indicators.csv')
print('saved:aapl_indicators.csv')