# Stock Analyzer Dashboard

An interactive application for stock market analysis built with Python and Streamlit

**Live App:** [Click here to open the app](https://stock-analyzer-z45hcwnwbx9t6bztjbdzon.streamlit.app/)

## What it does

- Fetches real-time stock price data from Yahoo Finance for any ticker
- Calculates three technical indicators from scratch using pandas:
  - SMA (Simple Moving Average) — 20-day and 50-day
  - RSI (Relative Strength Index, 14-day)
  - MACD (Moving Average Convergence Divergence)
- Runs a backtesting engine on the SMA crossover strategy
- Compares strategy returns against buy-and-hold benchmark
- Displays all results on an interactive Plotly dashboard

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Streamlit | Web application framework |
| yfinance | Live stock data from Yahoo Finance |
| pandas | Data manipulation and indicator maths |
| Plotly | Interactive charts |

## How to run locally

git clone https://github.com/yasshi7233/stock-analyzer.git
cd stock-analyzer
python -m venv venv
pip install -r requirements.txt
streamlit run app.py

## Project structure

app.py              Main Streamlit dashboard
indicators.py       SMA, RSI, MACD functions
backtest.py         Backtesting engine
fetch.py            Standalone data fetcher
requirements.txt    Python dependencies

*Built by [Yashi ], 2026*