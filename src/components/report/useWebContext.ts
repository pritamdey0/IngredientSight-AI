/** Web-context state for the report: user-triggered, cached per session. */

import { useCallback, useRef, useState } from 'react';
import { WebContext, searchWeb, searchWebBatch } from '../../lib/api';

/** One click may search at most six ingredients; the rest waits for the next click. */
export const WEB_MAX_PER_CLICK = 6;
/** Requests are grouped so the progress counter moves while the server works. */
const CHUNK_SIZE = 2;
const CHUNK_PAUSE_MS = 250;

export interface WebEntry {
  state: 'loading' | 'done' | 'error';
  data?: WebContext;
  error?: string;
  includeOther: boolean;
  topics: string[];
}

export interface WebRequest {
  name: string;
  topics: string[];
}

export interface BatchProgress {
  done: number;
  total: number;
  running: boolean;
}

function keyOf(name: string, topics: string[], includeOther: boolean): string {
  return `${name.trim().toLowerCase()}|${includeOther ? '1' : '0'}|${topics.join(',')}`;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function useWebContext() {
  const [entries, setEntries] = useState<Record<string, WebEntry>>({});
  const [batch, setBatch] = useState<BatchProgress | null>(null);
  const cache = useRef(new Map<string, WebContext>());

  const remember = useCallback(
    (name: string, data: WebContext, topics: string[], includeOther: boolean) => {
      cache.current.set(keyOf(name, topics, includeOther), data);
      setEntries((current) => ({
        ...current,
        [name]: { state: 'done', data, topics, includeOther },
      }));
    },
    [],
  );

  const markLoading = useCallback((name: string, topics: string[], includeOther: boolean) => {
    setEntries((current) => ({
      ...current,
      [name]: { state: 'loading', topics, includeOther },
    }));
  }, []);

  const markError = useCallback(
    (name: string, topics: string[], includeOther: boolean, error: string) => {
      setEntries((current) => ({ ...current, [name]: { state: 'error', topics, includeOther, error } }));
    },
    [],
  );

  const cachedFor = useCallback((name: string, topics: string[], includeOther: boolean) => {
    return cache.current.get(keyOf(name, topics, includeOther));
  }, []);

  /** Load one panel. Never searches the same ingredient + topics twice per session. */
  const load = useCallback(
    async (name: string, topics: string[], includeOther: boolean) => {
      const cached = cache.current.get(keyOf(name, topics, includeOther));
      if (cached) {
        remember(name, cached, topics, includeOther);
        return;
      }
      markLoading(name, topics, includeOther);
      try {
        const data = await searchWeb(name, topics, includeOther);
        remember(name, data, topics, includeOther);
      } catch (error) {
        markError(name, topics, includeOther, error instanceof Error ? error.message : 'The web search failed.');
      }
    },
    [markError, markLoading, remember],
  );

  /** Load every panel that still needs data, at most six per click, in order. */
  const loadMany = useCallback(
    async (requests: WebRequest[], includeOther: boolean) => {
      const pending = requests
        .filter((item) => item.name.trim() && !cache.current.has(keyOf(item.name, item.topics, includeOther)))
        .slice(0, WEB_MAX_PER_CLICK);
      if (pending.length === 0) {
        setBatch({ done: 0, total: 0, running: false });
        return;
      }

      setBatch({ done: 0, total: pending.length, running: true });
      for (let start = 0; start < pending.length; start += CHUNK_SIZE) {
        const chunk = pending.slice(start, start + CHUNK_SIZE);
        chunk.forEach((item) => markLoading(item.name, item.topics, includeOther));
        try {
          const payload = await searchWebBatch(
            chunk.map((item) => ({ ingredient: item.name, topics: item.topics })),
            includeOther,
          );
          chunk.forEach((item) => {
            const data = payload.results[item.name];
            if (data) {
              remember(item.name, data, item.topics, includeOther);
            } else {
              markError(item.name, item.topics, includeOther, 'No answer for this ingredient.');
            }
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'The web search failed.';
          chunk.forEach((item) => markError(item.name, item.topics, includeOther, message));
        }
        setBatch({
          done: Math.min(start + chunk.length, pending.length),
          total: pending.length,
          running: true,
        });
        if (start + CHUNK_SIZE < pending.length) await sleep(CHUNK_PAUSE_MS);
      }
      setBatch((current) => (current ? { ...current, running: false } : current));
    },
    [markError, markLoading, remember],
  );

  /** Called when a new analysis arrives: cached searches stay, panels reset. */
  const reset = useCallback(() => {
    setEntries({});
    setBatch(null);
  }, []);

  const loaded = useCallback((): Record<string, WebContext> => {
    const output: Record<string, WebContext> = {};
    for (const [name, entry] of Object.entries(entries)) {
      if (entry.state === 'done' && entry.data) output[name] = entry.data;
    }
    return output;
  }, [entries]);

  return { entries, batch, load, loadMany, reset, cachedFor, loaded };
}
