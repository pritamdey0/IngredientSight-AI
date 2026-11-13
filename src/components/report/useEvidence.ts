/** Automated evidence-review state for the report: one call, cached per session. */

import { useCallback, useRef, useState } from 'react';
import { Analysis, EvidenceBatchResponse, EvidenceResponse, researchEvidenceBatch } from '../../lib/api';

export interface EvidenceState {
  state: 'loading' | 'done' | 'error';
  data?: EvidenceBatchResponse;
  error?: string;
}

function keyOf(analysis: Analysis): string {
  return analysis.ingredients.map((ingredient) => ingredient.input_name.trim().toLowerCase()).join('|');
}

export function useEvidence() {
  const [batch, setBatch] = useState<EvidenceState | null>(null);
  const cache = useRef(new Map<string, EvidenceBatchResponse>());

  /** Research the dataset gaps of every ingredient. Reuses a cached answer. */
  const run = useCallback(async (analysis: Analysis): Promise<EvidenceBatchResponse | null> => {
    const key = keyOf(analysis);
    const cached = cache.current.get(key);
    if (cached) {
      setBatch({ state: 'done', data: cached });
      return cached;
    }
    setBatch({ state: 'loading' });
    try {
      const data = await researchEvidenceBatch(analysis, true);
      cache.current.set(key, data);
      setBatch({ state: 'done', data });
      return data;
    } catch (error) {
      setBatch({
        state: 'error',
        error: error instanceof Error ? error.message : 'The evidence review failed.',
      });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setBatch(null);
  }, []);

  const results = useCallback((): Record<string, EvidenceResponse> => {
    return batch?.data?.results ?? {};
  }, [batch]);

  return { batch, run, reset, results };
}
