"""Name matching against the reference dataset.

Order: alias -> exact name -> exact synonym -> CAS number -> fuzzy.
The matcher never guesses silently: every row it returns is reported to the
caller so the UI can show what matched and let the user correct the name.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz, process

from . import config, data_layer

FUZZY_HIGH_MIN = 92.0
FUZZY_POSSIBLE_MIN = 80.0
# token_set_ratio scores 100 when the query tokens are a subset of a longer
# name ("peg 40" inside "peg 40 sorbitan stearate"), so two names must have a
# comparable number of words to be treated as the same ingredient.
MIN_TOKEN_RATIO = 0.67
MAX_CANDIDATES = 3
MAX_ROWS = 5

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")

# Words that mark a group entry ("... and its salts", "... derivatives").
GROUP_ENTRY_MARKERS = ("and its salts", "compounds", "derivatives", "esters")


def sanitize_name(name: str | None) -> str:
    """Treat user text as data: strip control characters and cap the length."""
    if not name:
        return ""
    text = _CONTROL_CHARS_RE.sub(" ", str(name))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[: config.MAX_NAME_CHARS].strip()


def is_group_entry_row(row: dict) -> bool:
    if row.get("is_group_entry"):
        return True
    name = (row.get("ingredient_name") or "").lower()
    return any(marker in name for marker in GROUP_ENTRY_MARKERS)


def _word_counts_comparable(first: int, second: int) -> bool:
    if min(first, second) == 0:
        return False
    return min(first, second) / max(first, second) >= MIN_TOKEN_RATIO


def _candidate(row: dict, score: float | None) -> dict:
    return {
        "name": row.get("ingredient_name") or "",
        "score": score,
    }


def _result(
    input_name: str,
    match_type: str,
    score: float | None,
    row_ids: list[str] | None = None,
    candidates: list[dict] | None = None,
) -> dict:
    return {
        "input_name": input_name,
        "match_type": match_type,
        "match_score": score,
        "matched_row_ids": list(row_ids or []),
        "candidates": candidates or [],
    }


def match_ingredient(name: str | None) -> dict:
    dataset = data_layer.get_dataset()
    input_name = sanitize_name(name)
    key = data_layer.normalize(input_name)

    if not key:
        return _result(input_name, "none", None)

    # 1. Human-reviewed alias map.
    alias_key = dataset.aliases.get(key)
    lookup = alias_key or key

    # 2. Exact ingredient name.
    row_ids = dataset.by_name.get(lookup)
    if row_ids:
        return _confirmed(dataset, input_name, row_ids, "exact_name")

    # 3. Exact synonym.
    row_ids = dataset.by_synonym.get(lookup)
    if row_ids:
        return _confirmed(dataset, input_name, row_ids, "synonym")

    # 4. CAS number written in the text.
    cas_match = data_layer.CAS_NUMBER_RE.search(input_name)
    if cas_match and cas_match.group() in dataset.by_cas:
        return _confirmed(dataset, input_name, dataset.by_cas[cas_match.group()], "cas")

    # 5. Fuzzy matching over names and synonyms.
    choices = dataset.fuzz_keys()
    scores: dict[str, float] = {}
    for scorer in (fuzz.WRatio, fuzz.token_set_ratio):
        for _choice, score, index in process.extract(
            lookup, choices, scorer=scorer, limit=20, score_cutoff=FUZZY_POSSIBLE_MIN
        ):
            choice = choices[index]
            scores[choice] = max(scores.get(choice, 0.0), float(score))

    # token_set_ratio scores 100 when the query tokens are a subset of a long
    # name ("magnesium" inside "magnesium ascorbyl phosphate"), so names with a
    # very different word count are dropped instead of reported as matches.
    query_tokens = len(lookup.split())
    scores = {
        key: score
        for key, score in scores.items()
        if _word_counts_comparable(query_tokens, len(key.split()))
    }

    if not scores:
        return _result(input_name, "none", None)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_key, best_score = ranked[0]
    best_ids = dataset.ids_for_key(best_key)
    best_rows = dataset.get_rows(best_ids)

    if best_score >= FUZZY_HIGH_MIN and not any(is_group_entry_row(r) for r in best_rows):
        return _confirmed(dataset, input_name, best_ids, "fuzzy_high", score=round(best_score, 1))

    # 6. Group-entry safeguard and the 80-92 band both stay unconfirmed.
    candidates: list[dict] = []
    seen_names: set[str] = set()
    for choice, score in ranked:
        for row in dataset.get_rows(dataset.ids_for_key(choice)):
            name = row.get("ingredient_name") or ""
            if name in seen_names:
                continue
            seen_names.add(name)
            candidates.append(_candidate(row, round(score, 1)))
        if len(candidates) >= MAX_CANDIDATES:
            break

    top_ids = dataset.ids_for_key(best_key)[:MAX_ROWS]
    return _result(
        input_name,
        "fuzzy_possible" if best_score >= FUZZY_POSSIBLE_MIN else "none",
        round(best_score, 1),
        row_ids=top_ids,
        candidates=candidates[:MAX_CANDIDATES],
    )


def _confirmed(
    dataset: data_layer.Dataset,
    input_name: str,
    row_ids: list[str],
    match_type: str,
    score: float | None = None,
) -> dict:
    """A confirmed match, unless the matched row describes a whole group."""
    rows = dataset.get_rows(row_ids)
    if any(is_group_entry_row(row) for row in rows):
        candidates = [_candidate(row, score if score is not None else 100.0) for row in rows]
        return _result(
            input_name,
            "group_entry",
            score if score is not None else 100.0,
            row_ids=row_ids[:MAX_ROWS],
            candidates=candidates[:MAX_CANDIDATES],
        )
    return _result(input_name, match_type, score if score is not None else 100.0, row_ids=row_ids)


def match_ingredients(names: list[str]) -> list[dict]:
    return [match_ingredient(name) for name in names]
