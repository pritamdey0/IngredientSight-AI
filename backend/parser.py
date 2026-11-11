"""Ingredient-list parsing. Pure deterministic code, no LLM, no I/O."""

from __future__ import annotations

import re

from . import config

# "Ingredients:", "INGREDIENTS -", "Composition:" ...
_PREFIX_RE = re.compile(r"^\s*(?:ingredients?|composition)\s*[:\-]\s*", re.IGNORECASE)
# Start of the "may contain" section, compared case-insensitively.
_MAY_CONTAIN_RE = re.compile(r"(?:may\s+also\s+contain|may\s+contain|\(\s*\+/-?\s*\)|\+/-)", re.IGNORECASE)
# Characters OCR often leaves behind where a list separator belongs.
_STRAY_CHARS_RE = re.compile(r"[|_~]")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_DROP_CHARS_RE = re.compile(r"[\u200b-\u200f\ufeff]")
_OPENERS = "([{"
_CLOSERS = ")]}"


def _clean_text(text: str) -> str:
    text = _CONTROL_CHARS_RE.sub(" ", text)
    text = _DROP_CHARS_RE.sub("", text)
    text = _STRAY_CHARS_RE.sub(",", text)
    return text


def _split_top_level(text: str) -> list[str]:
    """Split on commas/semicolons that are not inside brackets or parentheses."""
    items: list[str] = []
    buffer: list[str] = []
    depth = 0
    for char in text:
        if char in _OPENERS:
            depth += 1
            buffer.append(char)
        elif char in _CLOSERS:
            depth = max(0, depth - 1)
            buffer.append(char)
        elif char in ",;" and depth == 0:
            items.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    items.append("".join(buffer))
    return items


def _clean_item(item: str) -> str:
    item = re.sub(r"\s+", " ", item.strip())
    item = item.strip(" .,;:*-–—")
    return item


def _split_sections(text: str) -> tuple[str, str]:
    match = _MAY_CONTAIN_RE.search(text)
    if not match:
        return text, ""
    return text[: match.start()], text[match.end() :]


def _to_items(section: str, warnings: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in _split_top_level(section):
        item = _clean_item(raw)
        if not item:
            continue
        if len(item) > config.MAX_NAME_CHARS:
            warnings.append(
                f"One ingredient name was longer than {config.MAX_NAME_CHARS} characters "
                "and was truncated."
            )
            item = item[: config.MAX_NAME_CHARS].rstrip()
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def parse_ingredient_list(text: str | None) -> dict:
    """Parse a pasted ingredient list into names plus warnings."""
    warnings: list[str] = []
    if text is None or not text.strip():
        return {
            "ingredients": [],
            "may_contain": [],
            "warnings": ["No ingredient text was provided."],
        }

    cleaned = _clean_text(text)
    cleaned = _PREFIX_RE.sub("", cleaned, count=1)
    cleaned = cleaned.replace("\r", " ").replace("\n", " ")

    main_section, may_contain_section = _split_sections(cleaned)
    ingredients = _to_items(main_section, warnings)
    may_contain = _to_items(may_contain_section, warnings)

    total = len(ingredients) + len(may_contain)
    if total == 0:
        warnings.append("No ingredients could be read from the text.")
    elif total < 2:
        warnings.append(
            "Only one ingredient was found. Check that the whole list was pasted."
        )

    return {
        "ingredients": ingredients,
        "may_contain": may_contain,
        "warnings": warnings,
    }
