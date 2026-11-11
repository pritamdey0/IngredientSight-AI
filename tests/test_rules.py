"""Rule tests: status, limits, flags and counts. Also the no-score rule."""

from __future__ import annotations

from backend import config, data_layer, hazard_codes, matcher, rules

NO_DATA = config.NO_DATA


def ingredient(name: str) -> dict:
    return rules.build_ingredient(matcher.match_ingredient(name))


def keys_anywhere(value) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key))
            found |= keys_anywhere(item)
    elif isinstance(value, list):
        for item in value:
            found |= keys_anywhere(item)
    return found


def test_status_mapping_for_each_safety_class():
    assert rules.status_for_row({"safety_class": "PROHIBITED"}) == rules.STATUS_PROHIBITED
    assert rules.status_for_row({"safety_class": "RESTRICTED"}) == rules.STATUS_RESTRICTED
    assert rules.status_for_row({"safety_class": "PERMITTED"}) == rules.STATUS_PERMITTED_WITH_LIMITS
    assert (
        rules.status_for_row({"safety_class": "NOT_LISTED_IN_ANNEXES"})
        == rules.STATUS_NO_ANNEX_ENTRY_FOUND
    )


def test_unknown_safety_class_is_never_treated_as_safe():
    status = rules.status_for_row({"safety_class": "SOMETHING_NEW"})
    assert status == rules.STATUS_UNIDENTIFIED


def test_prohibited_ingredient_facts():
    item = ingredient("Benzidine")
    assert item["status"] == rules.STATUS_PROHIBITED
    assert item["annex"] == "II"
    assert item["reference_number"] == "26"
    assert item["matched_name"] == "Benzidine"


def test_prohibited_ingredient_has_cmr_and_clp_flags():
    item = ingredient("Benzidine")
    assert "cmr" in item["flags"]
    assert "clp_hazards" in item["flags"]
    codes = [hazard["code"] for hazard in item["flags"]["clp_hazards"]]
    assert "H350" in codes


def test_hazard_text_comes_from_the_static_table():
    item = ingredient("Benzidine")
    for hazard in item["flags"]["clp_hazards"]:
        assert hazard["text"] == hazard_codes.describe(hazard["code"])


def test_restricted_ingredient_facts():
    item = ingredient("Benzyl alcohol")
    assert item["status"] == rules.STATUS_RESTRICTED
    assert item["annex"] == "III"
    assert item["flags"]["fragrance_allergen"]


def test_permitted_ingredient_limits_are_verbatim():
    item = ingredient("Phenoxyethanol")
    row_ids = matcher.match_ingredient("Phenoxyethanol")["matched_row_ids"]
    row = data_layer.get_dataset().get_rows(row_ids)[0]
    assert item["status"] == rules.STATUS_PERMITTED_WITH_LIMITS
    for field in rules.LIMIT_FIELDS:
        expected = row.get(field) or NO_DATA
        assert item["limits"][field] == expected


def test_no_annex_entry_found_is_not_a_verdict():
    item = ingredient("Glycerin")
    assert item["status"] == rules.STATUS_NO_ANNEX_ENTRY_FOUND
    assert item["annex"] == NO_DATA
    assert item["reference_number"] == NO_DATA


def test_skin_irritation_is_never_derived():
    for name in ("Benzidine", "Benzyl alcohol", "Glycerin"):
        assert ingredient(name)["skin_irritation"] == NO_DATA


def test_missing_fields_are_listed():
    item = ingredient("Benzidine")
    assert "skin_irritation" in item["unknown_fields"]
    assert "max_concentration_pct" in item["unknown_fields"]


def test_sources_are_only_added_for_present_flags():
    item = ingredient("Glycerin")
    assert [source["field"] for source in item["sources"]] == ["status"]
    assert item["sources"][0]["source"]


def test_every_source_row_has_all_five_fields():
    for name in ("Benzidine", "Benzyl alcohol", "Salicylic acid", "Glycerin"):
        for source in ingredient(name)["sources"]:
            assert set(source) == {"field", "source", "reference", "snapshot", "dataset_version"}
            assert source["source"]
            assert source["snapshot"]


def test_unidentified_ingredient_has_no_facts():
    item = ingredient("Zzxqv Plorbnak 9000")
    assert item["status"] == rules.STATUS_UNIDENTIFIED
    assert item["matched_name"] == NO_DATA
    assert item["sources"] == []
    assert item["flags"] == {}
    assert all(value == NO_DATA for value in item["limits"].values())


def test_group_entry_becomes_possible_match_verify():
    item = ingredient("Lead acetate")
    assert item["status"] == rules.STATUS_POSSIBLE_MATCH_VERIFY
    assert item["match_type"] == "group_entry"
    assert item["flags"].get(rules.UNCONFIRMED) is True
    assert item["candidates"]


def test_possible_match_never_claims_a_final_status():
    item = ingredient("Glycrn")
    assert item["status"] == rules.STATUS_POSSIBLE_MATCH_VERIFY
    assert item["candidates"]


def test_no_score_or_risk_field_exists():
    forbidden = {"score", "risk", "risk_score", "risk_label", "safety_score", "grade", "rating"}
    result = rules.analyze_names(["Benzidine", "Glycerin", "Parfum", "Benzyl alcohol"])
    assert keys_anywhere(result) & forbidden == set()


def test_summary_counts_add_up():
    names = ["Benzidine", "Glycerin", "Parfum", "Benzyl alcohol", "Phenoxyethanol"]
    summary = rules.analyze_names(names)["summary"]
    assert summary["total"] == len(names)
    counted = (
        summary["prohibited"]
        + summary["restricted"]
        + summary["permitted_with_limits"]
        + summary["possible_match_verify"]
        + summary["no_annex_entry_found"]
        + summary["unidentified"]
    )
    assert counted == summary["total"]


def test_summary_counts_match_the_ingredients():
    result = rules.analyze_names(["Benzidine", "Benzyl alcohol", "Glycerin", "Parfum"])
    summary = result["summary"]
    assert summary["prohibited"] == sum(
        1 for item in result["ingredients"] if item["status"] == rules.STATUS_PROHIBITED
    )
    assert summary["cmr_flagged"] == sum(
        1 for item in result["ingredients"] if "cmr" in item["flags"]
    )
    assert summary["fragrance_allergens"] == sum(
        1 for item in result["ingredients"] if "fragrance_allergen" in item["flags"]
    )


def test_ingredients_are_sorted_most_severe_first():
    result = rules.analyze_names(["Parfum", "Benzyl alcohol", "Benzidine", "Glycerin"])
    ranks = [rules.STATUS_RANK[item["status"]] for item in result["ingredients"]]
    assert ranks == sorted(ranks)


def test_empty_list_gives_empty_counts():
    result = rules.analyze_names([])
    assert result["ingredients"] == []
    assert result["summary"]["total"] == 0


def test_multi_row_match_uses_the_stricter_row():
    item = ingredient("Titanium dioxide")
    assert item["status"] == rules.STATUS_RESTRICTED
    assert len(item["sources"]) >= 1
