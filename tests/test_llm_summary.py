"""LLM summary tests: the validator drops anything the data does not support.

No network call is made here; the provider call itself is monkeypatched.
"""

from __future__ import annotations

import json

import pytest

from backend import config, llm_summary, rules


@pytest.fixture()
def result() -> dict:
    """A small finished result, exactly as the route would pass it in."""
    analysis = rules.analyze_names(["Benzidine", "Glycerin", "Benzyl alcohol"])
    return {
        "disclaimer": config.DISCLAIMER,
        "dataset": {"version": "IngredientSight-EU-v3", "snapshot": "test-snapshot"},
        "summary": analysis["summary"],
        "ingredients": analysis["ingredients"],
        "may_contain": [],
        "warnings": [],
    }


def test_extract_text_reads_the_gemini_shape():
    data = {"candidates": [{"content": {"parts": [{"text": "hello"}, {"text": " world"}]}}]}
    assert llm_summary._extract_text(data) == "hello world"


def test_extract_text_returns_none_for_an_empty_answer():
    assert llm_summary._extract_text({"candidates": []}) is None
    assert llm_summary._extract_text({}) is None


def test_disabled_without_configuration(monkeypatch, result):
    monkeypatch.setattr(config, "LLM_PROVIDER", "")
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    assert config.llm_enabled() is False
    assert llm_summary.build_summary(result) is None


def test_valid_intro_is_kept(result):
    intro = "3 ingredients were checked against the EU annex data."
    summary = llm_summary.validate(result, {"intro": intro, "notes": {}})
    assert summary == {"intro": intro, "notes": {}}


def test_answer_wrapped_in_an_extra_object_is_unwrapped(result):
    # Some models return {"report": {"intro": ..., "notes": {...}}} anyway.
    intro = "3 ingredients were checked against the EU annex data."
    parsed = {"report": {"intro": intro, "notes": {"Benzidine": "Annex II entry."}}}
    summary = llm_summary.validate(result, parsed)
    assert summary == {"intro": intro, "notes": {"Benzidine": "Annex II entry."}}


def test_wrapped_answer_is_still_validated(result):
    parsed = {"report": {"intro": "Everything here is safe.", "notes": {}}}
    assert llm_summary.validate(result, parsed) is None


def test_gemini_payload_turns_reasoning_tokens_off():
    quiet = llm_summary._gemini_payload("system", "user", True)
    plain = llm_summary._gemini_payload("system", "user", False)

    assert quiet["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}
    assert "thinkingConfig" not in plain["generationConfig"]
    assert quiet["generationConfig"]["responseMimeType"] == "application/json"
    assert quiet["system_instruction"]["parts"][0]["text"] == "system"


def test_banned_phrase_drops_the_intro(result):
    text = "3 ingredients were checked and everything is safe."
    assert llm_summary.validate(result, {"intro": text}) is None


def test_advice_wording_drops_the_intro(result):
    text = "3 ingredients were checked, so avoid this product."
    assert llm_summary.validate(result, {"intro": text}) is None


def test_invented_number_drops_the_intro(result):
    text = "3 ingredients were checked and 12 of them are prohibited."
    assert llm_summary.validate(result, {"intro": text}) is None


def test_invented_capitalised_name_drops_the_intro(result):
    text = "3 ingredients were checked, including Formaldehyde."
    assert llm_summary.validate(result, {"intro": text}) is None


def test_invented_severity_word_drops_the_intro(result):
    text = "3 ingredients were checked and one is dangerous."
    assert llm_summary.validate(result, {"intro": text}) is None


def test_too_long_intro_is_dropped(result):
    text = " ".join(["checked"] * (llm_summary.INTRO_MAX_WORDS + 1))
    assert llm_summary.validate(result, {"intro": text}) is None


def test_note_for_a_prohibited_ingredient_is_kept(result):
    note = "Listed in Annex II; the dataset records a CMR classification."
    summary = llm_summary.validate(result, {"notes": {"Benzidine": note}})
    assert summary["notes"] == {"Benzidine": note}


def test_note_for_an_ineligible_status_is_dropped(result):
    note = "No annex entry found in the dataset."
    summary = llm_summary.validate(result, {"notes": {"Glycerin": note}})
    assert summary is None or "Glycerin" not in summary["notes"]


def test_note_for_an_unknown_name_is_dropped(result):
    summary = llm_summary.validate(result, {"notes": {"Aspirin": "Not in the dataset."}})
    assert summary is None or "Aspirin" not in summary["notes"]


def test_note_mentioning_another_ingredient_is_dropped(result):
    note = "Benzyl alcohol is on a positive list with conditions."
    summary = llm_summary.validate(result, {"notes": {"Benzidine": note}})
    assert summary is None or "Benzidine" not in summary["notes"]


def test_note_with_an_invented_number_is_dropped(result):
    summary = llm_summary.validate(result, {"notes": {"Benzidine": "Annex II, entry 999."}})
    assert summary is None or "Benzidine" not in summary["notes"]


def test_non_dictionary_answer_is_rejected(result):
    assert llm_summary.validate(result, None) is None
    assert llm_summary.validate(result, "a string") is None
    assert llm_summary.validate(result, [1, 2, 3]) is None


def test_run_on_wording_is_not_accepted_as_a_note(result):
    note = "Safe to use daily."
    assert llm_summary.validate(result, {"notes": {"Benzided": note}}) is None


def test_retry_stops_after_two_attempts(monkeypatch, result):
    calls = []

    def fake_generate(_system: str, _user: str) -> str:
        calls.append(1)
        return "not json at all"

    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_summary, "generate", fake_generate)

    assert llm_summary.build_summary(result) is None
    assert len(calls) == 2


def test_second_attempt_can_succeed(monkeypatch, result):
    answers = ["not json", json.dumps({"intro": "3 ingredients were checked.", "notes": {}})]
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_summary, "generate", lambda _system, _user: answers.pop(0))

    summary = llm_summary.build_summary(result)
    assert summary == {"intro": "3 ingredients were checked.", "notes": {}}


def test_build_summary_never_raises_on_a_failing_provider(monkeypatch, result):
    def boom(_system: str, _user: str) -> str:
        raise RuntimeError("provider down")

    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_summary, "generate", boom)

    assert llm_summary.build_summary(result) is None


def test_user_payload_carries_only_the_structured_result(monkeypatch, result):
    seen = {}

    def fake_generate(system: str, user: str) -> str:
        seen["system"] = system
        seen["user"] = user
        return json.dumps({"intro": "3 ingredients were checked.", "notes": {}})

    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm_summary, "generate", fake_generate)
    llm_summary.build_summary(result)

    assert seen["system"] == llm_summary.SYSTEM_PROMPT
    assert json.loads(seen["user"]) == result
