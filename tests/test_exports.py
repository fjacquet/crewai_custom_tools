"""Smoke tests for package level exports."""

def test_package_exports():
    from crew_custom_tools import (
        PerplexitySearchTool, 
        YahooFinanceTickerInfoTool, 
        YahooFinanceNewsTool,
        SerperSearchTool,
        UnifiedScraperTool,
        CoinMarketCapInfoTool,
        FREDMacroTool,
        GitHubSearchTool,
        RenderReportTool,
        HtmlToPdfTool,
        TodoistTool
    )
    assert PerplexitySearchTool is not None
    assert YahooFinanceTickerInfoTool is not None
    assert YahooFinanceNewsTool is not None
    assert SerperSearchTool is not None
    assert UnifiedScraperTool is not None
    assert CoinMarketCapInfoTool is not None
    assert FREDMacroTool is not None
    assert GitHubSearchTool is not None
    assert RenderReportTool is not None
    assert HtmlToPdfTool is not None
    assert TodoistTool is not None
