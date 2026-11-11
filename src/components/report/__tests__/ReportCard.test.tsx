/** Render checks for the single-card report layout (spec: structure, No data, web panel). */

import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import type { Analysis, Ingredient, WebContext } from '../../../lib/api';
import { ReportCard } from '../ReportCard';

const mocks = vi.hoisted(() => ({
  downloadFile: vi.fn(),
  renderReport: vi.fn(async () => ({ markdown_report: '# Ingredient report\n' })),
  searchWeb: vi.fn(),
  searchWebBatch: vi.fn(),
}));

vi.mock('../../../lib/api', () => ({
  downloadFile: mocks.downloadFile,
  renderReport: mocks.renderReport,
  searchWeb: mocks.searchWeb,
  searchWebBatch: mocks.searchWebBatch,
}));

const DISCLAIMER =
  'This dataset view is informational only. It is not a safety assessment, it never infers safety from concentration, and it produces no score.';

function prohibited(): Ingredient {
  return {
    input_name: 'Benzidine',
    matched_name: 'Benzidine',
    match_type: 'exact_name',
    match_score: 100,
    status: 'PROHIBITED',
    annex: 'II',
    reference_number: '1',
    permitted_list: 'No data in dataset',
    limits: {},
    skin_irritation: 'No data in dataset',
    flags: { cmr: { categories: '1A', note: null } },
    unknown_fields: ['permitted_list', 'skin_irritation'],
    sources: [],
    candidates: [],
  };
}

function fullyPopulated(): Ingredient {
  return {
    input_name: 'Glycerin',
    matched_name: 'Glycerin',
    match_type: 'exact_name',
    match_score: 100,
    status: 'PERMITTED_WITH_LIMITS',
    annex: 'IV',
    reference_number: '1',
    permitted_list: 'Yes',
    limits: { max_concentration_pct: '95' },
    skin_irritation: 'Not irritant in the dataset entry',
    flags: {},
    unknown_fields: [],
    sources: [],
    candidates: [],
  };
}

function analysis(ingredients: Ingredient[]): Analysis {
  return {
    disclaimer: DISCLAIMER,
    dataset: { version: 'v1', snapshot: '2026-01-01' },
    summary: {
      total: ingredients.length,
      prohibited: ingredients.filter((item) => item.status === 'PROHIBITED').length,
      restricted: 0,
      permitted_with_limits: ingredients.filter((item) => item.status === 'PERMITTED_WITH_LIMITS').length,
      cmr_flagged: ingredients.filter((item) => item.flags.cmr).length,
      fragrance_allergens: 0,
      no_annex_entry_found: 0,
      possible_match_verify: 0,
      unidentified: 0,
    },
    ingredients,
    may_contain: [],
    warnings: [],
    product_name: 'Test cream',
    markdown_report: '# Ingredient report\n',
    friendly_summary: null,
  };
}

function webContext(): WebContext {
  return {
    enabled: true,
    items: [
      {
        title: 'Annex II entry',
        site: 'eur-lex.europa.eu',
        url: 'https://eur-lex.europa.eu/example',
        retrieved_date: '2026-11-11',
        source_type: 'official_scientific',
        excerpt: 'Benzidine is prohibited in cosmetic products under Annex II.',
      },
    ],
    message: null,
    notice: 'Unverified, not part of the assessment',
    include_other: false,
    topics: ['skin irritation'],
  };
}

function renderCard(ingredients: Ingredient[]) {
  const result = render(
    <ReportCard
      result={analysis(ingredients)}
      names={ingredients.map((item) => item.input_name)}
      webEnabled
      onNameChange={() => undefined}
      onRecheck={() => undefined}
    />,
  );
  return { ...result, card: screen.getByTestId('report-card') };
}

function columnWrapper(block: HTMLElement): HTMLElement {
  return block.children[0] as HTMLElement;
}

beforeEach(() => {
  cleanup();
  mocks.downloadFile.mockReset();
  mocks.renderReport.mockClear();
  mocks.searchWeb.mockReset();
  mocks.searchWebBatch.mockReset();
});

describe('report card shell', () => {
  it('renders one single card containing every ingredient block and the footer', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    expect(screen.getAllByTestId('report-card')).toHaveLength(1);
    expect(within(card).getAllByTestId('ingredient-block')).toHaveLength(2);
    expect(within(card).getByRole('heading', { name: 'Ingredient report' })).toBeInTheDocument();
    expect(within(card).getByText(DISCLAIMER)).toBeInTheDocument();
    expect(card.textContent).toContain('no overall score is produced');
  });
});

describe('ingredient blocks', () => {
  it('uses two columns and a web panel when a field has no data', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const blocks = within(card).getAllByTestId('ingredient-block');
    const withGap = blocks[0];

    expect(columnWrapper(withGap).className).toContain('min-[900px]:grid-cols-');
    expect(within(withGap).getByTestId('web-panel')).toBeInTheDocument();
  });

  it('keeps a fully populated ingredient in one column without a web panel', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const blocks = within(card).getAllByTestId('ingredient-block');
    const complete = blocks[1];

    expect(columnWrapper(complete).className).not.toContain('min-[900px]:grid-cols-');
    expect(within(complete).queryByTestId('web-panel')).toBeNull();
  });

  it('says "No data in dataset" once for the missing fields, in one line', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const withGap = within(card).getAllByTestId('ingredient-block')[0];

    expect(within(withGap).getByText('No data in dataset')).toBeInTheDocument();
    expect(withGap.textContent).toContain('for: positive list, skin irritation.');
    // The gaps are summarised once, not repeated as empty fact rows.
    expect(withGap.textContent?.match(/No data in dataset/g)).toHaveLength(2); // + the empty Sources list
  });

  it('keeps every block free of judgement words and green styling', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const disclaimer = Array.from(card.querySelectorAll('p')).find(
      (node) => node.textContent === DISCLAIMER,
    );

    for (const element of Array.from(card.querySelectorAll('*'))) {
      const className = element.getAttribute('class') ?? '';
      expect(className).not.toMatch(/\b(bg|text|border)-(green|emerald|lime|teal)/);
    }

    const leaves = Array.from(card.querySelectorAll('*')).filter(
      (element) => element.children.length === 0 && !disclaimer?.contains(element),
    );
    for (const element of leaves) {
      expect(element.textContent ?? '').not.toMatch(/\b(safe|harmless|suitable)\b/i);
    }
  });
});

describe('web context', () => {
  it('shows no web items until the user loads them', () => {
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const panel = within(card).getByTestId('web-panel');

    expect(panel.textContent).not.toContain('eur-lex.europa.eu');
    expect(within(panel).getByRole('button', { name: /Load web sources/ })).toBeInTheDocument();
    expect(panel.textContent).toContain('Searched for: skin irritation, allergy / sensitization');
  });

  it('renders verbatim items after a click and never changes the dataset text', async () => {
    mocks.searchWeb.mockResolvedValue(webContext());
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const block = within(card).getAllByTestId('ingredient-block')[0];
    const leftColumn = () => columnWrapper(block).children[0] as HTMLElement;
    const panel = within(block).getByTestId('web-panel');
    const before = leftColumn().textContent;

    fireEvent.click(within(panel).getByRole('button', { name: /Load web sources/ }));

    const link = await within(panel).findByRole('link', { name: /Annex II entry/ });
    expect(mocks.searchWeb).toHaveBeenCalledWith(
      'Benzidine',
      ['skin irritation', 'allergy / sensitization', 'hazard classification'],
      false,
    );
    expect(link).toHaveAttribute('href', 'https://eur-lex.europa.eu/example');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(panel.textContent).toContain('retrieved 2026-11-11');
    expect(panel.textContent).toContain('Official');

    // The dataset side of the block is untouched, and the status is unchanged.
    expect(leftColumn().textContent).toBe(before);
    expect(within(block).getByText('Prohibited')).toBeInTheDocument();
    expect(block.textContent).not.toContain('safe');
  });

  it('adds web_context to the JSON download only once something is loaded', async () => {
    mocks.searchWeb.mockResolvedValue(webContext());
    const { card } = renderCard([prohibited(), fullyPopulated()]);
    const panel = within(card).getByTestId('web-panel');

    fireEvent.click(within(card).getByRole('button', { name: 'Download .json' }));
    const before = JSON.parse(mocks.downloadFile.mock.calls[0][1] as string);
    expect(before.web_context).toBeUndefined();
    expect(before.ingredients).toHaveLength(2);

    fireEvent.click(within(panel).getByRole('button', { name: /Load web sources/ }));
    await within(panel).findByRole('link', { name: /Annex II entry/ });

    fireEvent.click(within(card).getByRole('button', { name: 'Download .json' }));
    const after = JSON.parse(mocks.downloadFile.mock.calls[1][1] as string);
    expect(Object.keys(after.web_context)).toEqual(['Benzidine']);
    expect(after.ingredients).toEqual(before.ingredients);
    expect(after.summary).toEqual(before.summary);
  });
});
