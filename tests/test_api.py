"""API tests through FastAPI's TestClient. No external call is made."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend import app as app_module
from backend import config, ocr, web_context


@pytest.fixture(scope="module")
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    """The summary step is optional; keep the tests offline and deterministic."""
    monkeypatch.setattr(config, "LLM_PROVIDER", "")


def headers(ip: str) -> dict[str, str]:
    return {"x-forwarded-for": ip}


def test_root_points_at_the_health_endpoint(client):
    payload = client.get("/").json()
    assert payload["service"] == "IngredientSight-AI"
    assert payload["health"] == "/api/health"


def test_health_reports_the_dataset(client):
    response = client.get("/api/health", headers=headers("198.51.100.1"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["dataset_loaded"] is True
    assert payload["dataset_rows"] > 4000
    assert payload["dataset_version"]
    for key in ("ocr_available", "llm_enabled", "web_context_enabled"):
        assert isinstance(payload[key], bool)


def test_analyze_happy_path(client):
    response = client.post(
        "/api/analyze",
        json={
            "text": "Ingredients: Benzidine, Glycerine, Parfum, Benzyl alcohol",
            "product_name": "Test cream",
            "include_summary": False,
        },
        headers=headers("198.51.100.2"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"] == config.DISCLAIMER
    assert payload["product_name"] == "Test cream"
    assert payload["summary"]["total"] == len(payload["ingredients"]) == 4
    assert payload["summary"]["prohibited"] == 1
    assert payload["summary"]["unidentified"] == 1
    assert payload["friendly_summary"] is None
    assert payload["markdown_report"].startswith("# Ingredient report")
    assert "> **Disclaimer:**" in payload["markdown_report"]
    assert payload["dataset"]["version"]


def test_analyze_returns_no_score_field(client):
    response = client.post(
        "/api/analyze",
        json={"text": "Benzidine, Glycerin", "include_summary": False},
        headers=headers("198.51.100.3"),
    )
    payload = response.json()
    for forbidden in ("score", "risk", "risk_score", "risk_label", "safety_score"):
        assert forbidden not in payload
    assert "score" not in payload["summary"]


def test_analyze_splits_the_may_contain_section(client):
    response = client.post(
        "/api/analyze",
        json={"text": "Glycerin, CI 77891, May Contain: CI 77491", "include_summary": False},
        headers=headers("198.51.100.4"),
    )
    payload = response.json()
    assert payload["may_contain"] == ["CI 77491"]
    assert "## May contain" in payload["markdown_report"]


def test_analyze_reports_parser_warnings(client):
    response = client.post(
        "/api/analyze",
        json={"text": "Glycerin", "include_summary": False},
        headers=headers("198.51.100.5"),
    )
    assert response.json()["warnings"]


def test_empty_text_is_rejected(client):
    response = client.post(
        "/api/analyze",
        json={"text": "   "},
        headers=headers("198.51.100.6"),
    )
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


def test_text_longer_than_the_limit_is_rejected(client):
    response = client.post(
        "/api/analyze",
        json={"text": "A" * (config.MAX_INPUT_CHARS + 1)},
        headers=headers("198.51.100.7"),
    )
    assert response.status_code == 422
    assert "longer than" in response.json()["detail"]


def test_missing_text_field_is_rejected_with_a_readable_message(client):
    response = client.post("/api/analyze", json={}, headers=headers("198.51.100.8"))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail.startswith("text")
    assert "Exception" not in detail


def test_product_name_is_cleaned_and_capped(client):
    response = client.post(
        "/api/analyze",
        json={"text": "Glycerin, Parfum", "product_name": "Bad\u0000name " + "x" * 200},
        headers=headers("198.51.100.9"),
    )
    name = response.json()["product_name"]
    assert "\u0000" not in name
    assert len(name) <= 120


def test_match_endpoint_accepts_corrected_names(client):
    response = client.post(
        "/api/match",
        json={"ingredients": ["Benzidine", "Glycerine"]},
        headers=headers("198.51.100.10"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 2
    assert payload["markdown_report"]


def test_match_rejects_an_empty_list(client):
    response = client.post(
        "/api/match",
        json={"ingredients": ["  "]},
        headers=headers("198.51.100.11"),
    )
    assert response.status_code == 422


def test_match_rejects_more_than_200_names(client):
    response = client.post(
        "/api/match",
        json={"ingredients": ["Glycerin"] * 201},
        headers=headers("198.51.100.12"),
    )
    assert response.status_code == 422
    assert "200" in response.json()["detail"]


def test_match_accepts_exactly_200_names(client):
    response = client.post(
        "/api/match",
        json={"ingredients": ["Glycerin"] * 200},
        headers=headers("198.51.100.13"),
    )
    assert response.status_code == 200
    assert response.json()["summary"]["total"] == 200


def test_image_upload_rejects_an_empty_file(client):
    response = client.post(
        "/api/analyze-image",
        files={"file": ("label.png", b"", "image/png")},
        headers=headers("198.51.100.14"),
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_image_upload_rejects_a_non_image(client):
    response = client.post(
        "/api/analyze-image",
        files={"file": ("label.txt", b"just text", "text/plain")},
        headers=headers("198.51.100.15"),
    )
    assert response.status_code == 400
    assert "PNG" in response.json()["detail"]


def test_image_upload_returns_the_ocr_text(client, monkeypatch):
    monkeypatch.setattr(ocr, "run_ocr", lambda raw: "Glycerin, Benzidine")
    response = client.post(
        "/api/analyze-image",
        files={"file": ("label.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")},
        data={"product_name": "Label test"},
        headers=headers("198.51.100.16"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ocr_text"] == "Glycerin, Benzidine"
    assert payload["product_name"] == "Label test"
    assert payload["summary"]["prohibited"] == 1


def test_image_upload_without_ocr_answers_422(client, monkeypatch):
    def unavailable(_raw):
        raise ocr.OcrUnavailable("not installed")

    monkeypatch.setattr(ocr, "run_ocr", unavailable)
    response = client.post(
        "/api/analyze-image",
        files={"file": ("label.jpg", b"\xff\xd8\xff" + b"0" * 64, "image/jpeg")},
        headers=headers("198.51.100.17"),
    )
    assert response.status_code == 422
    assert "paste the ingredient list as text" in response.json()["detail"]


def test_image_upload_without_text_answers_422(client, monkeypatch):
    monkeypatch.setattr(ocr, "run_ocr", lambda raw: "   ")
    response = client.post(
        "/api/analyze-image",
        files={"file": ("label.jpg", b"\xff\xd8\xff" + b"0" * 64, "image/jpeg")},
        headers=headers("198.51.100.18"),
    )
    assert response.status_code == 422
    assert "No text" in response.json()["detail"]


def test_web_context_endpoint_passes_the_request_through(client, monkeypatch):
    captured = {}

    def fake_search(ingredient: str, include_other: bool = False, topics=None) -> dict:
        captured["ingredient"] = ingredient
        captured["include_other"] = include_other
        captured["topics"] = topics
        return {
            "enabled": True,
            "items": [],
            "message": web_context.NO_RELIABLE_SOURCES,
            "notice": web_context.PANEL_NOTE,
            "include_other": include_other,
            "topics": ["skin irritation"],
        }

    monkeypatch.setattr(web_context, "search", fake_search)
    response = client.post(
        "/api/web-context",
        json={"ingredient": "  Benzidine ", "include_other": True, "topics": ["skin irritation"]},
        headers=headers("198.51.100.19"),
    )
    assert response.status_code == 200
    assert captured == {
        "ingredient": "Benzidine",
        "include_other": True,
        "topics": ["skin irritation"],
    }
    assert response.json()["notice"] == web_context.PANEL_NOTE


def test_web_context_batch_endpoint(client, monkeypatch):
    captured = {}

    def fake_many(items, include_other=False):
        captured["items"] = items
        captured["include_other"] = include_other
        return {
            "enabled": True,
            "results": {
                item["ingredient"]: {
                    "enabled": True,
                    "items": [],
                    "message": web_context.NO_RELIABLE_SOURCES,
                    "notice": web_context.PANEL_NOTE,
                    "include_other": include_other,
                    "topics": item["topics"],
                }
                for item in items
            },
        }

    monkeypatch.setattr(web_context, "search_many", fake_many)
    response = client.post(
        "/api/web-context/batch",
        json={
            "items": [
                {"ingredient": "Benzidine", "topics": ["skin irritation"]},
                {"ingredient": "Glycerin"},
            ]
        },
        headers=headers("198.51.100.31"),
    )
    assert response.status_code == 200
    assert set(response.json()["results"]) == {"Benzidine", "Glycerin"}
    assert len(captured["items"]) == 2
    assert captured["include_other"] is False


def test_web_context_batch_caps_at_six(client):
    response = client.post(
        "/api/web-context/batch",
        json={"items": [{"ingredient": f"Ingredient {index}"} for index in range(7)]},
        headers=headers("198.51.100.32"),
    )
    assert response.status_code == 422
    assert "At most 6" in response.json()["detail"]


def test_web_context_batch_rejects_an_empty_list(client):
    response = client.post(
        "/api/web-context/batch", json={"items": []}, headers=headers("198.51.100.33")
    )
    assert response.status_code == 422


def test_web_context_batch_shares_the_web_rate_limit(client, monkeypatch):
    monkeypatch.setattr(
        web_context,
        "search_many",
        lambda items, include_other=False: {"enabled": True, "results": {}},
    )
    limit = config.RATE_LIMIT_WEB
    ip = "198.51.100.34"
    for _ in range(limit):
        ok = client.post(
            "/api/web-context/batch",
            json={"items": [{"ingredient": "Benzidine"}]},
            headers=headers(ip),
        )
        assert ok.status_code == 200
    blocked = client.post(
        "/api/web-context/batch",
        json={"items": [{"ingredient": "Benzidine"}]},
        headers=headers(ip),
    )
    assert blocked.status_code == 429


def test_report_endpoint_renders_the_web_block(client):
    analysis = client.post(
        "/api/analyze",
        json={"text": "Benzidine, Glycerin", "include_summary": False},
        headers=headers("198.51.100.35"),
    ).json()
    web = {
        "Benzidine": {
            "enabled": True,
            "items": [
                {
                    "title": "SCCS opinion",
                    "site": "ec.europa.eu",
                    "url": "https://ec.europa.eu/x",
                    "retrieved_date": "2026-11-11",
                    "source_type": "official_scientific",
                    "excerpt": "Verbatim sentence from the source.",
                }
            ],
            "message": None,
            "notice": web_context.PANEL_NOTE,
            "include_other": False,
            "topics": ["skin irritation"],
        }
    }
    response = client.post(
        "/api/report",
        json={"analysis": analysis, "web_context": web},
        headers=headers("198.51.100.36"),
    )
    assert response.status_code == 200
    markdown = response.json()["markdown_report"]
    assert markdown.startswith("# Ingredient report")
    assert "Web context (unverified, not part of the assessment)" in markdown
    assert "Verbatim sentence from the source." in markdown
    assert "| Prohibited | 1 |" in markdown


def test_report_endpoint_rejects_a_non_analysis_body(client):
    response = client.post(
        "/api/report", json={"analysis": {"foo": 1}}, headers=headers("198.51.100.37")
    )
    assert response.status_code == 422


def test_web_context_does_not_change_the_analysis(client, monkeypatch):
    before = client.post(
        "/api/analyze",
        json={"text": "Benzidine, Glycerin", "include_summary": False},
        headers=headers("198.51.100.38"),
    ).json()
    monkeypatch.setattr(web_context, "_request_search", lambda query: [])
    client.post(
        "/api/web-context",
        json={"ingredient": "Benzidine"},
        headers=headers("198.51.100.38"),
    )
    after = client.post(
        "/api/analyze",
        json={"text": "Benzidine, Glycerin", "include_summary": False},
        headers=headers("198.51.100.38"),
    ).json()
    for key in ("summary", "ingredients", "may_contain", "warnings"):
        assert before[key] == after[key]


def test_web_context_requires_a_name(client):
    response = client.post(
        "/api/web-context", json={"ingredient": "  "}, headers=headers("198.51.100.20")
    )
    assert response.status_code == 422


def test_cors_allows_the_dev_frontend(client):
    response = client.options(
        "/api/analyze",
        headers={
            "origin": "http://localhost:5173",
            "access-control-request-method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_allows_vercel_previews(client):
    origin = "https://ingredient-sight-git-main-user.vercel.app"
    response = client.options(
        "/api/analyze",
        headers={"origin": origin, "access-control-request-method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_does_not_allow_other_origins(client):
    response = client.options(
        "/api/analyze",
        headers={"origin": "https://example.com", "access-control-request-method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit_answers_429(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ANALYZE", 1)
    ip = headers("203.0.113.250")
    first = client.post("/api/match", json={"ingredients": ["Glycerin"]}, headers=ip)
    second = client.post("/api/match", json={"ingredients": ["Glycerin"]}, headers=ip)
    assert first.status_code == 200
    assert second.status_code == 429
    assert "Too many requests" in second.json()["detail"]


def test_rate_limits_are_per_client(client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ANALYZE", 1)
    first = client.post(
        "/api/match", json={"ingredients": ["Glycerin"]}, headers=headers("203.0.113.251")
    )
    other = client.post(
        "/api/match", json={"ingredients": ["Glycerin"]}, headers=headers("203.0.113.252")
    )
    assert first.status_code == 200
    assert other.status_code == 200


def test_unknown_route_uses_the_standard_error_shape(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_analyze_can_include_the_optional_summary(client, monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(config, "LLM_MODEL", "test-model")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    from backend import llm_summary

    monkeypatch.setattr(llm_summary, "generate", lambda system, user: '{"intro": "2 ingredients were checked.", "notes": {}}')
    response = client.post(
        "/api/analyze",
        json={"text": "Glycerin, Benzidine", "include_summary": True},
        headers=headers("198.51.100.21"),
    )
    assert response.status_code == 200
    assert response.json()["friendly_summary"] == {"intro": "2 ingredients were checked.", "notes": {}}
