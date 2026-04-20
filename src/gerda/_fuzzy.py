"""Fuzzy matching for dataset name typos.

Mirrors the R package logic in load_gerda_web.R:234-274:
  1. Get candidate close matches.
  2. Prefix matches go first.
  3. Otherwise rank by Levenshtein distance.
"""

from __future__ import annotations

from rapidfuzz import fuzz, process


def suggest(name: str, choices: list[str], *, limit: int = 3) -> list[str]:
    """Return up to `limit` candidates close to `name`, prefix matches first."""
    raw = process.extract(
        name, choices, scorer=fuzz.WRatio, limit=max(limit * 3, 10), score_cutoff=50
    )
    candidates = [match for match, _score, _idx in raw]
    if not candidates:
        return []

    prefix = [c for c in candidates if c.startswith(name)]
    rest = [c for c in candidates if c not in prefix]
    rest_sorted = sorted(
        rest,
        key=lambda c: process.extractOne(name, [c], scorer=fuzz.ratio)[1],
        reverse=True,
    )
    return (prefix + rest_sorted)[:limit]
