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


def test_parse_lone_postal_not_taken_as_insee():
    p = parse_pname(", , Bourges, , 18000, Cher, Centre-Val de Loire, France")
    assert p.insee is None                 # 18000 is a postal, not an INSEE
    assert p.postal == "18000"
    assert p.commune == "Bourges"
    assert p.shifted is True               # France + no reliable code -> fuzzy, not authoritative


def test_parse_corsica_lone_insee_still_detected():
    p = parse_pname(", , Ajaccio, 2A004, , Corse-du-Sud, Corse, France")
    assert p.insee == "2A004"              # Corsica code is unambiguously INSEE
    assert p.commune == "Ajaccio"


def test_parse_two_codes_first_is_insee():
    p = parse_pname(", , Bourges, 18033, 18000, Cher, Centre-Val de Loire, France")
    assert p.insee == "18033" and p.postal == "18000"   # unchanged behavior


def test_parse_right_truncated_flat_name_is_commune():
    from crewai_custom_tools.tools.genealogy.standardize.places import parse_pname
    p = parse_pname(", , BOURGES, , , , ,")
    assert p.commune == "BOURGES"
    assert p.country == ""

def test_parse_single_token_is_commune():
    from crewai_custom_tools.tools.genealogy.standardize.places import parse_pname
    p = parse_pname("Bourges")
    assert p.commune == "Bourges"
    assert p.country == ""

def test_parse_known_country_last_segment_unchanged():
    from crewai_custom_tools.tools.genealogy.standardize.places import parse_pname
    p = parse_pname("Lausanne, Vaud, Suisse")
    assert p.commune == "Lausanne"
    assert p.country == "Suisse"

def test_parse_full_french_chain_unchanged():
    from crewai_custom_tools.tools.genealogy.standardize.places import parse_pname
    p = parse_pname("Bourges, Cher, Centre-Val de Loire, France")
    assert p.commune == "Bourges"
    assert p.country == "France"
    assert p.departement == "Cher"

def test_parse_garbage_becomes_commune_not_country():
    # A date/URL/description in the name field must NOT be invented as a country;
    # it becomes the commune so the downstream resolver returns nothing -> indecidable.
    from crewai_custom_tools.tools.genealogy.standardize.places import parse_pname
    p = parse_pname(", , 1790 ( avant), , , , ,")
    assert p.commune == "1790 ( avant)"
    assert p.country == ""


def test_parse_recognizes_ags_8_digit_and_keeps_land():
    p = parse_pname(", Waldeck, 06635021, 34513, Regierungsbezirk Kassel, Hesse, Germany")
    assert p.ags == "06635021"
    assert p.commune == "Waldeck"
    assert p.country == "Allemagne"
    assert p.region == "Hesse"           # Land récupéré (plus perdu par le tail)
    assert p.postal == "34513"


def test_parse_no_ags_when_no_8_digit_segment():
    p = parse_pname(", , Bourges, 18033, 18000, Cher, Centre-Val de Loire, France")
    assert p.ags is None                 # non-régression: 5 chiffres reste INSEE/postal
    assert p.insee == "18033"
