"""Thin wrapper around the AniList GraphQL API (no authentication required).

Only the manga search and direct-ID lookup are implemented, returning just
the fields needed for chapter/volume cross-unit estimation in the Behind
column.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Set

import requests

_log = logging.getLogger(__name__)

_URL = "https://graphql.anilist.co"
_SESSION = requests.Session()
_SESSION.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

# AniList allows 90 req/min; stay well under.
REQUEST_DELAY = 0.7

_QUERY_SEARCH = """
query ($search: String) {
  Media(search: $search, type: MANGA, isAdult: false, format_not_in: [NOVEL, ONE_SHOT]) {
    id
    title { romaji english }
    chapters
    volumes
  }
}
"""

_QUERY_BY_ID = """
query ($id: Int) {
  Media(id: $id, type: MANGA) {
    id
    title { romaji english }
    chapters
    volumes
  }
}
"""


def _tokenize(text: str) -> Set[str]:
    """Lower-case alphanumeric tokens, dropping 1-2 char words."""
    return {
        w for w in text.lower().split()
        if len(w) >= 3 and w.isalnum()
    }


def _title_similar(query: str, result_title: str) -> bool:
    """Quick token-overlap check to reject blatantly wrong fuzzy matches."""
    q = _tokenize(query)
    t = _tokenize(result_title)
    if not q or not t:
        # Fallback: substring check for very short titles.
        return query.lower() in result_title.lower() or result_title.lower() in query.lower()
    overlap = len(q & t)
    # Require at least 30% overlap or one exact word match.
    return overlap >= max(1, int(len(q) * 0.3))


def _execute(query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Run a GraphQL query with one retry on transient HTTP errors.

    Returns the ``data.Media`` dict or None on error / no match.
    """
    for attempt in range(2):
        try:
            resp = _SESSION.post(
                _URL,
                json={"query": query, "variables": variables},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return (data.get("data") or {}).get("Media")
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else 0
            if status in (404, 429, 500, 502, 503) and attempt == 0:
                _log.debug("AniList HTTP %s — retrying in 1s", status)
                time.sleep(1.0)
                continue
            _log.warning("AniList request failed (HTTP %s)", status)
            return None
        except Exception:  # noqa: BLE001
            _log.warning("AniList request failed", exc_info=True)
            return None
    return None


def _normalise(media: Dict[str, Any]) -> Dict[str, Any]:
    """Return a flat dict with id, title, chapters, volumes (all optional)."""
    titles = media.get("title") or {}
    title = titles.get("english") or titles.get("romaji") or ""
    return {
        "id": media.get("id"),
        "title": title,
        "chapters": media.get("chapters"),   # int | None
        "volumes": media.get("volumes"),     # int | None
    }


def search_manga(title: str) -> Optional[Dict[str, Any]]:
    """Search AniList for *title*; return normalised dict or None.

    Returns None if the best result is too dissimilar to the query.
    """
    _log.debug("anilist search_manga: %r", title)
    media = _execute(_QUERY_SEARCH, {"search": title})
    if media is None:
        return None
    result = _normalise(media)
    if not _title_similar(title, result["title"]):
        _log.debug("AniList result rejected (too dissimilar): %r vs %r",
                   title, result["title"])
        return None
    _log.debug("anilist search_manga result: %r", result)
    return result


def get_manga(anilist_id: int) -> Optional[Dict[str, Any]]:
    """Fetch AniList entry by *anilist_id*; return normalised dict or None."""
    _log.debug("anilist get_manga: id=%s", anilist_id)
    media = _execute(_QUERY_BY_ID, {"id": anilist_id})
    if media is None:
        return None
    result = _normalise(media)
    _log.debug("anilist get_manga result: %r", result)
    return result
