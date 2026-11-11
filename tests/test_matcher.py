"""Matcher tests against the real reference dataset."""

from __future__ import annotations

from backend import data_layer, matcher


def match(name: str) -> dict:
    return matcher.match_ingredient(name)


def matched_names(result: dict) -> list[str]:
    rows = data_layer.get_dataset().get_rows(result["matched_row_ids"])
    return [row["ingredient_name"] for row in rows]


def test_exact_name_match():
    result = match("Benzidine")
    assert result["match_type"] == "exact_name"
    assert result["match_score"] == 100.0
    assert matched_names(result) == ["Benzidine"]


def test_match_is_case_and_space_insensitive():
    result = match("  benzyl   ALCOHOL ")
    assert result["match_type"] == "exact_name"
    assert set(matched_names(result)) == {"BENZYL ALCOHOL"}


def test_reviewed_alias_resolves_to_the_dataset_name():
    result = match("Glycerine")
    assert result["match_type"] == "exact_name"
    assert matched_names(result) == ["GLYCERIN"]


def test_alias_for_a_multi_word_name():
    result = match("Vitamin E")
    assert result["match_type"] == "exact_name"
    assert matched_names(result) == ["TOCOPHEROL"]


def test_synonym_match():
    result = match("CI 77891")
    assert result["match_type"] == "synonym"
    assert set(matched_names(result)) == {"TITANIUM DIOXIDE/CI 77891"}


def test_cas_number_match():
    result = match("50-00-0")
    assert result["match_type"] == "cas"
    assert matched_names(result) == ["Formaldehyde"]


def test_cas_number_inside_a_longer_string():
    result = match("Formalin solution (50-00-0)")
    assert result["match_type"] == "cas"
    assert matched_names(result) == ["Formaldehyde"]


def test_high_confidence_fuzzy_typo():
    result = match("Glycern")
    assert result["match_type"] == "fuzzy_high"
    assert result["match_score"] >= matcher.FUZZY_HIGH_MIN
    assert matched_names(result) == ["GLYCERIN"]


def test_possible_fuzzy_match_lists_candidates():
    result = match("Glycrn")
    assert result["match_type"] == "fuzzy_possible"
    assert matcher.FUZZY_POSSIBLE_MIN <= result["match_score"] < matcher.FUZZY_HIGH_MIN
    assert result["candidates"]


def test_unrelated_name_is_not_matched():
    result = match("Zzxqv Plorbnak 9000")
    assert result["match_type"] == "none"
    assert result["matched_row_ids"] == []
    assert result["candidates"] == []


def test_a_single_word_does_not_match_a_long_name():
    """token_set_ratio would otherwise report a subset as a 100 score."""
    result = match("Parfum")
    assert result["match_type"] == "none"


def test_group_entry_is_never_confirmed():
    result = match("Lead acetate")
    assert result["match_type"] == "group_entry"
    assert result["candidates"]
    assert any("Lead and its compounds" == name for name in matched_names(result))


def test_group_entry_safeguard_keeps_the_candidate_visible():
    result = match("Methylparaben")
    assert result["match_type"] == "group_entry"
    assert result["candidates"][0]["name"]


def test_exact_name_beats_a_synonym_of_another_row():
    """A giant synonym list must not pull in an unrelated row."""
    dataset = data_layer.get_dataset()
    assert all(
        dataset.get_row(row_id)["ingredient_name"] == "GLYCERIN"
        for row_id in dataset.ids_for_key("glycerin")
    )


def test_empty_name_is_not_matched():
    result = match("   ")
    assert result["match_type"] == "none"
    assert result["input_name"] == ""


def test_none_name_is_not_matched():
    result = matcher.match_ingredient(None)
    assert result["match_type"] == "none"


def test_control_characters_are_stripped_before_matching():
    result = match("Benzidine\u0000\u0007")
    assert "\u0000" not in result["input_name"]
    assert result["input_name"] == "Benzidine"
    assert result["match_type"] == "exact_name"


def test_control_characters_inside_a_name_are_replaced_by_spaces():
    result = match("Benzi\u0000dine")
    assert result["input_name"] == "Benzi dine"
    assert result["match_type"] in {"fuzzy_high", "fuzzy_possible"}


def test_long_name_is_capped_at_120_characters():
    result = match("X" * 500)
    assert len(result["input_name"]) == 120


def test_no_match_carries_no_score():
    result = match("NotARealIngredient")
    assert result["match_score"] is None


def test_every_choice_key_points_at_real_rows():
    dataset = data_layer.get_dataset()
    missing = [key for key in dataset.fuzz_keys() if not dataset.ids_for_key(key)]
    assert missing == []


def test_match_ingredients_keeps_input_order():
    names = ["Benzidine", "NotARealIngredient", "Glycerin"]
    results = matcher.match_ingredients(names)
    assert [result["input_name"] for result in results] == names
