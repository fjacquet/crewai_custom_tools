import json

import pytest

from crewai_custom_tools.core.results import parse_tool_result
from crewai_custom_tools.tools.finance.yfinance_ticker import (
    GetTickerInfoInput,
    YahooFinanceTickerInfoTool,
)


@pytest.fixture
def ticker_info_tool_instance():
    """Provides a fresh instance of YahooFinanceTickerInfoTool."""
    return YahooFinanceTickerInfoTool()


@pytest.fixture(autouse=True)
def clear_cache():
    from crewai_custom_tools.config.cache import get_cache_manager

    get_cache_manager().clear()


def _mock_uncached(mocker):
    """Patch the cache manager to always miss, returning the mock so set() can be inspected."""
    mock_cache = mocker.MagicMock()
    mock_cache.get.return_value = None
    mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.get_cache_manager",
        return_value=mock_cache,
    )
    return mock_cache


def _data(result_str):
    payload = json.loads(result_str)
    assert payload["success"] is True, payload
    return payload["data"]


# --- Test Instantiation ---
def test_tool_instantiation(ticker_info_tool_instance):
    assert ticker_info_tool_instance.name == "Yahoo Finance Ticker Info Tool"
    assert (
        "Get current information about stocks, ETFs, or cryptocurrencies"
        in ticker_info_tool_instance.description
    )
    assert ticker_info_tool_instance.args_schema == GetTickerInfoInput


# --- Test _run Method ---
def test_run_success_stock(ticker_info_tool_instance, mocker):
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Apple Inc.",
        "currency": "USD",
        "currentPrice": 150.00,
        "previousClose": 149.00,
        "marketCap": 2500000000000,
        "volume": 100000000,
        "averageVolume": 90000000,
        "fiftyTwoWeekHigh": 180.00,
        "fiftyTwoWeekLow": 120.00,
        "trailingPE": 25.5,
        "dividendYield": 0.006,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    mock_yf_ticker.return_value = mock_ticker_instance

    data = _data(ticker_info_tool_instance._run(ticker="AAPL"))

    expected_data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "currency": "USD",
        "current_price": 150.00,
        "previous_close": 149.00,
        "market_cap": 2500000000000,
        "volume": 100000000,
        "average_volume": 90000000,
        "52wk_high": 180.00,
        "52wk_low": 120.00,
        "pe_ratio": 25.5,
        "dividend_yield": 0.006,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    for key, value in expected_data.items():
        assert data[key] == value
    assert data["data_source"] == "live_api"
    assert "timestamp" in data
    mock_yf_ticker.assert_called_once_with("AAPL")


def test_run_success_etf(ticker_info_tool_instance, mocker):
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Vanguard Total Stock Market ETF",
        "currency": "USD",
        "regularMarketPrice": 230.50,
        "previousClose": 229.80,
        "marketCap": 1300000000000,
        "volume": 3000000,
        "averageVolume": 2500000,
        "fiftyTwoWeekHigh": 250.00,
        "fiftyTwoWeekLow": 200.00,
    }
    mock_yf_ticker.return_value = mock_ticker_instance

    data = _data(ticker_info_tool_instance._run(ticker="VTI"))

    expected_data = {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "currency": "USD",
        "current_price": 230.50,
        "previous_close": 229.80,
        "market_cap": 1300000000000,
        "volume": 3000000,
        "average_volume": 2500000,
        "52wk_high": 250.00,
        "52wk_low": 200.00,
    }
    for key, value in expected_data.items():
        assert data[key] == value
    assert data["data_source"] == "live_api"
    assert "timestamp" in data


def test_run_success_with_regular_market_price(ticker_info_tool_instance, mocker):
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Test Ticker",
        "currency": "USD",
        "regularMarketPrice": 99.00,
        "previousClose": 98.00,
    }
    mock_yf_ticker.return_value = mock_ticker_instance

    data = _data(ticker_info_tool_instance._run(ticker="TEST"))
    assert data["current_price"] == 99.00
    assert data["name"] == "Test Ticker"


def test_run_minimal_data(ticker_info_tool_instance, mocker):
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {"shortName": "Minimal Corp", "currency": "EUR"}
    mock_yf_ticker.return_value = mock_ticker_instance

    data = _data(ticker_info_tool_instance._run(ticker="MINI"))
    assert data["symbol"] == "MINI"
    assert data["name"] == "Minimal Corp"
    assert data["currency"] == "EUR"
    assert data["data_source"] == "live_api"
    assert "timestamp" in data


def test_run_yfinance_exception(ticker_info_tool_instance, mocker):
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_yf_ticker.side_effect = Exception("Test yfinance error")

    payload = json.loads(ticker_info_tool_instance._run(ticker="ERROR"))
    assert payload["success"] is False
    assert "Test yfinance error" in payload["error"]


def test_run_invalid_ticker_empty_info(ticker_info_tool_instance, mocker):
    """An empty info dict yields an error envelope, not a bare {"symbol": ...} (finding L3)."""
    _mock_uncached(mocker)
    mock_yf_ticker = mocker.patch(
        "crewai_custom_tools.tools.finance.yfinance_ticker.yf.Ticker"
    )
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {}
    mock_yf_ticker.return_value = mock_ticker_instance

    payload = json.loads(ticker_info_tool_instance._run(ticker="INVALID"))
    assert payload["success"] is False
    assert "No data for ticker INVALID" in payload["error"]


def test_prefetched_data_short_circuits_network(mocker):
    from crewai_custom_tools.tools.finance import yfinance_ticker

    ticker_spy = mocker.patch.object(yfinance_ticker.yf, "Ticker")
    tool = yfinance_ticker.YahooFinanceTickerInfoTool()
    raw = tool._run(ticker="AAPL", prefetched_data={"AAPL": {"symbol": "AAPL", "current_price": 123.0}})
    data = parse_tool_result(raw)
    assert data["current_price"] == 123.0
    assert data["data_source"] == "prefetched"
    ticker_spy.assert_not_called()


def test_live_result_includes_extended_fields_and_metadata(mocker):
    from crewai_custom_tools.tools.finance import yfinance_ticker

    mocker.patch.object(
        yfinance_ticker.yf,
        "Ticker",
        return_value=mocker.Mock(
            info={
                "shortName": "Apple",
                "currentPrice": 190.0,
                "returnOnEquity": 1.5,
                "debtToEquity": 152.4,
                "profitMargins": 0.25,
                "beta3Year": 1.1,
                "regularMarketTime": 1750000000,
            }
        ),
    )
    data = parse_tool_result(yfinance_ticker.YahooFinanceTickerInfoTool()._run(ticker="AAPL"))
    assert data["return_on_equity"] == 1.5
    assert data["debt_to_equity"] == 152.4
    assert data["profit_margins"] == 0.25
    assert data["beta"] == 1.1  # falls back to beta3Year
    assert data["data_source"] == "live_api"
    assert "timestamp" in data
    assert "market_time" in data
