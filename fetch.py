import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, period='1y'):
    print(f"Fetching data for {ticker}...")
    stock =yf.Ticker(ticker)
    df = stock.history(period=period)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.index = pd.to_datetime(df.index).date
    return df

def display_summary(df,ticker):
   
    print(f'Total trading days: {len(df)}')
    print(f'Latest closing price: ${df["Close"].iloc[-1]:.2f}')
    print(f"Average daily value : {int(df['Volume'].mean()):,}")
    print(df.head()) 

if __name__ == "__main__":
    ticker = input("Enter the stock ticker symbol (e.g., AAPL): ").upper()
    df = fetch_stock_data(ticker)
    df.to_csv(f'{ticker}_stock_data.csv')
    display_summary(df,ticker)  
    print(f"Data saved to {ticker}_stock_data.csv")