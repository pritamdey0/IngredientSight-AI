"""
OCR Agent — IngredientSight AI

Extraction priority (all local-first, zero API quota on primary path):

  1. RapidOCR  (rapidocr-onnxruntime) — ONNX-based, no system binary,
               works out of the box in every environment.
  2. pytesseract — lightweight Tesseract wrapper; skipped gracefully if the
               Tesseract binary is not installed.
  3. Gemini Vision API  — API fallback (uses GOOGLE_API_KEY / GEMINI_API_KEY).
  4. Groq Vision API   — API fallback (uses GROQ_API_KEY).

Environment variables:
  TESSERACT_CMD   — (optional) full path to tesseract.exe on Windows,
                    e.g. C:\\Program Files\\Tesseract-OCR\\tesseract.exe
"""

import os
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

_gemini_client_instance = None
_rapidocr_instance = None


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

def _get_rapidocr():
    """Return (or lazily create) the singleton RapidOCR engine."""
    global _rapidocr_instance
    if _rapidocr_instance is not None:
        return _rapidocr_instance
    try:
        from rapidocr_onnxruntime import RapidOCR
        print("[INFO] Initializing RapidOCR engine (ONNX, local, no system binary)...")
        _rapidocr_instance = RapidOCR()
        print("[INFO] RapidOCR engine ready.")
        return _rapidocr_instance
    except Exception as e:
        print(f"[WARN] Could not initialise RapidOCR: {e}")
        return None


def _configure_tesseract() -> None:
    """Point pytesseract at the Tesseract executable if TESSERACT_CMD is set."""
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = cmd
        except ImportError:
            pass


def get_gemini_client():
    """Initialise and cache the GenAI client."""
    global _gemini_client_instance
    if _gemini_client_instance is not None:
        return _gemini_client_instance
    from google import genai
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Neither GOOGLE_API_KEY nor GEMINI_API_KEY was found in the "
            "environment / dotenv file."
        )
    _gemini_client_instance = genai.Client(api_key=api_key)
    return _gemini_client_instance


# ---------------------------------------------------------------------------
# OCR Node
# ---------------------------------------------------------------------------

_VISION_PROMPT = (
    "Analyze this image of a product label. "
    "Extract only the ingredients list. "
    "Ignore all marketing text, branding, instructions, or unrelated information. "
    "Correct any spelling errors or OCR inaccuracies you spot based on standard "
    "chemical/ingredient nomenclature. "
    "Return the extracted ingredients as a clean, plain text comma-separated list."
)


def ocr_node(state: dict) -> dict:
    """
    OCR Node — extracts ingredient text from a product-label image.

    Tries local engines first (free, no rate limits) and only reaches out
    to API-based vision models when local extraction fails.
    """
    image_path = state.get("image_path")
    if not image_path:
        raise ValueError("No 'image_path' provided in the state.")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    rapidocr_err = None
    tesseract_err = None
    gemini_err = None
    groq_err = None

    # ------------------------------------------------------------------
    # Stage 1: RapidOCR (primary — ONNX local, zero API cost)
    # ------------------------------------------------------------------
    try:
        engine = _get_rapidocr()
        if engine is not None:
            print(f"[INFO] Running RapidOCR on {os.path.basename(image_path)}...")
            result, elapse = engine(image_path)
            if result:
                # result is a list of [bbox, text, confidence] tuples
                lines = [item[1] for item in result if item[1]]
                if lines:
                    state["ocr_text"] = ", ".join(lines).strip()
                    # elapse may be a list of per-stage times or a single float
                    total_ms = sum(elapse) if isinstance(elapse, (list, tuple)) else elapse
                    print(
                        f"[INFO] RapidOCR extracted {len(lines)} text blocks "
                        f"in {total_ms:.3f}s (0 API cost)."
                    )
                    return state
            print("[WARN] RapidOCR returned empty text. Trying pytesseract...")
        else:
            rapidocr_err = "RapidOCR failed to initialise."
    except Exception as e:
        rapidocr_err = e
        print(f"[WARN] RapidOCR failed: {e}. Trying pytesseract...")

    # ------------------------------------------------------------------
    # Stage 2: pytesseract (local — needs Tesseract binary installed)
    # ------------------------------------------------------------------
    _configure_tesseract()
    try:
        import pytesseract

        img = Image.open(image_path)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # PSM 6 → uniform block of text (good for dense ingredient labels)
        ocr_text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")
        if ocr_text.strip():
            state["ocr_text"] = ocr_text.strip()
            print("[INFO] pytesseract extracted text successfully (0 API cost).")
            return state
        else:
            tesseract_err = "pytesseract returned empty text."
            print(f"[WARN] {tesseract_err} Trying Gemini Vision fallback...")
    except ImportError:
        tesseract_err = "pytesseract is not installed in this environment."
        print(f"[WARN] {tesseract_err} Skipping to Gemini Vision fallback...")
    except Exception as e:
        tesseract_err = e
        # TesseractNotFound means the binary isn't installed — not fatal
        err_str = str(e).lower()
        if "tesseract" in err_str and ("not installed" in err_str or "not found" in err_str):
            print(
                "[WARN] Tesseract binary not found. "
                "Install from https://github.com/UB-Mannheim/tesseract/wiki "
                "or set TESSERACT_CMD env var. Skipping to Gemini fallback..."
            )
        else:
            print(f"[WARN] pytesseract failed: {e}. Trying Gemini Vision fallback...")

    # ------------------------------------------------------------------
    # Stage 3: Gemini Vision API fallback
    # ------------------------------------------------------------------
    try:
        client = get_gemini_client()
        image = Image.open(image_path)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[_VISION_PROMPT, image],
        )
        state["ocr_text"] = response.text.strip() if response.text else ""
        print("[INFO] OCR processed via Gemini Vision API fallback.")
        return state
    except Exception as e:
        gemini_err = e
        print(f"[WARN] Gemini Vision failed: {e}. Trying Groq Vision fallback...")

    # ------------------------------------------------------------------
    # Stage 4: Groq Vision fallback
    # ------------------------------------------------------------------
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        try:
            import base64
            import io
            import requests

            img = Image.open(image_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            max_size = 1200
            if max(img.width, img.height) > max_size:
                ratio = max_size / max(img.width, img.height)
                img = img.resize(
                    (int(img.width * ratio), int(img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            encoded_image = base64.b64encode(buf.getvalue()).decode("utf-8")

            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            }
            for model in ["llama-3.2-11b-vision-preview", "qwen/qwen3.6-27b"]:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": _VISION_PROMPT},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{encoded_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        "temperature": 0.0,
                    }
                    resp = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30,
                    )
                    resp.raise_for_status()
                    ocr_text = resp.json()["choices"][0]["message"]["content"]
                    state["ocr_text"] = ocr_text.strip() if ocr_text else ""
                    print(f"[INFO] OCR recovered via Groq Vision ({model}).")
                    return state
                except Exception as model_err:
                    groq_err = model_err
                    continue
        except Exception as g_err:
            groq_err = g_err

    # ------------------------------------------------------------------
    # All stages exhausted
    # ------------------------------------------------------------------
    raise RuntimeError(
        "All OCR stages failed.\n"
        f"  1. RapidOCR       : {rapidocr_err}\n"
        f"  2. pytesseract    : {tesseract_err}\n"
        f"  3. Gemini Vision  : {gemini_err}\n"
        f"  4. Groq Vision    : {groq_err}\n\n"
        "Tip: RapidOCR should work in any environment — check that "
        "'rapidocr-onnxruntime' is installed in your active Python venv."
    )
