"""DHS (Dictionnaire historique de la Suisse) → Piste.

Pas une API de plus : la propriété Wikidata P902 porte l'identifiant HDS, dont
les articles existent en allemand, français et italien sous le même identifiant.
Ce module est donc une PROJECTION de la source Wikidata, pas un client.
"""

from crewai_custom_tools.tools.genealogy.models.domain import PersonFacts, Piste
from crewai_custom_tools.tools.genealogy.pistes.wikidata import pistes_wikidata

_ARTICLE = "https://hls-dhs-dss.ch/fr/articles/{id}/"


def pistes_dhs(person: PersonFacts, resultats: list[dict]) -> list[Piste]:
    """Une piste DHS par ligne SPARQL portant un P902. Les autres sont ignorées.

    On dérive ligne par ligne plutôt que d'apparier deux listes : `pistes_wikidata`
    saute les lignes dont l'URI n'est pas exploitable, donc un appariement
    positionnel décalerait silencieusement les identifiants HDS.
    """
    pistes: list[Piste] = []
    for row in resultats:
        identifiant = row.get("p902")
        if not identifiant:
            continue
        base = pistes_wikidata(person, [row])
        if not base:                      # URI Wikidata inexploitable -> on passe
            continue
        pistes.append(Piste(
            gramps_id=person.gramps_id, handle=person.handle,
            source="dhs", identite=identifiant,
            url=_ARTICLE.format(id=identifiant),
            requete=base[0].requete,
            concordances=list(base[0].concordances),
            divergences=list(base[0].divergences),
        ))
    return pistes
