"""Mock-based unit tests for unified OSINT and corporate registry tools."""

import json
import os
import pytest
import requests
from unittest.mock import MagicMock
from crew_custom_tools.tools.osint.github import GitHubSearchTool, GitHubOrgSearchTool
from crew_custom_tools.tools.osint.email_recon import HunterIOTool, SerperEmailSearchTool
from crew_custom_tools.tools.osint.person_recon import UsernameSearchTool
from crew_custom_tools.tools.osint.domain_recon import CrtShTool, RDAPDomainTool
from crew_custom_tools.tools.osint.registers import FrenchRegistryTool


# ==============================================================================
# 1. GitHub Tools Tests
# ==============================================================================

def test_github_search_success(mocker):
    """Test successful GitHub repository searching with token."""
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "test_gh_token"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total_count": 100,
        "items": [
            {
                "full_name": "owner/repo-name",
                "html_url": "https://github.com/owner/repo-name",
                "description": "A test repository",
                "stargazers_count": 42,
                "forks_count": 7
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = GitHubSearchTool()
    result_str = tool._run(query="OSINT", search_type="repositories")
    result = json.loads(result_str)
    
    assert result["search_type"] == "repositories"
    assert result["total_count"] == 100
    assert result["results"][0]["name"] == "owner/repo-name"


def test_github_org_search_success(mocker):
    """Test successful GitHub organization intelligence retrieval."""
    mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "test_gh_token"})
    
    # Mocking first GET to organization profile
    mock_org_response = mocker.MagicMock()
    mock_org_response.status_code = 200
    mock_org_response.json.return_value = {
        "name": "Acme Org",
        "login": "acme",
        "html_url": "https://github.com/acme",
        "description": "Standard Acme Corp",
        "public_repos": 10,
        "followers": 50,
        "repos_url": "https://api.github.com/orgs/acme/repos"
    }
    
    # Mocking second GET to organization repositories list
    mock_repos_response = mocker.MagicMock()
    mock_repos_response.status_code = 200
    mock_repos_response.json.return_value = [
        {"name": "core-lib", "html_url": "https://github.com/acme/core-lib"}
    ]
    
    def side_effect(url, *args, **kwargs):
        if "repos" in url:
            return mock_repos_response
        return mock_org_response
        
    mocker.patch("requests.get", side_effect=side_effect)

    tool = GitHubOrgSearchTool()
    result_str = tool._run(org_name="acme")
    result = json.loads(result_str)
    
    assert result["name"] == "Acme Org"
    assert len(result["top_repos"]) == 1
    assert result["top_repos"][0]["name"] == "core-lib"


# ==============================================================================
# 2. Email Intelligence Tests
# ==============================================================================

def test_hunter_io_success(mocker):
    """Test domain professional email lookup via Hunter.io."""
    mocker.patch.dict(os.environ, {"HUNTER_API_KEY": "test_hunter_key"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "domain": "acme.com",
            "emails": [
                {"value": "admin@acme.com", "first_name": "Admin"}
            ]
        }
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = HunterIOTool()
    result_str = tool._run(domain="acme.com")
    result = json.loads(result_str)
    
    assert result["domain"] == "acme.com"
    assert result["emails"][0]["value"] == "admin@acme.com"


def test_serper_email_search(mocker):
    """Test regex extraction of professional emails from Serper listings."""
    mocker.patch.dict(os.environ, {"SERPER_API_KEY": "test_serper_key"})
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "Contact Acme",
                "snippet": "Send a message to info@acme.com or sales@acme.com for inquiries.",
                "link": "https://acme.com/contact"
            }
        ]
    }
    mocker.patch("requests.post", return_value=mock_response)

    tool = SerperEmailSearchTool()
    result_str = tool._run(query="Acme")
    result = json.loads(result_str)
    
    assert "emails" in result[0]
    assert "info@acme.com" in result[0]["emails"]
    assert "sales@acme.com" in result[0]["emails"]


# ==============================================================================
# 3. Username Recon and Domain Recon Tests
# ==============================================================================

def test_username_search_success(mocker):
    """Test pure-Python Sherlock-style username scanning."""
    # Mocking requests.head so that only GitHub exists for this user
    def side_effect(url, *args, **kwargs):
        mock_resp = mocker.MagicMock()
        if "github.com" in url:
            mock_resp.status_code = 200
        else:
            mock_resp.status_code = 404
        return mock_resp
        
    mocker.patch("requests.head", side_effect=side_effect)

    tool = UsernameSearchTool()
    result_str = tool._run(username="johndoe")
    result = json.loads(result_str)
    
    assert len(result) == 1
    assert result[0]["platform"] == "GitHub"
    assert result[0]["status"] == "Found"


def test_crt_sh_subdomain_recon(mocker):
    """Test subdomain certificate harvesting via crt.sh."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name_value": "api.acme.com\nwww.acme.com"},
        {"name_value": "*.acme.com"} # Will be ignored as wildcard
    ]
    mocker.patch("requests.get", return_value=mock_response)

    tool = CrtShTool()
    result_str = tool._run(domain="acme.com")
    result = json.loads(result_str)
    
    assert len(result) == 2
    assert "api.acme.com" in result
    assert "www.acme.com" in result


def test_rdap_domain_recon(mocker):
    """Test structured domain registration WHOIS details fetching via whodap."""
    mock_response = mocker.MagicMock()
    mock_response.to_whois_dict.return_value = {
        "registrar_name": "MarkMonitor, Inc.",
        "created_date": "1997-09-15T04:00:00Z",
        "nameservers": ["ns1.google.com", "ns2.google.com"]
    }
    mocker.patch("whodap.lookup_domain", return_value=mock_response)

    tool = RDAPDomainTool()
    result_str = tool._run(domain="google.com")
    result = json.loads(result_str)
    
    assert result["domain"] == "google.com"
    assert result["registrar"] == "MarkMonitor, Inc."
    assert "ns1.google.com" in result["nameservers"]


# ==============================================================================
# 4. French Public corporate registries Tests
# ==============================================================================

def test_french_registry_search_success(mocker):
    """Test SIREN querying of public recherche-entreprises French API."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "siren": "123456789",
                "nom_complet": "ACME FRANCE SAS",
                "activite_principale": "62.01Z",
                "tranche_effectif_salarie": "11",
                "etat_administratif": "A",
                "siege": {
                    "siret": "12345678900010",
                    "numero_voie": "10",
                    "type_voie": "RUE",
                    "libelle_voie": "DE LA PAIX",
                    "code_postal": "75002",
                    "libelle_commune": "PARIS"
                },
                "dirigeants": [
                    {"prenoms": "Jean", "nom": "Dupont"}
                ],
                "complements": {
                    "site_web": "https://acme.fr"
                }
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    tool = FrenchRegistryTool()
    result_str = tool._run(query="123456789")
    result = json.loads(result_str)
    
    assert result["siren"] == "123456789"
    assert result["company_name"] == "ACME FRANCE SAS"
    assert result["address"] == "10 RUE DE LA PAIX 75002 PARIS"
    assert "Jean Dupont" in result["officers"]
