"""Evidence-review tests: dataset gaps are supplemented, never overwritten.

The Tavily search and the LLM rewrite are always monkeypatched, so no network
call is ever made.
"""

from __future__ import annotations

import copy
import json

import pytest

from backend import config, evidence, llm_summary, matcher, rules, web_context


@pytest.fixture(autouse=True)
def clean_cache():
    evidence.clear_cache()
    yield
    evidence.clear_cache()


@pytest.fixture()
def enabled(monkeypatch):
    """Both a web key and an LLM key, so evidence_enabled() is true."""
    monkeypatch.setattr(config, "TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")


def ingredient(name: str = "Benzidine") -> dict:
    return rules.build_ingredient(matcher.match_ingredient(name))


def missing_fields(item: dict) -> list[str]:
    return [state["field"] for state in evidence.dataset_endpoints(item) if state["missing"]]


def web_items() -> list[dict]:
    return [
        {
            "title": "SCCS opinion on the ingredient",
            "site": "ec.europa.eu",
            "url": "https://ec.europa.eu/health/sccs",
            "source_type": "official_scientific",
            "retrieved_date": "2026-11-11",
            "excerpt": "The committee reviewed dermal exposure.",
        }
    ]


def patch_search(monkeypatch, items: list[dict]) -> None:
    monkeypatch.setattr(
        web_context,
        "search",
        lambda name, include_other=False, topics=None: {"items": items},
    )


def findings_json(item: dict, finding: str = "The sources describe a dermal endpoint.") -> str:
    return json.dumps(
        {
            "fields": {
                field: {"finding": finding, "assessment": "Supported", "limitations": None}
                for field in missing_fields(item)
            },
            "conclusion": "The dataset leaves these endpoints open and the sources add a partial view.",
        }
    )


# ---- dataset endpoint state ----------------------------------------------
def test_dataset_endpoints_mark_the_unassessed_endpoints_missing():
    by_field = {state["field"]: state for state in evidence.dataset_endpoints(ingredient())}
    assert by_field["skin_irritation"]["missing"] is True
    assert by_field["eye_irritation"]["missing"] is True
    # Benzidine carries a CMR/CLP flag, so toxicity is answered by the dataset.
    assert by_field["toxicity"]["missing"] is False


def test_needs_review_is_true_when_an_endpoint_has_no_dataset_value():
    assert evidence.needs_review(ingredient()) is True


# ---- graceful degradation ------------------------------------------------
def test_research_reports_a_dataset_only_answer_without_configuration(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "")
    monkeypatch.setattr(config, "LLM_PROVIDER", "")
    payload = evidence.research_one(ingredient())
    assert payload["enabled"] is True
    assert payload["researched"] is False
    assert payload["message"]
    # The dataset's own endpoint states are still reported.
    assert payload["endpoints"]


def test_no_sources_gives_the_exact_no_evidence_sentence(enabled, monkeypatch):
    item = ingredient()
    patch_search(monkeypatch, [])
    payload = evidence.research_one(item)
    assert payload["researched"] is False
    for endpoint in payload["endpoints"]:
        if endpoint["missing"]:
            assert endpoint["finding"] == config.NO_WEB_EVIDENCE
            assert endpoint["assessment"] == "Insufficient"
            assert endpoint["sources"] == []


def test_a_provider_failure_keeps_the_sources_without_a_finding(enabled, monkeypatch):
    item = ingredient()
    patch_search(monkeypatch, web_items())
    monkeypatch.setattr(llm_summary, "generate", lambda system, user, max_tokens=None: None)
    payload = evidence.research_one(item)
    reviewed = [e for e in payload["endpoints"] if e["missing"]]
    assert reviewed
    for endpoint in reviewed:
        assert endpoint["finding"] is None
        assert endpoint["assessment"] == "Insufficient"
        assert endpoint["sources"][0]["url"] == "https://ec.europa.eu/health/sccs"


# ---- validated findings --------------------------------------------------
def test_research_adds_sourced_findings_with_an_evidence_label(enabled, monkeypatch):
    item = ingredient()
    patch_search(monkeypatch, web_items())
    monkeypatch.setattr(
        llm_summary, "generate", lambda system, user, max_tokens=None: findings_json(item)
    )
    payload = evidence.research_one(item)
    assert payload["researched"] is True
    reviewed = [e for e in payload["endpoints"] if e["missing"]]
    assert reviewed
    for endpoint in reviewed:
        assert endpoint["finding"]
        assert endpoint["evidence_label"] == evidence.EVIDENCE_LABEL
        assert endpoint["sources"]
    assert payload["conclusion"]


def test_a_finding_with_a_verdict_word_is_dropped(enabled, monkeypatch):
    item = ingredient()
    patch_search(monkeypatch, web_items())
    monkeypatch.setattr(
        llm_summary,
        "generate",
        lambda system, user, max_tokens=None: findings_json(item, finding="This ingredient is safe for skin."),
    )
    payload = evidence.research_one(item)
    for endpoint in payload["endpoints"]:
        if endpoint["missing"]:
            assert endpoint.get("finding") != "This ingredient is safe for skin."


def test_unknown_endpoint_keys_are_ignored(enabled, monkeypatch):
    item = ingredient()
    patch_search(monkeypatch, web_items())
    payload_json = json.dumps(
        {"fields": {"not_an_endpoint": {"finding": "Something.", "assessment": "Supported"}}}
    )
    monkeypatch.setattr(llm_summary, "generate", lambda system, user, max_tokens=None: payload_json)
    payload = evidence.research_one(item)
    assert all(endpoint["field"] in evidence.ENDPOINTS for endpoint in payload["endpoints"])
    assert not any(endpoint.get("finding") == "Something." for endpoint in payload["endpoints"])


def test_sources_keep_their_title_site_and_url():
    out = evidence._public_sources(
        [
            {"title": "A", "site": "ec.europa.eu", "url": "https://a", "retrieved_date": "2026-01-01"},
            {"title": "No URL"},
            {"title": "C", "site": "echa.europa.eu", "url": "https://c", "retrieved_date": "2026-01-02"},
        ]
    )
    assert [source["url"] for source in out] == ["https://a", "https://c"]
    assert out[0]["publisher"] == "ec.europa.eu"
    assert out[0]["retrieved_date"] == "2026-01-01"


# ---- cache and immutability ----------------------------------------------
def test_the_review_is_cached_per_ingredient(enabled, monkeypatch):
    item = ingredient()
    calls: list[str] = []

    def counting_search(name, include_other=False, topics=None):
        calls.append(name)
        return {"items": web_items()}

    monkeypatch.setattr(web_context, "search", counting_search)
    monkeypatch.setattr(
        llm_summary, "generate", lambda system, user, max_tokens=None: findings_json(item)
    )
    first = evidence.research_one(item)
    second = evidence.research_one(item)
    assert calls == ["Benzidine"]
    assert second == first


def test_the_dataset_record_is_never_changed(enabled, monkeypatch):
    item = ingredient()
    snapshot = copy.deepcopy(item)
    patch_search(monkeypatch, [])
    evidence.research_one(item)
    assert item == snapshot


# ---- product-level reading -----------------------------------------------
def test_product_summary_is_off_without_the_llm(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "")
    assert evidence.build_product_summary({"summary": {"total": 2}, "ingredients": []}, {}) is None


def test_product_summary_keeps_a_grounded_reading(enabled, monkeypatch):
    analysis = {
        "summary": {"total": 2, "prohibited": 1},
        "ingredients": [{"input_name": "Benzidine", "status": "PROHIBITED"}],
    }
    monkeypatch.setattr(
        llm_summary,
        "generate",
        lambda system, user, max_tokens=None: json.dumps({"summary": "2 ingredients were listed."}),
    )
    assert evidence.build_product_summary(analysis, {}) == "2 ingredients were listed."


def test_product_summary_rejects_a_verdict(enabled, monkeypatch):
    analysis = {"summary": {"total": 2}, "ingredients": []}
    monkeypatch.setattr(
        llm_summary,
        "generate",
        lambda system, user, max_tokens=None: json.dumps({"summary": "The product is safe."}),
    )
    assert evidence.build_product_summary(analysis, {}) is None


def test_product_summary_rejects_an_invented_number(enabled, monkeypatch):
    analysis = {"summary": {"total": 2}, "ingredients": []}
    monkeypatch.setattr(
        llm_summary,
        "generate",
        lambda system, user, max_tokens=None: json.dumps({"summary": "99 ingredients were checked."}),
    )
    assert evidence.build_product_summary(analysis, {}) is None
