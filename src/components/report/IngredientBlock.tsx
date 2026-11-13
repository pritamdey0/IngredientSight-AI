/** One ingredient: dataset facts on the left, unverified web context on the right. */

import React, { useState } from 'react';
import { ChevronDown, Info, Pencil, RotateCcw } from 'lucide-react';
import type { EvidenceResponse, Ingredient } from '../../lib/api';
import { EvidencePanel } from './EvidencePanel';
import { WebPanel } from './WebPanel';
import {
  DATASET_LABEL,
  LONG_FIELDS,
  MATCH_LABELS,
  NO_ANNEX_SENTENCE,
  STATUS_UI,
  isNoData,
  missingFieldLabels,
  needsWebPanel,
  presentFacts,
  webTopicsFor,
} from './status';
import type { WebEntry } from './useWebContext';

interface IngredientBlockProps {
  ingredient: Ingredient;
  index: number;
  name: string;
  note?: string;
  webEnabled: boolean;
  webEntry?: WebEntry;
  evidenceEntry?: EvidenceResponse;
  onNameChange: (value: string) => void;
  onRecheck: (name: string) => void;
  onLoadWeb: (includeOther: boolean) => void;
}

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p className="font-mono text-[9.5px] uppercase leading-tight tracking-[0.1em] text-[var(--report-muted)]">
    {children}
  </p>
);

const chipClass =
  'inline-flex items-center gap-1.5 border-l-2 bg-white/[0.05] px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.08em]';

export const IngredientBlock: React.FC<IngredientBlockProps> = ({
  ingredient,
  index,
  name,
  note,
  webEnabled,
  webEntry,
  evidenceEntry,
  onNameChange,
  onRecheck,
  onLoadWeb,
}) => {
  const ui = STATUS_UI[ingredient.status];
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const facts = presentFacts(ingredient);
  const missing = missingFieldLabels(ingredient);
  const showsWeb = needsWebPanel(ingredient);
  const topics = webTopicsFor(ingredient);
  const dirty = name.trim() !== ingredient.input_name;
  const flags = ingredient.flags;

  const identity: { label: string; value: string }[] = [];
  if (!isNoData(ingredient.chemical_name)) identity.push({ label: 'Chemical name', value: ingredient.chemical_name as string });
  if (!isNoData(ingredient.cas_number)) identity.push({ label: 'CAS number', value: ingredient.cas_number as string });
  if (!isNoData(ingredient.ec_number)) identity.push({ label: 'EC number', value: ingredient.ec_number as string });
  const sourceLinks = ingredient.dataset_links ?? [];
  const showsIdentity = identity.length > 0 || sourceLinks.length > 0;

  return (
    <article
      data-testid="ingredient-block"
      className={`report-block border-l-2 ${ui.rule} px-5 py-5 transition-colors hover:bg-white/[0.025] sm:px-7`}
    >
      <div className={showsWeb ? 'grid gap-6 min-[900px]:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]' : ''}>
        <div className="min-w-0">
          <header className="flex flex-wrap items-start gap-3">
            <span className="mt-1 font-mono text-[10.5px] leading-none text-[var(--report-muted)]">
              {String(index).padStart(2, '0')}
            </span>
            <div className="min-w-0 flex-1">
              <h3 className="break-words text-[19px] font-medium leading-snug tracking-tight text-[var(--report-ink)]">
                {ingredient.input_name}
              </h3>
              <p className="mt-1 break-words font-mono text-[10px] uppercase leading-relaxed tracking-[0.08em] text-[var(--report-muted)]">
                {MATCH_LABELS[ingredient.match_type] ?? ingredient.match_type}
                {ingredient.match_score !== null && ingredient.match_type.startsWith('fuzzy')
                  ? ` (${ingredient.match_score.toFixed(0)})`
                  : ''}
                {' / '}
                <span className="text-[var(--report-ink-strong)]">{ingredient.matched_name}</span>
              </p>
            </div>
            <span
              className={`inline-flex shrink-0 items-center gap-1.5 border-l-2 px-2 py-1 font-mono text-[9.5px] uppercase leading-none tracking-[0.1em] ${ui.badge}`}
            >
              <ui.Icon size={11} aria-hidden />
              {ui.label}
            </span>
          </header>

          <p className="mt-3 max-w-2xl text-[13.5px] leading-relaxed text-[var(--report-ink-strong)]">
            {ui.sentence}
          </p>

          {note && (
            <p className="mt-2 border-l border-[color:var(--report-border)] pl-3 text-[12px] leading-relaxed text-[var(--report-muted)]">
              {note}
            </p>
          )}

          {showsIdentity && (
            <div className="mt-3">
              <Label>Identity / {DATASET_LABEL}</Label>
              <ul className="mt-1 space-y-0.5">
                {identity.map((item) => (
                  <li key={item.label} className="font-mono text-[10.5px] leading-relaxed text-[var(--report-muted)]">
                    <span className="text-[var(--report-ink-strong)]">{item.label}</span> / {item.value}
                  </li>
                ))}
                {sourceLinks.map((link) => (
                  <li key={link.url}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-[10.5px] leading-relaxed text-[var(--web-link)] underline decoration-[color:var(--web-border)] underline-offset-4 hover:decoration-[color:var(--web-link)]"
                    >
                      Official source / {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {facts.map((fact) => {
              const isLong = LONG_FIELDS.has(fact.field);
              return (
                <div key={fact.field} className="min-w-0">
                  <Label>{fact.label}</Label>
                  <p
                    className={`mt-1 whitespace-pre-line break-words text-[13.5px] font-medium leading-relaxed text-[var(--report-ink)] ${
                      isLong && !expanded ? 'line-clamp-4' : ''
                    }`}
                  >
                    {fact.value}
                  </p>
                </div>
              );
            })}
          </div>

          {facts.some((fact) => LONG_FIELDS.has(fact.field)) && (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="mt-2 inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--report-muted)] underline decoration-white/25 underline-offset-4 hover:text-[var(--report-ink)] print:hidden"
            >
              <ChevronDown size={10} className={expanded ? 'rotate-180' : ''} aria-hidden />
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}

          {(flags.cmr || flags.fragrance_allergen) && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {flags.cmr && (
                <span className={`${chipClass} border-l-[color:var(--status-restricted)] text-[var(--status-restricted-ink)]`}>
                  CMR {flags.cmr.categories}
                  {flags.cmr.note ? ` / ${flags.cmr.note}` : ''}
                </span>
              )}
              {flags.fragrance_allergen && (
                <span className={`${chipClass} border-l-[color:var(--web-border)] text-[var(--report-ink)]`}>
                  <Info size={10} aria-hidden />
                  Fragrance allergen / {flags.fragrance_allergen.requirement}
                </span>
              )}
            </div>
          )}

          {flags.clp_hazards && flags.clp_hazards.length > 0 && (
            <div className="mt-3">
              <Label>CLP hazard statements</Label>
              <ul className="mt-1.5 flex flex-wrap gap-1.5">
                {flags.clp_hazards.map((hazard) => (
                  <li
                    key={hazard.code}
                    className="border-l border-white/20 pl-2 text-[11px] leading-relaxed text-[var(--report-ink-strong)]"
                  >
                    <span className="font-mono text-[10px] font-semibold text-[var(--report-ink)]">
                      {hazard.code}
                    </span>{' '}
                    {hazard.text}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {flags.sccs && (
            <div className="mt-3">
              <Label>SCCS opinion / {flags.sccs.document}</Label>
              <p
                className={`mt-1 whitespace-pre-line text-[12px] leading-relaxed text-[var(--report-ink-strong)] ${
                  expanded ? '' : 'line-clamp-4'
                }`}
              >
                {flags.sccs.conclusion}
              </p>
            </div>
          )}

          {flags.unconfirmed && (
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.08em] text-[var(--report-muted)]">
              Flags unconfirmed / match not confirmed
            </p>
          )}

          {ingredient.status === 'NO_ANNEX_ENTRY_FOUND' && (
            <p className="mt-3 text-[12.5px] leading-relaxed text-[var(--report-muted)]">
              {NO_ANNEX_SENTENCE}
            </p>
          )}

          {missing.length > 0 && (
            <p className="mt-2 text-[12.5px] leading-relaxed text-[var(--report-muted)]">
              <span className="font-medium text-[var(--report-ink)]">No data in dataset</span> for:{' '}
              {missing.join(', ')}.
            </p>
          )}

          {evidenceEntry &&
            (evidenceEntry.endpoints.some((endpoint) => endpoint.missing) ||
              Boolean(evidenceEntry.message)) && <EvidencePanel entry={evidenceEntry} />}

          {ingredient.candidates.length > 0 && (
            <div className="mt-3">
              <Label>Candidates to verify</Label>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {ingredient.candidates.map((candidate) => (
                  <button
                    key={candidate.name}
                    type="button"
                    onClick={() => onRecheck(candidate.name)}
                    title="Re-check with this name"
                    className="border-l-2 border-l-[color:var(--status-verify)] bg-white/[0.05] px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.06em] text-[var(--status-verify)] transition-colors hover:bg-[var(--status-verify)] hover:text-[var(--report-bg)]"
                  >
                    {candidate.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 print:hidden">
            <button
              type="button"
              onClick={() => setEditing((value) => !value)}
              className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--report-muted)] underline decoration-white/25 underline-offset-4 hover:text-[var(--report-ink)]"
              aria-expanded={editing}
            >
              <Pencil size={10} aria-hidden />
              {editing ? 'Close' : 'Edit name'}
            </button>
            {editing && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <input
                  value={name}
                  onChange={(event) => onNameChange(event.target.value)}
                  aria-label="Correct the ingredient name"
                  className="min-w-0 flex-1 border border-white/20 bg-black/40 px-2.5 py-1.5 font-mono text-[12px] text-[var(--report-ink)] focus:border-white/50"
                />
                <button
                  type="button"
                  onClick={() => onRecheck(name)}
                  disabled={!dirty || !name.trim()}
                  className="inline-flex items-center gap-1.5 border border-white/25 bg-white/10 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-white transition-colors hover:bg-white/20 disabled:opacity-40"
                >
                  <RotateCcw size={10} aria-hidden /> Re-check
                </button>
              </div>
            )}
          </div>

          <details className="mt-4 break-words">
            <summary className="flex cursor-pointer items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-[var(--report-muted)] hover:text-[var(--report-ink)]">
              <ChevronDown size={10} aria-hidden />
              Sources / {ingredient.sources.length}
            </summary>
            <ul className="mt-2 space-y-1.5 border-l border-[color:var(--report-border)] pl-3">
              {ingredient.sources.map((source, position) => (
                <li
                  key={`${source.field}-${position}`}
                  className="font-mono text-[10px] leading-relaxed text-[var(--report-muted)]"
                >
                  <span className="text-[var(--report-ink-strong)]">{source.field}</span> /{' '}
                  {source.source} / {source.reference} / snapshot {source.snapshot} / dataset{' '}
                  {source.dataset_version}
                </li>
              ))}
              {ingredient.sources.length === 0 && (
                <li className="font-mono text-[10px] text-[var(--report-muted)]">No data in dataset.</li>
              )}
            </ul>
          </details>
        </div>

        {showsWeb && (
          <WebPanel topics={topics} available={webEnabled} entry={webEntry} onLoad={onLoadWeb} />
        )}
      </div>
    </article>
  );
};

export default IngredientBlock;
