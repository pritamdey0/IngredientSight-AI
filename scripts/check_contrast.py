"""WCAG AA check for the report sheet colours.

The report tokens live in one place (``src/index.css``), so this script reads
them from there instead of copying hex values. Every text/background pair used
by the report must reach 4.5:1 (normal text) or 3:1 (large text only).

The sheet is translucent (``--report-glass``), so the tokens alone do not prove
anything: the real background is the glass composited over the photograph. The
second half of the check composites the glass over the brightest pixel found in
the asset and re-tests every text colour against that worst case.

Run:  .venv\\Scripts\\python scripts\\check_contrast.py
Exit code is non-zero when a pair fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src" / "index.css"
ASSET = ROOT / "public" / "assets" / "ascii-dna.webp"
MIN_RATIO = 4.5
FALLBACK_BRIGHTEST = "#ffffff"

# (label, foreground, background)
PAIRS: list[tuple[str, str, str]] = [
    ("body text on the sheet", "var(--report-ink)", "var(--report-bg)"),
    ("secondary text on the sheet", "var(--report-ink-strong)", "var(--report-bg)"),
    ("labels on the sheet", "var(--report-muted)", "var(--report-bg)"),
    ("prohibited chip", "var(--status-prohibited)", "var(--report-bg)"),
    ("restricted chip", "var(--status-restricted)", "var(--report-bg)"),
    ("positive list chip", "var(--status-permitted)", "var(--report-bg)"),
    ("verify match chip", "var(--status-verify)", "var(--report-bg)"),
    ("no annex entry chip", "var(--status-none)", "var(--report-bg)"),
    ("not identified chip", "var(--status-unidentified)", "var(--report-bg)"),
    ("disclaimer label", "var(--notice-ink)", "var(--notice-bg)"),
    ("disclaimer body", "var(--report-ink-strong)", "var(--notice-bg)"),
    ("web panel text", "var(--web-ink)", "var(--web-bg)"),
    ("web panel labels", "var(--web-muted)", "var(--web-bg)"),
    ("web panel link", "var(--web-link)", "var(--web-bg)"),
    ("error text on the sheet", "var(--status-error)", "var(--report-bg)"),
    ("focus ring on the sheet", "var(--report-focus)", "var(--report-bg)"),
    ("candidate chip on the sheet", "var(--status-verify)", "var(--report-bg)"),
]

# Text that sits directly on the translucent sheet, tested over the lightest
# pixel of the background photograph instead of the opaque reference colour.
GLASS_PAIRS: list[tuple[str, str]] = [
    ("body text on the glass", "var(--report-ink)"),
    ("secondary text on the glass", "var(--report-ink-strong)"),
    ("labels on the glass", "var(--report-muted)"),
    ("prohibited chip on the glass", "var(--status-prohibited)"),
    ("restricted chip on the glass", "var(--status-restricted)"),
    ("positive list chip on the glass", "var(--status-permitted)"),
    ("verify match chip on the glass", "var(--status-verify)"),
    ("no annex entry chip on the glass", "var(--status-none)"),
    ("not identified chip on the glass", "var(--status-unidentified)"),
    ("error text on the glass", "var(--status-error)"),
    ("focus ring on the glass", "var(--report-focus)"),
]

_VAR_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;")
_ROOT_RE = re.compile(r":root\s*\{(.*?)\}", re.S)
_GLASS_RE = re.compile(
    r"--report-glass\s*:\s*rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)"
)


def read_tokens(path: Path = CSS) -> dict[str, str]:
    """Tokens of the screen palette only.

    ``index.css`` redefines the same names inside ``@media print`` for paper; only
    the first ``:root`` block is read here.
    """
    root = _ROOT_RE.search(path.read_text(encoding="utf-8"))
    if root is None:
        raise ValueError(f"no :root block in {path}")
    return dict(_VAR_RE.findall(root.group(1)))


def read_glass(path: Path = CSS) -> tuple[tuple[int, int, int], float]:
    """The sheet fill as (rgb, alpha), parsed from ``--report-glass``."""
    root = _ROOT_RE.search(path.read_text(encoding="utf-8"))
    glass = _GLASS_RE.search(root.group(1) if root else "")
    if glass is None:
        raise ValueError(f"--report-glass not found in {path}")
    red, green, blue, alpha = glass.groups()
    return (int(red), int(green), int(blue)), float(alpha)


def brightest_asset_pixel() -> str:
    """Lightest colour in the background image, so the check uses the real worst case.

    The per-channel maximum is a slight over-estimate of the brightest pixel, which
    is the safe direction: the check never under-states how much light leaks through.
    """
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow is only needed for this sample
        return FALLBACK_BRIGHTEST
    if not ASSET.exists():
        return FALLBACK_BRIGHTEST
    with Image.open(ASSET) as image:
        extrema = image.convert("RGB").getextrema()
    return "#%02x%02x%02x" % tuple(upper for _lower, upper in extrema)


def composite(glass: tuple[tuple[int, int, int], float], under: str) -> str:
    """Glass over a background colour, as CSS composites it (sRGB, straight alpha)."""
    (red, green, blue), alpha = glass
    back = under.lstrip("#")
    channels = (int(back[index:index + 2], 16) for index in (0, 2, 4))
    blended = (
        round(alpha * front + (1 - alpha) * base)
        for front, base in zip((red, green, blue), channels)
    )
    return "#%02x%02x%02x" % tuple(blended)


def _channel(value: int) -> float:
    srgb = value / 255
    return srgb / 12.92 if srgb <= 0.03928 else ((srgb + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    clean = hex_colour.lstrip("#")
    red, green, blue = (int(clean[index:index + 2], 16) for index in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def resolve(value: str, tokens: dict[str, str]) -> str:
    if value.startswith("var("):
        name = value[4:-1].strip()
        if name not in tokens:
            raise KeyError(f"{name} is not defined in {CSS.name}")
        return tokens[name]
    return value


def main() -> int:
    tokens = read_tokens()
    failures = []
    print(f"{'pair':44s} {'fg':9s} {'bg':9s} ratio")
    for label, foreground, background in PAIRS:
        fg = resolve(foreground, tokens)
        bg = resolve(background, tokens)
        ratio = contrast_ratio(fg, bg)
        status = "ok" if ratio >= MIN_RATIO else "FAIL"
        print(f"{label:44s} {fg:9s} {bg:9s} {ratio:5.2f} {status}")
        if ratio < MIN_RATIO:
            failures.append((label, ratio))

    glass = read_glass()
    brightest = brightest_asset_pixel()
    sheet = composite(glass, brightest)
    print(
        f"\ntranslucent sheet: {glass[1]:.0%} glass over {brightest} "
        f"(lightest colour in {ASSET.name}) = {sheet}"
    )
    print(f"{'pair':44s} {'fg':9s} {'bg':9s} ratio")
    for label, foreground in GLASS_PAIRS:
        fg = resolve(foreground, tokens)
        ratio = contrast_ratio(fg, sheet)
        status = "ok" if ratio >= MIN_RATIO else "FAIL"
        print(f"{label:44s} {fg:9s} {sheet:9s} {ratio:5.2f} {status}")
        if ratio < MIN_RATIO:
            failures.append((label, ratio))

    total = len(PAIRS) + len(GLASS_PAIRS)
    if failures:
        print(f"\n{len(failures)} of {total} pair(s) below {MIN_RATIO}:1")
        return 1
    print(f"\nAll {total} pairs reach {MIN_RATIO}:1 (WCAG AA).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
