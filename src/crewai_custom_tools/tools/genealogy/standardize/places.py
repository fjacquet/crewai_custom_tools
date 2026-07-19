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
    nonempty_idx = [i for i, s in enumerate(segments) if s]
    country_idx = nonempty_idx[-1] if nonempty_idx else None
    country = normalize_country(segments[country_idx]) if country_idx is not None else ""

    insee = next((s for s in segments if INSEE_RE.match(s)), None)
    insee_idx = segments.index(insee) if insee is not None else None
    postal_idx = next((i for i, s in enumerate(segments)
                       if i != insee_idx and POSTAL_RE.match(s)), None)
    postal = segments[postal_idx] if postal_idx is not None else None

    # Commune = segment before the INSEE code; else first non-empty segment that is
    # neither the country position nor a bare code.
    if insee_idx is not None and insee_idx > 0:
        commune = segments[insee_idx - 1]
        commune_idx = insee_idx - 1
    else:
        commune, commune_idx = "", None
        for i in nonempty_idx:
            if i == country_idx or POSTAL_RE.match(segments[i]):
                continue
            commune, commune_idx = segments[i], i
            break

    # Département / région = remaining non-empty segments, excluded BY INDEX (not value).
    used = {country_idx, insee_idx, postal_idx, commune_idx}
    tail = [segments[i] for i in nonempty_idx if i not in used]
    departement = tail[0] if len(tail) >= 1 else ""
    region = tail[1] if len(tail) >= 2 else ""

    shifted = country == "France" and insee is None
    return ParsedPlace(raw=raw, commune=commune, insee=insee, postal=postal,
                       departement=departement, region=region, country=country, shifted=shifted)
