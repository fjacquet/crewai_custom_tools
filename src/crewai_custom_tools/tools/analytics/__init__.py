"""Valuation and ETF-analytics tools with pure-function engines.

Ported from finwiz's ``tools/valuation_tool.py`` + ``quantitative/price_targets.py``
and ``tools/etf_analysis_tool.py`` + ``quantitative/etf/etf_metrics.py``. Both
tools are pure computation over caller-supplied inputs — neither calls
yfinance or any other network API — so neither carries the ``@api_tool``
decorator used by network-backed tools elsewhere in this package.
"""

from crewai_custom_tools.tools.analytics.etf_analysis import ETFAnalysisTool
from crewai_custom_tools.tools.analytics.valuation import ValuationTool

__all__ = ["ValuationTool", "ETFAnalysisTool"]
