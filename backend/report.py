"""Deterministic Markdown report built from the structured result.

Only fixed sentences and dataset values appear here. No LLM output, and the
only web text is the verbatim excerpt list the caller explicitly supplies.
"""

from __future__ import annotations

from . import config, rules

STATUS_TEXT = {
    rules.STATUS_PROHIBITED: "Prohibited in cosmetic products (EU Annex II).",
    rules.STATUS_RESTRICTED: "Restricted: only allowed under the conditions of this annex entry.",
    rules.STATUS_PERMITTED_WITH_LIMITS: "On a positive list: allowed only as listed, under the entry conditions.",
    rules.STATUS_POSSIBLE_MATCH_VERIFY: (
        "Possible match, not confirmed. Check the matched name and pick the right entry before using it."
    ),
    rules.STATUS_NO_ANNEX_ENTRY_FOUND: (
        "No EU annex entry found for this name in the dataset. This is not a safety assessment."
    ),
    rules.STATUS_UNIDENTIFIED: (
        "Not identified in the dataset. The name may be missing from the dataset, and an EU annex "
        "entry may exist under a different chemical name."
    ),
}

# Short names used in tables and count chips.
STATUS_LABELS = {
    rules.STATUS_PROHIBITED: "Prohibited",
    rules.STATUS_RESTRICTED: "Restricted",
    rules.STATUS_PERMITTED_WITH_LIMITS: "Positive list",
    rules.STATUS_POSSIBLE_MATCH_VERIFY: "Verify match",
    rules.STATUS_NO_ANNEX_ENTRY_FOUND: "No annex entry",
    rules.STATUS_UNIDENTIFIED: "Not identified",
}

FIELD_LABELS = {
    "annex": "EU annex",
    "reference_number": "Annex reference number",
    "permitted_list": "Positive list",
    "max_concentration_pct": "Maximum concentration (%)",
    "max_concentration_raw": "Concentration limit as written",
    "conditions_of_use": "Conditions of use",
    "usage_condition": "Usage condition",
    "product_type_conditions": "Product type conditions",
    "other_conditions": "Other conditions",
    "skin_irritation": "Skin irritation",
}

# Lower-case names used inside the "No data in dataset for: ..." line.
GAP_LABELS = {
    "annex": "EU annex",
    "reference_number": "annex reference number",
    "permitted_list": "positive list",
    "max_concentration_pct": "maximum concentration",
    "max_concentration_raw": "concentration limit as written",
    "conditions_of_use": "conditions of use",
    "usage_condition": "usage condition",
    "product_type_conditions": "product type conditions",
    "other_conditions": "other conditions",
    "skin_irritation": "skin irritation",
}

FLAG_LABELS = {
    "cmr": "CMR classification",
    "fragrance_allergen": "Fragrance allergen",
    "clp_hazards": "CLP hazard statements",
    "sccs": "SCCS opinion",
}

MATCH_TYPE_LABELS = {
    "exact_name": "exact name",
    "synonym": "synonym",
    "cas": "CAS number",
    "fuzzy_high": "high-confidence fuzzy match",
    "fuzzy_possible": "possible fuzzy match",
    "group_entry": "group entry match",
    "none": "no match",
}

SOURCE_TYPE_LABELS = {
    "official_scientific": "Official",
    "retailer_brand": "Retailer or brand",
    "review": "Review",
    "blog_forum": "Blog or forum",
    "other": "Other",
}

ANNEX_FIELDS = ("annex", "reference_number", "permitted_list")
ANNEX_ONLY_FIELDS = ANNEX_FIELDS + tuple(rules.LIMIT_FIELDS)

FOOTER_NOTE = (
    "Every value above comes from the dataset or reads “No data in dataset”. Nothing is inferred "
    "from concentration, packaging or web text, and no overall score is produced."
)

WEB_HEADING = "Web context (unverified, not part of the assessment)"
NO_ANNEX_SUMMARY = "No annex entry, so no annex limits apply in the dataset."


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or singular + "s")


def _verb(count: int) -> str:
    return "carries" if count == 1 else "carry"


def _cell(value) -> str:
    """One table cell: pipes escaped, line breaks collapsed."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _annex_cell(ingredient: dict) -> str:
    parts = []
    if ingredient["annex"] != config.NO_DATA:
        parts.append(f"Annex {ingredient['annex']}")
    if ingredient["reference_number"] != config.NO_DATA:
        parts.append(f"entry {ingredient['reference_number']}")
    return " ".join(parts) if parts else config.NO_DATA


def _flags_cell(ingredient: dict) -> str:
    flags = ingredient["flags"]
    parts = []
    if "cmr" in flags:
        parts.append(f"CMR {flags['cmr']['categories']}")
    if "fragrance_allergen" in flags:
        parts.append("Fragrance allergen")
    if flags.get("clp_hazards"):
        parts.append(", ".join(hazard["code"] for hazard in flags["clp_hazards"]))
    if "sccs" in flags:
        parts.append("SCCS opinion")
    if flags.get(rules.UNCONFIRMED):
        parts.append("unconfirmed")
    return "; ".join(parts) if parts else config.NO_DATA


def _summary_sentence(summary: dict) -> str:
    total = summary["total"]
    sentence = f"{total} {_plural(total, 'ingredient')} {'was' if total == 1 else 'were'} checked"
    sentence += "."
    return sentence


def _summary_extras(summary: dict) -> list[str]:
    extras = []
    if summary["cmr_flagged"]:
        count = summary["cmr_flagged"]
        extras.append(f"{count} {_plural(count, 'ingredient')} {_verb(count)} a CMR classification flag.")
    if summary["fragrance_allergens"]:
        count = summary["fragrance_allergens"]
        extras.append(
            f"{count} {_plural(count, 'ingredient')} {_verb(count)} a fragrance allergen labelling requirement."
        )
    return extras


def _value_block(label: str, value: str) -> list[str]:
    """Render one dataset value, keeping line breaks as written."""
    lines = [f"- **{label}:**"]
    for line in str(value).splitlines():
        lines.append(f"    {line}" if line.strip() else "    ")
    return lines


def _flag_lines(flags: dict) -> list[str]:
    lines: list[str] = []
    cmr = flags.get("cmr")
    if cmr:
        text = f"- {FLAG_LABELS['cmr']}: {cmr['categories']}"
        if cmr.get("note"):
            text += f" ({cmr['note']})"
        lines.append(text)
    allergen = flags.get("fragrance_allergen")
    if allergen:
        lines.append(f"- {FLAG_LABELS['fragrance_allergen']}: {allergen['requirement']}")
    hazards = flags.get("clp_hazards")
    if hazards:
        joined = "; ".join(f"{hazard['code']} · {hazard['text']}" for hazard in hazards)
        lines.append(f"- {FLAG_LABELS['clp_hazards']}: {joined}")
    sccs = flags.get("sccs")
    if sccs:
        lines.append(f"- {FLAG_LABELS['sccs']} ({sccs['document']}):")
        for line in sccs["conclusion"].splitlines():
            lines.append(f"    {line}" if line.strip() else "    ")
    if flags.get(rules.UNCONFIRMED):
        lines.append("- These flags are unconfirmed because the match is not confirmed.")
    return lines


def _source_lines(sources: list[dict]) -> list[str]:
    lines = []
    for source in sources:
        lines.append(
            f"- {source['field']}: {source['source']} | {source['reference']} | "
            f"snapshot {source['snapshot']} | dataset {source['dataset_version']}"
        )
    return lines


def missing_field_labels(ingredient: dict) -> list[str]:
    """The gaps of one ingredient, in display order, for the single "No data" line."""
    status = ingredient.get("status")
    labels: list[str] = []
    for field in ingredient.get("unknown_fields") or []:
        if status == rules.STATUS_NO_ANNEX_ENTRY_FOUND and field in ANNEX_ONLY_FIELDS:
            continue
        labels.append(GAP_LABELS.get(field, field))
    return labels


def no_annex_sentence(ingredient: dict) -> str | None:
    """One sentence replacing the annex-only gaps of a no-entry ingredient."""
    if ingredient.get("status") != rules.STATUS_NO_ANNEX_ENTRY_FOUND:
        return None
    return NO_ANNEX_SUMMARY


def _missing_lines(ingredient: dict) -> list[str]:
    lines: list[str] = []
    sentence = no_annex_sentence(ingredient)
    if sentence:
        lines.append(f"- {sentence}")
    labels = missing_field_labels(ingredient)
    if labels:
        lines.append(f"- No data in dataset for: {', '.join(labels)}.")
    return lines


def _web_items(web) -> tuple[list[dict], str | None]:
    """Accept either a full web-context payload or a bare item list."""
    if isinstance(web, dict):
        items = web.get("items") or []
        return [item for item in items if isinstance(item, dict)], web.get("message")
    if isinstance(web, list):
        return [item for item in web if isinstance(item, dict)], None
    return [], None


def _web_lines(web) -> list[str]:
    items, message = _web_items(web)
    lines = [f"#### {WEB_HEADING}", ""]
    if not items:
        lines.append(f"- {message or 'No reliable web sources found'}")
        lines.append("")
        return lines
    for item in items:
        label = SOURCE_TYPE_LABELS.get(item.get("source_type", ""), "Other")
        title = item.get("title") or item.get("site") or "Source"
        site = item.get("site") or ""
        url = item.get("url") or ""
        retrieved = item.get("retrieved_date") or config.NO_DATA
        lines.append(f"- **{label}** · {site} · [{title}]({url}) · retrieved {retrieved}")
        excerpt = str(item.get("excerpt") or "").strip()
        if excerpt:
            lines.append(f"  > {excerpt}")
    lines.append("")
    return lines


def _detail_lines(index: int, ingredient: dict, web) -> list[str]:
    status = ingredient["status"]
    match_label = MATCH_TYPE_LABELS.get(ingredient["match_type"], ingredient["match_type"])
    lines = [
        f"### {index}. {ingredient['input_name']} — {STATUS_LABELS.get(status, status)}",
        "",
        STATUS_TEXT[status],
        "",
        f"- Matched as: {ingredient['matched_name']} ({match_label})",
    ]

    if ingredient["annex"] != config.NO_DATA:
        lines.append(f"- **{FIELD_LABELS['annex']}:** {ingredient['annex']}")
    if ingredient["reference_number"] != config.NO_DATA:
        lines.append(f"- **{FIELD_LABELS['reference_number']}:** {ingredient['reference_number']}")
    if ingredient["permitted_list"] != config.NO_DATA:
        lines.append(f"- **{FIELD_LABELS['permitted_list']}:** {ingredient['permitted_list']}")
    for field in rules.LIMIT_FIELDS:
        value = ingredient["limits"].get(field)
        if value and value != config.NO_DATA:
            lines.extend(_value_block(FIELD_LABELS[field], value))
    if ingredient["skin_irritation"] != config.NO_DATA:
        lines.append(f"- **{FIELD_LABELS['skin_irritation']}:** {ingredient['skin_irritation']}")

    lines.extend(_flag_lines(ingredient["flags"]))
    if not any(key in ingredient["flags"] for key in FLAG_LABELS):
        lines.append(f"- Hazard flags: {config.NO_DATA}")

    if ingredient["candidates"]:
        names = "; ".join(candidate["name"] for candidate in ingredient["candidates"])
        lines.append(f"- Candidates to verify: {names}")

    lines.extend(_missing_lines(ingredient))

    if ingredient["sources"]:
        lines.append("- Sources:")
        lines.extend("    " + line for line in _source_lines(ingredient["sources"]))
    else:
        lines.append(f"- Sources: {config.NO_DATA}")

    lines.append("")
    if web:
        lines.extend(_web_lines(web))
    return lines


def build_markdown(result: dict, web_context: dict | None = None,
                   generated_at: str | None = None) -> str:
    """Render the always-available template report.

    ``web_context`` maps an input ingredient name to the payload the user
    explicitly loaded; it is optional and never alters the dataset facts.
    """
    summary = result["summary"]
    dataset = result["dataset"]

    lines = ["# Ingredient report", ""]
    if result.get("product_name"):
        lines.append(f"**Product:** {result['product_name']}")
    if generated_at:
        lines.append(f"**Generated:** {generated_at}")
    lines.append(
        f"**Dataset:** {dataset.get('version') or config.NO_DATA} "
        f"(snapshot {dataset.get('snapshot') or config.NO_DATA})"
    )
    lines.append("")

    lines.append(f"> **Disclaimer:** {result['disclaimer']}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("| --- | ---: |")
    lines.append(f"| Total | {summary['total']} |")
    for status in rules.STATUS_ORDER:
        key = {
            rules.STATUS_PROHIBITED: "prohibited",
            rules.STATUS_RESTRICTED: "restricted",
            rules.STATUS_PERMITTED_WITH_LIMITS: "permitted_with_limits",
            rules.STATUS_POSSIBLE_MATCH_VERIFY: "possible_match_verify",
            rules.STATUS_NO_ANNEX_ENTRY_FOUND: "no_annex_entry_found",
            rules.STATUS_UNIDENTIFIED: "unidentified",
        }[status]
        lines.append(f"| {STATUS_LABELS[status]} | {summary[key]} |")
    lines.append("")
    lines.append(_summary_sentence(summary))
    lines.append("")
    for extra in _summary_extras(summary):
        lines.append(f"- {extra}")

    lines.append("## Ingredients")
    lines.append("")
    lines.append("| No. | Ingredient | Matched as | Status | Annex / reference | Flags |")
    lines.append("| ---: | --- | --- | --- | --- | --- |")
    for index, ingredient in enumerate(result["ingredients"], start=1):
        match_label = MATCH_TYPE_LABELS.get(ingredient["match_type"], ingredient["match_type"])
        lines.append(
            f"| {index} | {_cell(ingredient['input_name'])} | "
            f"{_cell(ingredient['matched_name'])} ({match_label}) | "
            f"{STATUS_LABELS.get(ingredient['status'], ingredient['status'])} | "
            f"{_cell(_annex_cell(ingredient))} | {_cell(_flags_cell(ingredient))} |"
        )
    lines.append("")

    lines.append("## Details")
    lines.append("")
    web_context = web_context or {}
    for index, ingredient in enumerate(result["ingredients"], start=1):
        web = web_context.get(ingredient["input_name"])
        if web is None:
            web = web_context.get(ingredient["input_name"].strip().lower())
        lines.extend(_detail_lines(index, ingredient, web))

    if result.get("may_contain"):
        lines.append("## May contain")
        lines.append("")
        for name in result["may_contain"]:
            lines.append(f"- {name}")
        lines.append("")

    if result.get("warnings"):
        lines.append("## Warnings")
        lines.append("")
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(FOOTER_NOTE)

    return "\n".join(lines).rstrip() + "\n"
