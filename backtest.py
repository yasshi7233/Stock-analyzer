import pandas as pd
import plotly.graph_objects as go
from indicators import add_sma

def run_backtest(filepath,initial_cash=100000) :
    df =pd.read_csv(filepath,index_col=0,parse_dates=True)
    df = add_sma(df,20)
    df = add_sma(df,50)
    df.dropna(inplace=True)

    df['Signal'] =0
    df.loc[df['SMA_20']> df['SMA_50'],'Signal'] =1
    df['Position'] =df['Signal'].diff()

    cash = initial_cash
    shares = 0
    portfolio = []
    trade_log =[]

    for date,row in df.iterrows():
        price =row['Close']

        if row['Position']==1:
            shares =cash/price
            cash=0
            trade_log.append({'Date': date,'Action': 'BUY',
                              'Price': round(price,2),
                              'Shares': round(shares,4)})
        elif row['Position']==-1:
            cash = shares*price
            shares =0
            trade_log.append({'Date': date,'Action': 'SELL',
                              'Price': round(price,2),
                              'Value': round(cash,2)})
    
        total_value = cash+(shares*price)
        portfolio.append({'Date': date, 'Value': total_value})
    portfolio_df = pd.DataFrame(portfolio).set_index('Date')
    trade_df = pd.DataFrame(trade_log)

    final_value =portfolio_df['Value'].iloc[-1]
    strategy_return =((final_value -initial_cash)/initial_cash)*100

    buy_hold_return =((df['Close'].iloc[-1] - df['Close'].iloc[0])/df['Close'].iloc[0])*100

    print(f'Initial capital : {initial_cash:,.0f}')
    print(f'Final value : {final_value:,.2f}')
    print(f'Strategy return : {strategy_return:.2f}%')
    print(f'Buy-and-hold return : {buy_hold_return:.2f}%')
    print(f'Total trades : {len(trade_df)}')
    print(f'\n Trade log:')
    print(trade_df.to_string(index=False))

    trade_df.to_csv('trade_log.csv',index=False)
    
    
    return portfolio_df, trade_df ,df



def plot_backtest(portfolio_df, trade_df,df):
    fig =go.Figure()

    fig.add_trace(go.Scatter(
        x=portfolio_df.index, 
        y=portfolio_df['Value'],
        name='Portfolio Value', line=dict(color='blue',width=2)
    ))

    buys = trade_df[trade_df['Action'] =='BUY']
    fig.add_trace(go.Scatter(
        x=buys['Date'],
        y=buys['Price'],
        mode='markers',
        name='Buy',
        marker=dict(symbol='triangles-up',size=12,color='green')

    ))

    sells =trade_df[trade_df['Action'] =='SELL']
    fig.add_trace(go.Scatter(
        x=sells['Date'],
        y=sells['Price'],
        mode='markers',
        name='Sell',
        marker=dict(symbol='triangles-down',size=12,color='red')
    ))

    fig.update_layout(
        title='Bacxktest: Portfolio Value+ Trade Signals',
        xaxis_title='Date',
        yaxis_title='Value',
        height=600
    )
    fig.show()