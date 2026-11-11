import React from 'react';
import { Hexagon, ChevronRight } from 'lucide-react';
import { ScrollVideoBackground } from './ScrollVideoBackground';
import { Reveal } from './Reveal';

interface NovaLandingPageProps {
  onOpenAnalyzer: () => void;
}

export const NovaLandingPage: React.FC<NovaLandingPageProps> = ({ onOpenAnalyzer }) => {
  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white selection:bg-white/20 selection:text-white font-sans overflow-x-hidden">
      {/* Scroll Video Background (Fixed z-0) */}
      <ScrollVideoBackground />

      {/* Content Layer (Relative z-10) */}
      <div className="relative z-10 w-full">
        {/* Fixed Navbar */}
        <nav className="fixed top-0 left-0 right-0 z-50 w-full border-b border-white/15 bg-black/30 backdrop-blur-md px-5 sm:px-8 md:px-12 py-4 flex items-center justify-between">
          {/* Brand Logo */}
          <Reveal delayMs={0}>
            <div
              className="flex items-center gap-2.5 cursor-pointer"

            >
              <Hexagon size={24} strokeWidth={1.5} className="text-white" />
              <span className="text-lg sm:text-xl font-medium tracking-tight text-white">
                IngredientSight AI
              </span>
            </div>
          </Reveal>
        </nav>

        {/* Main Sections */}
        <main className="px-5 sm:px-8 md:px-12 pt-24 sm:pt-28 pb-12 md:pb-16 max-w-7xl mx-auto">
          {/* SECTION ONE — HERO */}
          <section className="min-h-screen supports-[height:100svh]:min-h-[100svh] flex flex-col justify-between pt-8 pb-12">
            {/* Top Row */}
            <div className="flex flex-col gap-8 sm:flex-row sm:items-start justify-between">
              {/* Left Service List */}
              <div className="flex flex-col gap-2">
                <Reveal delayMs={150}>
                  <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/90 drop-shadow-md">
                    / INCI LIST + LABEL OCR
                  </div>
                </Reveal>
                <Reveal delayMs={270}>
                  <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/90 drop-shadow-md">
                    / EU COSING ANNEX LOOKUP
                  </div>
                </Reveal>
                <Reveal delayMs={390}>
                  <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/90 drop-shadow-md">
                    / ECHA CLP HAZARD CODES
                  </div>
                </Reveal>
              </div>

              {/* Right Intro Copy */}
              <Reveal delayMs={300} className="max-w-sm sm:text-right">
                <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-md font-sans">
                  Every name on the label, checked against the official EU annexes and ECHA CLP
                  classifications, with the source printed next to each fact.
                </p>
              </Reveal>
            </div>

            {/* Bottom Row */}
            <div className="flex flex-col gap-8 md:flex-row md:items-end justify-between mt-12">
              {/* Left Side */}
              <div>
                {/* Left-Accent Badge */}
                <Reveal delayMs={150}>
                  <div className="inline-block border-l-2 border-white bg-white/15 px-3 py-1.5 backdrop-blur-md mb-5">
                    <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-white">
                      REGULATORY LOOKUP ENGINE
                    </span>
                  </div>
                </Reveal>

                {/* H1 Headline */}
                <Reveal delayMs={280}>
                  <h1 className="text-5xl sm:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-tight text-white drop-shadow-lg max-w-2xl">
                    Sourced. Cited.
                    <br />
                    Not Scored.
                  </h1>
                </Reveal>
              </div>
            </div>
          </section>

          {/* MID SPACER DIV (Critical for Video Scroll-Scrubbing) */}
          <div className="h-[80vh]" aria-hidden="true" />

          {/* SECTION TWO — CAPABILITY */}
          <section className="min-h-screen supports-[height:100svh]:min-h-[100svh] flex flex-col justify-between pt-8 pb-12">
            {/* Top Row */}
            <div className="flex flex-col gap-6 sm:flex-row sm:items-start justify-between">
              {/* Left Badge */}
              <Reveal delayMs={120}>
                <div className="inline-block border-l-2 border-white bg-white/15 px-3 py-1.5 backdrop-blur-md">
                  <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-white">
                    WHAT THE DATASET SAYS, NOTHING MORE
                  </span>
                </div>
              </Reveal>

              {/* Right Copy */}
              <Reveal delayMs={220} className="max-w-sm sm:text-right">
                <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-md">
                  One deterministic lookup per ingredient. No risk score, no grade, and the same
                  result every time you run it.
                </p>
              </Reveal>
            </div>

            {/* Bottom Area */}
            <div className="flex-1 flex flex-col justify-end gap-12 md:flex-row md:items-end md:justify-between gap-16 mt-16">
              {/* Left Column */}
              <div className="max-w-xl">
                {/* H2 Headline */}
                <Reveal delayMs={180}>
                  <h2 className="text-5xl sm:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-tight text-white drop-shadow-lg">
                    Check a label
                    <br />
                    in seconds.
                  </h2>
                </Reveal>

                {/* Body */}
                <Reveal delayMs={320}>
                  <p className="mt-6 max-w-md text-sm sm:text-base text-white/80 drop-shadow-md leading-relaxed">
                    Paste the INCI list or photograph the pack. Each name is matched to its annex
                    entry, concentration limit and CLP hazard codes, or plainly marked as having no
                    data in the dataset.
                  </p>
                </Reveal>

                {/* CTAs */}
                <Reveal delayMs={420}>
                  <div className="mt-8 flex flex-wrap gap-3">
                    <button
                      onClick={onOpenAnalyzer}
                      className="rounded-full border border-white/25 bg-white/10 backdrop-blur-md px-6 py-3 text-xs sm:text-sm font-medium text-white hover:bg-white/20 transition-colors cursor-pointer shadow-lg"
                    >
                      Check an ingredient list
                    </button>
                  </div>
                </Reveal>
              </div>

              {/* Right — Frosted Capability Panel */}
              <div className="w-full max-w-md rounded-2xl border border-white/15 bg-white/10 backdrop-blur-md px-5 sm:px-6 shadow-2xl">
                {/* Row 01 */}
                <Reveal delayMs={300}>
                  <div
                    className="flex gap-5 py-5 border-b border-white/15 group cursor-pointer"

                  >
                    <span className="font-mono text-[11px] tracking-[0.15em] text-white/55 pt-1">
                      01
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-base sm:text-lg font-medium text-white">
                          Label photo OCR
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Local text recognition turns a photo of the ingredient panel into a list you
                        can correct before anything is checked.
                      </p>
                    </div>
                  </div>
                </Reveal>

                {/* Row 02 */}
                <Reveal delayMs={410}>
                  <div
                    className="flex gap-5 py-5 border-b border-white/15 group cursor-pointer"

                  >
                    <span className="font-mono text-[11px] tracking-[0.15em] text-white/55 pt-1">
                      02
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-base sm:text-lg font-medium text-white">
                          Annex status per name
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Prohibited, restricted, on a positive list, no annex entry found or not
                        identified, taken straight from the CosIng annex columns.
                      </p>
                    </div>
                  </div>
                </Reveal>

                {/* Row 03 */}
                <Reveal delayMs={520}>
                  <div
                    className="flex gap-5 py-5 group cursor-pointer"

                  >
                    <span className="font-mono text-[11px] tracking-[0.15em] text-white/55 pt-1">
                      03
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="text-base sm:text-lg font-medium text-white">
                          Every fact has a source
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Limits, CMR categories and CLP codes are printed with the annex entry and
                        dataset snapshot they came from. Optional web context stays separate.
                      </p>
                    </div>
                  </div>
                </Reveal>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default NovaLandingPage;
