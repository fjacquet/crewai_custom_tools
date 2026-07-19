import json

import httpx
import pytest

from crewai_custom_tools.tools.genealogy.gramps.client import GrampsClient, GrampsConfig
from crewai_custom_tools.tools.genealogy.gramps import write_tools
from crewai_custom_tools.tools.genealogy.gramps.write_tools import (
    GrampsCreatePlaceTool, GrampsUpdatePlaceTool,
)

CONFIG = GrampsConfig(api_url="http://g.test/api", username="u", password="p")


@pytest.fixture(autouse=True)
def _no_global_dry_run(monkeypatch):
    monkeypatch.setenv("GENECREW_DRY_RUN", "false")


def _client(on_put=None, on_post=None, existing=None):
    def handler(request):
        if request.url.path == "/api/token/":
            return httpx.Response(200, json={"access_token": "t"})
        if request.method == "GET" and request.url.path.startswith("/api/places/"):
            return httpx.Response(200, json=existing or {})
        if request.method == "POST" and request.url.path == "/api/places/":
            return on_post(request) if on_post else httpx.Response(201, json={"handle": "NEW"})
        if request.method == "PUT":
            return on_put(request) if on_put else httpx.Response(200, json={})
        return httpx.Response(404)
    return GrampsClient(CONFIG, transport=httpx.MockTransport(handler))


def test_create_place_dry_run_returns_synthetic_handle(mocker):
    mocker.patch.object(write_tools, "get_client", return_value=_client())
    data = json.loads(GrampsCreatePlaceTool()._run(name="France", place_type="Country", dry_run=True))
    assert data["success"] is True
    assert data["data"]["handle"] == "DRYRUN:France"     # handle synthétique, aucun POST


def test_create_place_writes_and_returns_handle(mocker):
    posts = []

    def on_post(request):
        posts.append(json.loads(request.content))
        return httpx.Response(201, json={"handle": "H_FR"})

    mocker.patch.object(write_tools, "get_client", return_value=_client(on_post=on_post))
    data = json.loads(GrampsCreatePlaceTool()._run(name="France", place_type="Country"))
    assert data["data"]["handle"] == "H_FR" and len(posts) == 1
    assert posts[0]["place_type"] == "Country"


def test_update_place_noop_when_conforming(mocker):
    existing = {"handle": "h1", "gramps_id": "P1", "name": {"value": "Bourges"},
                "place_type": "Municipality", "lat": "47.081", "long": "2.399",
                "placeref_list": [{"ref": "H_CHER"}], "alt_names": []}

    def on_put(request):
        raise AssertionError("no PUT expected when already conforming")

    mocker.patch.object(write_tools, "get_client", return_value=_client(on_put=on_put, existing=existing))
    data = json.loads(GrampsUpdatePlaceTool()._run(
        handle="h1", name="Bourges", place_type="Municipality", lat="47.081", long="2.399",
        placeref_list=[{"ref": "H_CHER"}]))
    assert data["data"]["noop"] is True
