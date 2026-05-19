import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from  datetime import date,timedelta
from indicators import add_sma,add_rsi,add_macd
from backtest import run_backtest,plot_backtest

st.set_page_config(
    page_title='Stock Analyzer',
    layout='wide',
    page_icon=':chart_with_upwards_trend:'
)
st.title('Stock Analyzer Dashboard')
st.markdown('Fetchlive adta,view technical indicators, and run a backtest- all in one place')

st.sidebar.header('Settings')

ticker = st.sidebar.text_input(
    label ='Stock Ticker',
    value ='AAPL',
    help='Enter a valid ticker. Indian stocks: add .NS' 
)

end_date= st.sidebar.date_input('End date', value = date.today())
start_date = st.sidebar.date_input('Start date',value = date.today() -timedelta(days=365))

st.sidebar.subheader('Indicators')
show_sma =st.sidebar.checkbox('show SMA 20/50' , value = True)
show_rsi = st.sidebar.checkbox('Show RSI(14)', value = True)
show_macd = st.sidebar.checkbox('Show MACD', value = True)

run_btn = st.sidebar.button('Run Analysis',use_container_width = True)

if run_btn:
    with st.spinner(f'fetching data for{ticker}'):
        try:
            df =yf.download(ticker ,start=start_date, end = end_date,progress =False)

            if df.empty:
                st.error(f' No data found for ticker:{ticker}. check the symbol and try again.')
                st.stop()

            df.columns =df.columns.get_level_values(0)
            df = df[['Open' ,'High','Low','Close','Volume']]

            if show_sma:
                df=add_sma(df, 20)

                df = add_sma(df,50)
            
            if show_rsi:
                df= add_rsi(df)
            if show_macd:
                df= add_macd(df)

            df.dropna(inplace =True)

        except Exception as e:
            st.error(f'Error fetching data: {e}')
            st.stop()

    # INDICATOR chart 
    st.subheader(f'{ticker} Price and Indicators')

    rows_needed =1
    if show_rsi:
        rows_needed +=1
    if show_macd:
        rows_needed +=1

    row_heights =[0.5] +[0.25]*(rows_needed -1)
    fig = make_subplots(
        rows =rows_needed,cols=1,
     shared_xaxes=True,
     row_heights=row_heights,
    
    )

    fig.add_trace(go.Scatter(x=df.index,y=df['Close'],
                         name='Close',
                         line=dict(color='#1f77b4',width=1.5)),
                         row=1,col=1)

    if show_sma and 'SMA_20' in df.columns:
         fig.add_trace(go.Scatter(x=df.index,y=df['SMA_20'],
                             name='SMA_20',line=dict(color='orange',width=1 )),
                             row=1,col=1)
         fig.add_trace(go.Scatter(x=df.index,y=df['SMA_50'],
                             name='SMA_50',line=dict(color='red',width=1)),
                                row=1,col=1)
    
    current_row = 2
    if show_rsi and 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df['RSI'],
                             name='RSI',line=dict(color='purple',width=1)),
                                 row=current_row,col=1)
        fig.add_hline(y=70, line_dash='dash',line_color='red', row=current_row,col=1)
        fig.add_hline(y=30, line_dash='dash',line_color='green', row=current_row,col=1)
        current_row +=1

    if show_macd and 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df['MACD'],
                             name='MACD',line=dict(color='blue',width=1)),
                             row=current_row,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['MACD_Signal'],
                             name='Signal',line=dict(color='orange',width=1)),
                             row=current_row,col=1)
        fig.add_bar(x=df.index,y=df['MACD_Hist'],
                name='Histogram',row=current_row,col=1)

    fig.update_layout(height= 700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

#backtest results 
    st.subheader('Backtest Results')

    if show_sma and 'SMA_20' in df.columns:
     df[['Open','High','Low','Close','Volume']].to_csv('AAPL_backtest_data.csv')

    portfolio_df, trade_df, df = run_backtest('AAPL_backtest_data.csv')

    initial = 100000
    final = portfolio_df['Value'].iloc [-1]
    strategy_return =((final - initial)/initial)*100
    buy_hold_return =((df['Close'].iloc[-1] - df['Close'].iloc[0])/df['Close'].iloc[0])*100

    #metric cards in 4 columns 
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Initial Capital', f'{initial:,.0f}')
    c2.metric('Final Value', f'{final:,.2f}', delta = f'{strategy_return:.2f}%')
    c3.metric('Strategy Return', f'{strategy_return:.2f}%')
    c4.metric('Buy-and-Hold Return', f'{buy_hold_return:.2f}%')

# portfolio value cahrt 
    fig2 =  go.Figure()
    fig2.add_trace(go.Scatter(x=portfolio_df.index,y=portfolio_df['Value'],
                              name='Portfolio Value',line=dict(color='blue',width=2)))
    if not trade_df.empty:
        buy_trades = trade_df[trade_df['Action']=='BUY']
        sell_trades = trade_df[trade_df['Action']=='SELL']

        fig2.add_trace(go.Scatter(x=buy_trades['Date'],y=buy_trades['Price'],
                                  mode='markers',name='Buy',marker=dict(color='green',size=10,symbol='triangle-up')))

        fig2.add_trace(go.Scatter(x=sell_trades['Date'],y=sell_trades['Price'],
                                  mode='markers',name='Sell',marker=dict(color='red',size=10,symbol='triangle-down')))
        
    fig2.update_layout(title='Portfolio Value Over Time',height=400)
    st.plotly_chart(fig2, use_container_width=True)

    #trade log table 
    if not trade_df.empty:
        st.subheader('Trade Log')
        st.dataframe(trade_df,use_container_width=True)

else:
    st.info('Backtest requires SMA indicators. Please enable SMA 20/50 to run the backtest.')