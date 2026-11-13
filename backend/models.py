"""Pydantic request/response models. Validation lives here, not in routes."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from . import config

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")


def _clean_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    text = _CONTROL_CHARS_RE.sub(" ", str(value))
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:max_length] or None


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Pasted ingredient list")
    product_name: str | None = Field(default=None, description="Optional product name")
    include_summary: bool = Field(
        default=True, description="Ask for the optional AI-written summary"
    )

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("The ingredient list is empty.")
        if len(value) > config.MAX_INPUT_CHARS:
            raise ValueError(
                f"The ingredient list is longer than {config.MAX_INPUT_CHARS} characters."
            )
        return value

    @field_validator("product_name")
    @classmethod
    def _validate_product_name(cls, value: str | None) -> str | None:
        return _clean_text(value, 120)


class MatchRequest(BaseModel):
    ingredients: list[str] = Field(..., description="Ingredient names, already corrected by the user")
    product_name: str | None = None

    @field_validator("ingredients")
    @classmethod
    def _validate_ingredients(cls, value: list[str]) -> list[str]:
        cleaned = [name.strip() for name in value if name and name.strip()]
        if not cleaned:
            raise ValueError("At least one ingredient name is required.")
        if len(cleaned) > 200:
            raise ValueError("At most 200 ingredient names can be re-checked at once.")
        return cleaned

    @field_validator("product_name")
    @classmethod
    def _validate_product_name(cls, value: str | None) -> str | None:
        return _clean_text(value, 120)


class WebContextRequest(BaseModel):
    ingredient: str = Field(..., description="Ingredient name to search the web for")
    topics: list[str] = Field(
        default_factory=list,
        description="Topics from the fixed mapping: skin irritation, allergy / sensitization, "
        "use limits, hazard classification. Unknown topic strings are ignored.",
    )
    include_other: bool = Field(
        default=False, description="Also return consumer, retailer and forum sources"
    )

    @field_validator("ingredient")
    @classmethod
    def _validate_ingredient(cls, value: str) -> str:
        cleaned = _clean_text(value, config.MAX_NAME_CHARS)
        if not cleaned:
            raise ValueError("An ingredient name is required.")
        return cleaned

    @field_validator("topics")
    @classmethod
    def _validate_topics(cls, value: list[str]) -> list[str]:
        return [str(topic)[:60] for topic in value][:8]


class WebBatchItem(BaseModel):
    ingredient: str
    topics: list[str] = Field(default_factory=list)

    @field_validator("ingredient")
    @classmethod
    def _validate_ingredient(cls, value: str) -> str:
        cleaned = _clean_text(value, config.MAX_NAME_CHARS)
        if not cleaned:
            raise ValueError("An ingredient name is required.")
        return cleaned

    @field_validator("topics")
    @classmethod
    def _validate_topics(cls, value: list[str]) -> list[str]:
        return [str(topic)[:60] for topic in value][:8]


class WebBatchRequest(BaseModel):
    items: list[WebBatchItem] = Field(..., description="Up to six ingredients to search in one click")
    include_other: bool = False

    @field_validator("items")
    @classmethod
    def _validate_items(cls, value: list[WebBatchItem]) -> list[WebBatchItem]:
        if not value:
            raise ValueError("At least one ingredient is required.")
        if len(value) > config.WEB_BATCH_MAX:
            raise ValueError(
                f"At most {config.WEB_BATCH_MAX} ingredients can be searched at once."
            )
        return value


class ReportRequest(BaseModel):
    analysis: dict = Field(..., description="The finished analysis, exactly as returned by /api/analyze")
    web_context: dict[str, Any] | None = Field(
        default=None,
        description="Web panels the user loaded, keyed by input ingredient name",
    )
    evidence: dict[str, Any] | None = Field(
        default=None,
        description="Automated evidence reviews, keyed by input ingredient name",
    )
    product_summary: str | None = Field(
        default=None, description="Optional validated product-level reading"
    )


class EvidenceRequest(BaseModel):
    ingredient: dict = Field(
        ..., description="One ingredient object, exactly as returned by /api/analyze"
    )


class EvidenceBatchRequest(BaseModel):
    analysis: dict = Field(
        ..., description="The finished analysis, exactly as returned by /api/analyze"
    )
    include_product_summary: bool = Field(
        default=True, description="Also ask for one validated product-level reading"
    )

    @field_validator("analysis")
    @classmethod
    def _validate_analysis(cls, value: dict) -> dict:
        ingredients = value.get("ingredients") if isinstance(value, dict) else None
        if not isinstance(ingredients, list) or not ingredients:
            raise ValueError("analysis: expected an analysis result with ingredients.")
        return value


class SourceOut(BaseModel):
    field: str
    source: str
    reference: str
    snapshot: str
    dataset_version: str


class CandidateOut(BaseModel):
    name: str
    score: float | None = None


class DatasetLinkOut(BaseModel):
    label: str
    url: str


class IngredientOut(BaseModel):
    input_name: str
    matched_name: str
    match_type: str
    match_score: float | None = None
    status: str
    annex: str
    reference_number: str
    permitted_list: str
    limits: dict[str, str]
    skin_irritation: str
    flags: dict[str, Any]
    unknown_fields: list[str]
    sources: list[SourceOut]
    candidates: list[CandidateOut]
    # Dataset identity (FROM DATASET).
    chemical_name: str = config.NO_DATA
    cas_number: str = config.NO_DATA
    ec_number: str = config.NO_DATA
    annex_title: str = config.NO_DATA
    toxicity_class: str = config.NO_DATA
    allergy_risk: str = config.NO_DATA
    echa_hazard_classes: str = config.NO_DATA
    regulation_basis: str = config.NO_DATA
    source_url: str | None = None
    dataset_links: list[DatasetLinkOut] = Field(default_factory=list)


class SummaryOut(BaseModel):
    total: int
    prohibited: int
    restricted: int
    permitted_with_limits: int
    cmr_flagged: int
    fragrance_allergens: int
    no_annex_entry_found: int
    possible_match_verify: int
    unidentified: int


class DatasetOut(BaseModel):
    version: str | None = None
    snapshot: str | None = None


class FriendlySummaryOut(BaseModel):
    intro: str | None = None
    notes: dict[str, str]


class AnalyzeResponse(BaseModel):
    disclaimer: str
    dataset: DatasetOut
    summary: SummaryOut
    ingredients: list[IngredientOut]
    may_contain: list[str]
    warnings: list[str]
    product_name: str | None = None
    markdown_report: str
    friendly_summary: FriendlySummaryOut | None = None


class ImageAnalyzeResponse(AnalyzeResponse):
    ocr_text: str


class WebContextItemOut(BaseModel):
    title: str
    site: str
    url: str
    retrieved_date: str
    source_type: str
    excerpt: str


class WebContextResponse(BaseModel):
    enabled: bool
    items: list[WebContextItemOut]
    message: str | None = None
    notice: str | None = None
    include_other: bool | None = None
    topics: list[str] = Field(default_factory=list)


class WebBatchResponse(BaseModel):
    enabled: bool
    results: dict[str, WebContextResponse]


class ReportResponse(BaseModel):
    markdown_report: str


class EvidenceSourceOut(BaseModel):
    title: str
    site: str
    publisher: str
    url: str
    source_type: str
    retrieved_date: str
    excerpt: str


class EvidenceEndpointOut(BaseModel):
    field: str
    label: str
    dataset_status: str
    dataset_value: str | None = None
    missing: bool
    finding: str | None = None
    assessment: str | None = None
    limitations: str | None = None
    evidence_label: str | None = None
    sources: list[EvidenceSourceOut] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    enabled: bool
    researched: bool
    ingredient: str
    message: str | None = None
    conclusion: str | None = None
    endpoints: list[EvidenceEndpointOut] = Field(default_factory=list)


class EvidenceBatchResponse(BaseModel):
    enabled: bool
    results: dict[str, EvidenceResponse]
    product_summary: str | None = None


class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    dataset_rows: int
    dataset_version: str | None = None
    source_snapshot: str | None = None
    ocr_available: bool
    llm_enabled: bool
    web_context_enabled: bool
    evidence_enabled: bool
