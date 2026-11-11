"""Web-context tests. The Tavily call itself is always monkeypatched."""

from __future__ import annotations

import pytest

from backend import config, web_context

LONG_TEXT = " ".join(f"word{index}" for index in range(1, 41))


@pytest.fixture(autouse=True)
def clean_cache():
    web_context.clear_cache()
    yield
    web_context.clear_cache()


@pytest.fixture()
def enabled(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "test-key")


def results() -> list[dict]:
    return [
        {
            "title": "SCCS opinion on the ingredient",
            "url": "https://ec.europa.eu/health/scientific_committees/sccs_en",
            "content": LONG_TEXT,
            "score": 0.9,
        },
        {
            "title": "Shop page",
            "url": "https://www.sephora.com/product/123",
            "content": "A shop page about the ingredient.",
        },
        {
            "title": "Pin",
            "url": "https://pinterest.com/pin/1",
            "content": "Blocked domain.",
        },
        {
            "title": "Empty",
            "url": "https://example.org/none",
            "content": "   ",
        },
    ]


def test_disabled_when_no_key(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "")
    payload = web_context.search("Benzidine")
    assert payload == {"enabled": False, "items": [], "message": web_context.NOT_CONFIGURED}


def test_official_sources_only_by_default(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    payload = web_context.search("Benzidine")
    assert payload["enabled"] is True
    assert [item["site"] for item in payload["items"]] == ["ec.europa.eu"]
    assert payload["items"][0]["source_type"] == "official_scientific"
    assert payload["notice"] == web_context.PANEL_NOTE
    assert payload["message"] is None
    assert payload["include_other"] is False


def test_blocked_and_empty_results_never_reach_the_panel(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    payload = web_context.search("Benzidine", include_other=True)
    sites = [item["site"] for item in payload["items"]]
    assert "pinterest.com" not in sites
    assert "example.org" not in sites


def test_include_other_adds_non_official_sources(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    payload = web_context.search("Benzidine", include_other=True)
    assert [item["site"] for item in payload["items"]] == ["ec.europa.eu", "sephora.com"]
    assert payload["items"][1]["source_type"] == "retailer_brand"


def test_excerpt_is_verbatim_and_at_most_25_words(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    item = web_context.search("Benzidine")["items"][0]
    assert item["excerpt"] == " ".join(f"word{index}" for index in range(1, 26))
    assert len(item["excerpt"].split()) == config.WEB_EXCERPT_MAX_WORDS


def test_no_official_result_reports_no_reliable_sources(enabled, monkeypatch):
    only_shop = [results()[1]]
    monkeypatch.setattr(web_context, "_request_search", lambda query: only_shop)
    payload = web_context.search("Benzidine")
    assert payload["items"] == []
    assert payload["message"] == web_context.NO_RELIABLE_SOURCES


def test_network_failure_is_reported_not_raised(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: None)
    payload = web_context.search("Benzidine")
    assert payload["items"] == []
    assert payload["message"] == web_context.NETWORK_ERROR


def test_results_are_cached(enabled, monkeypatch):
    calls = []

    def fake_search(query: str) -> list[dict]:
        calls.append(query)
        return results()

    monkeypatch.setattr(web_context, "_request_search", fake_search)
    first = web_context.search("Benzidine")
    second = web_context.search("Benzidine")
    assert calls == ["benzidine cosmetic ingredient SCCS CIR"]
    assert first == second


def test_topics_reach_the_query_in_a_fixed_order(enabled, monkeypatch):
    calls = []
    monkeypatch.setattr(
        web_context, "_request_search", lambda query: calls.append(query) or results()
    )
    web_context.search("Benzidine", topics=["use limits", "skin irritation"])
    assert calls == [
        "benzidine cosmetic ingredient skin irritation use limits SCCS CIR"
    ]


def test_unknown_topics_are_ignored(enabled, monkeypatch):
    calls = []
    monkeypatch.setattr(
        web_context, "_request_search", lambda query: calls.append(query) or results()
    )
    web_context.search("Benzidine", topics=["drop table", "<script>", "USE LIMITS"])
    assert calls == ["benzidine cosmetic ingredient use limits SCCS CIR"]
    assert web_context.search("Benzidine", topics=["nonsense"])["topics"] == []


def test_topics_are_part_of_the_cache_key(enabled, monkeypatch):
    calls = []
    monkeypatch.setattr(
        web_context, "_request_search", lambda query: calls.append(query) or results()
    )
    web_context.search("Benzidine")
    web_context.search("Benzidine", topics=["skin irritation"])
    web_context.search("Benzidine", topics=["skin irritation"])
    assert len(calls) == 2


def test_batch_returns_results_keyed_by_input_name(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    payload = web_context.search_many(
        [
            {"ingredient": "Benzidine", "topics": ["skin irritation"]},
            {"ingredient": "Glycerin"},
        ],
        delay_seconds=0,
    )
    assert payload["enabled"] is True
    assert set(payload["results"]) == {"Benzidine", "Glycerin"}
    assert payload["results"]["Benzidine"]["topics"] == ["skin irritation"]
    assert payload["results"]["Glycerin"]["items"][0]["site"] == "ec.europa.eu"


def test_batch_reuses_the_cache(enabled, monkeypatch):
    calls = []
    monkeypatch.setattr(
        web_context, "_request_search", lambda query: calls.append(query) or results()
    )
    web_context.search("Benzidine")
    web_context.search_many([{"ingredient": "Benzidine"}], delay_seconds=0)
    assert len(calls) == 1


def test_batch_refuses_more_than_six_ingredients():
    with pytest.raises(web_context.TooManyIngredients):
        web_context.search_many(
            [{"ingredient": f"Ingredient {index}"} for index in range(7)], delay_seconds=0
        )


def test_batch_skips_an_empty_name(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    payload = web_context.search_many([{"ingredient": "   "}], delay_seconds=0)
    assert payload["results"] == {}


def test_include_other_is_cached_separately(enabled, monkeypatch):
    calls = []

    def fake_search(query: str) -> list[dict]:
        calls.append(query)
        return results()

    monkeypatch.setattr(web_context, "_request_search", fake_search)
    web_context.search("Benzidine")
    web_context.search("Benzidine", include_other=True)
    assert len(calls) == 2


def test_cache_can_be_cleared(enabled, monkeypatch):
    calls = []

    def fake_search(query: str) -> list[dict]:
        calls.append(query)
        return results()

    monkeypatch.setattr(web_context, "_request_search", fake_search)
    web_context.search("Benzidine")
    web_context.clear_cache()
    web_context.search("Benzidine")
    assert len(calls) == 2


def test_empty_name_returns_a_message(enabled):
    assert web_context.search("   ")["message"] == "No ingredient name provided."


def test_retrieved_date_is_iso_today(enabled, monkeypatch):
    monkeypatch.setattr(web_context, "_request_search", lambda query: results())
    item = web_context.search("Benzidine")["items"][0]
    assert len(item["retrieved_date"]) == 10
    assert item["retrieved_date"].count("-") == 2


def test_site_name_drops_the_www_prefix():
    assert web_context._site_of("https://www.ewg.org/skindeep") == "ewg.org"
    assert web_context._site_of("https://ec.europa.eu/x") == "ec.europa.eu"


def test_source_type_mapping():
    assert config.source_type_for("ec.europa.eu") == "official_scientific"
    assert config.source_type_for("pubchem.ncbi.nlm.nih.gov") == "official_scientific"
    assert config.source_type_for("www.amazon.com") == "retailer_brand"
    assert config.source_type_for("ewg.org") == "review"
    assert config.source_type_for("reddit.com") == "blog_forum"
    assert config.source_type_for("example.org") == "other"


def test_blocked_hosts_cover_subdomains():
    assert config.is_blocked_host("pinterest.com") is True
    assert config.is_blocked_host("kr.pinterest.com") is True
    assert config.is_blocked_host("europa.eu") is False


def test_items_are_limited_to_the_configured_count(enabled, monkeypatch):
    many = [
        {
            "title": f"Opinion {index}",
            "url": f"https://ec.europa.eu/doc/{index}",
            "content": "Official text about the ingredient.",
        }
        for index in range(8)
    ]
    monkeypatch.setattr(web_context, "_request_search", lambda query: many)
    payload = web_context.search("Benzidine")
    assert len(payload["items"]) == config.WEB_RESULTS_RETURNED
