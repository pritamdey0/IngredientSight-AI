/** The whole result in ONE sheet: header, disclaimer, ledger, blocks, footer. */

import React, { useEffect, useMemo, useState } from 'react';
import { Download, FileJson, FileText, Globe, Loader2, Printer, TriangleAlert } from 'lucide-react';
import type { Analysis } from '../../lib/api';
import { downloadFile, renderReport } from '../../lib/api';
import { IngredientBlock } from './IngredientBlock';
import { SUMMARY_CHIPS, STATUS_UI, needsWebPanel, webTopicsFor } from './status';
import { useWebContext } from './useWebContext';

interface ReportCardProps {
  result: Analysis;
  names: string[];
  webEnabled: boolean;
  onNameChange: (index: number, value: string) => void;
  onRecheck: (index: number, value: string) => void;
}

function fileSlug(result: Analysis): string {
  const base = (result.product_name || 'ingredient-report')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  const stamp = new Date().toISOString().slice(0, 16).replace(/[:t]/gi, '-');
  return `${base || 'ingredient-report'}-${stamp}`;
}

const toolClass =
  'inline-flex items-center gap-1.5 border border-white/15 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--report-muted)] transition-colors hover:border-white/40 hover:text-[var(--report-ink)] disabled:opacity-50';

export const ReportCard: React.FC<ReportCardProps> = ({
  result,
  names,
  webEnabled,
  onNameChange,
  onRecheck,
}) => {
  const web = useWebContext();
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<'md' | 'json' | null>(null);
  const summary = result.summary;

  useEffect(() => {
    web.reset();
    setMessage(null);
    // A new analysis starts with empty panels; cached searches are reused.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  const pendingRequests = useMemo(
    () =>
      result.ingredients
        .filter(needsWebPanel)
        .map((ingredient) => ({ name: ingredient.input_name, topics: webTopicsFor(ingredient) })),
    [result.ingredients],
  );

  const loadedWeb = web.loaded();
  const hasWeb = Object.keys(loadedWeb).length > 0;
  const batch = web.batch;

  const downloadJson = () => {
    const payload = hasWeb ? { ...result, web_context: loadedWeb } : result;
    downloadFile(`${fileSlug(result)}.json`, JSON.stringify(payload, null, 2), 'application/json');
  };

  const downloadMarkdown = async () => {
    setBusy('md');
    setMessage(null);
    try {
      const payload = hasWeb
        ? await renderReport(result, loadedWeb)
        : { markdown_report: result.markdown_report };
      downloadFile(`${fileSlug(result)}.md`, payload.markdown_report, 'text/markdown');
    } catch {
      downloadFile(`${fileSlug(result)}.md`, result.markdown_report, 'text/markdown');
      setMessage('The report was downloaded without the web panel: the server could not re-render it.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <article
      data-testid="report-card"
      className="report-card border border-white/15 bg-[var(--report-glass)] text-[var(--report-ink)] backdrop-blur-xl print:backdrop-blur-none"
    >
      {/* A. Header */}
      <header className="flex flex-wrap items-start justify-between gap-6 border-b border-[color:var(--report-rule)] px-5 py-5 sm:px-7">
        <div className="min-w-0">
          <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-[var(--report-muted)]">
            Regulatory lookup / dataset only
          </p>
          <h2 className="mt-2 text-[27px] font-normal leading-none tracking-tight text-[var(--report-ink)]">
            Ingredient report
          </h2>
          {result.product_name && (
            <p className="mt-2.5 text-[13px] text-[var(--report-ink-strong)]">{result.product_name}</p>
          )}
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--report-muted)]">
            Dataset {result.dataset.version ?? 'No data in dataset'} / snapshot{' '}
            {result.dataset.snapshot ?? 'No data in dataset'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 print:hidden">
          <button type="button" onClick={() => void downloadMarkdown()} disabled={busy !== null} className={toolClass}>
            {busy === 'md' ? <Loader2 size={11} className="animate-spin" /> : <FileText size={11} aria-hidden />}
            Download .md
          </button>
          <button type="button" onClick={downloadJson} className={toolClass}>
            <FileJson size={11} aria-hidden />
            Download .json
          </button>
          <button type="button" onClick={() => window.print()} className={toolClass}>
            <Printer size={11} aria-hidden />
            Print
          </button>
        </div>
      </header>

      {/* B. Disclaimer, always visible and never shortened */}
      <div className="border-l-2 border-[color:var(--notice-border)] bg-[var(--notice-bg)] px-5 py-3.5 sm:px-7">
        <p className="font-mono text-[9.5px] uppercase tracking-[0.15em] text-[var(--notice-ink)]">
          Disclaimer
        </p>
        <p className="mt-1.5 text-[12px] leading-relaxed text-[var(--report-ink-strong)]">
          {result.disclaimer}
        </p>
      </div>

      {/* C. Counts, as one mono line of dots and numbers, never as stat cards */}
      <section className="px-5 py-5 sm:px-7">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.15em] text-[var(--report-muted)]">
            Counts / {summary.total} {summary.total === 1 ? 'ingredient' : 'ingredients'} checked
          </h3>
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--report-muted)]">
            No score
          </span>
        </div>

        <ul className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2.5 border-t border-[color:var(--report-rule)] pt-4">
          {SUMMARY_CHIPS.map((chip) => {
            const value = summary[chip.key];
            const ui = STATUS_UI[chip.status];
            return (
              <li key={chip.key} className="flex items-center gap-2">
                <span aria-hidden className={`h-1.5 w-1.5 shrink-0 ${ui.dot}`} />
                <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-[var(--report-muted)]">
                  {chip.label}
                </span>
                <span
                  className={`text-[15px] leading-none tabular-nums ${
                    value === 0 ? 'text-[var(--report-muted)]' : 'text-[var(--report-ink)]'
                  }`}
                >
                  {value}
                </span>
              </li>
            );
          })}
        </ul>

        <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--report-muted)]">
          {summary.cmr_flagged} CMR {summary.cmr_flagged === 1 ? 'flag' : 'flags'} &middot;{' '}
          {summary.fragrance_allergens} fragrance allergen{' '}
          {summary.fragrance_allergens === 1 ? 'label' : 'labels'}
        </p>

        {result.friendly_summary?.intro && (
          <div className="mt-4 border-l border-[color:var(--report-border)] pl-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--report-muted)]">
              AI-written summary of the data below
            </p>
            <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--report-ink-strong)]">
              {result.friendly_summary.intro}
            </p>
          </div>
        )}

        {result.warnings.length > 0 && (
          <ul className="mt-4 space-y-1 border-l-2 border-[color:var(--status-error)] pl-3">
            {result.warnings.map((warning) => (
              <li key={warning} className="flex items-start gap-1.5 text-[12px] leading-relaxed text-[var(--status-error)]">
                <TriangleAlert size={11} className="mt-1 shrink-0" aria-hidden />
                {warning}
              </li>
            ))}
          </ul>
        )}

        {message && <p className="mt-3 text-[12px] text-[var(--status-error)]">{message}</p>}
      </section>

      {/* Web-context toolbar */}
      {pendingRequests.length > 0 && webEnabled && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--report-rule)] px-5 py-3 sm:px-7 print:hidden">
          <button
            type="button"
            onClick={() => void web.loadMany(pendingRequests, false)}
            disabled={batch?.running ?? false}
            className={toolClass}
          >
            {batch?.running ? <Loader2 size={11} className="animate-spin" /> : <Globe size={11} aria-hidden />}
            Load web sources for all ingredients with missing data
          </button>
          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--report-muted)]">
            {batch
              ? batch.total === 0
                ? 'Already loaded'
                : `${batch.running ? 'Searching' : 'Searched'} ${batch.done} of ${batch.total} / max 6 per click`
              : 'Off by default / never changes the facts'}
          </span>
        </div>
      )}

      {/* D. Ingredients, inside the same sheet */}
      <section className="border-t border-[color:var(--report-rule)]">
        <div className="flex items-baseline justify-between gap-3 px-5 pb-3 pt-5 sm:px-7">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.15em] text-[var(--report-muted)]">
            Ingredients / severity order
          </h3>
          <span className="font-mono text-[10px] tabular-nums text-[var(--report-muted)]">
            {result.ingredients.length.toString().padStart(2, '0')}
          </span>
        </div>
        <div className="divide-y divide-[color:var(--report-rule)] border-t border-[color:var(--report-rule)]">
          {result.ingredients.map((ingredient, index) => (
            <IngredientBlock
              key={`${ingredient.input_name}-${index}`}
              ingredient={ingredient}
              index={index + 1}
              name={names[index] ?? ingredient.input_name}
              note={result.friendly_summary?.notes[ingredient.input_name]}
              webEnabled={webEnabled}
              webEntry={web.entries[ingredient.input_name]}
              onNameChange={(value) => onNameChange(index, value)}
              onRecheck={(value) => onRecheck(index, value)}
              onLoadWeb={(includeOther) =>
                void web.load(ingredient.input_name, webTopicsFor(ingredient), includeOther)
              }
            />
          ))}
        </div>
      </section>

      {result.may_contain.length > 0 && (
        <section className="border-t border-[color:var(--report-rule)] px-5 py-4 sm:px-7">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.15em] text-[var(--report-muted)]">
            May contain
          </h3>
          <p className="mt-2 text-[12.5px] leading-relaxed text-[var(--report-ink-strong)]">
            {result.may_contain.join(', ')}
          </p>
          <p className="mt-1 text-[11px] text-[var(--report-muted)]">
            Listed separately and not analysed.
          </p>
        </section>
      )}

      {result.ocr_text && (
        <details className="border-t border-[color:var(--report-rule)] px-5 py-4 sm:px-7">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[0.12em] text-[var(--report-muted)]">
            Text read from the image
          </summary>
          <p className="mt-2 whitespace-pre-line font-mono text-[11.5px] leading-relaxed text-[var(--report-muted)]">
            {result.ocr_text}
          </p>
        </details>
      )}

      {/* E. Footer, same sheet */}
      <footer className="border-t border-[color:var(--report-rule)] px-5 py-4 sm:px-7">
        <p className="text-[11.5px] leading-relaxed text-[var(--report-muted)]">
          Every value above comes from the dataset or reads “No data in dataset”. Nothing is inferred
          from concentration, packaging or web text, and no overall score is produced.
        </p>
        <p className="mt-1.5 flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.1em] text-[var(--report-muted)] print:hidden">
          <Download size={10} aria-hidden />
          .md and .json hold the same facts as this sheet
        </p>
      </footer>
    </article>
  );
};

export default ReportCard;
