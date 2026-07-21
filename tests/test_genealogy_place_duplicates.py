"""Tests de la détection pure des doublons de lieux."""

from crewai_custom_tools.tools.genealogy.analysis.place_duplicates import (
    normaliser_nom_lieu,
)


def test_casse_accents_et_separateurs_convergent():
    assert normaliser_nom_lieu("Saint-Palais") == normaliser_nom_lieu("SAINT PALAIS")
    assert normaliser_nom_lieu("Nohant-en-Goût") == normaliser_nom_lieu("nohant en gout")


def test_apostrophe_typographique_equivaut_a_l_ascii():
    """L'apostrophe courbe est l'usage typographique standard ; elle arrive par copier-coller."""
    assert normaliser_nom_lieu("L'Isle-Adam") == normaliser_nom_lieu("L’Isle-Adam")


def test_ligature_oe_equivaut_a_oe():
    """NFD décompose les accents, pas les ligatures. Vœuil-et-Giget (Charente) et
    Œuilly (Aisne) sont des communes réelles ; Ænes est un hameau norvégien réel —
    la ligature en minuscule (œ) et en majuscule (Œ, Æ) doit converger avec sa forme
    dépliée (« oe », « OE », « ae », « AE »)."""
    assert normaliser_nom_lieu("Vœuil-et-Giget") == normaliser_nom_lieu("Voeuil-et-Giget")
    assert normaliser_nom_lieu("Œuilly") == normaliser_nom_lieu("Oeuilly")
    assert normaliser_nom_lieu("Ænes") == normaliser_nom_lieu("Aenes")


def test_lettre_barree_ne_converge_pas_avec_sa_transliteration():
    """La table _LIGATURES couvre les ligatures (œ, æ), pas les lettres barrées.
    ø/Ø est une lettre scandinave à part entière, qu'Unicode ne décompose pas et
    qui n'est ni un accent ni une ligature composée. La transformer en "o" serait
    un choix arbitraire : rien ne justifierait alors d'ignorer le ł polonais ou le
    đ croate. Décision délibérée : les lettres barrées restent hors du périmètre
    de cette table, et Tønder ne doit pas s'y confondre avec Tonder."""
    assert normaliser_nom_lieu("Tønder") != normaliser_nom_lieu("Tonder")


def test_l_apostrophe_reste_un_separateur_et_ne_disparait_pas():
    """Si l'apostrophe était supprimée au lieu d'être séparée, deux communes
    distinctes se confondraient."""
    assert normaliser_nom_lieu("L'Isle-Adam") != normaliser_nom_lieu("Lisle-Adam")


def test_chaine_vide_et_blancs():
    assert normaliser_nom_lieu("") == ""
    assert normaliser_nom_lieu("   ") == ""
