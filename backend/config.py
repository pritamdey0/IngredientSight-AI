"""Environment settings, domain lists and shared constants.

Every setting with an environment override is optional: the application runs
with no configuration at all (template report only, no web context).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
REFERENCE_CSV = DATA_DIR / "reference.csv"
ALIASES_JSON = DATA_DIR / "aliases.json"

# Input limits (single source of truth for validation).
MAX_INPUT_CHARS = 10_000
MAX_NAME_CHARS = 120
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_SIDE_PX = 2000

# The one sentence every analysis and report starts with.
DISCLAIMER = (
    "This tool checks ingredients against EU cosmetic regulation (CosIng annexes) and "
    "ECHA CLP classifications. An ingredient with no entry has no EU annex restriction "
    "found; this is not a safety assessment, medical advice, or a prediction of how your "
    "skin will react. Concentrations are not on labels, so limits cannot be checked."
)

# Literal text shown for every field the dataset does not fill in.
NO_DATA = "No data in dataset"

# ---- Optional LLM summary -------------------------------------------------
SUPPORTED_LLM_PROVIDERS = ("gemini", "groq")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()

# If explicit LLM_PROVIDER/LLM_API_KEY not set, auto-detect from known keys.
if not LLM_PROVIDER:
    _gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    _groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if _gemini_key:
        LLM_PROVIDER = "gemini"
        LLM_API_KEY = _gemini_key
        LLM_MODEL = LLM_MODEL or "gemini-2.0-flash"
    elif _groq_key:
        LLM_PROVIDER = "groq"
        LLM_API_KEY = _groq_key
        LLM_MODEL = LLM_MODEL or "llama-3.3-70b-versatile"
else:
    if LLM_PROVIDER == "gemini" and not LLM_API_KEY:
        LLM_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
        LLM_MODEL = LLM_MODEL or "gemini-2.0-flash"
    elif LLM_PROVIDER == "groq" and not LLM_API_KEY:
        LLM_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
        LLM_MODEL = LLM_MODEL or "llama-3.3-70b-versatile"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

LLM_TIMEOUT_SECONDS = 15.0
LLM_MAX_OUTPUT_TOKENS = 400


def llm_enabled() -> bool:
    """The summary step only runs when provider, model and key are all set."""
    return LLM_PROVIDER in SUPPORTED_LLM_PROVIDERS and bool(LLM_MODEL) and bool(LLM_API_KEY)


# ---- Optional web context (Tavily) ---------------------------------------
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
WEB_TIMEOUT_SECONDS = 10.0
WEB_RESULTS_FETCHED = 8
WEB_RESULTS_RETURNED = 3
WEB_EXCERPT_MAX_WORDS = 25
WEB_CACHE_TTL_SECONDS = 24 * 60 * 60
# A batch lookup is one user click: six ingredients at most, with a small pause
# between the calls so the provider is not hit in a burst.
WEB_BATCH_MAX = 6
WEB_BATCH_DELAY_SECONDS = 0.25


def web_context_enabled() -> bool:
    return bool(TAVILY_API_KEY)


# ---- Server --------------------------------------------------------------
def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


PORT = _int_env("PORT", 8000)
RATE_LIMIT_ANALYZE = _int_env("RATE_LIMIT_ANALYZE", 30)
RATE_LIMIT_WEB = _int_env("RATE_LIMIT_WEB", 10)

LOCAL_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000")
EXTRA_ALLOWED_ORIGINS = tuple(
    origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()
)
VERCEL_ORIGIN_REGEX = r""

# ---- Web-context source classification -----------------------------------
# Host suffixes, checked in this order. Anything else is "other".
OFFICIAL_SCIENTIFIC_DOMAINS = (
    "europa.eu",
    "ec.europa.eu",
    "echa.europa.eu",
    "sccs.europa.eu",
    "cir-safety.org",
    "pubchem.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "nih.gov",
    "who.int",
)
RETAILER_BRAND_DOMAINS = (
    "amazon.com",
    "sephora.com",
    "ulta.com",
    "target.com",
    "walmart.com",
    "boots.com",
    "iherb.com",
    "coupang.com",
    "oliveyoung.co.kr",
    "yesstyle.com",
    "beautycounter.com",
    "theordinary.com",
)
REVIEW_DOMAINS = (
    "ewg.org",
    "incidecoder.com",
    "skincarisma.com",
    "cosdna.com",
    "beautypedia.com",
    "paulaschoice.com",
)
BLOG_FORUM_DOMAINS = (
    "reddit.com",
    "quora.com",
    "medium.com",
    "blogspot.com",
    "wordpress.com",
    "youtube.com",
    "tiktok.com",
    "instagram.com",
)

# Low-quality / spam domains that never reach the response.
BLOCKED_DOMAINS = (
    "pinterest.com",
    "scribd.com",
    "slideshare.net",
    "answers.com",
    "docplayer.net",
)


def _host_matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def source_type_for(host: str) -> str:
    """Map a host name to one of the five source types shown in the UI."""
    host = (host or "").lower().strip(".")
    if _host_matches(host, OFFICIAL_SCIENTIFIC_DOMAINS):
        return "official_scientific"
    if _host_matches(host, RETAILER_BRAND_DOMAINS):
        return "retailer_brand"
    if _host_matches(host, REVIEW_DOMAINS):
        return "review"
    if _host_matches(host, BLOG_FORUM_DOMAINS):
        return "blog_forum"
    return "other"


def is_blocked_host(host: str) -> bool:
    host = (host or "").lower().strip(".")
    return _host_matches(host, BLOCKED_DOMAINS)
