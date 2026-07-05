"""Smoke tests for package level exports."""

def test_package_exports():
    from crew_custom_tools import PerplexitySearchTool, YahooFinanceTickerInfoTool, YahooFinanceNewsTool
    assert PerplexitySearchTool is not None
    assert YahooFinanceTickerInfoTool is not None
    assert YahooFinanceNewsTool is not None
