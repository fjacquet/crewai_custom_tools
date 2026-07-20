"""Wikidata → Piste. Pure : la collecte passe par sparql_rows(), pas par ce module.

Seule source capable de pistes FORTES : ses propriétés sont structurées, donc on
peut en tirer plusieurs facteurs distincts. Réserve connue : Wikidata ne décrit
que des personnes notables, le rendement sur un arbre ordinaire sera faible.
"""

from crewai_custom_tools.tools.genealogy.models.domain import PersonFacts, Piste
from crewai_custom_tools.tools.genealogy.pistes.matchid import event_iso, norm_nom

_SPARQL = """SELECT ?item ?itemLabel ?birthDate ?birthPlaceLabel ?p902 WHERE {{
  ?item wdt:P31 wd:Q5 ;
        rdfs:label ?label .
  FILTER(CONTAINS(LCASE(?label), LCASE("{nom}")))
  OPTIONAL {{ ?item wdt:P569 ?birthDate . }}
  OPTIONAL {{ ?item wdt:P19 ?birthPlace . }}
  OPTIONAL {{ ?item wdt:P902 ?p902 . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,de,en". }}
}} LIMIT 25"""


def requete_wikidata(person: PersonFacts) -> str:
    """La requête SPARQL exacte, rejouable telle quelle. Pure."""
    nom = f"{person.given} {person.surname}".strip()
    return _SPARQL.format(nom=nom.replace('"', ""))


def q_item(uri: str) -> str:
    """"http://www.wikidata.org/entity/Q42" -> "Q42". Chaîne vide si non reconnaissable."""
    return uri.rsplit("/", 1)[-1] if uri else ""


def pistes_wikidata(person: PersonFacts, resultats: list[dict]) -> list[Piste]:
    """Une piste par résultat SPARQL. N'écrit rien, ne conclut rien."""
    requete = requete_wikidata(person)
    naissance_arbre = event_iso(person.birth)
    lieu_arbre = person.birth.place_name if person.birth else ""
    pistes: list[Piste] = []
    for row in resultats:
        identite = q_item(row.get("item", ""))
        if not identite:
            continue
        concordances: list[str] = []
        divergences: list[str] = []

        label = row.get("itemLabel", "")
        if label and norm_nom(person.surname) in norm_nom(label):
            concordances.append("nom")

        # wdt:P569 rend un dateTime complet quelle que soit la précision réelle ;
        # on ne compare donc que les 10 premiers caractères, et seulement si
        # l'arbre porte lui aussi une date COMPLÈTE (10 caractères).
        naissance_wd = (row.get("birthDate") or "")[:10]
        if len(naissance_wd) == 10 and len(naissance_arbre) == 10:
            if naissance_wd == naissance_arbre:
                concordances.append("date complète")
            else:
                divergences.append("dates de naissance différentes")

        lieu_wd = row.get("birthPlaceLabel", "")
        if lieu_arbre and lieu_wd and norm_nom(lieu_arbre) == norm_nom(lieu_wd):
            concordances.append("lieu")

        pistes.append(Piste(
            gramps_id=person.gramps_id, handle=person.handle,
            source="wikidata", identite=identite,
            url=row.get("item") or None,
            requete=requete,
            concordances=concordances, divergences=divergences,
        ))
    return pistes
