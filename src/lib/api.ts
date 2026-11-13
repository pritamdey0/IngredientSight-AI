/** Single place that talks to the FastAPI backend. */

export type Status =
  | 'PROHIBITED'
  | 'RESTRICTED'
  | 'PERMITTED_WITH_LIMITS'
  | 'POSSIBLE_MATCH_VERIFY'
  | 'NO_ANNEX_ENTRY_FOUND'
  | 'UNIDENTIFIED';

export type MatchType =
  | 'exact_name'
  | 'synonym'
  | 'cas'
  | 'fuzzy_high'
  | 'fuzzy_possible'
  | 'group_entry'
  | 'none';

export interface Source {
  field: string;
  source: string;
  reference: string;
  snapshot: string;
  dataset_version: string;
}

export interface Candidate {
  name: string;
  score: number | null;
}

export interface DatasetLink {
  label: string;
  url: string;
}

export interface ClpHazard {
  code: string;
  text: string;
}

export interface IngredientFlags {
  cmr?: { categories: string; note: string | null };
  fragrance_allergen?: { requirement: string };
  clp_hazards?: ClpHazard[];
  sccs?: { conclusion: string; document: string };
  unconfirmed?: boolean;
}

export interface Ingredient {
  input_name: string;
  matched_name: string;
  match_type: MatchType;
  match_score: number | null;
  status: Status;
  annex: string;
  reference_number: string;
  permitted_list: string;
  limits: Record<string, string>;
  skin_irritation: string;
  flags: IngredientFlags;
  unknown_fields: string[];
  sources: Source[];
  candidates: Candidate[];
  // Dataset identity (FROM DATASET).
  chemical_name?: string;
  cas_number?: string;
  ec_number?: string;
  annex_title?: string;
  toxicity_class?: string;
  allergy_risk?: string;
  echa_hazard_classes?: string;
  regulation_basis?: string;
  source_url?: string | null;
  dataset_links?: DatasetLink[];
}

export interface Summary {
  total: number;
  prohibited: number;
  restricted: number;
  permitted_with_limits: number;
  cmr_flagged: number;
  fragrance_allergens: number;
  no_annex_entry_found: number;
  possible_match_verify: number;
  unidentified: number;
}

export interface FriendlySummary {
  intro: string | null;
  notes: Record<string, string>;
}

export interface Analysis {
  disclaimer: string;
  dataset: { version: string | null; snapshot: string | null };
  summary: Summary;
  ingredients: Ingredient[];
  may_contain: string[];
  warnings: string[];
  product_name?: string | null;
  markdown_report: string;
  friendly_summary: FriendlySummary | null;
  ocr_text?: string;
}

export interface WebContextItem {
  title: string;
  site: string;
  url: string;
  retrieved_date: string;
  source_type: 'official_scientific' | 'retailer_brand' | 'review' | 'blog_forum' | 'other';
  excerpt: string;
}

export interface WebContext {
  enabled: boolean;
  items: WebContextItem[];
  message: string | null;
  notice: string | null;
  include_other: boolean | null;
  topics: string[];
}

export interface WebBatchResponse {
  enabled: boolean;
  results: Record<string, WebContext>;
}

/** One retrieved source, listed verbatim. Never a dataset record. */
export interface EvidenceSource {
  title: string;
  site: string;
  publisher: string;
  url: string;
  source_type: string;
  retrieved_date: string;
  excerpt: string;
}

/** One toxicological endpoint: the dataset's value plus any web review. */
export interface EvidenceEndpoint {
  field: string;
  label: string;
  dataset_status: string;
  dataset_value?: string | null;
  missing: boolean;
  finding?: string | null;
  assessment?: string | null;
  limitations?: string | null;
  evidence_label?: string | null;
  sources: EvidenceSource[];
}

export interface EvidenceResponse {
  enabled: boolean;
  researched: boolean;
  ingredient: string;
  message?: string | null;
  conclusion?: string | null;
  endpoints: EvidenceEndpoint[];
}

export interface EvidenceBatchResponse {
  enabled: boolean;
  results: Record<string, EvidenceResponse>;
  product_summary?: string | null;
}

export type WebTopic =
  | 'skin irritation'
  | 'eye irritation'
  | 'skin sensitization'
  | 'toxicity'
  | 'allergy / sensitization'
  | 'use limits'
  | 'hazard classification';

export interface Health {
  status: string;
  dataset_loaded: boolean;
  dataset_rows: number;
  dataset_version: string | null;
  source_snapshot: string | null;
  ocr_available: boolean;
  llm_enabled: boolean;
  web_context_enabled: boolean;
  evidence_enabled: boolean;
}

const BASE_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '');

async function request<T>(path: string, init: RequestInit, timeoutMs = 60_000): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch {
    window.clearTimeout(timer);
    throw new Error('The server could not be reached. Please try again.');
  }
  window.clearTimeout(timer);

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload && typeof payload.detail === 'string' ? payload.detail : null;
    throw new Error(detail ?? `Request failed (${response.status}).`);
  }
  return payload as T;
}

export function analyze(
  text: string,
  productName: string,
  includeSummary: boolean,
): Promise<Analysis> {
  return request<Analysis>('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, product_name: productName || null, include_summary: includeSummary }),
  });
}

export function analyzeImage(file: File, productName: string): Promise<Analysis> {
  const body = new FormData();
  body.append('file', file);
  if (productName) body.append('product_name', productName);
  return request<Analysis>('/api/analyze-image', { method: 'POST', body }, 120_000);
}

export function recheck(ingredients: string[], productName: string): Promise<Analysis> {
  return request<Analysis>('/api/match', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ingredients, product_name: productName || null }),
  });
}

export function searchWeb(
  ingredient: string,
  topics: string[],
  includeOther: boolean,
): Promise<WebContext> {
  return request<WebContext>('/api/web-context', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ingredient, topics, include_other: includeOther }),
  });
}

/** One click, up to six ingredients; the server spaces the provider calls out. */
export function searchWebBatch(
  items: { ingredient: string; topics: string[] }[],
  includeOther: boolean,
): Promise<WebBatchResponse> {
  return request<WebBatchResponse>('/api/web-context/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, include_other: includeOther }),
  }, 120_000);
}

/** Re-render the template Markdown report with the panels the user loaded. */
export function renderReport(
  analysis: Analysis,
  webContext: Record<string, WebContext>,
  evidence?: Record<string, EvidenceResponse>,
  productSummary?: string | null,
): Promise<{ markdown_report: string }> {
  return request<{ markdown_report: string }>('/api/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis,
      web_context: webContext,
      evidence: evidence ?? {},
      product_summary: productSummary ?? null,
    }),
  });
}

/**
 * Automatically research the dataset gaps of every ingredient in one call.
 * The server only ever adds findings; it never changes a dataset record.
 */
export function researchEvidenceBatch(
  analysis: Analysis,
  includeProductSummary = true,
): Promise<EvidenceBatchResponse> {
  return request<EvidenceBatchResponse>('/api/evidence/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ analysis, include_product_summary: includeProductSummary }),
  }, 180_000);
}

export function health(): Promise<Health> {
  return request<Health>('/api/health', { method: 'GET' }, 15_000);
}

export function downloadFile(filename: string, content: string, type: string): void {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
