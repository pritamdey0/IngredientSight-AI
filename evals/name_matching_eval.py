"""Name-matching evaluation. Writes evals/results_name_matching.md.

Run from the repository root:

    python evals/name_matching_eval.py

The script is deterministic (fixed random seed) and only reads the dataset, so
the numbers in the report can be reproduced after any matcher change.
"""

from __future__ import annotations

import random
import string
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend import data_layer, matcher  # noqa: E402

SEED = 20261111
SAMPLE_SIZE = 150
RESULTS_PATH = Path(__file__).resolve().parent / "results_name_matching.md"
CONFIRMED_TYPES = {"exact_name", "synonym", "cas", "fuzzy_high"}
UNCONFIRMED_TYPES = {"fuzzy_possible", "group_entry"}
EXCLUDED_SYLLABLES = set(string.ascii_lowercase)


def usable_rows(dataset: data_layer.Dataset) -> list[dict]:
    """Short, unique names: the kind of string a label actually carries."""
    seen: Counter[str] = Counter()
    for row in dataset.rows:
        seen[data_layer.normalize(row.get("ingredient_name"))] += 1
    rows = []
    for row in dataset.rows:
        key = data_layer.normalize(row.get("ingredient_name"))
        name = row.get("ingredient_name") or ""
        if not key or seen[key] > 1:
            continue
        if len(name) < 4 or len(name) > 45 or len(key.split()) > 5:
            continue
        rows.append(row)
    rows.sort(key=lambda row: row["ingredient_id"])
    return rows


def matches_row(result: dict, row_id: str) -> bool:
    return row_id in (result.get("matched_row_ids") or [])


def confirmed(result: dict) -> bool:
    return result["match_type"] in CONFIRMED_TYPES


def typo(name: str, rng: random.Random) -> str:
    """Remove or swap one interior character, the way a label typo looks."""
    if len(name) < 5:
        return name
    index = rng.randrange(1, len(name) - 1)
    if rng.random() < 0.5:
        return name[:index] + name[index + 1 :]
    return name[:index] + name[index + 1] + name[index] + name[index + 2 :]


def gibberish(rng: random.Random) -> str:
    """A pronounceable nonsense name that is not in the dataset."""
    chunks = ["zor", "vex", "quin", "flarn", "mibb", "trel", "skad", "purn", "glim", "waste"]
    return "".join(rng.choice(chunks) for _ in range(2)).capitalize() + str(rng.randrange(100, 999))


def evaluate_case(rows: list[dict], transform) -> dict:
    hits = 0
    wrong = 0
    unconfirmed = 0
    misses = 0
    examples: list[tuple[str, str, str]] = []
    for row in rows:
        name = transform(row["ingredient_name"])
        result = matcher.match_ingredient(name)
        if matches_row(result, row["ingredient_id"]):
            hits += 1
            if not confirmed(result):
                unconfirmed += 1
        elif result["match_type"] == "none":
            misses += 1
            if len(examples) < 5:
                examples.append((name, result["match_type"], "no match"))
        else:
            wrong += 1
            if len(examples) < 5:
                matched = [
                    data_layer.get_dataset().get_row(row_id)["ingredient_name"]
                    for row_id in result["matched_row_ids"][:1]
                ]
                examples.append((name, result["match_type"], matched[0] if matched else ""))
    total = len(rows)
    return {
        "total": total,
        "hits": hits,
        "wrong": wrong,
        "misses": misses,
        "unconfirmed": unconfirmed,
        "recall": hits / total if total else 0.0,
        "wrong_rate": wrong / total if total else 0.0,
        "examples": examples,
    }


def evaluate_gibberish(count: int, rng: random.Random) -> dict:
    false_confirmed = 0
    notes = 0
    none = 0
    examples: list[tuple[str, str, str]] = []
    for _ in range(count):
        name = gibberish(rng)
        result = matcher.match_ingredient(name)
        if confirmed(result):
            false_confirmed += 1
            if len(examples) < 5:
                matched = [
                    data_layer.get_dataset().get_row(row_id)["ingredient_name"]
                    for row_id in result["matched_row_ids"][:1]
                ]
                examples.append((name, result["match_type"], matched[0] if matched else ""))
        elif result["match_type"] in UNCONFIRMED_TYPES:
            notes += 1
        else:
            none += 1
    return {
        "total": count,
        "false_confirmed": false_confirmed,
        "unconfirmed": notes,
        "none": none,
        "false_confirmed_rate": false_confirmed / count if count else 0.0,
        "examples": examples,
    }


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def example_rows(examples: list[tuple[str, str, str]]) -> list[str]:
    if not examples:
        return ["| - | - | - |"]
    return [f"| `{name}` | {match_type} | {matched or '-'} |" for name, match_type, matched in examples]


def main() -> None:
    dataset = data_layer.load()
    rng = random.Random(SEED)
    rows = usable_rows(dataset)
    rng.shuffle(rows)
    sample = rows[:SAMPLE_SIZE]
    print(f"Evaluating {len(sample)} names out of {len(rows)} usable rows.")

    exact = evaluate_case(sample, lambda name: name)
    lower = evaluate_case(sample, lambda name: name.lower())
    spaced = evaluate_case(sample, lambda name: f"  {name.upper()}  ")
    typos = evaluate_case(sample, lambda name: typo(name, rng))
    random_names = evaluate_gibberish(SAMPLE_SIZE, rng)

    groups = sum(1 for row in sample if matcher.is_group_entry_row(row))

    lines = [
        "# Name matching evaluation",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Dataset: {dataset.info['rows']} rows, version `{dataset.info['dataset_version']}`, "
        f"snapshot `{dataset.info['source_snapshot']}`",
        f"- Seed: {SEED}; sample: {len(sample)} unique names of 4-45 characters "
        f"({groups} of them group entries)",
        f"- Fuzzy bands: confirmed at WRatio/token_set_ratio >= {matcher.FUZZY_HIGH_MIN}, "
        f"possible match from {matcher.FUZZY_POSSIBLE_MIN}, both after the word-count guard",
        "",
        "## Summary",
        "",
        "| Check | Correct row | Wrong row | No match | Confirmed | Target |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| Exact name | {percent(exact['recall'])} | {percent(exact['wrong_rate'])} | "
        f"{exact['misses']} | {exact['hits']} | 100% correct |",
        f"| Lowercase | {percent(lower['recall'])} | {percent(lower['wrong_rate'])} | "
        f"{lower['misses']} | {lower['hits']} | 100% correct |",
        f"| Upper case + spaces | {percent(spaced['recall'])} | {percent(spaced['wrong_rate'])} | "
        f"{spaced['misses']} | {spaced['hits']} | 100% correct |",
        f"| One-character typo | {percent(typos['recall'])} | {percent(typos['wrong_rate'])} | "
        f"{typos['misses']} | {typos['hits'] - typos['unconfirmed']} | wrong row < 5% |",
        f"| Nonsense names | 0% | {percent(random_names['false_confirmed_rate'])} | "
        f"{random_names['none']} | 0 | wrong row 0% |",
        "",
        "`Wrong row` means a confirmed match to a different dataset row than the sampled name.",
        "`Confirmed` counts matches the UI would show as a final status; possible matches and "
        "group entries are shown to the user as `POSSIBLE_MATCH_VERIFY` instead.",
        "",
        "## Details",
        "",
        "| Check | Sample | Correct row | Wrong row | No match | Unconfirmed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for label, data in (
        ("Exact name", exact),
        ("Lowercase", lower),
        ("Upper case + spaces", spaced),
        ("One-character typo", typos),
    ):
        lines.append(
            f"| {label} | {data['total']} | {data['hits']} | {data['wrong']} | "
            f"{data['misses']} | {data['unconfirmed']} |"
        )
    lines.append(
        f"| Nonsense names | {random_names['total']} | - | {random_names['false_confirmed']} | "
        f"{random_names['none']} | {random_names['unconfirmed']} |"
    )

    lines += [
        "",
        "## Wrong rows and misses (typos)",
        "",
        "| Input | Match type | Matched row |",
        "| --- | --- | --- |",
        *example_rows(typos["examples"]),
        "",
        "## Nonsense names that were matched anyway",
        "",
        "| Input | Match type | Matched row |",
        "| --- | --- | --- |",
        *example_rows(random_names["examples"]),
        "",
        "## What this does not measure",
        "",
        "- Whether the dataset itself is complete or correct. It only measures the matcher.",
        "- Real label wording. INCI names in the dataset and on labels can differ in ways a "
        "one-character mutation does not reproduce.",
        "- Names that exist in several rows (duplicates were removed from the sample so a "
        "'wrong row' result stays meaningful).",
        "",
    ]

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH}")
    print(
        f"exact={percent(exact['recall'])} typo_correct={percent(typos['recall'])} "
        f"typo_wrong={percent(typos['wrong_rate'])} "
        f"nonsense_wrong={percent(random_names['false_confirmed_rate'])}"
    )


if __name__ == "__main__":
    main()
