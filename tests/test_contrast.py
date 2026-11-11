"""Contrast guard: the report tokens must stay readable (WCAG AA)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_contrast", ROOT / "scripts" / "check_contrast.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contrast = _load_script()


def test_every_report_colour_pair_meets_wcag_aa():
    tokens = contrast.read_tokens()
    for label, foreground, background in contrast.PAIRS:
        ratio = contrast.contrast_ratio(
            contrast.resolve(foreground, tokens), contrast.resolve(background, tokens)
        )
        assert ratio >= contrast.MIN_RATIO, f"{label}: {ratio:.2f}"


def test_report_tokens_are_defined_in_the_stylesheet():
    tokens = contrast.read_tokens()
    for name in (
        "--report-bg",
        "--report-ink",
        "--report-muted",
        "--status-prohibited",
        "--status-restricted",
        "--status-permitted",
        "--status-verify",
        "--status-none",
        "--status-unidentified",
        "--notice-bg",
        "--notice-ink",
        "--web-bg",
        "--web-ink",
    ):
        assert name in tokens, name


def test_translucent_sheet_stays_readable_over_the_brightest_pixel():
    tokens = contrast.read_tokens()
    sheet = contrast.composite(contrast.read_glass(), contrast.brightest_asset_pixel())
    for label, foreground in contrast.GLASS_PAIRS:
        ratio = contrast.contrast_ratio(contrast.resolve(foreground, tokens), sheet)
        assert ratio >= contrast.MIN_RATIO, f"{label}: {ratio:.2f}"
