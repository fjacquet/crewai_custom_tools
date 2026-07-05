"""Mock-based unit tests for unified stock, crypto, and market tools."""

import json
import os
import pytest
import requests
import pandas as pd
from unittest.mock import MagicMock
from crew_custom_tools.tools.finance.company_info import YahooFinanceCompanyInfoTool
from crew_custom_tools.tools.finance.history_holdings import YahooFinanceETFHoldingsTool, YahooFinanceHistoryTool
from crew_custom_tools.tools.finance.crypto import CoinMarketCapInfoTool, KrakenTickerInfoTool, KrakenAssetListTool
from crew_custom_tools.tools.finance.market_data import FREDMacroTool, AlphaVantageOverviewTool
from crew_custom_tools.tools.finance.fear_greed import FearGreedTool
from crew_custom_tools.tools.finance.exchange_rate import ExchangeRateTool


# ==============================================================================
# 1. Yahoo Finance Info, Holdings & History Tests
# ==============================================================================

def test_yfinance_company_info(mocker):
    """Test Yahoo Finance company profile lookup and cleaning."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "website": "https://apple.com",
        "country": "United States",
        "fullTimeEmployees": 150000,
        "longBusinessSummary": "Designs and sells iPhones...",
        "totalRevenue": 380000000000,
        "profitMargins": 0.25,
        "marketCap": 3000000000000
    }
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)

    tool = YahooFinanceCompanyInfoTool()
    result_str = tool._run(ticker="AAPL")
    result = json.loads(result_str)
    
    assert result["name"] == "Apple Inc."
    assert result["industry"] == "Consumer Electronics"
    assert result["financial_metrics"]["revenue"] == 380000000000


def test_yfinance_etf_holdings(mocker):
    """Test Yahoo Finance ETF holdings extraction."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        "shortName": "Vanguard Total Stock Market",
        "categoryName": "Large Blend",
        "totalAssets": 1300000000000
    }
    
    # Mocking holdings pandas DataFrame
    holdings_df = pd.DataFrame([
        {"Name": "Microsoft Corp", "% Assets": 0.065, "Shares": 120000000},
        {"Name": "Apple Inc", "% Assets": 0.058, "Shares": 140000000}
    ], index=["MSFT", "AAPL"])
    
    mock_ticker.get_holdings.return_value = holdings_df
    mock_ticker.get_sector_data.return_value = {"technology": 0.28, "financials": 0.13}
    
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)

    tool = YahooFinanceETFHoldingsTool()
    result_str = tool._run(ticker="VTI")
    result = json.loads(result_str)
    
    assert result["symbol"] == "VTI"
    assert result["asset_class"] == "Large Blend"
    assert len(result["top_holdings"]) == 2
    assert result["top_holdings"][0]["symbol"] == "MSFT"


# ==============================================================================
# 2. CoinMarketCap and Kraken Cryptocurrency Tests
# ==============================================================================

def test_coinmarketcap_info_success(mocker):
    """Test CoinMarketCap quote retrieval and schema formatting."""
    mocker.patch.dict(os.environ, {"COINMARKETCAP_API_KEY": "test_cmc_key"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "BTC": {
                "name": "Bitcoin",
                "symbol": "BTC",
                "cmc_rank": 1,
                "quote": {
                    "USD": {
                        "price": 65000.0,
                        "market_cap": 1200000000000,
                        "percent_change_24h": 2.5
                    }
                }
            }
        }
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = CoinMarketCapInfoTool()
    result_str = tool._run(symbol="BTC")
    result = json.loads(result_str)
    
    assert result["name"] == "Bitcoin"
    assert result["price_usd"] == 65000.0
    assert result["cmc_rank"] == 1


def test_kraken_ticker_info(mocker):
    """Test fetching crypto ticker from Kraken API."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "XXBTZUSD": {
                "a": ["65000.00000", "1", "1.000"],
                "b": ["64999.00000", "1", "1.000"],
                "c": ["65010.00000", "0.05000000"]
            }
        }
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = KrakenTickerInfoTool()
    result_str = tool._run(pair="XXBTZUSD")
    result = json.loads(result_str)
    
    assert "a" in result
    assert result["a"][0] == "65000.00000"


# ==============================================================================
# 3. Market indicators & Sentiment Tests (FRED & CNN Fear/Greed)
# ==============================================================================

def test_fred_macro_success(mocker):
    """Test FRED macro economic indicators fetcher."""
    mocker.patch.dict(os.environ, {"FRED_API_KEY": "test_fred_key"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "observations": [
            {"date": "2026-07-01", "value": "5.25"}
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = FREDMacroTool()
    result_str = tool._run(indicator="fed_rate")
    result = json.loads(result_str)
    
    assert result["indicator"] == "fed_rate"
    assert result["value"] == "5.25"
    assert result["date"] == "2026-07-01"


def test_fear_greed_sentiment_success(mocker):
    """Test scraping market-wide sentiment from CNN Fear & Greed index."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "fear_and_greed": {
            "score": 72.0,
            "rating": "greed",
            "previous_close": 70.0
        }
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = FearGreedTool()
    result_str = tool._run()
    result = json.loads(result_str)
    
    assert result["score"] == 72.0
    assert result["sentiment"] == "Greed"
    assert result["previous_close_score"] == 70.0


# ==============================================================================
# 4. Exchange Rates Tests
# ==============================================================================

def test_exchange_rates_success(mocker):
    """Test fetching fiat exchange rates from OpenExchangeRates."""
    mocker.patch.dict(os.environ, {"OPENEXCHANGERATES_API_KEY": "test_oer_key"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "base": "USD",
        "rates": {
            "EUR": 0.92,
            "GBP": 0.78,
            "JPY": 160.0
        }
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = ExchangeRateTool()
    result = tool._run(base_currency="USD", target_currencies=["EUR", "GBP"])
    
    assert "Exchange rates based on USD" in result
    assert "EUR" in result
    assert "0.92" in result
