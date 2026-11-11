# Name matching evaluation

- Date: 2026-11-11
- Dataset: 4722 rows, version `IngredientSight-EU-v3`, snapshot `cosing-annex-2026-11-11, cosing-inventory-2020`
- Seed: 20261111; sample: 150 unique names of 4-45 characters (10 of them group entries)
- Fuzzy bands: confirmed at WRatio/token_set_ratio >= 92.0, possible match from 80.0, both after the word-count guard

## Summary

| Check | Correct row | Wrong row | No match | Confirmed | Target |
| --- | --- | --- | --- | --- | --- |
| Exact name | 100.0% | 0.0% | 0 | 150 | 100% correct |
| Lowercase | 100.0% | 0.0% | 0 | 150 | 100% correct |
| Upper case + spaces | 100.0% | 0.0% | 0 | 150 | 100% correct |
| One-character typo | 96.0% | 2.7% | 2 | 116 | wrong row < 5% |
| Nonsense names | 0% | 0.0% | 150 | 0 | wrong row 0% |

`Wrong row` means a confirmed match to a different dataset row than the sampled name.
`Confirmed` counts matches the UI would show as a final status; possible matches and group entries are shown to the user as `POSSIBLE_MATCH_VERIFY` instead.

## Details

| Check | Sample | Correct row | Wrong row | No match | Unconfirmed |
| --- | --- | --- | --- | --- | --- |
| Exact name | 150 | 150 | 0 | 0 | 10 |
| Lowercase | 150 | 150 | 0 | 0 | 10 |
| Upper case + spaces | 150 | 150 | 0 | 0 | 10 |
| One-character typo | 150 | 144 | 4 | 2 | 28 |
| Nonsense names | 150 | - | 0 | 150 | 0 |

## Wrong rows and misses (typos)

| Input | Match type | Matched row |
| --- | --- | --- |
| `CI 7740` | fuzzy_high | CI 77400 |
| `PEG- LAURATE` | fuzzy_possible | PEG-18 |
| `N--2Naphthylaniline` | none | no match |
| `PEG-10LANOLIN` | fuzzy_possible | DIETHYLENE GLYCOL |
| `PEG4- ISOSTEARATE` | fuzzy_possible | Secondary alkyl- and alkanolamines and their salts |

## Nonsense names that were matched anyway

| Input | Match type | Matched row |
| --- | --- | --- |
| - | - | - |

## What this does not measure

- Whether the dataset itself is complete or correct. It only measures the matcher.
- Real label wording. INCI names in the dataset and on labels can differ in ways a one-character mutation does not reproduce.
- Names that exist in several rows (duplicates were removed from the sample so a 'wrong row' result stays meaningful).
