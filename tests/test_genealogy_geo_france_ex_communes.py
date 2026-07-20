# tests/test_genealogy_geo_france_ex_communes.py
from crewai_custom_tools.tools.genealogy.geo import france_ex_communes as fec

# Ligne réellement rendue par query.wikidata.org pour ?item wdt:P374 "55451"
_ROW_SAINT_AGNANT = {
    "item": "http://www.wikidata.org/entity/Q25398054",
    "dissolved": "1972-12-31T00:00:00Z",
    "succInsee": "55012",
    "coord": "Point(5.622588 48.842142)",
}


def test_parse_wkt_point_is_lon_lat():
    # WKT met la LONGITUDE en premier, comme GeoJSON. Inverser placerait
    # Saint-Agnant au large de la Somalie.
    assert fec.parse_wkt_point("Point(5.622588 48.842142)") == ("48.842142", "5.622588")


def test_parse_wkt_point_handles_negative_longitude():
    assert fec.parse_wkt_point("Point(-1.553621 47.218371)") == ("47.218371", "-1.553621")


def test_parse_wkt_point_rejects_garbage():
    assert fec.parse_wkt_point("") is None
    assert fec.parse_wkt_point("MULTIPOLYGON((0 0))") is None


def test_wikidata_ex_commune_single_row(monkeypatch):
    seen = {}

    def fake_rows(query):
        seen["query"] = query
        return [_ROW_SAINT_AGNANT]

    monkeypatch.setattr(fec, "sparql_rows", fake_rows)
    facts = fec.wikidata_ex_commune("55451")
    assert facts is not None
    assert facts.dissolved == "1972-12-31"           # tronqué à la date ISO
    assert facts.successor_insee == "55012"
    assert facts.lat == "48.842142" and facts.long == "5.622588"
    assert '"55451"' in seen["query"] and "wdt:P374" in seen["query"]


def test_wikidata_ex_commune_no_row_is_none(monkeypatch):
    monkeypatch.setattr(fec, "sparql_rows", lambda query: [])
    assert fec.wikidata_ex_commune("55451") is None


def test_wikidata_ex_commune_distinct_items_is_none(monkeypatch):
    # Vraie ambiguïté : deux ?item DIFFÉRENTS pour le même code INSEE. Cas réel
    # mesuré — l'INSEE 55093 est porté par Q1048039 et Q123186720.
    row_a = {
        "item": "http://www.wikidata.org/entity/Q1048039",
        "dissolved": "1972-12-31T00:00:00Z",
        "succInsee": "55012",
        "coord": "Point(5.622588 48.842142)",
    }
    row_b = {
        "item": "http://www.wikidata.org/entity/Q123186720",
        "dissolved": "1973-01-01T00:00:00Z",
        "succInsee": "55012",
        "coord": "Point(5.6 48.8)",
    }
    monkeypatch.setattr(fec, "sparql_rows", lambda query: [row_a, row_b])
    assert fec.wikidata_ex_commune("55093") is None


def test_wikidata_ex_commune_multivalued_coord_is_not_ambiguous(monkeypatch):
    # Fan-out SPARQL, pas ambiguïté : MÊME ?item, mais P625 multivaluée rend
    # deux lignes (deux revendications de coordonnées). La datation doit passer.
    row_a = dict(_ROW_SAINT_AGNANT)
    row_b = dict(_ROW_SAINT_AGNANT, coord="Point(5.6 48.8)")
    monkeypatch.setattr(fec, "sparql_rows", lambda query: [row_a, row_b])
    facts = fec.wikidata_ex_commune("55451")
    assert facts is not None
    assert facts.dissolved == "1972-12-31"
    assert facts.successor_insee == "55012"


def test_wikidata_ex_commune_missing_optionals(monkeypatch):
    # OPTIONAL non satisfaits : la variable est simplement absente de la ligne.
    monkeypatch.setattr(fec, "sparql_rows",
                        lambda query: [{"item": "http://www.wikidata.org/entity/Q1"}])
    facts = fec.wikidata_ex_commune("55451")
    assert facts is not None
    assert facts.dissolved is None and facts.successor_insee is None
    assert facts.lat is None and facts.long is None


def test_wikidata_ex_commune_network_failure_is_none(monkeypatch):
    import requests

    def boom(query):
        raise requests.ConnectionError("wikidata down")

    monkeypatch.setattr(fec, "sparql_rows", boom)
    # Wikidata n'est qu'un enrichisseur : une panne réseau ne doit pas faire
    # échouer la résolution, seulement priver de la datation.
    assert fec.wikidata_ex_commune("55451") is None


def test_wikidata_ex_commune_malformed_json_is_none(monkeypatch):
    import requests

    def boom(query):
        # requests.exceptions.JSONDecodeError hérite de RequestException (vérifié) :
        # un JSON malformé est donc couvert par la même clause que le réseau.
        raise requests.exceptions.JSONDecodeError("bad", "", 0)

    monkeypatch.setattr(fec, "sparql_rows", boom)
    assert fec.wikidata_ex_commune("55451") is None


def test_wikidata_ex_commune_programming_error_propagates(monkeypatch):
    import pytest

    def boom(query):
        raise KeyError("variable SPARQL absente du gabarit")

    monkeypatch.setattr(fec, "sparql_rows", boom)
    # Convention du dépôt (cf. places_apply.py) : un bug de programmation remonte,
    # il n'est pas déguisé en « pas de datation ».
    with pytest.raises(KeyError):
        fec.wikidata_ex_commune("55451")
