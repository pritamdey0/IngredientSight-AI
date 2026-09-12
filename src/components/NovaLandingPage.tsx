import React from 'react';
import { Hexagon, ChevronRight } from 'lucide-react';
import { ScrollVideoBackground } from './ScrollVideoBackground';
import { Reveal } from './Reveal';

interface NovaLandingPageProps {
  onOpenDashboard: () => void;
}

export const NovaLandingPage: React.FC<NovaLandingPageProps> = ({ onOpenDashboard }) => {
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
                    / INCI MOLECULAR OCR
                  </div>
                </Reveal>
                <Reveal delayMs={270}>
                  <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/90 drop-shadow-md">
                    / TOXICOLOGICAL RISK MATRIX
                  </div>
                </Reveal>
                <Reveal delayMs={390}>
                  <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/90 drop-shadow-md">
                    / AUTONOMOUS RESEARCH AGENTS
                  </div>
                </Reveal>
              </div>

              {/* Right Intro Copy */}
              <Reveal delayMs={300} className="max-w-sm sm:text-right">
                <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-md font-sans">
                  We synthesize real-time scientific literature, FDA monographs, and EWG safety indices to bring total clarity to cosmetic formulation safety.
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
                      MOLECULAR SAFETY ENGINE
                    </span>
                  </div>
                </Reveal>

                {/* H1 Headline */}
                <Reveal delayMs={280}>
                  <h1 className="text-5xl sm:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-tight text-white drop-shadow-lg max-w-2xl">
                    Pure. Transparent.
                    <br />
                    Scientifically Proven.
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
                    MOLECULAR INTELLIGENCE ON DEMAND
                  </span>
                </div>
              </Reveal>

              {/* Right Copy */}
              <Reveal delayMs={220} className="max-w-sm sm:text-right">
                <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-md">
                  Our multi-agent pipeline doesn't just list ingredients — it extracts, evaluates, and synthesizes complete toxicological safety profiles.
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
                    Analyze formulations
                    <br />
                    with evidence.
                  </h2>
                </Reveal>

                {/* Body */}
                <Reveal delayMs={320}>
                  <p className="mt-6 max-w-md text-sm sm:text-base text-white/80 drop-shadow-md leading-relaxed">
                    From raw label images to comprehensive toxicity reports, IngredientSight AI synthesizes PubMed literature and CIR safety monographs in real time.
                  </p>
                </Reveal>

                {/* CTAs */}
                <Reveal delayMs={420}>
                  <div className="mt-8 flex flex-wrap gap-3">
                    <button
                      onClick={onOpenDashboard}
                      className="rounded-full border border-white/25 bg-white/10 backdrop-blur-md px-6 py-3 text-xs sm:text-sm font-medium text-white hover:bg-white/20 transition-colors cursor-pointer shadow-lg"
                    >
                      Get Started
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
                          Optical Label OCR
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Extracts INCI ingredient labels instantly from cosmetic packaging photos using high-density neural recognition.
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
                          Toxicological Mapping
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Calculates dermal risk indices, EWG hazard score approximations, and allergen flags across formulas.
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
                          Scientific Synthesis
                        </h3>

                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-white/70">
                        Cross-references PubMed, FDA monographs, and CIR panels to generate evidence-backed safety audits.
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
