from backtest import plot_backtest, run_backtest
from fetch import fetch_stock_data

if __name__ == "__main__":
    ticker_input = input("Enter ticker to backtest (default AAPL): ").strip().upper() or "AAPL"
    print(f"Fetching data for {ticker_input}...")
    df, meta = fetch_stock_data(ticker_input, period="2y")

    if not df.empty:
        portfolio_df, trade_df, processed_df, metrics = run_backtest(df)
        print("\n=== Backtest Summary ===")
        print(f"Ticker: {ticker_input}")
        print(f"Initial Capital: {meta.get('currency', 'USD')} {metrics['initial_capital']:,.2f}")
        print(f"Final Value:     {meta.get('currency', 'USD')} {metrics['final_value']:,.2f}")
        print(f"Strategy Return: {metrics['strategy_return_pct']:+.2f}%")
        print(f"Buy & Hold Return: {metrics['buy_hold_return_pct']:+.2f}%")
        print(f"Total Trades:    {metrics['total_trades']}")
        if not trade_df.empty:
            print("\nRecent Trades:")
            print(trade_df.tail(10).to_string(index=False))

        fig = plot_backtest(portfolio_df, trade_df, processed_df)
        fig.show()
    else:
        print(f"No data returned for ticker {ticker_input}.")