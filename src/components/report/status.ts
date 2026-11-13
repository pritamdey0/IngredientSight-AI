/** Report design system: status styles, field labels and the web-topic mapping. */

import {
  Ban,
  CircleHelp,
  FileQuestion,
  HelpCircle,
  ListChecks,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react';
import type { Ingredient, Status, Summary } from '../../lib/api';

export const NO_DATA = 'No data in dataset';

export interface StatusStyle {
  label: string;
  short: string;
  sentence: string;
  Icon: LucideIcon;
  /** Landing-style chip: a 2 px status rule, translucent fill, mono label. */
  badge: string;
  /** 2 px rule on the left edge of the block, same colour as the chip. */
  rule: string;
  /** 6 px square before the count in the counts line. Decorative only. */
  dot: string;
}

// No status is green and no status implies safety.
export const STATUS_UI: Record<Status, StatusStyle> = {
  PROHIBITED: {
    label: 'Prohibited',
    short: 'Prohibited',
    sentence: 'Listed in EU Annex II: prohibited in cosmetic products.',
    Icon: Ban,
    badge: 'border-l-[color:var(--status-prohibited)] text-[var(--status-prohibited)]',
    rule: 'border-l-[color:var(--status-prohibited)]',
    dot: 'bg-[var(--status-prohibited)]',
  },
  RESTRICTED: {
    label: 'Restricted',
    short: 'Restricted',
    sentence: 'Listed in EU Annex III: allowed only under the conditions of the entry.',
    Icon: TriangleAlert,
    badge: 'border-l-[color:var(--status-restricted)] text-[var(--status-restricted)]',
    rule: 'border-l-[color:var(--status-restricted)]',
    dot: 'bg-[var(--status-restricted)]',
  },
  PERMITTED_WITH_LIMITS: {
    label: 'On a positive list',
    short: 'Positive list',
    sentence:
      'On a positive list (Annex IV to VI): allowed only as listed and under the entry conditions.',
    Icon: ListChecks,
    badge: 'border-l-[color:var(--status-permitted)] text-[var(--status-permitted)]',
    rule: 'border-l-[color:var(--status-permitted)]',
    dot: 'bg-[var(--status-permitted)]',
  },
  POSSIBLE_MATCH_VERIFY: {
    label: 'Verify match',
    short: 'Verify match',
    sentence: 'Possible match, not confirmed. Check the matched name and pick the right entry.',
    Icon: HelpCircle,
    badge: 'border-l-[color:var(--status-verify)] text-[var(--status-verify)]',
    rule: 'border-l-[color:var(--status-verify)]',
    dot: 'bg-[var(--status-verify)]',
  },
  NO_ANNEX_ENTRY_FOUND: {
    label: 'No EU annex entry found',
    short: 'No annex entry',
    sentence:
      'No EU annex entry found for this name in the dataset. This is not a safety assessment.',
    Icon: FileQuestion,
    badge: 'border-l-[color:var(--status-none)] text-[var(--status-none)]',
    rule: 'border-l-[color:var(--status-none)]',
    dot: 'bg-[var(--status-none)]',
  },
  UNIDENTIFIED: {
    label: 'Not identified',
    short: 'Not identified',
    sentence: 'Not identified in the dataset. An entry may exist under a different chemical name.',
    Icon: CircleHelp,
    badge: 'border-l-[color:var(--status-unidentified)] text-[var(--status-unidentified)]',
    rule: 'border-l-[color:var(--status-unidentified)]',
    dot: 'bg-[var(--status-unidentified)]',
  },
};

export const SUMMARY_CHIPS: { key: keyof Summary; label: string; status: Status }[] = [
  { key: 'prohibited', label: 'Prohibited', status: 'PROHIBITED' },
  { key: 'restricted', label: 'Restricted', status: 'RESTRICTED' },
  { key: 'permitted_with_limits', label: 'Positive list', status: 'PERMITTED_WITH_LIMITS' },
  { key: 'possible_match_verify', label: 'Verify match', status: 'POSSIBLE_MATCH_VERIFY' },
  { key: 'no_annex_entry_found', label: 'No annex entry', status: 'NO_ANNEX_ENTRY_FOUND' },
  { key: 'unidentified', label: 'Not identified', status: 'UNIDENTIFIED' },
];

export const MATCH_LABELS: Record<string, string> = {
  exact_name: 'exact name',
  synonym: 'synonym',
  cas: 'CAS number',
  fuzzy_high: 'fuzzy name',
  fuzzy_possible: 'possible fuzzy name',
  group_entry: 'group entry',
  none: 'no match',
};

export const FACT_LABELS: Record<string, string> = {
  annex: 'EU annex',
  reference_number: 'Annex reference number',
  permitted_list: 'Positive list',
  max_concentration_pct: 'Maximum concentration (%)',
  max_concentration_raw: 'Concentration limit as written',
  conditions_of_use: 'Conditions of use',
  usage_condition: 'Usage condition',
  product_type_conditions: 'Product type',
  other_conditions: 'Other conditions',
  skin_irritation: 'Skin irritation',
};

/** Same fields, lower case, for the single "No data in dataset for: ..." line. */
export const GAP_LABELS: Record<string, string> = {
  annex: 'EU annex',
  reference_number: 'annex reference number',
  permitted_list: 'positive list',
  max_concentration_pct: 'maximum concentration',
  max_concentration_raw: 'concentration limit as written',
  conditions_of_use: 'conditions of use',
  usage_condition: 'usage condition',
  product_type_conditions: 'product type',
  other_conditions: 'other conditions',
  skin_irritation: 'skin irritation',
};

export const LIMIT_FIELDS = [
  'max_concentration_pct',
  'max_concentration_raw',
  'conditions_of_use',
  'usage_condition',
  'product_type_conditions',
  'other_conditions',
] as const;

/** Fields summarised by one sentence when the ingredient has no annex entry. */
export const ANNEX_ONLY_FIELDS = [
  'annex',
  'reference_number',
  'permitted_list',
  ...LIMIT_FIELDS,
] as unknown as string[];

/** Text that is clamped to four lines until the user expands it. */
export const LONG_FIELDS = new Set(['conditions_of_use', 'other_conditions']);

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  official_scientific: 'Official',
  retailer_brand: 'Retailer or brand',
  review: 'Review',
  blog_forum: 'Blog or forum',
  other: 'Other',
};

/** The two evidence origins, used as visible labels in the report. */
export const DATASET_LABEL = 'FROM DATASET';
export const EVIDENCE_LABEL = 'FROM WEB SOURCE REVIEW';

/** Neutral wording for a validated evidence assessment. Never a verdict. */
export const EVIDENCE_ASSESSMENT_LABELS: Record<string, string> = {
  Supported: 'Supported by the retrieved sources',
  Limited: 'Limited evidence in the retrieved sources',
  Conflicting: 'Conflicting evidence in the retrieved sources',
  Insufficient: 'Insufficient evidence in the retrieved sources',
};

export const WEB_TOPICS = [
  'skin irritation',
  'allergy / sensitization',
  'use limits',
  'hazard classification',
] as const;

export const NO_ANNEX_SENTENCE = 'No annex entry, so no annex limits apply in the dataset.';

export function isNoData(value: string | null | undefined): boolean {
  return !value || value === NO_DATA;
}

/** Facts with data, in display order. Empty values are never repeated here. */
export function presentFacts(ingredient: Ingredient): { field: string; label: string; value: string }[] {
  const facts: { field: string; label: string; value: string }[] = [];
  const add = (field: string, value: string | null | undefined) => {
    if (!isNoData(value)) facts.push({ field, label: FACT_LABELS[field] ?? field, value: value as string });
  };
  add('annex', ingredient.annex);
  add('reference_number', ingredient.reference_number);
  add('permitted_list', ingredient.permitted_list);
  for (const field of LIMIT_FIELDS) add(field, ingredient.limits[field]);
  add('skin_irritation', ingredient.skin_irritation);
  return facts;
}

/** The gaps of one ingredient, ready for the single "No data" line. */
export function missingFieldLabels(ingredient: Ingredient): string[] {
  return ingredient.unknown_fields
    .filter((field) =>
      ingredient.status === 'NO_ANNEX_ENTRY_FOUND' ? !ANNEX_ONLY_FIELDS.includes(field) : true,
    )
    .map((field) => GAP_LABELS[field] ?? field);
}

export function needsWebPanel(ingredient: Ingredient): boolean {
  if (ingredient.unknown_fields.length > 0) return true;
  return (
    ingredient.status === 'NO_ANNEX_ENTRY_FOUND' ||
    ingredient.status === 'POSSIBLE_MATCH_VERIFY' ||
    ingredient.status === 'UNIDENTIFIED'
  );
}

/** Fixed mapping from data gaps to search topics. No free text ever reaches the API. */
export function webTopicsFor(ingredient: Ingredient): string[] {
  const unknown = new Set(ingredient.unknown_fields);
  const topics: string[] = [];
  if (unknown.has('skin_irritation')) topics.push('skin irritation');
  if (unknown.has('fragrance_allergen') || !ingredient.flags.fragrance_allergen) {
    topics.push('allergy / sensitization');
  }
  if (LIMIT_FIELDS.some((field) => unknown.has(field))) topics.push('use limits');
  if (!ingredient.flags.clp_hazards) topics.push('hazard classification');
  return topics;
}
