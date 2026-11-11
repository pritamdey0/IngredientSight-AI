/** Right column of an ingredient block: unverified web context, loaded on click. */

import React from 'react';
import { ExternalLink, Globe, Info, Loader2, Search } from 'lucide-react';
import { SOURCE_TYPE_LABELS } from './status';
import type { WebEntry } from './useWebContext';

interface WebPanelProps {
  topics: string[];
  available: boolean;
  entry?: WebEntry;
  onLoad: (includeOther: boolean) => void;
}

export const WebPanel: React.FC<WebPanelProps> = ({ topics, available, entry, onLoad }) => {
  const includeOther = entry?.includeOther ?? false;
  const loading = entry?.state === 'loading';
  const items = entry?.data?.items ?? [];
  const message = entry?.data?.message;

  return (
    <aside
      aria-label="Web context, unverified"
      data-testid="web-panel"
      className={`h-fit min-w-0 border border-dashed border-[color:var(--web-border)] bg-[var(--web-bg)] px-4 py-4 text-[var(--web-ink)] ${
        entry?.state === 'done' ? '' : 'print:hidden'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Globe size={11} aria-hidden />
          <h3 className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--web-ink)]">
            Web context
          </h3>
        </div>
        <span className="font-mono text-[9.5px] uppercase tracking-[0.08em] text-[var(--web-muted)]">
          unverified
        </span>
      </div>
      <p className="mt-1.5 text-[10.5px] leading-relaxed text-[var(--web-muted)]">
        Unverified, not part of the assessment
      </p>

      {!available ? (
        <p className="mt-3 text-[12px] leading-relaxed text-[var(--web-muted)]">
          Web context is not configured on this server.
        </p>
      ) : (
        <>
          <p className="mt-3 border-t border-[color:var(--web-border)] pt-3 text-[11.5px] leading-relaxed text-[var(--web-muted)]">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.1em]">Searched for: </span>
            <span className="text-[var(--web-ink)]">{topics.join(', ') || 'the missing data'}</span>
          </p>

          <div className="mt-2.5 flex flex-wrap items-center gap-2 print:hidden">
            <button
              type="button"
              onClick={() => onLoad(includeOther)}
              disabled={loading}
              className="inline-flex items-center gap-1.5 border border-white/20 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--web-ink)] transition-colors hover:border-white/45 hover:bg-white/5 disabled:opacity-50"
            >
              {loading ? <Loader2 size={10} className="animate-spin" /> : <Search size={10} />}
              {loading ? 'Searching…' : entry?.state === 'done' ? 'Search again' : 'Load web sources'}
            </button>
            {entry?.state === 'done' && (
              <label className="inline-flex cursor-pointer items-center gap-1.5 text-[10.5px] text-[var(--web-muted)]">
                <input
                  type="checkbox"
                  checked={includeOther}
                  onChange={(event) => onLoad(event.target.checked)}
                  className="h-3 w-3 accent-[var(--report-focus)]"
                />
                Show consumer and retailer sources
              </label>
            )}
          </div>

          {includeOther && entry?.state === 'done' && (
            <p className="mt-1.5 flex items-start gap-1.5 text-[10.5px] leading-relaxed text-[var(--web-muted)]">
              <Info size={10} className="mt-0.5 shrink-0" aria-hidden />
              individual experiences and marketing, not evidence of safety or harm
            </p>
          )}

          {entry?.state === 'error' && (
            <p className="mt-3 text-[11.5px] leading-relaxed text-[var(--status-error)]">{entry.error}</p>
          )}

          {entry?.state === 'done' && items.length === 0 && (
            <p className="mt-3 text-[11.5px] leading-relaxed text-[var(--web-muted)]">
              {message || 'No reliable web sources found'}
            </p>
          )}

          {entry?.state === 'done' && items.length > 0 && (
            <ul className="mt-3 space-y-3">
              {items.map((item) => (
                <li key={item.url} className="border-t border-[color:var(--web-border)] pt-3 first:border-t-0 first:pt-0">
                  <div className="flex flex-wrap items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.08em] text-[var(--web-muted)]">
                    <span className="border border-[color:var(--web-border)] px-1 py-0.5">
                      {SOURCE_TYPE_LABELS[item.source_type] ?? 'Other'}
                    </span>
                    <span className="min-w-0 max-w-full truncate">{item.site}</span>
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 flex items-start gap-1 text-[12px] font-medium leading-snug text-[var(--web-link)] underline decoration-[color:var(--web-border)] underline-offset-4 hover:decoration-[color:var(--web-link)]"
                  >
                    <span className="min-w-0 break-words">{item.title || item.site}</span>
                    <ExternalLink size={9} className="mt-1 shrink-0" aria-hidden />
                  </a>
                  <p className="mt-1 break-words text-[11.5px] leading-relaxed text-[var(--web-ink)]">
                    “{item.excerpt}”
                  </p>
                  <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.08em] text-[var(--web-muted)]">
                    retrieved {item.retrieved_date}
                  </p>
                </li>
              ))}
            </ul>
          )}

          {entry?.state === 'done' && (
            <p className="mt-3 border-t border-[color:var(--web-border)] pt-2 text-[10px] leading-relaxed text-[var(--web-muted)]">
              Verbatim excerpts. They never change the dataset facts, the status or the counts.
            </p>
          )}
        </>
      )}
    </aside>
  );
};

export default WebPanel;
