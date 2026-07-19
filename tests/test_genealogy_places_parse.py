# crewai_custom_tools/tests/test_genealogy_places_parse.py
from crewai_custom_tools.tools.genealogy.standardize.places import (
    normalize_country, parse_pname,
)


def test_parse_aligned_fr_with_insee():
    p = parse_pname(", , Bourges, 18033, 18000, Cher, Centre-Val de Loire, France")
    assert (p.commune, p.insee, p.postal) == ("Bourges", "18033", "18000")
    assert (p.departement, p.region, p.country) == ("Cher", "Centre-Val de Loire", "France")
    assert p.shifted is False


def test_parse_shifted_fr_without_code_flags_shift():
    # établissement en tête, pas de code INSEE trouvé pour un lieu français
    p = parse_pname("Hôpital, , , , , , , France")
    assert p.insee is None
    assert p.shifted is True
    assert p.country == "France"


def test_parse_non_fr_no_code_not_shifted():
    p = parse_pname(", , Zürich, , , , , Suisse")
    assert p.commune == "Zürich"
    assert p.insee is None
    assert p.country == "Suisse"
    assert p.shifted is False            # hors FR : pas de code attendu → pas un décalage


def test_normalize_country_variants():
    assert normalize_country("FRANCE") == "France"
    assert normalize_country("Switzerland") == "Suisse"
    assert normalize_country("Germany>") == "Allemagne"
    assert normalize_country("Algerie") == "Algérie"
    assert normalize_country("") == ""


def test_parse_repeated_value_not_deduped_by_value():
    # commune/département homonyme (Marne) : l'exclusion doit être par INDEX, pas par valeur
    p = parse_pname(", , Marne, , , Marne, Grand Est, France")
    assert p.commune == "Marne"
    assert p.departement == "Marne" and p.region == "Grand Est"


def test_parse_country_only_string_has_empty_commune():
    p = parse_pname(", , , , , , , France")
    assert p.commune == ""            # le pays n'est jamais choisi comme commune
    assert p.country == "France" and p.shifted is True
