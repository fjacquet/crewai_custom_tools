"""Pure parsing of flat GEDCOM-style place strings + country normalization.

A GEDCOM place is comma-delimited, most-specific first, country last. Import
tools (Geneanet/Heredis) often embed an INSEE code. This module is dataset-
agnostic: it reads positions and known-code shapes, it does not hardcode any
particular tree.
"""

from __future__ import annotations

import re
import unicodedata

from crewai_custom_tools.tools.genealogy.models.domain import ParsedPlace

INSEE_RE = re.compile(r"^(?:\d{5}|2[AB]\d{3})$")     # 18033, 2A004
POSTAL_RE = re.compile(r"^\d{4,5}$")

# Table de normalisation des pays : variantes (casse/langue/accent/parasite) → label FR.
_COUNTRY = {
    "france": "France",
    "suisse": "Suisse", "switzerland": "Suisse", "schweiz": "Suisse",
    "allemagne": "Allemagne", "germany": "Allemagne", "deutschland": "Allemagne",
    "italie": "Italie", "italia": "Italie", "italy": "Italie",
    "algerie": "Algérie", "algerie francaise": "Algérie", "algeria": "Algérie",
    "belgique": "Belgique", "belgium": "Belgique",
    "pologne": "Pologne", "poland": "Pologne",
    "etats-unis": "États-Unis", "usa": "États-Unis", "united states": "États-Unis",
}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_country(raw: str) -> str:
    """Map a messy country segment to a canonical French label ('' if empty/unknown)."""
    key = _strip_accents(raw).strip().strip(">").strip().lower()
    if not key:
        return ""
    return _COUNTRY.get(key, raw.strip().strip(">").strip())


def parse_pname(raw: str) -> ParsedPlace:
    """Parse one flat place string into ParsedPlace (positional + code detection)."""
    segments = [s.strip() for s in raw.split(",")]
    nonempty = [s for s in segments if s]
    country = normalize_country(nonempty[-1]) if nonempty else ""

    insee = next((s for s in segments if INSEE_RE.match(s)), None)
    postal = next((s for s in segments if s != insee and POSTAL_RE.match(s)), None)

    commune = ""
    if insee is not None:
        idx = segments.index(insee)
        commune = segments[idx - 1] if idx > 0 else ""
    else:
        # pas de code : commune = 1er segment non vide qui n'est pas le pays
        for s in nonempty[:-1] or nonempty:
            if s and not POSTAL_RE.match(s):
                commune = s
                break

    # département / région : segments non vides entre le code postal et le pays
    tail = [s for s in nonempty if s not in (commune, insee, postal, nonempty[-1] if nonempty else "")]
    departement = tail[0] if len(tail) >= 1 else ""
    region = tail[1] if len(tail) >= 2 else ""

    shifted = country == "France" and insee is None
    return ParsedPlace(raw=raw, commune=commune, insee=insee, postal=postal,
                       departement=departement, region=region, country=country, shifted=shifted)
