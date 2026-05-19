from backtest import run_backtest,plot_backtest

FILEPATH ='AAPL_stock_data.csv'

portfolio_df,trade_df,df = run_backtest(FILEPATH)
plot_backtest(portfolio_df,trade_df,df)