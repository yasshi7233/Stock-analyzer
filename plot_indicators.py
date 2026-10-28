import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fetch import fetch_stock_data
from indicators import add_macd, add_rsi, add_sma


def plot_stock_indicators(df, ticker="Stock"):
    """Creates a multi-pane technical indicator chart for Close price, SMA, RSI, and MACD."""
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=[f"{ticker} Price + SMA", "RSI (14)", "MACD"],
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="#1f77b4", width=1.5)),
        row=1,
        col=1,
    )

    if "SMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_20"], name="SMA 20", line=dict(color="#FF9800", width=1.2)),
            row=1,
            col=1,
        )

    if "SMA_50" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50", line=dict(color="#E91E63", width=1.2)),
            row=1,
            col=1,
        )

    if "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#9C27B0", width=1)),
            row=2,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#D32F2F", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#388E3C", row=2, col=1)

    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="#2196F3", width=1)),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal", line=dict(color="#FF9800", width=1)),
            row=3,
            col=1,
        )
        fig.add_bar(
            x=df.index, y=df["MACD_Hist"], name="Histogram", marker_color="#9E9E9E", row=3, col=1
        )

    fig.update_layout(
        title=f"{ticker} Technical Indicators",
        height=850,
        showlegend=True,
    )
    return fig


if __name__ == "__main__":
    ticker_input = input("Enter ticker to plot indicators (default AAPL): ").strip().upper() or "AAPL"
    print(f"Fetching data for {ticker_input}...")
    df, _ = fetch_stock_data(ticker_input, period="1y")

    if not df.empty:
        df = add_sma(df, 20)
        df = add_sma(df, 50)
        df = add_rsi(df)
        df = add_macd(df)
        fig = plot_stock_indicators(df, ticker=ticker_input)
        fig.show()
    else:
        print(f"No data returned for ticker {ticker_input}.")