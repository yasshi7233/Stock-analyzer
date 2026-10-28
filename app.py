from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from backtest import DEFAULT_INITIAL_CAPITAL, plot_backtest, run_backtest
from fetch import fetch_stock_data
from indicators import add_macd, add_rsi, add_sma
from sentiment import get_sentiment, get_sentiment_summary

# Configure page layout and visual identity
st.set_page_config(
    page_title="Stock Analyzer Dashboard",
    layout="wide",
    page_icon="📈",
)

st.title("Stock Analyzer Dashboard")
st.markdown("Fetch live data, view technical indicators, and run a backtest — all in one place.")

# --- Sidebar Controls ---
st.sidebar.header("Settings")

raw_ticker = st.sidebar.text_input(
    label="Stock Ticker",
    value="AAPL",
    help="Enter a valid ticker (e.g. AAPL, MSFT, GOOG). For Indian stocks, add .NS (e.g. RELIANCE.NS)",
)
clean_ticker = raw_ticker.strip().upper() if raw_ticker else "AAPL"

end_date = st.sidebar.date_input("End Date", value=date.today())
start_date = st.sidebar.date_input("Start Date", value=date.today() - timedelta(days=365))

# Date validation check
is_date_valid = True
if start_date >= end_date:
    st.sidebar.error("Start date must be before end date.")
    is_date_valid = False

st.sidebar.subheader("Indicators")
show_sma = st.sidebar.checkbox("Show SMA (20/50)", value=True)
show_rsi = st.sidebar.checkbox("Show RSI (14)", value=True)
show_macd = st.sidebar.checkbox("Show MACD", value=True)

st.sidebar.subheader("Backtest Settings")
initial_capital = st.sidebar.number_input(
    "Starting Capital",
    min_value=1000.0,
    max_value=10000000.0,
    value=float(DEFAULT_INITIAL_CAPITAL),
    step=1000.0,
    format="%.2f",
)

run_btn = st.sidebar.button("Run Analysis", use_container_width=True)


# --- Cached Fetch Helpers ---
@st.cache_data(show_spinner=False, ttl=300)
def cached_fetch_data(ticker_symbol: str, start_d: date, end_d: date):
    """Caches market data retrieval keyed by ticker and date range."""
    return fetch_stock_data(ticker_symbol, start=start_d, end=end_d)


@st.cache_data(show_spinner=False, ttl=300)
def cached_sentiment_data(ticker_symbol: str):
    """Caches news sentiment analysis to avoid rate-limiting."""
    return get_sentiment(ticker_symbol)


# Execute analysis when button is pressed
if run_btn:
    if not is_date_valid:
        st.error("Cannot run analysis with an invalid date range. Please adjust Start Date to be before End Date.")
        st.stop()

    if not clean_ticker:
        st.error("Please enter a valid stock ticker symbol.")
        st.stop()

    # Step 1: Fetch Stock Data
    with st.spinner(f"Fetching data for {clean_ticker}..."):
        try:
            raw_df, metadata = cached_fetch_data(clean_ticker, start_date, end_date)
        except Exception:
            st.error(f"Unable to connect to market data service for '{clean_ticker}'. Please check your network connection.")
            st.stop()

    if raw_df is None or raw_df.empty:
        st.error(f"No price data found for ticker '{clean_ticker}'. Please check the symbol and date range, then try again.")
        st.stop()

    currency = metadata.get("currency", "USD")

    # Step 2: Compute Indicators conditionally on a fresh copy
    working_df = raw_df.copy()

    try:
        if show_sma:
            working_df = add_sma(working_df, 20)
            working_df = add_sma(working_df, 50)
        if show_rsi:
            working_df = add_rsi(working_df, period=14)
        if show_macd:
            working_df = add_macd(working_df)
    except Exception as e:
        st.error(f"Error calculating technical indicators: {e}")
        st.stop()

    # Create UI Tabs
    tab_analysis, tab_backtest, tab_sentiment = st.tabs(["Analysis", "Backtest", "News Sentiment"])

    # ==========================================
    # TAB 1: TECHNICAL ANALYSIS
    # ==========================================
    with tab_analysis:
        st.subheader(f"{clean_ticker} Price and Technical Indicators")

        # Top metric row
        latest_close = working_df["Close"].iloc[-1]
        first_close = working_df["Close"].iloc[0]
        price_change = latest_close - first_close
        pct_change = (price_change / first_close) * 100 if first_close != 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Latest Close", f"{currency} {latest_close:,.2f}", delta=f"{pct_change:+.2f}%")
        m2.metric("Period High", f"{currency} {working_df['High'].max():,.2f}")
        m3.metric("Period Low", f"{currency} {working_df['Low'].min():,.2f}")
        m4.metric("Avg Daily Volume", f"{int(working_df['Volume'].mean()):,}")

        # Build dynamic multi-pane Plotly chart
        rows_needed = 1
        if show_rsi:
            rows_needed += 1
        if show_macd:
            rows_needed += 1

        if rows_needed == 1:
            row_heights = [1.0]
        elif rows_needed == 2:
            row_heights = [0.65, 0.35]
        else:
            row_heights = [0.55, 0.22, 0.23]

        fig = make_subplots(
            rows=rows_needed,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=row_heights,
        )

        # Pane 1: Price and SMAs
        fig.add_trace(
            go.Scatter(
                x=working_df.index,
                y=working_df["Close"],
                name="Close",
                line=dict(color="#1f77b4", width=1.5),
            ),
            row=1,
            col=1,
        )

        if show_sma:
            if "SMA_20" in working_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=working_df.index,
                        y=working_df["SMA_20"],
                        name="SMA 20",
                        line=dict(color="#FF9800", width=1.2),
                    ),
                    row=1,
                    col=1,
                )
            if "SMA_50" in working_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=working_df.index,
                        y=working_df["SMA_50"],
                        name="SMA 50",
                        line=dict(color="#E91E63", width=1.2),
                    ),
                    row=1,
                    col=1,
                )

        current_row = 2
        if show_rsi and "RSI" in working_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=working_df.index,
                    y=working_df["RSI"],
                    name="RSI (14)",
                    line=dict(color="#9C27B0", width=1.2),
                ),
                row=current_row,
                col=1,
            )
            fig.add_hline(y=70, line_dash="dash", line_color="#D32F2F", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#388E3C", row=current_row, col=1)
            current_row += 1

        if show_macd and "MACD" in working_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=working_df.index,
                    y=working_df["MACD"],
                    name="MACD",
                    line=dict(color="#2196F3", width=1.2),
                ),
                row=current_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=working_df.index,
                    y=working_df["MACD_Signal"],
                    name="Signal",
                    line=dict(color="#FF9800", width=1.2),
                ),
                row=current_row,
                col=1,
            )
            fig.add_bar(
                x=working_df.index,
                y=working_df["MACD_Hist"],
                name="Histogram",
                marker_color="#9E9E9E",
                row=current_row,
                col=1,
            )

        fig.update_layout(
            height=650,
            showlegend=True,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # TAB 2: BACKTEST ENGINE
    # ==========================================
    with tab_backtest:
        st.subheader("SMA 20/50 Crossover Backtest")

        if not show_sma:
            st.info("The crossover backtest strategy uses SMA (20/50). Enable 'Show SMA (20/50)' in the sidebar to activate the backtest.")
        else:
            try:
                # Pass data directly in-memory; calculations happen in backtest.py
                portfolio_df, trade_df, bt_processed_df, metrics = run_backtest(
                    raw_df, initial_cash=float(initial_capital)
                )

                # Render metric cards with accurate currency labels
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Initial Capital", f"{currency} {metrics['initial_capital']:,.2f}")
                c2.metric(
                    "Final Value",
                    f"{currency} {metrics['final_value']:,.2f}",
                    delta=f"{metrics['strategy_return_pct']:+.2f}%",
                )
                c3.metric("Strategy Return", f"{metrics['strategy_return_pct']:+.2f}%")
                c4.metric("Buy-and-Hold Return", f"{metrics['buy_hold_return_pct']:+.2f}%")

                # Unified Plotly figure from backtest.py
                bt_fig = plot_backtest(portfolio_df, trade_df, bt_processed_df)
                st.plotly_chart(bt_fig, use_container_width=True)

                st.subheader("Trade Log")
                if not trade_df.empty:
                    st.dataframe(trade_df, use_container_width=True)
                else:
                    st.info("No buy/sell crossover signals occurred during the selected time period.")

            except ValueError as ve:
                st.warning(f"Backtest cannot be completed: {ve}")
            except Exception as e:
                st.error(f"Unexpected error while executing backtest: {e}")

    # ==========================================
    # TAB 3: NEWS SENTIMENT
    # ==========================================
    with tab_sentiment:
        st.subheader(f"News Sentiment — {clean_ticker}")

        with st.spinner("Fetching latest news headlines..."):
            try:
                sentiment_df = cached_sentiment_data(clean_ticker)
            except Exception:
                sentiment_df = pd.DataFrame()

        if sentiment_df is None or sentiment_df.empty:
            st.info(f"No recent news headlines available for ticker '{clean_ticker}'.")
        else:
            summary, avg_pol = get_sentiment_summary(sentiment_df)

            if avg_pol is None:
                st.info("Sentiment data could not be computed.")
            elif avg_pol > 0.1:
                st.success(f"Overall Sentiment: {summary}")
            elif avg_pol < -0.1:
                st.error(f"Overall Sentiment: {summary}")
            else:
                st.warning(f"Overall Sentiment: {summary}")

            # Sentiment breakdown chart
            counts = sentiment_df["Sentiment"].value_counts().reset_index()
            counts.columns = ["Sentiment", "Count"]

            colour_map = {
                "Positive": "#2E7D32",
                "Negative": "#C62828",
                "Neutral": "#757575",
            }
            fig_bar = px.bar(
                counts,
                x="Sentiment",
                y="Count",
                color="Sentiment",
                color_discrete_map=colour_map,
                title="Headline Sentiment Breakdown",
            )
            fig_bar.update_layout(height=350, margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Individual Headlines")
            for _, row in sentiment_df.iterrows():
                sentiment_tag = row["Sentiment"]
                headline_text = f"**{row['Headline']}** — Polarity: `{row['polarity']}` | Subjectivity: `{row['subjectivity']}`"
                if sentiment_tag == "Positive":
                    st.success(headline_text)
                elif sentiment_tag == "Negative":
                    st.error(headline_text)
                else:
                    st.info(headline_text)