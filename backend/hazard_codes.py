"""Static map of CLP hazard statement codes to short, neutral wording.

Wording follows the official CLP hazard statements. Text is descriptive only:
it states what the classification says, never what a person should do.
"""

from __future__ import annotations

import re

HAZARD_CODES: dict[str, str] = {
    # Physical hazards present in the dataset
    "H200": "Unstable explosive",
    "H201": "Explosive; mass explosion hazard",
    "H203": "Explosive; fire, blast or projection hazard",
    "H220": "Extremely flammable gas",
    "H221": "Flammable gas",
    "H224": "Extremely flammable liquid and vapour",
    "H225": "Highly flammable liquid and vapour",
    "H226": "Flammable liquid and vapour",
    "H228": "Flammable solid",
    "H241": "Heating may cause a fire or explosion",
    "H242": "Heating may cause a fire",
    "H250": "Catches fire spontaneously if exposed to air",
    "H260": "In contact with water releases flammable gases which may ignite spontaneously",
    "H261": "In contact with water releases flammable gas",
    "H270": "May cause or intensify fire; oxidiser",
    "H271": "May cause fire or explosion; strong oxidiser",
    "H272": "May intensify fire; oxidiser",
    "H290": "May be corrosive to metals",
    # Health hazards
    "H300": "Fatal if swallowed",
    "H301": "Toxic if swallowed",
    "H302": "Harmful if swallowed",
    "H304": "May be fatal if swallowed and enters airways",
    "H310": "Fatal in contact with skin",
    "H311": "Toxic in contact with skin",
    "H312": "Harmful in contact with skin",
    "H314": "Causes severe skin burns and eye damage",
    "H315": "Causes skin irritation",
    "H317": "May cause an allergic skin reaction",
    "H318": "Causes serious eye damage",
    "H319": "Causes serious eye irritation",
    "H330": "Fatal if inhaled",
    "H331": "Toxic if inhaled",
    "H332": "Harmful if inhaled",
    "H334": "May cause allergy or asthma symptoms or breathing difficulties if inhaled",
    "H335": "May cause respiratory irritation",
    "H336": "May cause drowsiness or dizziness",
    "H340": "May cause genetic defects",
    "H341": "Suspected of causing genetic defects",
    "H350": "May cause cancer",
    "H351": "Suspected of causing cancer",
    "H360": "May damage fertility or the unborn child",
    "H361": "Suspected of damaging fertility or the unborn child",
    "H362": "May cause harm to breast-fed children",
    "H370": "Causes damage to organs",
    "H371": "May cause damage to organs",
    "H372": "Causes damage to organs through prolonged or repeated exposure",
    "H373": "May cause damage to organs through prolonged or repeated exposure",
    # Environmental hazards
    "H400": "Very toxic to aquatic life",
    "H410": "Very toxic to aquatic life with long lasting effects",
    "H411": "Toxic to aquatic life with long lasting effects",
    "H412": "Harmful to aquatic life with long lasting effects",
    "H413": "May cause long lasting harmful effects to aquatic life",
    "H420": "Harms public health and the environment by destroying ozone in the upper atmosphere",
    # Supplementary EU statements
    "EUH066": "Repeated exposure may cause skin dryness or cracking",
}

_BASE_CODE_RE = re.compile(r"^(EUH\d{3}|H\d{3})")

UNKNOWN_DESCRIPTION = "description not available"


def base_code(code: str) -> str:
    """Return the base statement code, dropping suffixes such as H350i or H360D."""
    match = _BASE_CODE_RE.match((code or "").strip().upper())
    return match.group(1) if match else (code or "").strip().upper()


def describe(code: str) -> str:
    """Plain-language text for a hazard code, or an honest fallback."""
    cleaned = (code or "").strip().upper()
    if cleaned in HAZARD_CODES:
        return HAZARD_CODES[cleaned]
    return HAZARD_CODES.get(base_code(cleaned), UNKNOWN_DESCRIPTION)
