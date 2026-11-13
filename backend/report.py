"""Deterministic Markdown report built from the structured result.

Only fixed sentences, dataset values and already-validated evidence findings
appear here. Dataset facts are always labelled FROM DATASET. Optional web
source review is labelled FROM WEB SOURCE REVIEW and is shown in its own
section: it never replaces a dataset value and never changes a status, a flag
or a count.
"""

from __future__ import annotations

from . import config, evidence, rules

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

# Identity fields shown from the dataset's own columns, in order.
IDENTITY_KEYS = (
    ("Chemical name", "chemical_name"),
    ("CAS number", "cas_number"),
    ("EC number", "ec_number"),
)

# Evidence labels and assessment wording (neutral, never a verdict).
DATASET_LABEL = "FROM DATASET"
WEB_LABEL = "FROM WEB SOURCE REVIEW"
IDENTITY_HEADING = f"Identity ({DATASET_LABEL})"
ENDPOINT_HEADING = f"Toxicological endpoints ({DATASET_LABEL})"
EVIDENCE_HEADING = f"External evidence review ({WEB_LABEL})"

EVIDENCE_ASSESSMENT_LABELS = {
    "Supported": "Supported by the retrieved sources",
    "Limited": "Limited evidence in the retrieved sources",
    "Conflicting": "Conflicting evidence in the retrieved sources",
    "Insufficient": "Insufficient evidence in the retrieved sources",
}

ANNEX_FIELDS = ("annex", "reference_number", "permitted_list")
ANNEX_ONLY_FIELDS = ANNEX_FIELDS + tuple(rules.LIMIT_FIELDS)

FOOTER_NOTE = (
    "Every value above comes from the dataset or reads “No data in dataset”. Nothing is inferred "
    "from concentration, packaging or web text, and no overall score is produced."
)

WEB_HEADING = "Web context (unverified, not part of the assessment)"
NO_ANNEX_SUMMARY = "No annex entry, so no annex limits apply in the dataset."
PRODUCT_LIMITATION = (
    "This check covers the listed ingredients only. It is not a conclusion about the product as "
    "a whole, and finding no prohibited entry is not an assessment of the finished product."
)


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


# ---- dataset identity + toxicological endpoints (FROM DATASET) -------------
def _identity_lines(ingredient: dict) -> list[str]:
    """Identity values and official source links, all straight from the dataset."""
    lines = [f"#### {IDENTITY_HEADING}", ""]
    match_label = MATCH_TYPE_LABELS.get(ingredient["match_type"], ingredient["match_type"])
    lines.append(f"- Input name: {ingredient['input_name']}")
    lines.append(f"- Matched dataset name: {ingredient['matched_name']}")
    lines.append(f"- Match type: {match_label}")
    for label, key in IDENTITY_KEYS:
        value = ingredient.get(key)
        if value and value != config.NO_DATA:
            lines.append(f"- {label}: {value}")
    for link in ingredient.get("dataset_links") or []:
        url = link.get("url")
        if url:
            lines.append(f"- Official source: [{link.get('label')}]({url})")
    lines.append("")
    return lines


def _endpoint_lines(ingredient: dict) -> list[str]:
    """The dataset's answer per toxicological endpoint; gaps are stated plainly."""
    lines = [f"#### {ENDPOINT_HEADING}", ""]
    for state in evidence.dataset_endpoints(ingredient):
        if state["missing"]:
            lines.append(f"- {state['label']}: {state['dataset_status']} (no dataset value)")
        else:
            lines.append(f"- {state['label']}: {state['dataset_value']}")
    lines.append("")
    return lines


# ---- external web source review (FROM WEB SOURCE REVIEW) ------------------
def has_research(payload) -> bool:
    """True when a review payload carries at least one retrieved source."""
    if not isinstance(payload, dict):
        return False
    for endpoint in payload.get("endpoints") or []:
        if endpoint.get("sources"):
            return True
    return False


def _evidence_lines(payload) -> list[str]:
    """Render a validated review payload, or nothing when none was supplied."""
    if not isinstance(payload, dict):
        return []
    lines = [f"#### {EVIDENCE_HEADING}", ""]
    if payload.get("message"):
        lines.append(f"- {payload['message']}")
        lines.append("")
        return lines

    for endpoint in payload.get("endpoints") or []:
        if not endpoint.get("missing"):
            continue
        lines.append(f"- **{endpoint.get('label') or endpoint.get('field')}**")
        lines.append(f"    - Dataset status: {endpoint.get('dataset_status')}")
        if endpoint.get("finding"):
            lines.append(f"    - External finding: {endpoint['finding']}")
        if endpoint.get("assessment"):
            label = EVIDENCE_ASSESSMENT_LABELS.get(endpoint["assessment"], endpoint["assessment"])
            lines.append(f"    - Evidence assessment: {label}")
        if endpoint.get("limitations"):
            lines.append(f"    - Limitation: {endpoint['limitations']}")
        lines.append(f"    - Evidence label: {endpoint.get('evidence_label') or WEB_LABEL}")
        for source in endpoint.get("sources") or []:
            site = source.get("site") or ""
            title = source.get("title") or site or "Source"
            url = source.get("url") or ""
            retrieved = source.get("retrieved_date") or config.NO_DATA
            lines.append(f"    - Source: [{title}]({url}) · {site} · retrieved {retrieved}")
    if payload.get("conclusion"):
        lines.append(f"- Conclusion: {payload['conclusion']}")
    lines.append("")
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


def _detail_lines(index: int, ingredient: dict, web, review) -> list[str]:
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
    lines.extend(_identity_lines(ingredient))
    lines.extend(_endpoint_lines(ingredient))
    lines.extend(_evidence_lines(review))
    if web:
        lines.extend(_web_lines(web))
    return lines


# ---- product-level sections ----------------------------------------------
def _researched_count(ingredients: list[dict], evidence_map: dict) -> int:
    total = 0
    for ingredient in ingredients:
        review = evidence_map.get(ingredient["input_name"], evidence_map.get(
            ingredient["input_name"].strip().lower()
        ))
        if has_research(review):
            total += 1
    return total


def _product_overview(result: dict, evidence_map: dict) -> list[str]:
    ingredients = result["ingredients"]
    summary = result["summary"]
    matched = sum(1 for item in ingredients if item["status"] != rules.STATUS_UNIDENTIFIED)
    researched = _researched_count(ingredients, evidence_map)
    with_gaps = sum(1 for item in ingredients if missing_field_labels(item))
    lines = ["## Product overview", ""]
    lines.append(f"- Extracted ingredient names: {summary['total']}")
    lines.append(f"- Dataset matches: {matched}")
    lines.append(f"- Unmatched ingredients: {summary['unidentified']}")
    lines.append(f"- Ingredients to verify: {summary['possible_match_verify']}")
    lines.append(f"- Ingredients with no dataset value for at least one field: {with_gaps}")
    lines.append(f"- Ingredients researched through web sources: {researched}")
    lines.append(f"- {PRODUCT_LIMITATION}")
    lines.append("")
    return lines


def _product_analysis(result: dict, evidence_map: dict, product_summary: str | None) -> list[str]:
    ingredients = result["ingredients"]
    summary = result["summary"]
    researched = _researched_count(ingredients, evidence_map)
    with_gaps = sum(1 for item in ingredients if missing_field_labels(item))
    lines = ["## Overall product analysis", ""]
    lines.append(f"- Total ingredients: {summary['total']}")
    lines.append(f"- Prohibited entries identified: {summary['prohibited']}")
    lines.append(f"- Restricted entries identified: {summary['restricted']}")
    lines.append(f"- Positive-list entries identified: {summary['permitted_with_limits']}")
    lines.append(f"- Unmatched ingredients: {summary['unidentified']}")
    lines.append(f"- Ingredients requiring manual verification: {summary['possible_match_verify']}")
    lines.append(f"- Ingredients with missing dataset information: {with_gaps}")
    lines.append(f"- Ingredients researched through web sources: {researched}")
    if summary["cmr_flagged"]:
        lines.append(f"- Ingredients with a CMR classification flag: {summary['cmr_flagged']}")
    if summary["fragrance_allergens"]:
        lines.append(
            f"- Ingredients with a fragrance allergen labelling requirement: {summary['fragrance_allergens']}"
        )
    lines.append(f"- {PRODUCT_LIMITATION}")
    if product_summary:
        lines.append("")
        lines.append(f"- AI-written reading of the data above: {product_summary}")
    lines.append("")
    return lines


def build_markdown(result: dict, web_context: dict | None = None,
                   generated_at: str | None = None, evidence: dict | None = None,
                   product_summary: str | None = None) -> str:
    """Render the always-available template report.

    ``web_context`` and ``evidence`` map an input ingredient name to the payload
    the caller supplied. Both are optional and never alter the dataset facts.
    """
    summary = result["summary"]
    dataset = result["dataset"]
    evidence_map = evidence if isinstance(evidence, dict) else {}

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

    lines.extend(_product_overview(result, evidence_map))

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
        review = evidence_map.get(ingredient["input_name"])
        if review is None:
            review = evidence_map.get(ingredient["input_name"].strip().lower())
        lines.extend(_detail_lines(index, ingredient, web, review))

    lines.extend(_product_analysis(result, evidence_map, product_summary))

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
