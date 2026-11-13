/** Analyzer page: animated hero + drag-and-drop OCR upload, then report sheet. */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  ArrowLeft,
  Hexagon,
  Loader2,
  Upload,
  X,
} from 'lucide-react';
import { Analysis, analyzeImage, health, recheck } from '../lib/api';
import { Spotlight } from './core/spotlight';
import { TextRoll } from './core/text-roll';
import { ReportCard } from './report/ReportCard';

interface AnalyzerProps {
  onBackToLanding: () => void;
}

export const Analyzer: React.FC<AnalyzerProps> = ({ onBackToLanding }) => {
  const [productName, setProductName] = useState('');
  const [result, setResult] = useState<Analysis | null>(null);
  const [names, setNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [serverInfo, setServerInfo] = useState<{ web: boolean; ocr: boolean; evidence: boolean } | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;
    health()
      .then((info) => {
        if (active) {
          setServerInfo({
            web: info.web_context_enabled,
            ocr: info.ocr_available,
            evidence: info.evidence_enabled,
          });
        }
      })
      .catch(() => {
        if (active) setServerInfo({ web: false, ocr: true, evidence: false });
      });
    return () => { active = false; };
  }, []);

  const acceptResult = useCallback((analysis: Analysis) => {
    setResult(analysis);
    setNames(analysis.ingredients.map((item) => item.input_name));
    window.setTimeout(
      () => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
      60,
    );
  }, []);

  const readImage = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      acceptResult(await analyzeImage(file, productName));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The image could not be read.');
    } finally {
      setLoading(false);
    }
  };

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Use a PNG, JPG, JPEG, WEBP or GIF image.');
      return;
    }
    void readImage(file);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const runRecheck = async (list: string[]) => {
    const cleaned = list.map((name) => name.trim()).filter(Boolean);
    if (cleaned.length === 0) {
      setError('At least one ingredient name is needed.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      acceptResult(await recheck(cleaned, productName));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The re-check failed.');
    } finally {
      setLoading(false);
    }
  };

  const recheckOne = (index: number, value: string) => {
    const updated = names.map((name, position) => (position === index ? value : name));
    setNames(updated);
    void runRecheck(updated);
  };

  return (
    <div className="report-page relative min-h-screen overflow-x-hidden bg-[#0a0a0a] text-white">
      {/* Background image */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden print:hidden" aria-hidden="true">
        <img
          src="/assets/ascii-magic-1.png"
          alt=""
          className="h-full w-full scale-[1.02] object-cover opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/45 to-black/85" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_20%,rgba(0,0,0,0.6)_100%)]" />
      </div>

      {/* Header */}
      <header className="fixed inset-x-0 top-0 z-40 flex items-center justify-between gap-4 border-b border-white/15 bg-black/30 px-5 py-4 backdrop-blur-md sm:px-8 md:px-12 print:hidden">
        <button
          type="button"
          onClick={onBackToLanding}
          title="Back to the landing page"
          className="group flex items-center gap-2.5"
        >
          <ArrowLeft
            size={16}
            className="text-white/45 transition-transform group-hover:-translate-x-0.5 group-hover:text-white"
          />
          <Hexagon size={22} strokeWidth={1.5} className="text-white" />
          <span className="text-lg font-medium tracking-tight text-white sm:text-xl">
            IngredientSight AI
          </span>
        </button>
        <span className="hidden font-mono text-[11px] uppercase tracking-[0.15em] text-white/45 sm:block">
          EU annex + ECHA CLP
        </span>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-3xl px-5 pb-24 pt-28 sm:px-8 sm:pt-32 md:px-12">
        <section className="print:hidden">

          {/* ── Hero heading (new design) ── */}
          <div className="relative z-10 flex flex-col items-center pt-6 pb-6 px-6 text-center">
            <motion.span
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-[10px] font-mono text-zinc-500 uppercase tracking-[0.2em] mb-4 block"
            >
              AI-Powered Cosmetic Safety Platform
            </motion.span>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-[-0.05em] leading-none">
              <TextRoll className="text-white">IngredientSight AI</TextRoll>
            </h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1, duration: 0.6 }}
              className="mt-4 text-sm text-zinc-500 font-mono tracking-normal max-w-md"
            >
              Upload a product label or enter a product name — the AI does the rest.
            </motion.p>
          </div>

          {/* ── Upload card ── */}
          <motion.section
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="relative mt-6 rounded-3xl border border-white/10 bg-transparent shadow-2xl overflow-hidden"
          >
            <Spotlight
              className="from-white/10 via-transparent to-transparent blur-2xl"
              size={260}
            />

            <div className="relative z-10 p-6 sm:p-8">
              <div className="flex items-center gap-2 mb-6">
                <Upload className="w-4 h-4 text-zinc-400" />
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-widest">
                  Upload &amp; Analyze
                </span>
              </div>

              {/* Optional product name */}
              <div className="mb-5">
                <label
                  htmlFor="product-name"
                  className="font-mono text-[10px] uppercase tracking-[0.15em] text-white/45"
                >
                  Product name (optional)
                </label>
                <input
                  id="product-name"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g. CeraVe Moisturising Cream"
                  maxLength={120}
                  className="mt-2 w-full border-b border-white/20 bg-transparent pb-2 text-sm text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/60"
                />
              </div>

              {/* Drag-and-drop zone */}
              <div className="flex justify-center w-full">
                <motion.div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  onClick={() => !loading && fileRef.current?.click()}
                  animate={{ borderColor: dragOver ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.12)' }}
                  className="relative cursor-pointer rounded-2xl border border-white/10 bg-transparent p-8 flex flex-col items-center justify-center text-center gap-3 group hover:border-white/25 transition-colors w-full max-w-lg"
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                    onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
                    className="hidden"
                  />

                  <div className="w-12 h-12 rounded-2xl bg-white/8 border border-white/10 flex items-center justify-center group-hover:scale-110 transition-transform text-white">
                    {loading
                      ? <Loader2 className="w-5 h-5 animate-spin" />
                      : <Upload className="w-5 h-5" />}
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-white uppercase tracking-tight">
                      {loading ? 'Reading image…' : 'Drop Image Here'}
                    </p>
                    <p className="text-[11px] text-zinc-600 font-mono mt-1 tracking-normal">
                      or click to browse · PNG · JPG · JPEG · WEBP
                    </p>
                  </div>

                  <p className="text-[10px] font-mono text-zinc-700 max-w-[14rem] leading-snug">
                    For best OCR results use a well-lit, in-focus photo of the ingredient list panel.
                  </p>

                  <AnimatePresence>
                    {dragOver && (
                      <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="absolute inset-0 rounded-2xl bg-blue-500/10 border-2 border-blue-400/40 flex items-center justify-center"
                      >
                        <span className="text-sm font-bold text-blue-300">Release to analyze</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </div>
            </div>
          </motion.section>

          {/* Error */}
          {error && (
            <div className="mt-6 flex items-start gap-2 border-l-2 border-[color:var(--status-error)] pl-3 text-[13px] leading-relaxed text-[var(--status-error)] print:hidden">
              <AlertTriangle size={13} className="mt-0.5 shrink-0" aria-hidden />
              <span>{error}</span>
              <button
                type="button"
                onClick={() => setError(null)}
                className="ml-auto text-white/40 hover:text-white"
                aria-label="Dismiss"
              >
                <X size={12} />
              </button>
            </div>
          )}
        </section>

        {result && (
          <div ref={resultsRef} className="mt-14 scroll-mt-24">
            <ReportCard
              result={result}
              names={names}
              webEnabled={serverInfo?.web ?? true}
              evidenceEnabled={serverInfo?.evidence ?? false}
              onNameChange={(index, value) =>
                setNames((current) =>
                  current.map((name, position) => (position === index ? value : name)),
                )
              }
              onRecheck={recheckOne}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default Analyzer;
