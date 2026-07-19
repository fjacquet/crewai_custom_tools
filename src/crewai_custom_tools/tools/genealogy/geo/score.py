"""Pure scoring for place resolution (dataset-agnostic)."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

AMBIGUITY_MARGIN = 0.10


def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.strip().upper()


def similarity(a: str, b: str) -> float:
    """Accent/case-insensitive string similarity in [0,1]."""
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def fuzzy_score(provider_conf: float, asked: str, returned: str) -> float:
    """Combine provider confidence with name similarity (penalizes 'right score, wrong place')."""
    return max(0.0, min(1.0, provider_conf)) * similarity(asked, returned)


def is_ambiguous(candidates: list[float], margin: float = AMBIGUITY_MARGIN) -> bool:
    """True when the top two candidate scores are within `margin` (undecidable → proposition)."""
    if len(candidates) < 2:
        return False
    top2 = sorted(candidates, reverse=True)[:2]
    return (top2[0] - top2[1]) < margin


_PAREN = re.compile(r"\s*\([^)]*\)")             # " (VD)", " (68)"


def _forms(returned: str) -> set[str]:
    """Formes-cœur candidates d'un libellé décoré : le tout, le tout sans suffixe parenthésé,
    et chaque jeton (espaces) de chacun — pour matcher un nom-cœur dans un libellé multi-mots
    ou multi-scripts."""
    stripped = _PAREN.sub("", returned).strip()
    forms = {returned.strip(), stripped}
    for base in (returned, stripped):
        forms.update(tok for tok in base.split() if tok)
    return {f for f in forms if f}


def best_similarity(asked: str, returned: str) -> float:
    """Meilleure similarité entre `asked` et une forme-cœur de `returned`. Monotone :
    toujours >= similarity(asked, returned) — les exacts restent 1.0, les décorations
    ('(VD)', alias multi-scripts) ne dépriment plus le score."""
    return max((similarity(asked, f) for f in _forms(returned)), default=0.0)
