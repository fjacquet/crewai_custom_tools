"""Shared deterministic identity scoring against nominal registers.

One rule everywhere (INSEE/MatchID, Mémoire des hommes, future registers):
same name + same birth YEAR alone is a near-certain homonym on a national file —
year-only concordance is capped so it can never cross the proposal threshold alone.
"""

from __future__ import annotations

from crewai_custom_tools.tools.genealogy.geo.score import similarity


def birth_concordance(birth_iso: str, other_iso: str) -> float:
    """Concordance of two ISO-ish birth dates ('YYYY-MM-DD' or 'YYYY'). Pure.

    1.0 exact full date, 0.5 same year only, 0.0 mismatch/absent.
    """
    a = (birth_iso or "").replace("-", "").strip()
    b = (other_iso or "").replace("-", "").strip()
    if not a or not b:
        return 0.0
    if len(a) == 8 and len(b) == 8:
        return 1.0 if a == b else (0.5 if a[:4] == b[:4] else 0.0)
    return 0.5 if a[:4] == b[:4] else 0.0


def score_identity(surname: str, given: str, birth_iso: str,
                   m_surname: str, m_givens: list[str], m_birth_iso: str) -> float:
    """0.5·sim(surname) + 0.2·sim(given head vs best candidate given) + 0.3·birth.

    A divergent birth eliminates (0.0). Pure.
    """
    conc = birth_concordance(birth_iso, m_birth_iso)
    if conc == 0.0:
        return 0.0
    sim_nom = similarity(surname, m_surname or "")
    given_head = ((given or "").replace(",", " ").split() or [""])[0]
    sim_prenom = max((similarity(given_head, g) for g in m_givens if g), default=0.0)
    return round(0.5 * sim_nom + 0.2 * sim_prenom + 0.3 * conc, 3)
