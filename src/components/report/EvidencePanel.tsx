/** External web source review of an ingredient's dataset gaps (validated server-side). */

import React from 'react';
import { ExternalLink, FlaskConical } from 'lucide-react';
import type { EvidenceResponse } from '../../lib/api';
import { EVIDENCE_ASSESSMENT_LABELS, EVIDENCE_LABEL, SOURCE_TYPE_LABELS } from './status';

interface EvidencePanelProps {
  entry: EvidenceResponse;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ entry }) => {
  const missing = entry.endpoints.filter((endpoint) => endpoint.missing);

  return (
    <section
      aria-label="External evidence review"
      data-testid="evidence-panel"
      className="mt-4 border border-dashed border-[color:var(--web-border)] bg-[var(--web-bg)] px-4 py-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <FlaskConical size={11} aria-hidden className="text-[var(--web-muted)]" />
        <h4 className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--web-ink)]">
          External evidence review
        </h4>
        <span className="ml-auto font-mono text-[9px] uppercase tracking-[0.08em] text-[var(--web-muted)]">
          {EVIDENCE_LABEL}
        </span>
      </div>

      {entry.message && (
        <p className="mt-2 text-[11.5px] leading-relaxed text-[var(--web-muted)]">{entry.message}</p>
      )}

      {missing.map((endpoint) => (
        <div key={endpoint.field} className="mt-3 border-t border-[color:var(--web-border)] pt-3">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <p className="text-[12.5px] font-medium text-[var(--web-ink)]">{endpoint.label}</p>
            <span className="font-mono text-[9.5px] uppercase tracking-[0.06em] text-[var(--web-muted)]">
              dataset {endpoint.dataset_status}
            </span>
          </div>

          {endpoint.finding && (
            <p className="mt-1 text-[12px] leading-relaxed text-[var(--web-ink)]">{endpoint.finding}</p>
          )}

          {endpoint.assessment && (
            <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.06em] text-[var(--web-muted)]">
              {EVIDENCE_ASSESSMENT_LABELS[endpoint.assessment] ?? endpoint.assessment}
            </p>
          )}

          {endpoint.limitations && (
            <p className="mt-1 text-[10.5px] leading-relaxed text-[var(--web-muted)]">
              {endpoint.limitations}
            </p>
          )}

          {endpoint.sources.length > 0 && (
            <ul className="mt-1.5 space-y-1.5">
              {endpoint.sources.map((source) => (
                <li key={source.url} className="text-[11px] leading-snug">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-start gap-1 break-words text-[var(--web-link)] underline decoration-[color:var(--web-border)] underline-offset-4 hover:decoration-[color:var(--web-link)]"
                  >
                    <span className="min-w-0 break-words">{source.title || source.site}</span>
                    <ExternalLink size={9} className="mt-1 shrink-0" aria-hidden />
                  </a>
                  <span className="ml-1 font-mono text-[9px] uppercase tracking-[0.06em] text-[var(--web-muted)]">
                    {SOURCE_TYPE_LABELS[source.source_type] ?? 'Other'}
                    {source.site ? ` · ${source.site}` : ''} · retrieved {source.retrieved_date}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}

      {entry.conclusion && (
        <p className="mt-3 border-t border-[color:var(--web-border)] pt-2 text-[11.5px] leading-relaxed text-[var(--web-ink)]">
          {entry.conclusion}
        </p>
      )}

      <p className="mt-3 border-t border-[color:var(--web-border)] pt-2 text-[10px] leading-relaxed text-[var(--web-muted)]">
        Retrieved web sources. They never change the dataset facts, the status or the counts.
      </p>
    </section>
  );
};

export default EvidencePanel;
