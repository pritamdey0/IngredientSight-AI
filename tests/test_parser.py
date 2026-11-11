"""Parser tests: splitting, cleaning and warnings. No dataset needed."""

from __future__ import annotations

from backend import parser


def test_brackets_keep_their_commas():
    result = parser.parse_ingredient_list("Aqua, Parfum (Fragrance, Linalool), Glycerin")
    assert result["ingredients"] == ["Aqua", "Parfum (Fragrance, Linalool)", "Glycerin"]
    assert result["warnings"] == []


def test_prefix_is_removed():
    result = parser.parse_ingredient_list("Ingredients: Aqua, Glycerin")
    assert result["ingredients"] == ["Aqua", "Glycerin"]


def test_prefix_is_removed_case_insensitively():
    result = parser.parse_ingredient_list("COMPOSITION - Aqua, Glycerin")
    assert result["ingredients"] == ["Aqua", "Glycerin"]


def test_may_contain_section_is_separate():
    result = parser.parse_ingredient_list(
        "Aqua, CI 77891, May Contain: CI 77491, CI 77492"
    )
    assert result["ingredients"] == ["Aqua", "CI 77891"]
    assert result["may_contain"] == ["CI 77491", "CI 77492"]


def test_plus_minus_marker_starts_the_may_contain_section():
    result = parser.parse_ingredient_list("Aqua, CI 77491 +/- CI 77492, CI 77499")
    assert result["ingredients"] == ["Aqua", "CI 77491"]
    assert result["may_contain"] == ["CI 77492", "CI 77499"]


def test_semicolons_split_like_commas():
    result = parser.parse_ingredient_list("Aqua; Glycerin; Parfum")
    assert result["ingredients"] == ["Aqua", "Glycerin", "Parfum"]


def test_duplicates_are_dropped_case_insensitively():
    result = parser.parse_ingredient_list("Aqua, AQUA, aqua, Glycerin")
    assert result["ingredients"] == ["Aqua", "Glycerin"]


def test_control_characters_are_removed():
    result = parser.parse_ingredient_list("Aq\u0000ua, Gly\u0007cerin\u200b")
    assert result["ingredients"] == ["Aq ua", "Gly cerin"]


def test_ocr_stray_characters_are_removed():
    result = parser.parse_ingredient_list("Aqua | Glycerin _ Parfum ~ Linalool")
    assert result["ingredients"] == ["Aqua", "Glycerin", "Parfum", "Linalool"]


def test_newlines_do_not_create_items():
    result = parser.parse_ingredient_list("Aqua,\nGlycerin,\nParfum")
    assert result["ingredients"] == ["Aqua", "Glycerin", "Parfum"]


def test_long_name_is_truncated_with_a_warning():
    long_name = "Sodium " + "verylongpart" * 20
    result = parser.parse_ingredient_list(f"{long_name}, Aqua")
    assert len(result["ingredients"][0]) == 120
    assert any("120" in warning for warning in result["warnings"])


def test_empty_text_returns_a_warning():
    result = parser.parse_ingredient_list("   ")
    assert result["ingredients"] == []
    assert result["may_contain"] == []
    assert result["warnings"] == ["No ingredient text was provided."]


def test_none_returns_a_warning():
    result = parser.parse_ingredient_list(None)
    assert result["ingredients"] == []
    assert result["warnings"] == ["No ingredient text was provided."]


def test_single_ingredient_warns_about_a_partial_list():
    result = parser.parse_ingredient_list("Aqua")
    assert result["ingredients"] == ["Aqua"]
    assert any("Only one ingredient" in warning for warning in result["warnings"])


def test_separator_only_text_warns():
    result = parser.parse_ingredient_list(",,, ;;; ")
    assert result["ingredients"] == []
    assert any("No ingredients could be read" in warning for warning in result["warnings"])


def test_unclosed_bracket_does_not_lose_the_rest():
    result = parser.parse_ingredient_list("Parfum (Fragrance, Aqua, Glycerin")
    assert result["ingredients"] == ["Parfum (Fragrance, Aqua, Glycerin"]
