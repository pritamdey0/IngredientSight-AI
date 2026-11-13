"""Report tests: the template report is always available and always honest."""

from __future__ import annotations

import re

from backend import config, evidence, matcher, report, rules


def build(names: list[str], may_contain: list[str] | None = None,
          warnings: list[str] | None = None, product_name: str | None = None) -> dict:
    analysis = rules.analyze_names(names)
    result: dict = {
        "disclaimer": config.DISCLAIMER,
        "dataset": {"version": "IngredientSight-EU-v3", "snapshot": "test-snapshot"},
        "summary": analysis["summary"],
        "ingredients": analysis["ingredients"],
        "may_contain": may_contain or [],
        "warnings": warnings or [],
    }
    if product_name:
        result["product_name"] = product_name
    return result


def web_payload() -> dict:
    return {
        "items": [
            {
                "title": "SCCS opinion on the ingredient",
                "site": "ec.europa.eu",
                "url": "https://ec.europa.eu/health/sccs",
                "retrieved_date": "2026-11-11",
                "source_type": "official_scientific",
                "excerpt": "The committee could not conclude on the safety of the ingredient.",
            }
        ],
        "message": None,
        "notice": "Unverified web context. This is not part of the assessment.",
    }


def evidence_payload(finding: str = "The retrieved sources describe a dermal endpoint.") -> dict:
    return {
        "enabled": True,
        "researched": True,
        "ingredient": "Benzidine",
        "message": None,
        "conclusion": "The dataset leaves the skin endpoints open and the sources add a partial view.",
        "endpoints": [
            {
                "field": "skin_irritation",
                "label": "Skin irritation",
                "dataset_status": "NOT_ASSESSED",
                "dataset_value": None,
                "missing": True,
                "finding": finding,
                "assessment": "Supported",
                "limitations": None,
                "evidence_label": evidence.EVIDENCE_LABEL,
                "sources": [
                    {
                        "title": "SCCS opinion on the ingredient",
                        "site": "ec.europa.eu",
                        "publisher": "ec.europa.eu",
                        "url": "https://ec.europa.eu/health/sccs",
                        "source_type": "official_scientific",
                        "retrieved_date": "2026-11-11",
                        "excerpt": "The committee reviewed dermal exposure.",
                    }
                ],
            }
        ],
    }


def test_report_starts_with_the_title_then_the_disclaimer():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert markdown.startswith("# Ingredient report\n")
    assert "> **Disclaimer:**" in markdown
    assert markdown.index("> **Disclaimer:**") < markdown.index("## Summary")
    assert "not a safety assessment" in markdown


def test_report_header_carries_product_dataset_and_generation_time():
    markdown = report.build_markdown(
        build(["Glycerin"], product_name="Test cream"), generated_at="2026-11-11 15:40 UTC"
    )
    assert "**Product:** Test cream" in markdown
    assert "**Generated:** 2026-11-11 15:40 UTC" in markdown
    assert "**Dataset:** IngredientSight-EU-v3 (snapshot test-snapshot)" in markdown


def test_generated_at_is_optional_so_the_template_stays_deterministic():
    first = report.build_markdown(build(["Benzidine", "Glycerin"]))
    second = report.build_markdown(build(["Benzidine", "Glycerin"]))
    assert first == second
    assert "**Generated:**" not in first


def test_summary_table_counts_equal_the_structured_summary():
    result = build(["Benzidine", "Glycerin", "Benzyl alcohol", "Parfum"])
    markdown = report.build_markdown(result)
    assert "## Summary" in markdown
    assert "| Status | Count |" in markdown
    keys = {
        "Prohibited": "prohibited",
        "Restricted": "restricted",
        "Positive list": "permitted_with_limits",
        "Verify match": "possible_match_verify",
        "No annex entry": "no_annex_entry_found",
        "Not identified": "unidentified",
    }
    for label, key in keys.items():
        assert f"| {label} | {result['summary'][key]} |" in markdown
    assert f"| Total | {result['summary']['total']} |" in markdown


def test_summary_reports_cmr_and_fragrance_lines():
    markdown = report.build_markdown(build(["Benzidine", "Benzyl alcohol"]))
    assert "carries a CMR classification flag" in markdown
    assert "carries a fragrance allergen labelling requirement" in markdown


def test_overview_table_lists_every_ingredient_in_severity_order():
    markdown = report.build_markdown(build(["Parfum", "Benzidine", "Glycerin"]))
    assert "| No. | Ingredient | Matched as | Status | Annex / reference | Flags |" in markdown
    rows = re.findall(r"^\| \d+ \| (.+?) \|", markdown, flags=re.MULTILINE)
    assert rows == ["Benzidine", "Glycerin", "Parfum"]


def test_details_has_one_subsection_per_ingredient():
    markdown = report.build_markdown(build(["Parfum", "Benzidine", "Glycerin"]))
    assert "## Details" in markdown
    headers = re.findall(r"^### \d+\. (.+?) — ", markdown, flags=re.MULTILINE)
    assert headers == ["Benzidine", "Glycerin", "Parfum"]


def test_details_are_bullets_of_present_fields_only():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert "- **EU annex:** II" in markdown
    assert "- **Annex reference number:**" in markdown
    # Empty limit fields are not repeated as ten separate rows.
    assert "Maximum concentration (%): No data in dataset" not in markdown


def test_report_states_no_annex_entry_without_a_verdict():
    markdown = report.build_markdown(build(["Glycerin"]))
    assert "No EU annex entry found" in markdown
    assert "This is not a safety assessment." in markdown
    assert report.NO_ANNEX_SUMMARY in markdown


def test_one_no_data_line_per_ingredient():
    result = build(["Benzidine", "Glycerin"])
    markdown = report.build_markdown(result)
    lines = [line for line in markdown.splitlines() if "No data in dataset for:" in line]
    assert len(lines) == len(result["ingredients"])
    assert config.NO_DATA in markdown


def test_no_annex_fields_are_not_listed_one_by_one():
    markdown = report.build_markdown(build(["Glycerin"]))
    gap_line = next(line for line in markdown.splitlines() if "No data in dataset for:" in line)
    for field in ("EU annex", "annex reference number", "positive list", "maximum concentration"):
        assert field not in gap_line
    assert "skin irritation" in gap_line


def test_report_never_uses_verdict_words():
    markdown = report.build_markdown(
        build(["Benzidine", "Glycerin", "Parfum", "Benzyl alcohol", "Phenoxyethanol"])
    )
    # The disclaimer and the footer state the absence of a score; the rest of
    # the report must not contain verdict or scoring language at all.
    body = markdown.replace(report.FOOTER_NOTE, "").replace(config.DISCLAIMER, "").lower()
    for phrase in ("safe", "harmless", "low risk", "risk score"):
        assert not re.search(r"\b" + phrase + r"\b", body)
    for phrase in ("score", "/100", "grade"):
        assert phrase not in body


def test_report_includes_candidates_for_an_unconfirmed_match():
    markdown = report.build_markdown(build(["Lead acetate"]))
    assert "Candidates to verify:" in markdown
    assert "unconfirmed" in markdown


def test_report_lists_sources():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert "- Sources:" in markdown
    assert "snapshot test-snapshot" in markdown


def test_report_renders_may_contain():
    markdown = report.build_markdown(build(["Glycerin"], may_contain=["CI 77491", "CI 77492"]))
    assert "## May contain" in markdown
    assert "- CI 77491" in markdown


def test_report_renders_warnings_only_when_present():
    with_warnings = report.build_markdown(build(["Glycerin"], warnings=["Check the list."]))
    without = report.build_markdown(build(["Glycerin"]))
    assert "## Warnings" in with_warnings
    assert "## Warnings" not in without


def test_report_ends_with_the_footer_note():
    markdown = report.build_markdown(build(["Glycerin"]))
    assert report.FOOTER_NOTE in markdown
    assert markdown.index(report.FOOTER_NOTE) > markdown.index("## Details")
    assert markdown.endswith("\n")
    assert not markdown.endswith("\n\n")


def test_web_block_is_absent_until_it_is_supplied():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert report.WEB_HEADING not in markdown


def test_web_block_is_verbatim_and_only_for_supplied_ingredients():
    result = build(["Benzidine", "Glycerin"])
    markdown = report.build_markdown(result, web_context={"Benzidine": web_payload()})
    assert markdown.count(f"#### {report.WEB_HEADING}") == 1
    block = markdown.split(f"#### {report.WEB_HEADING}")[1]
    assert "**Official** · ec.europa.eu" in block
    assert "The committee could not conclude on the safety of the ingredient." in block
    assert "https://ec.europa.eu/health/sccs" in block
    assert "retrieved 2026-11-11" in block


def test_web_block_does_not_change_the_dataset_facts():
    result = build(["Benzidine"])
    without = report.build_markdown(result)
    with_web = report.build_markdown(result, web_context={"Benzidine": web_payload()})
    prefix = with_web.split(f"#### {report.WEB_HEADING}")[0]
    # Everything before the web block is byte-identical to the report without it.
    assert without.startswith(prefix)
    assert "| Prohibited | 1 |" in with_web
    assert "not a safety assessment" in with_web


def test_web_block_reports_an_empty_result():
    result = build(["Glycerin"])
    markdown = report.build_markdown(
        result, web_context={"Glycerin": {"items": [], "message": "No reliable web sources found"}}
    )
    assert "No reliable web sources found" in markdown


def test_every_status_has_report_text_and_a_label():
    for status in rules.STATUS_ORDER:
        assert status in report.STATUS_TEXT
        assert status in report.STATUS_LABELS


def test_every_match_type_has_a_label():
    for match_type in ("exact_name", "synonym", "cas", "fuzzy_high", "fuzzy_possible",
                       "group_entry", "none"):
        assert match_type in report.MATCH_TYPE_LABELS


def test_empty_analysis_still_renders():
    markdown = report.build_markdown(build([]))
    assert "| Total | 0 |" in markdown
    assert "0 ingredients were checked" in markdown


def test_unidentified_ingredient_is_explained():
    markdown = report.build_markdown(build(["Parfum"]))
    assert "Not identified in the dataset" in markdown


def test_cmr_flag_is_reported_with_its_categories():
    item = rules.build_ingredient(matcher.match_ingredient("Benzidine"))
    markdown = report.build_markdown(build(["Benzidine"]))
    assert item["flags"]["cmr"]["categories"] in markdown


# ---- dataset identity and endpoints (FROM DATASET) -----------------------
def test_identity_and_endpoint_blocks_are_labelled_from_dataset():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert report.DATASET_LABEL == "FROM DATASET"
    assert report.IDENTITY_HEADING in markdown
    assert report.ENDPOINT_HEADING in markdown
    assert f"#### {report.IDENTITY_HEADING}" in markdown
    assert f"#### {report.ENDPOINT_HEADING}" in markdown


def test_dataset_endpoint_block_states_the_missing_and_present_endpoints():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert "- Skin irritation: NOT_ASSESSED (no dataset value)" in markdown
    assert "- Eye irritation: NOT_IN_DATASET (no dataset value)" in markdown


# ---- external evidence review (FROM WEB SOURCE REVIEW) -------------------
def test_evidence_block_is_absent_until_it_is_supplied():
    markdown = report.build_markdown(build(["Benzidine"]))
    assert report.EVIDENCE_HEADING not in markdown


def test_evidence_block_labels_web_findings_and_keeps_the_source_url():
    markdown = report.build_markdown(build(["Benzidine"]), evidence={"Benzidine": evidence_payload()})
    assert report.EVIDENCE_HEADING == "External evidence review (FROM WEB SOURCE REVIEW)"
    assert f"#### {report.EVIDENCE_HEADING}" in markdown
    assert "The retrieved sources describe a dermal endpoint." in markdown
    assert "Supported by the retrieved sources" in markdown
    assert f"Evidence label: {report.WEB_LABEL}" in markdown
    assert "https://ec.europa.eu/health/sccs" in markdown
    assert "retrieved 2026-11-11" in markdown


def test_evidence_block_shows_only_the_missing_endpoints():
    markdown = report.build_markdown(build(["Benzidine"]), evidence={"Benzidine": evidence_payload()})
    block = markdown.split(f"#### {report.EVIDENCE_HEADING}")[1].split("## Overall product analysis")[0]
    assert "Skin irritation" in block
    assert "Eye irritation" not in block


def test_evidence_block_reports_the_no_evidence_sentence_verbatim():
    payload = evidence_payload()
    payload["researched"] = False
    payload["endpoints"][0]["finding"] = config.NO_WEB_EVIDENCE
    payload["endpoints"][0]["assessment"] = "Insufficient"
    payload["endpoints"][0]["sources"] = []
    markdown = report.build_markdown(build(["Benzidine"]), evidence={"Benzidine": payload})
    assert config.NO_WEB_EVIDENCE in markdown
    assert "Insufficient evidence in the retrieved sources" in markdown


def test_evidence_block_does_not_change_the_dataset_facts():
    result = build(["Benzidine", "Glycerin"])
    without = report.build_markdown(result)
    with_evidence = report.build_markdown(result, evidence={"Benzidine": evidence_payload()})
    row = next(line for line in without.splitlines() if line.startswith("| 1 | Benzidine"))
    assert row in with_evidence
    assert with_evidence.count("| Prohibited | 1 |") == without.count("| Prohibited | 1 |")
    assert "> **Disclaimer:**" in with_evidence


def test_evidence_block_reports_a_missing_configuration_message():
    payload = {
        "enabled": True,
        "researched": False,
        "ingredient": "Benzidine",
        "message": "Automated evidence review is not configured.",
        "conclusion": None,
        "endpoints": [],
    }
    markdown = report.build_markdown(build(["Benzidine"]), evidence={"Benzidine": payload})
    assert "Automated evidence review is not configured." in markdown


def test_evidence_block_never_uses_verdict_words():
    markdown = report.build_markdown(build(["Benzidine"]), evidence={"Benzidine": evidence_payload()})
    body = markdown.replace(report.FOOTER_NOTE, "").replace(config.DISCLAIMER, "").lower()
    for phrase in ("safe", "harmless", "low risk", "risk score"):
        assert not re.search(r"\b" + phrase + r"\b", body)


# ---- product-level sections ----------------------------------------------
def test_product_overview_counts_matches_and_researched_ingredients():
    result = build(["Benzidine", "Glycerin"])
    markdown = report.build_markdown(result, evidence={"Benzidine": evidence_payload()})
    assert "## Product overview" in markdown
    assert "- Extracted ingredient names: 2" in markdown
    assert "- Dataset matches: 2" in markdown
    assert "- Ingredients researched through web sources: 1" in markdown


def test_product_analysis_lists_the_researched_count():
    markdown = report.build_markdown(build(["Benzidine", "Glycerin"]), evidence={"Benzidine": evidence_payload()})
    assert "## Overall product analysis" in markdown
    assert "- Ingredients researched through web sources: 1" in markdown
    assert report.PRODUCT_LIMITATION in markdown


def test_product_summary_is_shown_when_supplied():
    without = report.build_markdown(build(["Benzidine"]))
    with_summary = report.build_markdown(
        build(["Benzidine"]), product_summary="Two ingredient names were checked."
    )
    assert "AI-written reading of the data above" not in without
    assert "AI-written reading of the data above: Two ingredient names were checked." in with_summary
