"""Shared title-matching utilities used by mu_worker and table_model."""

from __future__ import annotations

import re
from typing import List, Optional

# A stored mu_score below this is considered a weak/suspect auto-match.
WEAK_THRESHOLD = 0.25


def norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def jaccard(a: str, b: str) -> float:
    """Jaccard similarity on word sets of two already-normalised strings."""
    sa, sb = set(a.split()), set(b.split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _is_subset_pair(a_words: set, b_words: set) -> bool:
    """True if either non-empty word set is a subset of the other."""
    return bool(a_words and b_words and (a_words <= b_words or b_words <= a_words))


def score_candidate(query_title: str, query_alt: Optional[str],
                    record: dict, hit_title: str) -> float:
    """Return the best Jaccard score between the query titles and all MU titles.

    *record* is a SeriesModelSearchV1 dict.
    *hit_title* is the MU-reported matching alt title for this candidate.

    Titles compared:
      - record["title"]  (primary MU title)
      - hit_title        (the alt title MU matched on, may equal primary)
      - each entry in record.get("associated", [])  (all known alt titles)

    The query is compared against every MU title; the maximum score wins.
    A subset relationship is treated as a perfect score (1.0).
    """
    q_norm = norm(query_title)
    q_words = set(q_norm.split())

    q_alt_norm = norm(query_alt) if query_alt else ""
    q_alt_words = set(q_alt_norm.split()) if q_alt_norm else set()

    mu_titles: List[str] = []
    primary = record.get("title") or ""
    if primary:
        mu_titles.append(primary)
    if hit_title and hit_title != primary:
        mu_titles.append(hit_title)
    for assoc in record.get("associated") or []:
        t = assoc.get("title") or "" if isinstance(assoc, dict) else str(assoc)
        if t and t not in mu_titles:
            mu_titles.append(t)

    best = 0.0
    for raw_mu in mu_titles:
        mu_n = norm(raw_mu)
        mu_words = set(mu_n.split())
        if not mu_words:
            continue

        # Score against folder title
        s = jaccard(q_norm, mu_n)
        if _is_subset_pair(q_words, mu_words):
            return 1.0
        best = max(best, s)

        # Score against alt title if present
        if q_alt_norm:
            s2 = jaccard(q_alt_norm, mu_n)
            if _is_subset_pair(q_alt_words, mu_words):
                return 1.0
            best = max(best, s2)

    return best


def associated_titles(record: dict, hit_title: str) -> List[str]:
    """Collect all unique title strings from a candidate record."""
    titles: List[str] = []
    primary = record.get("title") or ""
    if primary:
        titles.append(primary)
    if hit_title and hit_title not in titles:
        titles.append(hit_title)
    for assoc in record.get("associated") or []:
        t = assoc.get("title") or "" if isinstance(assoc, dict) else str(assoc)
        if t and t not in titles:
            titles.append(t)
    return titles


def is_weak_match(mu_score: float) -> bool:
    """Return True when the stored match score indicates a weak/suspect match."""
    return mu_score < WEAK_THRESHOLD
