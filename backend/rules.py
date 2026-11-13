"""Status, limits and hazard flags derived from dataset rows.

Pure functions: no I/O, no LLM, no web. Every value returned either comes
straight from a dataset row or is the literal "No data in dataset".
"""

from __future__ import annotations

from . import config, data_layer, hazard_codes, matcher

STATUS_PROHIBITED = "PROHIBITED"
STATUS_RESTRICTED = "RESTRICTED"
STATUS_PERMITTED_WITH_LIMITS = "PERMITTED_WITH_LIMITS"
STATUS_POSSIBLE_MATCH_VERIFY = "POSSIBLE_MATCH_VERIFY"
STATUS_NO_ANNEX_ENTRY_FOUND = "NO_ANNEX_ENTRY_FOUND"
STATUS_UNIDENTIFIED = "UNIDENTIFIED"

# Display / sort order used by the report and the UI (most severe first).
STATUS_ORDER = (
    STATUS_PROHIBITED,
    STATUS_RESTRICTED,
    STATUS_PERMITTED_WITH_LIMITS,
    STATUS_POSSIBLE_MATCH_VERIFY,
    STATUS_NO_ANNEX_ENTRY_FOUND,
    STATUS_UNIDENTIFIED,
)
STATUS_RANK = {status: rank for rank, status in enumerate(STATUS_ORDER)}

UNCONFIRMED = "unconfirmed"
DISAGREEMENT_NOTE = "sources disagree; the stricter classification applies"

# Fields shown per ingredient whose empty value must read "No data in dataset".
LIMIT_FIELDS = (
    "max_concentration_pct",
    "max_concentration_raw",
    "conditions_of_use",
    "usage_condition",
    "product_type_conditions",
    "other_conditions",
)
ANNEX_FIELDS = ("annex", "reference_number", "permitted_list")
SKIN_IRRITATION_FIELD = "skin_irritation"


def status_for_row(row: dict) -> str:
    """Map a dataset row to exactly one status."""
    safety_class = (row.get("safety_class") or "").upper()
    if safety_class == "PROHIBITED":
        return STATUS_PROHIBITED
    if safety_class == "RESTRICTED":
        return STATUS_RESTRICTED
    if safety_class == "PERMITTED":
        return STATUS_PERMITTED_WITH_LIMITS
    if safety_class == "NOT_LISTED_IN_ANNEXES":
        return STATUS_NO_ANNEX_ENTRY_FOUND
    # A row with an unknown class cannot be described, so the name stays open.
    return STATUS_UNIDENTIFIED


def _annex_reference(row: dict) -> str:
    parts = []
    if row.get("annex") and row["annex"].upper() != "NONE":
        parts.append(f"Annex {row['annex']}")
    if row.get("reference_number"):
        parts.append(f"entry {row['reference_number']}")
    return " ".join(parts) if parts else config.NO_DATA


def _status_source(row: dict) -> str:
    title = row.get("annex_title") or "EU CosIng annex dataset"
    basis = row.get("regulation_basis")
    return f"{title}; regulation basis {basis}" if basis else title


def _source_entries(row: dict, flags: dict) -> list[dict]:
    """One source object per field shown, all from the dataset's own columns."""
    snapshot = row.get("source_snapshot") or config.NO_DATA
    version = row.get("dataset_version") or config.NO_DATA
    reference = _annex_reference(row)
    entries = [
        {
            "field": "status",
            "source": _status_source(row),
            "reference": reference,
            "snapshot": snapshot,
            "dataset_version": version,
        }
    ]
    if "cmr" in flags and row.get("toxicity_source"):
        entries.append(
            {
                "field": "cmr",
                "source": row["toxicity_source"],
                "reference": reference,
                "snapshot": snapshot,
                "dataset_version": version,
            }
        )
    if "fragrance_allergen" in flags and row.get("allergy_source"):
        entries.append(
            {
                "field": "fragrance_allergen",
                "source": row["allergy_source"],
                "reference": reference,
                "snapshot": snapshot,
                "dataset_version": version,
            }
        )
    if "clp_hazards" in flags and row.get("echa_source"):
        entries.append(
            {
                "field": "clp_hazards",
                "source": row["echa_source"],
                "reference": reference,
                "snapshot": snapshot,
                "dataset_version": version,
            }
        )
    if "sccs" in flags:
        entries.append(
            {
                "field": "sccs",
                "source": row.get("sccs_document") or config.NO_DATA,
                "reference": reference,
                "snapshot": snapshot,
                "dataset_version": version,
            }
        )
    return entries


def _cmr_flag(row: dict) -> dict | None:
    toxicity_class = (row.get("toxicity_class") or "").upper()
    flagged = (row.get("cmr_flag") or "").upper() == "YES" or toxicity_class in ("CMR_1A_1B", "CMR_2")
    if not flagged:
        return None
    flag = {
        "categories": row.get("cmr_categories") or toxicity_class,
        "note": None,
    }
    if (row.get("echa_vs_annex_cmr") or "").upper() in ("ECHA_CMR_ONLY", "ANNEX_CMR_ONLY"):
        flag["note"] = DISAGREEMENT_NOTE
    return flag


def _fragrance_allergen_flag(row: dict) -> dict | None:
    if (row.get("allergy_risk") or "").upper() != "FRAGRANCE_ALLERGEN_LABELLING_REQUIRED":
        return None
    return {"requirement": "Fragrance allergen labelling required (EU)"}


def _clp_hazards(row: dict) -> list[dict]:
    codes = [code.strip() for code in (row.get("echa_h_codes") or "").split("|") if code.strip()]
    return [{"code": code, "text": hazard_codes.describe(code)} for code in codes]


def _sccs_flag(row: dict) -> dict | None:
    conclusion = row.get("sccs_conclusion")
    if not conclusion:
        return None
    text = conclusion if len(conclusion) <= 300 else conclusion[:300].rstrip() + "..."
    return {"conclusion": text, "document": row.get("sccs_document") or config.NO_DATA}


def build_flags(row: dict, unconfirmed: bool) -> dict:
    flags: dict = {}
    cmr = _cmr_flag(row)
    if cmr:
        flags["cmr"] = cmr
    allergen = _fragrance_allergen_flag(row)
    if allergen:
        flags["fragrance_allergen"] = allergen
    hazards = _clp_hazards(row)
    if hazards:
        flags["clp_hazards"] = hazards
    sccs = _sccs_flag(row)
    if sccs:
        flags["sccs"] = sccs
    if unconfirmed and flags:
        flags[UNCONFIRMED] = True
    return flags


def _pick_primary_row(rows: list[dict]) -> dict:
    """Most severe row wins; every matched row is still listed in sources."""
    return min(rows, key=lambda row: STATUS_RANK.get(status_for_row(row), len(STATUS_ORDER)))


def _identity_fields(row: dict | None) -> dict:
    """Dataset identity and official source links, straight from the row.

    Everything here is a dataset value or a link built from the dataset's own
    annex number; nothing is derived or inferred.
    """
    if row is None:
        return {
            "chemical_name": config.NO_DATA,
            "cas_number": config.NO_DATA,
            "ec_number": config.NO_DATA,
            "annex_title": config.NO_DATA,
            "toxicity_class": config.NO_DATA,
            "allergy_risk": config.NO_DATA,
            "echa_hazard_classes": config.NO_DATA,
            "regulation_basis": config.NO_DATA,
            "source_url": None,
            "dataset_links": [],
        }
    annex = row.get("annex")
    url = config.cosing_annex_url(annex)
    links: list[dict] = []
    if url:
        links.append({"label": f"EU CosIng Annex {str(annex).upper()}", "url": url})
    if row.get("echa_h_codes"):
        links.append({"label": "ECHA CLP inventory", "url": config.ECHA_CLP_INVENTORY_URL})
    return {
        "chemical_name": row.get("chemical_name") or config.NO_DATA,
        "cas_number": row.get("cas_number") or config.NO_DATA,
        "ec_number": row.get("ec_number") or config.NO_DATA,
        "annex_title": row.get("annex_title") or config.NO_DATA,
        "toxicity_class": row.get("toxicity_class") or config.NO_DATA,
        "allergy_risk": row.get("allergy_risk") or config.NO_DATA,
        "echa_hazard_classes": row.get("echa_hazard_classes") or config.NO_DATA,
        "regulation_basis": row.get("regulation_basis") or config.NO_DATA,
        "source_url": url,
        "dataset_links": links,
    }


def _empty_ingredient(match: dict, status: str) -> dict:
    unknown_fields = list(ANNEX_FIELDS) + list(LIMIT_FIELDS) + [SKIN_IRRITATION_FIELD]
    return {
        "input_name": match["input_name"],
        "matched_name": config.NO_DATA,
        "match_type": match["match_type"],
        "match_score": match["match_score"],
        "status": status,
        "annex": config.NO_DATA,
        "reference_number": config.NO_DATA,
        "permitted_list": config.NO_DATA,
        "limits": {field: config.NO_DATA for field in LIMIT_FIELDS},
        "skin_irritation": config.NO_DATA,
        "flags": {},
        "unknown_fields": unknown_fields,
        "sources": [],
        "candidates": match.get("candidates") or [],
        **_identity_fields(None),
    }


def build_ingredient(match: dict) -> dict:
    """Turn one matcher result into the per-ingredient part of the result."""
    dataset = data_layer.get_dataset()
    rows = dataset.get_rows(match.get("matched_row_ids") or [])

    if not rows:
        return _empty_ingredient(match, STATUS_UNIDENTIFIED)

    unconfirmed = match["match_type"] in ("fuzzy_possible", "group_entry")
    statuses = [status_for_row(row) for row in rows]
    if all(status == STATUS_UNIDENTIFIED for status in statuses):
        return _empty_ingredient(match, STATUS_UNIDENTIFIED)

    primary = _pick_primary_row(rows)
    status = STATUS_POSSIBLE_MATCH_VERIFY if unconfirmed else status_for_row(primary)

    unknown_fields: list[str] = []
    annex_values = {}
    for field in ANNEX_FIELDS:
        value = primary.get(field)
        if value:
            annex_values[field] = value
        else:
            annex_values[field] = config.NO_DATA
            unknown_fields.append(field)

    limits = {}
    for field in LIMIT_FIELDS:
        value = primary.get(field)
        if value:
            limits[field] = value
        else:
            limits[field] = config.NO_DATA
            unknown_fields.append(field)

    # Skin irritation is never derived. When H315 is classified it appears only
    # as a CLP hazard code in flags.clp_hazards.
    unknown_fields.append(SKIN_IRRITATION_FIELD)

    flags = build_flags(primary, unconfirmed)
    sources = []
    for row in rows:
        row_flags = flags if row["ingredient_id"] == primary["ingredient_id"] else build_flags(row, unconfirmed)
        for entry in _source_entries(row, row_flags):
            if entry not in sources:
                sources.append(entry)

    return {
        "input_name": match["input_name"],
        "matched_name": primary.get("ingredient_name") or config.NO_DATA,
        "match_type": match["match_type"],
        "match_score": match["match_score"],
        "status": status,
        "annex": annex_values["annex"],
        "reference_number": annex_values["reference_number"],
        "permitted_list": annex_values["permitted_list"],
        "limits": limits,
        "skin_irritation": config.NO_DATA,
        "flags": flags,
        "unknown_fields": unknown_fields,
        "sources": sources,
        "candidates": match.get("candidates") or [],
        **_identity_fields(primary),
    }


def summarize(ingredients: list[dict]) -> dict:
    """Transparent counts only: no score, no grade, no risk label."""

    def count(status: str) -> int:
        return sum(1 for item in ingredients if item["status"] == status)

    return {
        "total": len(ingredients),
        "prohibited": count(STATUS_PROHIBITED),
        "restricted": count(STATUS_RESTRICTED),
        "permitted_with_limits": count(STATUS_PERMITTED_WITH_LIMITS),
        "cmr_flagged": sum(1 for item in ingredients if "cmr" in item["flags"]),
        "fragrance_allergens": sum(1 for item in ingredients if "fragrance_allergen" in item["flags"]),
        "no_annex_entry_found": count(STATUS_NO_ANNEX_ENTRY_FOUND),
        "possible_match_verify": count(STATUS_POSSIBLE_MATCH_VERIFY),
        "unidentified": count(STATUS_UNIDENTIFIED),
    }


def analyze_names(names: list[str]) -> dict:
    """Match and evaluate a list of already-parsed names."""
    matches = matcher.match_ingredients(names)
    ingredients = [build_ingredient(match) for match in matches]
    ingredients.sort(key=lambda item: STATUS_RANK[item["status"]])
    return {"summary": summarize(ingredients), "ingredients": ingredients}
