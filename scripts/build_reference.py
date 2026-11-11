"""Build the slim reference dataset used by the app.

Reads data/ingredientsight_ml_dataset_4338e6.csv (never modified) and writes
data/reference.csv with only the columns the checker needs.

Usage:  python scripts/build_reference.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Windows consoles may default to a legacy code page that cannot encode the
# project path; keep log output from crashing the build.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "ingredientsight_ml_dataset_4338e6.csv"
OUTPUT = ROOT / "data" / "reference.csv"

# Identity, annex, limits, hazard and provenance columns.
# Deliberately excluded: skin_irritation (all UNKNOWN), ghs_* and cir_*
# (mostly empty), descriptors, sources URLs and internal helper flags.
COLUMNS = [
    # Identity
    "ingredient_id",
    "ingredient_name",
    "chemical_name",
    "cosing_inci_synonyms",
    "cas_number",
    "cas_number_all",
    "ec_number",
    # Annex
    "safety_class",
    "annex",
    "annex_title",
    "reference_number",
    "permitted_list",
    "is_group_entry",
    # Limits
    "max_concentration_pct",
    "max_concentration_raw",
    "concentration_unit",
    "product_type_conditions",
    "usage_condition",
    "conditions_of_use",
    "other_conditions",
    # Hazard
    "cmr_flag",
    "cmr_categories",
    "toxicity_class",
    "allergy_risk",
    "echa_h_codes",
    "echa_hazard_classes",
    "echa_cmr_flag",
    "echa_vs_annex_cmr",
    "sccs_conclusion",
    "sccs_document",
    # Provenance
    "toxicity_source",
    "allergy_source",
    "echa_source",
    "regulation_basis",
    "source_snapshot",
    "annex_last_update",
    "dataset_version",
]


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(
            f"Dataset not found: {SOURCE}\n"
            "Place ingredientsight_ml_dataset_4338e6.csv in the data/ folder."
        )

    # Read everything as text with no NA coercion so the slim file is a faithful
    # copy of the source values (empty cells stay empty strings).
    df = pd.read_csv(SOURCE, dtype=str, keep_default_na=False, low_memory=False)

    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f"Source dataset is missing required columns: {', '.join(missing)}")

    slim = df[COLUMNS].copy()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    slim.to_csv(OUTPUT, index=False, encoding="utf-8")

    print(f"Wrote {len(slim)} rows x {len(slim.columns)} columns -> {OUTPUT}")
    print(slim["safety_class"].value_counts().to_string())


if __name__ == "__main__":
    main()
