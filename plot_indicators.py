import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from indicators import add_sma,add_rsi,add_macd

df = pd.read_csv('AAPL_indicators.csv',index_col=0,parse_dates=True)

fig = make_subplots(
    rows =3,cols=1,
    shared_xaxes=True,
    row_heights =[0.5,0.25,0.25],
    subplot_titles=['Price +SMA', 'RSI(14)','MACD']
)

fig.add_trace(go.Scatter(
    x=df.index, y=df['Close'],
    name='Close', line=dict(color='#1f77b4',width=1.5)

),row=1,col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df['SMA_20'],
    name='SMA_20', line=dict(color='orange',width=1.2)

),row=1,col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df['SMA_50'],
    name='SMA_50', line=dict(color='red',width=1.2)

),row=1,col=1)

fig.add_trace(go.Scatter(
    x=df.index,y=df['RSI'],
    name ='RSI', line =dict(color='purple',width=1)

), row=2,col=1)

fig.add_hline(y=70, line_dash='dash',line_color='red', row=2,col=1)
fig.add_hline(y=30, line_dash='dash',line_color='green', row=2,col=1)   

fig.add_trace(go.Scatter(
    x=df.index,y=df['MACD'],
    name='MACD', line=dict(color='blue',width=1)
), row=3,col=1)

fig.add_trace(go.Scatter(
    x=df.index,y=df['MACD_Signal'],
    name='Signal', line=dict(color='red',width=1)
), row=3,col=1)

fig.add_bar(
    x=df.index,y=df['MACD_Hist'],
    name='Histogram', row=3, col=1
)

fig.update_layout(
    title='AAPL Price and Technical Indicators',
    height=900,
    showlegend=False
)
fig.show()