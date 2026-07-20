# tests/test_genealogy_wikidata_sparql.py
from crewai_custom_tools.tools.web import wikidata


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_sparql_rows_flattens_bindings(monkeypatch):
    payload = {
        "head": {"vars": ["item", "dissolved"]},
        "results": {"bindings": [
            {"item": {"value": "http://www.wikidata.org/entity/Q25398054"},
             "dissolved": {"value": "1972-12-31T00:00:00Z"}},
        ]},
    }
    seen = {}

    def fake_get(url, params, headers, timeout):
        seen["url"] = url
        seen["query"] = params["query"]
        seen["format"] = params["format"]
        return _FakeResponse(payload)

    monkeypatch.setattr(wikidata.requests, "get", fake_get)
    rows = wikidata.sparql_rows("SELECT ?item WHERE { ?item wdt:P374 '55451' }")
    assert rows == [{"item": "http://www.wikidata.org/entity/Q25398054",
                     "dissolved": "1972-12-31T00:00:00Z"}]
    assert seen["url"] == wikidata.SPARQL_ENDPOINT
    assert seen["format"] == "json"


def test_sparql_rows_empty_results(monkeypatch):
    monkeypatch.setattr(wikidata.requests, "get",
                        lambda *a, **k: _FakeResponse({"results": {"bindings": []}}))
    assert wikidata.sparql_rows("SELECT ?x WHERE { ?x wdt:P374 '00000' }") == []
