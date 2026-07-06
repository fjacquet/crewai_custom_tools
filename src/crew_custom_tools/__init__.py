"""Centralized CrewAI custom tools library."""

__version__ = "0.1.0"

# 1. Web Search & Scraping
from crew_custom_tools.tools.web.perplexity import PerplexitySearchTool
from crew_custom_tools.tools.web.serper import SerperSearchTool
from crew_custom_tools.tools.web.scraper import UnifiedScraperTool
from crew_custom_tools.tools.web.wikipedia import WikipediaSearchTool, WikipediaArticleTool
from crew_custom_tools.tools.web.rss import RssFeedParserTool, OpmlParserTool
from crew_custom_tools.tools.web.fact_checking import GoogleFactCheckTool

# 2. Stocks & Market Data
from crew_custom_tools.tools.finance.yfinance_ticker import YahooFinanceTickerInfoTool
from crew_custom_tools.tools.finance.yfinance_news import YahooFinanceNewsTool
from crew_custom_tools.tools.finance.company_info import YahooFinanceCompanyInfoTool
from crew_custom_tools.tools.finance.history_holdings import YahooFinanceETFHoldingsTool, YahooFinanceHistoryTool
from crew_custom_tools.tools.finance.crypto import CoinMarketCapInfoTool, KrakenTickerInfoTool, KrakenAssetListTool
from crew_custom_tools.tools.finance.market_data import FREDMacroTool, AlphaVantageOverviewTool
from crew_custom_tools.tools.finance.fear_greed import FearGreedTool
from crew_custom_tools.tools.finance.exchange_rate import ExchangeRateTool

# 3. OSINT & Cyber Recon
from crew_custom_tools.tools.osint.github import GitHubSearchTool, GitHubOrgSearchTool
from crew_custom_tools.tools.osint.email_recon import HunterIOTool, SerperEmailSearchTool, EpieosEmailLookupTool, HoleheEmailScannerTool
from crew_custom_tools.tools.osint.person_recon import UsernameSearchTool
from crew_custom_tools.tools.osint.domain_recon import CrtShTool, RDAPDomainTool
from crew_custom_tools.tools.osint.registers import FrenchRegistryTool
from crew_custom_tools.tools.osint.corporate_global import OpenCorporatesSearchTool

# 4. Reports & PDFs formatting
from crew_custom_tools.reporting.html_generator import RenderReportTool, validate_html
from crew_custom_tools.reporting.pdf_generator import HtmlToPdfTool
from crew_custom_tools.reporting.template_renderers import PestelReportRenderer, FinancialReportRenderer

# 5. Workspace Enterprise integrations
from crew_custom_tools.enterprise.todoist import TodoistTool
from crew_custom_tools.enterprise.airtable import AirtableReaderTool, AirtableTool
from crew_custom_tools.enterprise.accuweather import AccuWeatherTool
from crew_custom_tools.enterprise.rag_tools import SaveToRagTool

__all__ = [
    # Web Tools
    "PerplexitySearchTool",
    "SerperSearchTool",
    "UnifiedScraperTool",
    "WikipediaSearchTool",
    "WikipediaArticleTool",
    "RssFeedParserTool",
    "OpmlParserTool",
    "GoogleFactCheckTool",
    
    # Finance Tools
    "YahooFinanceTickerInfoTool",
    "YahooFinanceNewsTool",
    "YahooFinanceCompanyInfoTool",
    "YahooFinanceETFHoldingsTool",
    "YahooFinanceHistoryTool",
    "CoinMarketCapInfoTool",
    "KrakenTickerInfoTool",
    "KrakenAssetListTool",
    "FREDMacroTool",
    "AlphaVantageOverviewTool",
    "FearGreedTool",
    "ExchangeRateTool",
    
    # OSINT Tools
    "GitHubSearchTool",
    "GitHubOrgSearchTool",
    "HunterIOTool",
    "SerperEmailSearchTool",
    "EpieosEmailLookupTool",
    "HoleheEmailScannerTool",
    "UsernameSearchTool",
    "CrtShTool",
    "RDAPDomainTool",
    "FrenchRegistryTool",
    "OpenCorporatesSearchTool",
    
    # Reporting Tools
    "validate_html",
    "RenderReportTool",
    "HtmlToPdfTool",
    "PestelReportRenderer",
    "FinancialReportRenderer",
    
    # Enterprise Tools
    "TodoistTool",
    "AirtableReaderTool",
    "AirtableTool",
    "AccuWeatherTool",
    "SaveToRagTool",
]
