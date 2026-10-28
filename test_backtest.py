import numpy as np
import pandas as pd
import pytest

from backtest import DEFAULT_INITIAL_CAPITAL, plot_backtest, run_backtest


@pytest.fixture
def backtest_sample_df():
    """Generates 120 days of deterministic price data designed to create

    clear SMA-20 / SMA-50 crossovers (bullish and bearish).
    """
    dates = pd.date_range("2023-01-01", periods=120, freq="D")
    # Base prices: first 50 days steady at 100, next 35 days surge to 150 (SMA20 crosses above SMA50),
    # next 35 days drop to 80 (SMA20 crosses below SMA50)
    prices = [100.0] * 50 + [100.0 + (i * 1.5) for i in range(35)] + [152.5 - (i * 2.0) for i in range(35)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p + 2.0 for p in prices],
            "Low": [p - 2.0 for p in prices],
            "Close": prices,
            "Volume": [500000] * 120,
        },
        index=dates,
    )


class TestBacktest:
    def test_run_backtest_with_dataframe_input(self, backtest_sample_df):
        portfolio_df, trade_df, processed_df, metrics = run_backtest(
            backtest_sample_df, initial_cash=10000.0
        )
        assert isinstance(portfolio_df, pd.DataFrame)
        assert isinstance(trade_df, pd.DataFrame)
        assert isinstance(processed_df, pd.DataFrame)
        assert isinstance(metrics, dict)
        assert "Value" in portfolio_df.columns
        assert metrics["initial_capital"] == 10000.0
        assert metrics["final_value"] > 0
        assert "strategy_return_pct" in metrics
        assert "buy_hold_return_pct" in metrics

    def test_backtest_calculates_smas_if_missing(self, backtest_sample_df):
        assert "SMA_20" not in backtest_sample_df.columns
        assert "SMA_50" not in backtest_sample_df.columns
        portfolio_df, trade_df, processed_df, metrics = run_backtest(backtest_sample_df)
        assert "SMA_20" in processed_df.columns
        assert "SMA_50" in processed_df.columns

    def test_backtest_respects_existing_smas_without_recalculating(self, backtest_sample_df):
        df = backtest_sample_df.copy()
        df["SMA_20"] = 120.0
        df["SMA_50"] = 100.0
        # If SMA_20 is always > SMA_50, first bar after warmup triggers BUY
        portfolio_df, trade_df, processed_df, metrics = run_backtest(df)
        assert not trade_df.empty
        assert trade_df["Action"].iloc[0] == "BUY"

    def test_trade_log_columns_consistency(self, backtest_sample_df):
        portfolio_df, trade_df, processed_df, metrics = run_backtest(backtest_sample_df)
        expected_cols = ["Date", "Action", "Price", "Shares", "Value"]
        assert list(trade_df.columns) == expected_cols

        # Test empty trades scenario
        dates = pd.date_range("2023-01-01", periods=60, freq="D")
        flat_df = pd.DataFrame({"Close": [100.0] * 60}, index=dates)
        _, empty_trade_df, _, _ = run_backtest(flat_df)
        assert list(empty_trade_df.columns) == expected_cols
        assert empty_trade_df.empty

    def test_warmup_row_handling(self, backtest_sample_df):
        # 120 days of data. SMA-50 needs 50 days. Post-warmup length should be 120 - 49 = 71
        portfolio_df, trade_df, processed_df, metrics = run_backtest(backtest_sample_df)
        assert len(processed_df) == 71
        assert not processed_df["SMA_50"].isna().any()
        assert not processed_df["SMA_20"].isna().any()

    def test_insufficient_data_error(self):
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        short_df = pd.DataFrame({"Close": [100.0] * 30}, index=dates)
        with pytest.raises(ValueError, match="Insufficient data points"):
            run_backtest(short_df)

    def test_invalid_arguments(self, backtest_sample_df):
        with pytest.raises(TypeError):
            run_backtest("not_a_df")
        with pytest.raises(ValueError):
            run_backtest(backtest_sample_df, initial_cash=-100)
        with pytest.raises(ValueError):
            run_backtest(pd.DataFrame({"Price": [1, 2, 3]}))

    def test_plot_backtest_returns_figure(self, backtest_sample_df):
        portfolio_df, trade_df, processed_df, _ = run_backtest(backtest_sample_df)
        fig = plot_backtest(portfolio_df, trade_df, processed_df)
        assert fig is not None
        assert "Backtest" in fig.layout.title.text
        # Ensure correct marker symbols in figure data traces
        symbols = [trace.marker.symbol for trace in fig.data if hasattr(trace, "marker") and trace.marker.symbol]
        assert "triangles-up" not in symbols  # Should be triangle-up, not invalid plural

    def test_plot_backtest_axes_configuration_with_df(self, backtest_sample_df):
        portfolio_df, trade_df, processed_df, _ = run_backtest(backtest_sample_df)
        fig = plot_backtest(portfolio_df, trade_df, processed_df)

        trace_names = [trace.name for trace in fig.data]
        assert "Portfolio Value" in trace_names
        assert "Stock Price" in trace_names
        assert "Buy Signal" in trace_names

        # Check trace axis assignments
        for trace in fig.data:
            yaxis = getattr(trace, "yaxis", None)
            if trace.name == "Portfolio Value":
                assert yaxis in ("y", None)
            elif trace.name in ("Stock Price", "Buy Signal", "Sell Signal"):
                assert yaxis == "y2"

        # Check layout defines both primary and secondary yaxes
        assert hasattr(fig.layout, "yaxis")
        assert fig.layout.yaxis.title.text == "Portfolio Value"
        assert hasattr(fig.layout, "yaxis2")
        assert fig.layout.yaxis2.title.text == "Stock Price"
        assert fig.layout.yaxis2.overlaying == "y"
        assert fig.layout.yaxis2.side == "right"

    def test_plot_backtest_axes_configuration_without_df(self, backtest_sample_df):
        portfolio_df, trade_df, _, _ = run_backtest(backtest_sample_df)
        fig = plot_backtest(portfolio_df, trade_df, df=None)

        trace_names = [trace.name for trace in fig.data]
        assert "Portfolio Value" in trace_names
        assert "Stock Price" not in trace_names

        # When df is None, markers use y and layout does not have dangling yaxis2
        for trace in fig.data:
            yaxis = getattr(trace, "yaxis", None)
            assert yaxis in ("y", None)

        assert hasattr(fig.layout, "yaxis")
        assert "yaxis2" not in fig.layout

    def test_plot_backtest_serialization(self, backtest_sample_df):
        import json
        portfolio_df, trade_df, processed_df, _ = run_backtest(backtest_sample_df)
        fig = plot_backtest(portfolio_df, trade_df, processed_df)

        # Verify serialization to dictionary
        fig_dict = fig.to_dict()
        assert isinstance(fig_dict, dict)
        assert "data" in fig_dict
        assert "layout" in fig_dict

        # Verify JSON serialization
        fig_json = fig.to_json()
        assert isinstance(fig_json, str)
        parsed = json.loads(fig_json)
        assert "data" in parsed
        assert "layout" in parsed
        assert "yaxis2" in parsed["layout"]
