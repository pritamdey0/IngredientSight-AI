"""Dataset loading, normalization and lookup indexes.

The slim dataset (data/reference.csv, built by scripts/build_reference.py) is
loaded once per process. Nothing here invents data: empty cells, NaN and the
literal "UNKNOWN" all become None.

Data semantics (also documented in the README):
- safety_class PROHIBITED / RESTRICTED / PERMITTED are official EU annex
  entries (Annex II / III / IV-V-VI).
- safety_class NOT_LISTED_IN_ANNEXES rows are only a SAMPLE of unregulated
  inventory ingredients, not a complete list of safe substances.
- A confident match to a NOT_LISTED_IN_ANNEXES row gives NO_ANNEX_ENTRY_FOUND.
  A name that cannot be matched at all is UNIDENTIFIED, because annex entries
  often use chemical names that differ from the INCI name on the label.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import pandas as pd

from . import config

CAS_NUMBER_RE = re.compile(r"\d{2,7}-\d{2}-\d")
_PERCENTAGE_RE = re.compile(r"\d+(?:[.,]\d+)?\s*%")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_SYNONYM_SPLIT_RE = re.compile(r"[;|/,]")
_WHITESPACE_RE = re.compile(r"\s+")

# Values that mean "the dataset has nothing here".
_MISSING_VALUES = {"", "nan", "none", "null", "unknown", "na", "n/a"}

# A few rows carry an entire inventory in the synonym column. Such a blob is
# not an alias for anything, so it is kept out of the synonym index.
MAX_SYNONYM_WORDS = 20


def normalize(text: str | None) -> str:
    """Normalize a name for matching keys only (never for display)."""
    if not text:
        return ""
    value = str(text).lower()
    value = _PERCENTAGE_RE.sub(" ", value)
    value = value.replace("&", " and ")
    value = _NON_ALNUM_RE.sub(" ", value)
    return " ".join(value.split())


def clean_value(value: object) -> str | None:
    """Return a stripped string, or None when the dataset has no value."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _MISSING_VALUES:
        return None
    return text


@dataclass
class Dataset:
    rows: list[dict]
    by_id: dict[str, dict]
    by_name: dict[str, list[str]] = field(default_factory=dict)
    by_synonym: dict[str, list[str]] = field(default_factory=dict)
    by_cas: dict[str, list[str]] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    fuzz_map: dict[str, list[str]] = field(default_factory=dict)
    info: dict = field(default_factory=dict)

    def get_row(self, row_id: str) -> dict | None:
        return self.by_id.get(str(row_id))

    def get_rows(self, row_ids: list[str]) -> list[dict]:
        rows = []
        for row_id in row_ids:
            row = self.by_id.get(str(row_id))
            if row is not None:
                rows.append(row)
        return rows

    def fuzz_keys(self) -> list[str]:
        """Keys used for fuzzy matching (names and split synonyms)."""
        return list(self.fuzz_map)

    def build_fuzz_cache(self) -> None:
        merged: dict[str, list[str]] = {}
        for key, ids in self.by_name.items():
            merged.setdefault(key, []).extend(ids)
        for key, ids in self.by_synonym.items():
            merged.setdefault(key, []).extend(ids)
        # Remove duplicates while keeping the order stable.
        self.fuzz_map = {key: list(dict.fromkeys(ids)) for key, ids in merged.items()}

    def ids_for_key(self, key: str) -> list[str]:
        """Rows for a fuzzy key: an exact name wins over synonym entries.

        Some rows list a whole inventory as synonyms, so a very common word such
        as "glycerin" can also be a synonym of an unrelated entry. The name
        index is therefore authoritative whenever it has the key.
        """
        name_ids = self.by_name.get(key)
        if name_ids:
            return list(name_ids)
        return self.fuzz_map.get(key, [])


_dataset: Dataset | None = None


def _load_aliases() -> dict[str, str]:
    if not config.ALIASES_JSON.exists():
        return {}
    with config.ALIASES_JSON.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    aliases: dict[str, str] = {}
    for source, target in raw.items():
        source_key = normalize(source)
        target_key = normalize(target)
        if source_key and target_key:
            aliases[source_key] = target_key
    return aliases


def _split_cas_numbers(value: str | None) -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in value.replace(";", "|").split("|")]
    return [part for part in parts if CAS_NUMBER_RE.fullmatch(part)]


def load() -> Dataset:
    """Load the dataset once. Raises RuntimeError when it has not been built."""
    global _dataset
    if _dataset is not None:
        return _dataset

    if not config.REFERENCE_CSV.exists():
        raise RuntimeError(
            f"Dataset not found at {config.REFERENCE_CSV}. "
            "Run: python scripts/build_reference.py"
        )

    frame = pd.read_csv(
        config.REFERENCE_CSV, dtype=str, keep_default_na=False, low_memory=False
    )

    rows: list[dict] = []
    for record in frame.to_dict(orient="records"):
        row = {key: clean_value(value) for key, value in record.items()}
        row["ingredient_id"] = str(record.get("ingredient_id", "")).strip()
        row["is_group_entry"] = str(record.get("is_group_entry", "")).strip().lower() == "true"
        rows.append(row)

    by_id: dict[str, dict] = {}
    by_name: dict[str, list[str]] = {}
    by_synonym: dict[str, list[str]] = {}
    by_cas: dict[str, list[str]] = {}

    for row in rows:
        row_id = row["ingredient_id"]
        by_id[row_id] = row

        name_key = normalize(row.get("ingredient_name"))
        if name_key:
            by_name.setdefault(name_key, []).append(row_id)

        synonyms = row.get("cosing_inci_synonyms")
        if synonyms:
            # Full entry first (it may contain commas inside a chemical name),
            # then each part split on ; | / and , as documented.
            for key in [normalize(synonyms)] + [
                normalize(part) for part in _SYNONYM_SPLIT_RE.split(synonyms)
            ]:
                if key and len(key) >= 3 and len(key.split()) <= MAX_SYNONYM_WORDS:
                    by_synonym.setdefault(key, []).append(row_id)

        for cas in _split_cas_numbers(row.get("cas_number_all")):
            by_cas.setdefault(cas, []).append(row_id)

    versions = sorted({row["dataset_version"] for row in rows if row.get("dataset_version")})
    snapshots = sorted({row["source_snapshot"] for row in rows if row.get("source_snapshot")})

    dataset = Dataset(
        rows=rows,
        by_id=by_id,
        by_name=by_name,
        by_synonym=by_synonym,
        by_cas=by_cas,
        aliases=_load_aliases(),
        info={
            "rows": len(rows),
            "dataset_version": ", ".join(versions) if versions else None,
            "source_snapshot": ", ".join(snapshots) if snapshots else None,
        },
    )
    dataset.build_fuzz_cache()
    _dataset = dataset
    return dataset


def is_loaded() -> bool:
    return _dataset is not None


def get_dataset() -> Dataset:
    return load()


def reset() -> None:
    """Drop the cached dataset (used by tests)."""
    global _dataset
    _dataset = None
