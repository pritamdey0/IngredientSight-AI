"""FastAPI application: routes, CORS, rate limiting.

The analysis path is fully deterministic. The LLM summary and the web context
are optional add-ons that never change a status, flag, limit or count.
"""

from __future__ import annotations

import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config, data_layer, llm_summary, models, ocr, parser, report, rules, web_context

RATE_WINDOW_SECONDS = 60
_buckets: dict[tuple[str, str], deque[float]] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # A missing dataset must not stop the server: /api/health reports it and
    # the analysis routes answer 503 with the build command.
    try:
        dataset = data_layer.load()
        print(f"Dataset loaded: {dataset.info['rows']} rows.")
    except RuntimeError:
        print("Dataset could not be loaded. Run: python scripts/build_reference.py")
    yield


app = FastAPI(
    title="IngredientSight-AI API",
    description="Source-backed cosmetic ingredient checker (EU annexes + ECHA CLP).",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.LOCAL_ORIGINS) + list(config.EXTRA_ALLOWED_ORIGINS),
    allow_origin_regex=config.VERCEL_ORIGIN_REGEX if config.VERCEL_ORIGIN_REGEX else None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---- helpers -------------------------------------------------------------
def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate(request: Request, bucket: str, limit: int) -> None:
    key = (bucket, _client_ip(request))
    now = time.time()
    window = _buckets.setdefault(key, deque())
    while window and now - window[0] > RATE_WINDOW_SECONDS:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a minute and try again.",
        )
    window.append(now)


def _require_dataset() -> data_layer.Dataset:
    try:
        return data_layer.load()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _analysis_result(ingredients: list[str], may_contain: list[str], warnings: list[str],
                     product_name: str | None) -> dict:
    dataset = _require_dataset()
    analysis = rules.analyze_names(ingredients)
    result: dict = {
        "disclaimer": config.DISCLAIMER,
        "dataset": {
            "version": dataset.info.get("dataset_version"),
            "snapshot": dataset.info.get("source_snapshot"),
        },
        "summary": analysis["summary"],
        "ingredients": analysis["ingredients"],
        "may_contain": may_contain,
        "warnings": warnings,
    }
    if product_name:
        result["product_name"] = product_name
    return result


def _respond(result: dict, include_summary: bool) -> dict:
    friendly = llm_summary.build_summary(result) if include_summary else None
    return {
        **result,
        "markdown_report": report.build_markdown(result, generated_at=_timestamp()),
        "friendly_summary": friendly,
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _looks_like_image(raw: bytes) -> bool:
    return (
        raw[:3] == b"\xff\xd8\xff"
        or raw[:8] == b"\x89PNG\r\n\x1a\n"
        or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")
        or raw[:6] in (b"GIF87a", b"GIF89a")
        or raw[:2] == b"BM"
    )


# ---- routes --------------------------------------------------------------
@app.get("/api/health", response_model=models.HealthResponse)
def health() -> dict:
    loaded = data_layer.is_loaded()
    info = data_layer.get_dataset().info if loaded else {}
    return {
        "status": "ok" if loaded else "degraded",
        "dataset_loaded": loaded,
        "dataset_rows": int(info.get("rows") or 0),
        "dataset_version": info.get("dataset_version"),
        "source_snapshot": info.get("source_snapshot"),
        "ocr_available": ocr.is_available(),
        "llm_enabled": config.llm_enabled(),
        "web_context_enabled": config.web_context_enabled(),
    }


@app.post("/api/analyze", response_model=models.AnalyzeResponse)
def analyze(payload: models.AnalyzeRequest, request: Request) -> dict:
    _check_rate(request, "analyze", config.RATE_LIMIT_ANALYZE)
    parsed = parser.parse_ingredient_list(payload.text)
    result = _analysis_result(
        parsed["ingredients"], parsed["may_contain"], parsed["warnings"], payload.product_name
    )
    return _respond(result, payload.include_summary)


@app.post("/api/analyze-image", response_model=models.ImageAnalyzeResponse)
def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    product_name: str | None = Form(default=None),
) -> dict:
    _check_rate(request, "analyze", config.RATE_LIMIT_ANALYZE)
    raw = file.file.read(config.MAX_IMAGE_BYTES + 1)
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(raw) > config.MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"The image is larger than {config.MAX_IMAGE_BYTES // (1024 * 1024)} MB.",
        )
    if not _looks_like_image(raw):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file. Please upload a PNG, JPEG, WebP, GIF or BMP image.",
        )

    try:
        text = ocr.run_ocr(raw)
    except ocr.OcrUnavailable:
        raise HTTPException(
            status_code=503,
            detail="OCR is not available on this server. Please install rapidocr-onnxruntime.",
        ) from None

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be read from this image. Please paste the ingredient list as text.",
        )

    parsed = parser.parse_ingredient_list(text)
    result = _analysis_result(
        parsed["ingredients"], parsed["may_contain"], parsed["warnings"],
        (product_name or "").strip() or None,
    )
    return {**_respond(result, include_summary=False), "ocr_text": text}


@app.post("/api/match", response_model=models.AnalyzeResponse)
def match(payload: models.MatchRequest, request: Request) -> dict:
    _check_rate(request, "analyze", config.RATE_LIMIT_ANALYZE)
    result = _analysis_result(payload.ingredients, [], [], payload.product_name)
    return _respond(result, include_summary=False)


@app.post("/api/web-context", response_model=models.WebContextResponse)
def web_context_endpoint(payload: models.WebContextRequest, request: Request) -> dict:
    _check_rate(request, "web", config.RATE_LIMIT_WEB)
    return web_context.search(
        payload.ingredient, include_other=payload.include_other, topics=payload.topics
    )


@app.post("/api/web-context/batch", response_model=models.WebBatchResponse)
def web_context_batch(payload: models.WebBatchRequest, request: Request) -> dict:
    # One click is one action: the batch counts once against the web bucket.
    _check_rate(request, "web", config.RATE_LIMIT_WEB)
    return web_context.search_many(
        [item.model_dump() for item in payload.items], include_other=payload.include_other
    )


@app.post("/api/report", response_model=models.ReportResponse)
def report_endpoint(payload: models.ReportRequest) -> dict:
    """Re-render the template report with the web panels the user loaded."""
    analysis = payload.analysis
    if not isinstance(analysis.get("ingredients"), list) or "summary" not in analysis:
        raise HTTPException(status_code=422, detail="analysis: not an analysis result.")
    web = payload.web_context or {}
    if not isinstance(web, dict):
        raise HTTPException(status_code=422, detail="web_context: expected an object.")
    return {
        "markdown_report": report.build_markdown(
            analysis, web_context=web, generated_at=_timestamp()
        )
    }


# ---- error handling ------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if errors:
        location = ".".join(str(part) for part in errors[0].get("loc", ())[1:])
        message = str(errors[0].get("msg", "Invalid input."))
        detail = f"{location}: {message}" if location else message
    else:
        detail = "Invalid input."
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Never send a stack trace to the client.
    print(f"Unhandled error: {type(exc).__name__}")
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error."})


@app.get("/")
def root() -> dict:
    return {"service": "IngredientSight-AI", "health": "/api/health", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=config.PORT)
