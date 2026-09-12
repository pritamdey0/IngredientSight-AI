import React from 'react';

interface LandingHeroProps {
  onOpenDashboard: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onOpenDashboard }) => {
  return (
    <div className="relative min-h-screen w-full flex flex-col justify-between overflow-hidden bg-[hsl(201,100%,13%)] text-white select-none">
      {/* Fullscreen Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover z-0"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4"
      />

      {/* Glassmorphic Navigation Bar */}
      <header className="relative z-10 flex flex-row items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
        {/* Brand Logo */}
        <div
          className="text-3xl tracking-tight text-white cursor-pointer"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          IngredientSight<sup className="text-xs">®</sup>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-8">
          <span className="text-sm text-white font-medium cursor-pointer">Home</span>
          <span className="text-sm text-zinc-400 hover:text-white transition-colors cursor-pointer" onClick={onOpenDashboard}>Features</span>
          <span className="text-sm text-zinc-400 hover:text-white transition-colors cursor-pointer" onClick={onOpenDashboard}>About</span>
          <span className="text-sm text-zinc-400 hover:text-white transition-colors cursor-pointer" onClick={onOpenDashboard}>Docs</span>
          <span className="text-sm text-zinc-400 hover:text-white transition-colors cursor-pointer" onClick={onOpenDashboard}>Contact</span>
        </nav>

        {/* Top CTA Button */}
        <button
          onClick={onOpenDashboard}
          className="liquid-glass rounded-full px-6 py-2.5 text-sm text-white hover:scale-[1.03] transition-transform duration-200 cursor-pointer"
        >
          Get Started
        </button>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 flex flex-col items-center justify-center text-center px-6 pt-32 pb-40 py-[90px] max-w-7xl mx-auto my-auto">
        {/* H1 Heading */}
        <h1
          className="text-5xl sm:text-7xl md:text-8xl leading-[0.95] tracking-[-2.46px] max-w-7xl font-normal text-white animate-fade-rise"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Where <em className="not-italic text-zinc-400">dreams</em> rise{' '}
          <em className="not-italic text-zinc-400">through the silence.</em>
        </h1>

        {/* Subtext */}
        <p className="text-zinc-400 text-base sm:text-lg max-w-2xl mt-8 leading-relaxed animate-fade-rise-delay font-sans">
          We're designing tools for deep thinkers, bold creators, and quiet rebels. Amid the chaos, we build digital spaces for sharp focus and inspired work.
        </p>

        {/* Hero CTA Button */}
        <button
          onClick={onOpenDashboard}
          className="liquid-glass rounded-full px-14 py-5 text-base text-white mt-12 hover:scale-[1.03] cursor-pointer transition-transform duration-200 animate-fade-rise-delay-2 font-sans"
        >
          Get Started
        </button>
      </main>

      {/* Minimal Footer Spacer */}
      <div className="relative z-10 pb-6 text-center text-xs text-zinc-500 font-sans">
        © {new Date().getFullYear()} IngredientSight AI. All rights reserved.
      </div>
    </div>
  );
};

export default LandingHero;
