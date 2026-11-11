import React, { useEffect, useState } from 'react';
import { Analyzer } from './components/Analyzer';
import { CustomCursor } from './components/CustomCursor';
import { NovaLandingPage } from './components/NovaLandingPage';

type View = 'landing' | 'analyzer';

const viewFromHash = (): View => (window.location.hash === '#analyzer' ? 'analyzer' : 'landing');

export const App: React.FC = () => {
  const [view, setView] = useState<View>(viewFromHash);

  // The hash keeps the current page on reload and makes the browser back
  // button work without adding a router.
  useEffect(() => {
    const sync = () => setView(viewFromHash());
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, []);

  const go = (next: View) => {
    window.location.hash = next === 'analyzer' ? 'analyzer' : '';
    setView(next);
    window.scrollTo({ top: 0 });
  };

  return (
    <div className="relative min-h-screen bg-[#0a0a0a] font-sans text-white selection:bg-white/20 selection:text-white">
      {view === 'landing' ? (
        <>
          <CustomCursor />
          <NovaLandingPage onOpenAnalyzer={() => go('analyzer')} />
        </>
      ) : (
        <Analyzer onBackToLanding={() => go('landing')} />
      )}
    </div>
  );
};

export default App;
