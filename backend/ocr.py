"""Local OCR with RapidOCR (required).

RapidOCR must be installed. The /api/analyze-image endpoint raises 503 if the
package is missing at startup rather than silently falling back to text paste.
"""

from __future__ import annotations

import io

from . import config

_engine = None


class OcrUnavailable(RuntimeError):
    """Raised when OCR cannot run on this machine."""


def is_available() -> bool:
    """Always True — OCR is a required dependency."""
    return True


def _ensure_engine():
    """Raise OcrUnavailable if rapidocr_onnxruntime is not installed."""
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # noqa: PLC0415
            _engine = RapidOCR()
        except ImportError as exc:
            raise OcrUnavailable(
                "rapidocr_onnxruntime is not installed. "
                "Run: pip install rapidocr-onnxruntime"
            ) from exc
    return _engine


def _get_engine():
    return _ensure_engine()


def _load_image(image_bytes: bytes):
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert("RGB")
    # Downscale to the maximum side; thumbnail keeps the aspect ratio.
    image.thumbnail((config.MAX_IMAGE_SIDE_PX, config.MAX_IMAGE_SIDE_PX))
    return image


def _lines_in_reading_order(raw_result) -> list[str]:
    """RapidOCR returns [box, text, score] entries; sort them top-down, left-right."""
    entries = []
    for entry in raw_result or []:
        try:
            box, text = entry[0], entry[1]
        except (IndexError, TypeError):
            continue
        if not text:
            continue
        ys = [point[1] for point in box]
        xs = [point[0] for point in box]
        entries.append((min(ys), min(xs), str(text)))
    # Group rows by a small vertical tolerance so one label line stays together.
    entries.sort(key=lambda item: (round(item[0] / 20), item[1]))
    return [text for _y, _x, text in entries]


def run_ocr(image_bytes: bytes) -> str:
    """Return the text found in the image, in reading order."""
    try:
        import numpy as np

        engine = _get_engine()
        image = _load_image(image_bytes)
        raw_result, _elapse = engine(np.array(image))
    except OcrUnavailable:
        raise
    except Exception as exc:  # OCR backend failures must not crash the API
        raise OcrUnavailable(f"OCR failed: {exc}") from exc

    return "\n".join(_lines_in_reading_order(raw_result))
