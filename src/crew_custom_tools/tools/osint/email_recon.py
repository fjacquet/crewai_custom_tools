"""Email Intelligence OSINT Tools."""

import json
import logging
import os
import re
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from crew_custom_tools.core.decorators import api_tool

logger = logging.getLogger(__name__)


class HunterIOInput(BaseModel):
    """Input schema for Hunter.io Search."""
    domain: str = Field(..., description="Domain name to search for emails (e.g., 'google.com').")


class SerperEmailSearchInput(BaseModel):
    """Input schema for Serper email search."""
    query: str = Field(..., description="The name of the company or topic to scan for emails.")


class HunterIOTool(BaseTool):
    """A tool to search for professional email addresses related to a domain via Hunter.io API."""
    name: str = "hunter_io_search"
    description: str = "Find professional email addresses for a given domain using Hunter.io."
    args_schema: type[BaseModel] = HunterIOInput

    @api_tool(provider="HunterIO", endpoint="DomainSearch", default_return="{}")
    def _run(self, domain: str) -> str:
        """Search for emails via Hunter.io REST endpoint."""
        api_key = os.getenv("HUNTER_API_KEY")
        if not api_key:
            return json.dumps({"error": "HUNTER_API_KEY environment variable not configured"})

        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps(data.get("data", {}))


class SerperEmailSearchTool(BaseTool):
    """A tool to scrape public emails mentioned on Google using Serper API."""
    name: str = "serper_email_search"
    description: str = "Search Google organic listings for publicly mentioned email addresses related to a company name."
    args_schema: type[BaseModel] = SerperEmailSearchInput

    @api_tool(provider="Serper", endpoint="EmailSearch", default_return="[]")
    def _run(self, query: str) -> str:
        """Execute web query search and parse email addresses."""
        api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPER_API_KEY")
        if not api_key:
            return json.dumps({"error": "SERPER_API_KEY environment variable not set."})

        # Clean query and formulate search string for email listings
        clean_query = query.strip().lower()
        search_query = f'"{clean_query}" "@"{clean_query.replace(" ", "")} email'

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": search_query}

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        results = response.json().get("organic", [])
        emails_found = set()
        email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        for item in results:
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            link = item.get("link", "")
            combined_text = f"{title} {snippet} {link}"
            emails_found.update(email_regex.findall(combined_text))

        result_list = list(emails_found)
        if result_list:
            return json.dumps([{"emails": result_list}])
        return json.dumps([{"message": "No emails found"}])
