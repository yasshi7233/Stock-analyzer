import numpy as np
import pandas as pd
import plotly.graph_objects as go
from indicators import add_sma

DEFAULT_INITIAL_CAPITAL = 100000.0


def run_backtest(df: pd.DataFrame, initial_cash: float = DEFAULT_INITIAL_CAPITAL):
    """Runs an SMA 20/50 crossover backtest directly on an in-memory DataFrame.

    Parameters:
        df: pandas DataFrame containing at least a 'Close' column.
        initial_cash: Starting cash for the strategy (default 100,000).

    Returns:
        tuple: (portfolio_df, trade_df, processed_df, metrics)
        - portfolio_df: DataFrame indexed by Date with 'Value' column
        - trade_df: DataFrame of executed trades with consistent columns:
                    ['Date', 'Action', 'Price', 'Shares', 'Value']
        - processed_df: DataFrame with SMA indicators and non-warmup rows
        - metrics: dict containing initial_capital, final_value,
                   strategy_return_pct, buy_hold_return_pct, total_trades
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input df must be a pandas DataFrame.")
    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column.")
    if initial_cash <= 0:
        raise ValueError("initial_cash must be greater than 0.")

    # Work on a copy to avoid mutating the caller's DataFrame
    working_df = df.copy()

    # Ensure SMA columns exist. If not present or partly present, calculate them
    if "SMA_20" not in working_df.columns:
        working_df = add_sma(working_df, 20)
    if "SMA_50" not in working_df.columns:
        working_df = add_sma(working_df, 50)

    # SMA-50 requires at least 50 data points to warm up.
    # Exclude warm-up NaN rows specifically from SMA columns once.
    working_df = working_df.dropna(subset=["Close", "SMA_20", "SMA_50"]).copy()

    if len(working_df) < 2:
        raise ValueError("Insufficient data points after SMA warm-up to run backtest (minimum 2 required).")

    # Generate signals: 1 when SMA_20 > SMA_50 (bullish), 0 otherwise
    # Avoid SettingWithCopyWarning by explicitly working on copies
    working_df["Signal"] = 0
    working_df.loc[working_df["SMA_20"] > working_df["SMA_50"], "Signal"] = 1
    working_df["Position"] = working_df["Signal"].diff().fillna(working_df["Signal"])

    cash = float(initial_cash)
    shares = 0.0
    portfolio = []
    trade_log = []

    for date_idx, row in working_df.iterrows():
        price = float(row["Close"])
        pos = row["Position"]

        if pos == 1 and cash > 0 and price > 0:
            # BUY with all available cash
            shares_bought = cash / price
            value_traded = cash
            shares += shares_bought
            cash = 0.0
            trade_log.append(
                {
                    "Date": date_idx,
                    "Action": "BUY",
                    "Price": round(price, 2),
                    "Shares": round(shares_bought, 4),
                    "Value": round(value_traded, 2),
                }
            )
        elif pos == -1 and shares > 0 and price > 0:
            # SELL all currently held shares
            value_traded = shares * price
            cash += value_traded
            shares_sold = shares
            shares = 0.0
            trade_log.append(
                {
                    "Date": date_idx,
                    "Action": "SELL",
                    "Price": round(price, 2),
                    "Shares": round(shares_sold, 4),
                    "Value": round(value_traded, 2),
                }
            )

        total_value = cash + (shares * price)
        portfolio.append({"Date": date_idx, "Value": round(total_value, 2)})

    portfolio_df = pd.DataFrame(portfolio).set_index("Date")

    if trade_log:
        trade_df = pd.DataFrame(trade_log)
    else:
        # Guarantee consistent columns even when no trades triggered
        trade_df = pd.DataFrame(columns=["Date", "Action", "Price", "Shares", "Value"])

    final_value = float(portfolio_df["Value"].iloc[-1])
    strategy_return_pct = ((final_value - initial_cash) / initial_cash) * 100.0

    first_close = float(working_df["Close"].iloc[0])
    last_close = float(working_df["Close"].iloc[-1])
    buy_hold_return_pct = ((last_close - first_close) / first_close) * 100.0 if first_close != 0 else 0.0

    metrics = {
        "initial_capital": float(initial_cash),
        "final_value": round(final_value, 2),
        "strategy_return_pct": round(strategy_return_pct, 2),
        "buy_hold_return_pct": round(buy_hold_return_pct, 2),
        "total_trades": len(trade_df),
    }

    return portfolio_df, trade_df, working_df, metrics


def plot_backtest(portfolio_df: pd.DataFrame, trade_df: pd.DataFrame, df: pd.DataFrame = None):
    """Generates a reusable Plotly figure for portfolio equity curve and trade signals.

    Returns:
        go.Figure object (does not call fig.show() directly).
    """
    fig = go.Figure()

    if portfolio_df is not None and not portfolio_df.empty:
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df["Value"],
                name="Portfolio Value",
                line=dict(color="#2962FF", width=2),
            )
        )

    if trade_df is not None and not trade_df.empty:
        buys = trade_df[trade_df["Action"] == "BUY"]
        if not buys.empty:
            fig.add_trace(
                go.Scatter(
                    x=buys["Date"],
                    y=buys["Price"],
                    mode="markers",
                    name="Buy Signal",
                    marker=dict(symbol="triangle-up", size=11, color="#00C853"),
                    yaxis="y2" if df is not None else "y",
                )
            )

        sells = trade_df[trade_df["Action"] == "SELL"]
        if not sells.empty:
            fig.add_trace(
                go.Scatter(
                    x=sells["Date"],
                    y=sells["Price"],
                    mode="markers",
                    name="Sell Signal",
                    marker=dict(symbol="triangle-down", size=11, color="#D50000"),
                    yaxis="y2" if df is not None else "y",
                )
            )

    fig.update_layout(
        title="Backtest: Portfolio Value and Trade Signals",
        xaxis_title="Date",
        yaxis_title="Portfolio Value",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig