"""Optional web context (Tavily): separate, user-triggered, never part of the facts.

This module returns verbatim snippets only. It never summarizes, never scores
and never changes the analysis: the caller shows it in its own panel.
"""

from __future__ import annotations

import time
from datetime import date
from urllib.parse import urlsplit

import httpx

from . import config, data_layer

_cache: dict[tuple, tuple[float, dict]] = {}

NOT_CONFIGURED = "Web context is not configured"
NO_RELIABLE_SOURCES = "No reliable web sources found"
NETWORK_ERROR = "Web search is unavailable right now. Please try again later."
PANEL_NOTE = "Unverified web context. This is not part of the assessment."

# The only topic strings that may reach the query. Anything else is ignored.
# The first four are the report's fixed mapping; the last three are the
# toxicological endpoints the evidence review adds for dataset gaps.
TOPIC_MAP = (
    "skin irritation",
    "allergy / sensitization",
    "use limits",
    "hazard classification",
    "eye irritation",
    "skin sensitization",
    "toxicity",
)


class TooManyIngredients(ValueError):
    """Raised when a batch carries more names than one click may search."""


def clean_topics(topics) -> list[str]:
    """Keep the known topics, de-duplicated, in a stable order."""
    wanted = {str(topic).strip().lower() for topic in (topics or [])}
    return [topic for topic in TOPIC_MAP if topic in wanted]


def build_query(ingredient: str, topics) -> str:
    words = [ingredient, "cosmetic", "ingredient", *clean_topics(topics), "SCCS", "CIR"]
    return " ".join(words)


def _site_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _excerpt(content: str) -> str:
    """Verbatim snippet, truncated to the configured number of words."""
    words = (content or "").split()
    return " ".join(words[: config.WEB_EXCERPT_MAX_WORDS])


def _cache_get(key: tuple) -> dict | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    created_at, payload = entry
    if time.time() - created_at > config.WEB_CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return payload


def _cache_put(key: tuple, payload: dict) -> None:
    _cache[key] = (time.time(), payload)


def clear_cache() -> None:
    _cache.clear()


def _request_search(query: str) -> list[dict] | None:
    """Return raw Tavily results, or None when the call failed."""
    payload = {
        "query": query,
        "max_results": config.WEB_RESULTS_FETCHED,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
    }
    headers = {
        "Authorization": f"Bearer {config.TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=config.WEB_TIMEOUT_SECONDS) as client:
            response = client.post(config.TAVILY_SEARCH_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    results = data.get("results")
    return results if isinstance(results, list) else []


def _to_item(result: dict) -> dict | None:
    url = (result.get("url") or "").strip()
    content = (result.get("content") or "").strip()
    site = _site_of(url)
    if not url or not site or not content:
        return None
    if config.is_blocked_host(site):
        return None
    excerpt = _excerpt(content)
    if not excerpt:
        return None
    return {
        "title": (result.get("title") or site).strip(),
        "site": site,
        "url": url,
        "retrieved_date": date.today().isoformat(),
        "source_type": config.source_type_for(site),
        "excerpt": excerpt,
    }


def search(ingredient: str, include_other: bool = False, topics=None) -> dict:
    """Search the web for one ingredient. Never raises."""
    name = data_layer.normalize(ingredient) or ""
    if not config.web_context_enabled():
        return {"enabled": False, "items": [], "message": NOT_CONFIGURED}

    if not name:
        return {"enabled": True, "items": [], "message": "No ingredient name provided."}

    cleaned_topics = clean_topics(topics)
    cache_key = (name, tuple(cleaned_topics), bool(include_other))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    query = build_query(name, cleaned_topics)
    results = _request_search(query)
    if results is None:
        return {"enabled": True, "items": [], "message": NETWORK_ERROR}

    items = []
    for result in results:
        item = _to_item(result) if isinstance(result, dict) else None
        if item is None:
            continue
        if not include_other and item["source_type"] != "official_scientific":
            continue
        items.append(item)
        if len(items) >= config.WEB_RESULTS_RETURNED:
            break

    payload = {
        "enabled": True,
        "items": items,
        "message": None if items else NO_RELIABLE_SOURCES,
        "notice": PANEL_NOTE,
        "include_other": bool(include_other),
        "topics": cleaned_topics,
    }
    _cache_put(cache_key, payload)
    return payload


def search_many(items: list[dict], include_other: bool = False,
                delay_seconds: float | None = None) -> dict:
    """Search several ingredients one after another, keyed by input name.

    One batch is one user action, so the caller applies a single rate-limit
    check. Results (including failures) always come back per ingredient.
    """
    if len(items) > config.WEB_BATCH_MAX:
        raise TooManyIngredients(
            f"At most {config.WEB_BATCH_MAX} ingredients can be searched at once."
        )

    pause = config.WEB_BATCH_DELAY_SECONDS if delay_seconds is None else delay_seconds
    results: dict[str, dict] = {}
    for position, item in enumerate(items):
        if position and pause > 0:
            time.sleep(pause)
        name = str(item.get("ingredient") or "").strip()
        if not name:
            continue
        results[name] = search(name, include_other=include_other, topics=item.get("topics"))
    return {"enabled": config.web_context_enabled(), "results": results}
