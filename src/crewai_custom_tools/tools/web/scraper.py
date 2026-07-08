"""Web scraping tools with automatic fallback escalation."""

import logging
import os
from typing import Optional

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_custom_tools.core.decorators import api_tool
from crewai_custom_tools.core.results import err, ok

logger = logging.getLogger(__name__)


def _clean_text(html: str) -> str:
    """Strip scripts/styles and collapse whitespace from an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    lines = (line.strip() for line in soup.get_text(separator=" ").splitlines())
    return "\n".join(line for line in lines if line)


class UnifiedScraperInput(BaseModel):
    """Input schema for the Unified Scraper Tool."""

    url: str = Field(..., description="The URL of the website to scrape.")
    provider: Optional[str] = Field(
        None,
        description="Optional: force a provider: 'standard' (BeautifulSoup), 'scrapeninja', 'firecrawl'.",
    )


class UnifiedScraperTool(BaseTool):
    """A highly resilient web scraper with multi-provider fallback logic."""

    name: str = "web_scraper"
    description: str = (
        "Scrapes HTML content and text from any website URL. Automatically detects and uses "
        "ScrapeNinja or Firecrawl if standard scraping is blocked by Cloudflare or JS rendering."
    )
    args_schema: type[BaseModel] = UnifiedScraperInput

    def _scrape_standard(self, url: str) -> dict:
        """Standard BeautifulSoup scraping via requests."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else "No title"
        return {
            "provider": "standard",
            "title": title,
            "content": _clean_text(response.text)[:20000],
        }

    def _scrape_scrapeninja(self, url: str, api_key: str) -> dict:
        """Scrape via ScrapeNinja proxy API."""
        response = requests.post(
            "https://scrapeninja.p.rapidapi.com/scrape",
            headers={
                "Content-Type": "application/json",
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "scrapeninja.p.rapidapi.com",
            },
            json={"url": url, "retryNum": 1, "followRedirects": True, "timeout": 10},
            timeout=15,
        )
        response.raise_for_status()
        return {
            "provider": "scrapeninja",
            "title": None,
            "content": _clean_text(response.json().get("body", ""))[:20000],
        }

    def _scrape_firecrawl(self, url: str, api_key: str) -> dict:
        """Scrape via the Firecrawl App (tolerant of SDK dict or object results)."""
        from firecrawl import FirecrawlApp

        data = FirecrawlApp(api_key=api_key).scrape_url(url, formats=["html"])
        if isinstance(data, dict):
            html = data.get("html", "")
        else:
            html = getattr(data, "html", "") or ""
            if not html and hasattr(data, "model_dump"):
                html = data.model_dump().get("html", "")
        return {
            "provider": "firecrawl",
            "title": None,
            "content": _clean_text(html)[:20000],
        }

    @api_tool(provider="UniversalScraper", endpoint="Scrape")
    def _run(self, url: str, provider: Optional[str] = None) -> str:
        """Execute web scraping with fallback orchestration."""
        provider_env = os.getenv("WEB_SCRAPER_PROVIDER", "").strip().lower()
        selected_provider = provider.lower() if provider else provider_env

        if selected_provider == "scrapeninja":
            api_key = os.getenv("RAPIDAPI_KEY")
            if not api_key:
                return err("RAPIDAPI_KEY not set for ScrapeNinja")
            return ok(self._scrape_scrapeninja(url, api_key))

        if selected_provider == "firecrawl":
            api_key = os.getenv("FIRECRAWL_API_KEY")
            if not api_key:
                return err("FIRECRAWL_API_KEY not set for Firecrawl")
            return ok(self._scrape_firecrawl(url, api_key))

        # Standard with auto-escalation to any provider whose key is present.
        try:
            return ok(self._scrape_standard(url))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Standard scraping failed for {url}: {e}. Escalating...")

        ninja_key = os.getenv("RAPIDAPI_KEY")
        if ninja_key:
            try:
                return ok(self._scrape_scrapeninja(url, ninja_key))
            except Exception as ninja_err:  # noqa: BLE001
                logger.error(f"Escalation to ScrapeNinja failed: {ninja_err}")

        firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        if firecrawl_key:
            try:
                return ok(self._scrape_firecrawl(url, firecrawl_key))
            except Exception as firecrawl_err:  # noqa: BLE001
                logger.error(f"Escalation to Firecrawl failed: {firecrawl_err}")

        return err(f"Scrape failed across all available providers for {url}")
