from crewai_custom_tools.tools.genealogy.models.domain import EventFact, PersonFacts
from crewai_custom_tools.tools.genealogy.pistes import pistes_dhs


def _person():
    birth = EventFact(type="Birth", year=1800, dateval=[3, 4, 1800, False],
                      place_name="Lausanne", place="Lausanne, Vaud, Suisse")
    return PersonFacts(gramps_id="I0500", handle="H5", name="Louis Perret",
                       surname="Perret", given="Louis", sex="M", birth=birth)


def test_ligne_sans_p902_ne_produit_aucune_piste():
    rows = [{"item": "http://www.wikidata.org/entity/Q42", "itemLabel": "Louis Perret",
             "birthDate": "1800-04-03T00:00:00Z", "birthPlaceLabel": "Lausanne"}]
    assert pistes_dhs(_person(), rows) == []


def test_ligne_avec_p902_produit_une_piste_dhs():
    rows = [{"item": "http://www.wikidata.org/entity/Q42", "itemLabel": "Louis Perret",
             "birthDate": "1800-04-03T00:00:00Z", "birthPlaceLabel": "Lausanne",
             "p902": "012345"}]
    pistes = pistes_dhs(_person(), rows)
    assert len(pistes) == 1
    p = pistes[0]
    assert p.source == "dhs"
    assert p.identite == "012345"
    assert p.url == "https://hls-dhs-dss.ch/fr/articles/012345/"
    # Les concordances sont héritées de la ligne Wikidata dont elle dérive.
    assert set(p.concordances) == {"nom", "date complète", "lieu"}
    assert p.force == "forte"
