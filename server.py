"""
IngredientSight AI - FastAPI Web Server

Exposes backend REST API endpoints for the React Frontend / Dashboard to invoke
the 5-Agent LangGraph Pipeline (OCR -> Ingredient -> Research -> Safety -> Report).

CHANGES / FIXES:
- Health check now validates that required API keys are configured.
- Static files are mounted for /uploads and /reports so saved reports are
  reachable by the dashboard via direct URLs.
- Typed product-name submissions no longer silently fall back to the same
  sample ingredients image (which produced identical "demo" output for every
  query).  Instead a clear 400 error is returned asking the user to upload a
  real product-label image.
- Uploaded files are validated as real images before being handed to OCR.
- Pipeline exceptions are wrapped with actionable diagnostics so the dashboard
  can distinguish between "missing key", "bad image", and "LLM failure".
"""
import os
import sys
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")


class HealthResponse(BaseModel):
    status: str
    service: str
    gemini_configured: bool
    tavily_configured: bool
    upload_dir: str
    reports_dir: str
    port: int
    host: str


app = FastAPI(
    title="IngredientSight AI API",
    description="Backend service powering PRMPT Archive & IngredientSight AI Frontend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # A wildcard origin cannot be combined with allow_credentials=True
    # (browsers reject it). Use explicit dev/prod origins and no credentials.
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
# NOTE: the previously bundled sample image (ingredients_en.5.full.jpg) is no
# longer present in the repo, so the product-name-only "demo" fallback has
# been removed — /api/analyze now requires a real uploaded label photo.

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")


def _find_free_port(start: int = 8000, max_tries: int = 20) -> int:
    """Return the first free TCP port in the range [start, start + max_tries)."""
    import socket

    for port in range(start, start + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
            return port
        except OSError:
            continue
    raise RuntimeError(f"No free TCP port available in range {start}-{start + max_tries - 1}")


DEFAULT_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
_env_port = os.environ.get("SERVER_PORT") or os.environ.get("PORT")
if _env_port:
    try:
        SERVER_PORT = int(_env_port)
    except (TypeError, ValueError):
        SERVER_PORT = _find_free_port(8000)
else:
    SERVER_PORT = _find_free_port(8000)


pipeline_app = None
pipeline_error: Optional[str] = None

print("=" * 60)
print("IngredientSight AI API server starting up")
print("=" * 60)

if not GEMINI_KEY:
    pipeline_error = (
        "Neither GOOGLE_API_KEY nor GEMINI_API_KEY is configured. "
        "Copy .env.example to .env and add a valid Gemini API key."
    )
    print("WARNING:", pipeline_error)
else:
    print("GOOGLE_API_KEY / GEMINI_API_KEY: found")

if not TAVILY_KEY:
    print("WARNING: TAVILY_API_KEY is not set — research agent will use LLM-only knowledge.")
else:
    print("TAVILY_API_KEY: found")

try:
    from langgraphagentic.graph import build_graph

    print("Compiling LangGraph StateGraph pipeline...")
    pipeline_app = build_graph()
    print("Graph compiled successfully.")
except Exception as exc:
    pipeline_error = f"Failed to compile LangGraph pipeline: {exc}"
    print("ERROR:", pipeline_error)


def _require_pipeline():
    if pipeline_app is None:
        detail = pipeline_error or "LangGraph pipeline was not compiled — check server startup logs."
        raise HTTPException(status_code=503, detail=detail)


def _validate_image_bytes(raw: bytes, filename: str) -> None:
    """Raise HTTPException if the bytes are clearly not a PNG/JPEG image."""
    ext = os.path.splitext(filename)[1].lower()
    magic = raw[:12]
    is_jpeg = magic[:3] == b"\xff\xd8\xff"
    is_png = magic[:8] == b"\x89PNG\r\n\x1a\n"
    is_gif = magic[:6] in (b"GIF87a", b"GIF89a")
    is_webp = magic[:4] == b"RIFF" and magic[8:12] == b"WEBP"
    is_bmp = magic[:2] == b"BM"
    looks_like_image = is_jpeg or is_png or is_gif or is_webp or is_bmp

    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp") and not looks_like_image:
        raise HTTPException(
            status_code=400,
            detail=(
                f"The uploaded file '{filename}' does not appear to contain "
                "valid image data. Please upload a real product-label photo "
                "(PNG / JPG)."
            ),
        )


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok" if pipeline_app is not None else "degraded",
        service="IngredientSight AI LangGraph Pipeline",
        gemini_configured=bool(GEMINI_KEY),
        tavily_configured=bool(TAVILY_KEY),
        upload_dir=UPLOAD_DIR,
        reports_dir=REPORTS_DIR,
        port=SERVER_PORT,
        host=DEFAULT_HOST,
    )


ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@app.post("/api/analyze")
def analyze_label(
    file: Optional[UploadFile] = File(None),
    product_name: Optional[str] = Form(None),
):
    """
    Run 5-Agent LangGraph Pipeline on an uploaded cosmetic label image.

    Declared as a plain `def` (not `async def`) on purpose: the LangGraph
    pipeline is fully synchronous and can take minutes. FastAPI runs `def`
    routes in a threadpool, so the event loop stays responsive to health
    checks and other requests while an analysis is running.

    - `file`:         (required) the uploaded product-label image.
    - `product_name`: (optional) display name for the analyzed product.
    """
    _require_pipeline()

    try:
        if file and file.filename:
            safe_name = os.path.basename(file.filename or "product.png")
            file_ext = os.path.splitext(safe_name)[1].lower() or ".png"

            if file_ext not in ALLOWED_IMAGE_EXT:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type '{file_ext}'. "
                        "Please upload a PNG or JPG image of the product label."
                    ),
                )

            file_name = f"upload_{uuid.uuid4().hex[:12]}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, file_name)

            # Synchronous read — this route runs in FastAPI's threadpool
            # (plain `def`), so awaiting is not available here.
            content = file.file.read()
            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please try again with a valid image.",
                )

            _validate_image_bytes(content, safe_name)

            with open(file_path, "wb") as f:
                f.write(content)

            default_name = os.path.splitext(safe_name)[0]
        else:
            # A real product-label image is required. The old behaviour of
            # silently analysing a bundled sample image produced identical
            # "demo" output for every query and made the dashboard appear
            # broken; the sample file itself has also been removed from the
            # repo, so any fallback here would fail with a confusing 500.
            raise HTTPException(
                status_code=400,
                detail=(
                    "No product label image was uploaded. "
                    "Please take or upload a clear photo of the product's "
                    "ingredient list panel so the AI can read it."
                ),
            )

        display_name = (product_name or default_name).strip() or default_name

        print(f"\n[PIPELINE] Invoking LangGraph with image: {file_path}")
        print(f"[PIPELINE] Display product name: {display_name}")
        result = pipeline_app.invoke({"image_path": file_path})

        safety_analysis = result.get("safety_analysis", {}) or {}

        return {
            "success": True,
            "product_name": display_name,
            "safety_score": result.get("safety_score"),
            "risk_label": result.get("risk_label"),
            "ocr_text": result.get("ocr_text", ""),
            "ingredients": result.get("ingredients", []),
            "research_results": result.get("research_results", {}),
            "safety_analysis": safety_analysis,
            "markdown_report": result.get("markdown_report", ""),
            "json_report": result.get("json_report", {}),
            "report_md_path": result.get("report_md_path", ""),
            "report_json_path": result.get("report_json_path", ""),
            "source_image_path": file_path,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        msg = str(exc)
        if "GOOGLE_API_KEY" in msg or "GEMINI_API_KEY" in msg or "neither" in msg.lower():
            raise HTTPException(
                status_code=500,
                detail=(
                    "Gemini API key is missing or invalid. Please set "
                    "GOOGLE_API_KEY / GEMINI_API_KEY in the .env file next "
                    "to server.py and restart the backend."
                ),
            )
        raise HTTPException(status_code=500, detail=msg)
    except Exception as exc:
        print(f"[ERROR] Pipeline failed: {exc!r}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {exc}",
        )


if __name__ == "__main__":
    import uvicorn

    print(f"Binding to {DEFAULT_HOST}:{SERVER_PORT}")
    uvicorn.run(
        f"{__name__}:app",
        host=DEFAULT_HOST,
        port=SERVER_PORT,
        reload=False,
        log_level="info",
    )
