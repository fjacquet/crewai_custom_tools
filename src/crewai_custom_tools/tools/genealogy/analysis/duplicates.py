"""Deterministic duplicate detection (R10) — pure, stdlib only."""

from __future__ import annotations

from difflib import SequenceMatcher
from itertools import combinations

from crewai_custom_tools.tools.genealogy.analysis.phonetics import (
    cle_phonetique,
    normalize_name,
)
from crewai_custom_tools.tools.genealogy.models.domain import (
    DuplicateCandidate,
    PersonFacts,
)

__all__ = [
    "find_duplicates",
    "normalize_name",
    "MAX_BLOC",
    "blocking_keys",
    "candidate_pairs",
]

BIRTH_YEAR_WINDOW = 2


def _key(p: PersonFacts) -> str:
    return normalize_name(f"{p.given} {p.surname}")


def find_duplicates(
    people: list[PersonFacts], threshold: float = 0.85
) -> list[DuplicateCandidate]:
    """Return candidate duplicate pairs within `people` (O(n²) over the batch)."""
    out: list[DuplicateCandidate] = []
    keyed = [(p, _key(p), p.birth.year if p.birth else None) for p in people]
    for i in range(len(keyed)):
        pa, ka, ya = keyed[i]
        if ya is None or not ka:
            continue
        for j in range(i + 1, len(keyed)):
            pb, kb, yb = keyed[j]
            if yb is None or not kb or abs(ya - yb) > BIRTH_YEAR_WINDOW:
                continue
            score = SequenceMatcher(None, ka, kb).ratio()
            if score >= threshold:
                out.append(DuplicateCandidate(
                    gramps_id_a=pa.gramps_id, gramps_id_b=pb.gramps_id,
                    score=round(score, 3),
                    reason=f"Homonymes ({ka!r} ≈ {kb!r}), naissances {ya}/{yb}."))
    return out


MAX_BLOC = 60
"""Au-delà, un bloc est ignoré : `Pagan` (151 personnes) produirait 11 325 paires
à lui seul. Le rappel perdu est couvert par les quatre autres clés (spec §4.2)."""

_FENETRE_ANNEE = 2
"""Chaque personne enregistre ses années ±2, si bien que deux personnes distantes
d'au plus 2 ans partagent forcément une clé."""


def blocking_keys(p: PersonFacts) -> set[str]:
    """Rend les clés de blocage d'une personne — du RAPPEL, jamais une preuve."""
    cles: set[str] = set()
    nom = normalize_name(f"{p.given} {p.surname}")
    patronyme = normalize_name(p.surname)
    if nom:
        cles.add(f"nom:{nom}")
    initiale = normalize_name(p.given)[:1]
    phonetique = cle_phonetique(p.surname)
    if phonetique and initiale:
        cles.add(f"pho:{phonetique}:{initiale}")
    if patronyme and p.birth and p.birth.year:
        for delta in range(-_FENETRE_ANNEE, _FENETRE_ANNEE + 1):
            cles.add(f"an:{patronyme}:{p.birth.year + delta}")
    for handle in p.family_handles:
        cles.add(f"fam:{handle}")
    for handle in p.parent_family_handles:
        cles.add(f"par:{handle}")
    return cles


def candidate_pairs(
    people: list[PersonFacts], max_bloc: int = MAX_BLOC
) -> tuple[dict[tuple[str, str], set[str]], list[str]]:
    """Rend les paires candidates et les clés écartées pour cause de bloc trop gros."""
    blocs: dict[str, list[PersonFacts]] = {}
    for personne in people:
        for cle in blocking_keys(personne):
            blocs.setdefault(cle, []).append(personne)
    paires: dict[tuple[str, str], set[str]] = {}
    ignores: list[str] = []
    for cle, membres in blocs.items():
        if len(membres) < 2:
            continue
        if len(membres) > max_bloc:
            ignores.append(cle)
            continue
        for a, b in combinations(membres, 2):
            paires.setdefault(tuple(sorted((a.handle, b.handle))), set()).add(cle)
    return paires, ignores
