import React, { useState } from 'react';
import { CustomCursor } from './components/CustomCursor';
import { NovaLandingPage } from './components/NovaLandingPage';
import { Dashboard } from './components/Dashboard';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'dashboard'>('landing');

  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white selection:bg-white/20 selection:text-white font-sans">
      {/* Custom mix-blend-mode cursor */}
      <CustomCursor />

      {currentView === 'landing' ? (
        <NovaLandingPage onOpenDashboard={() => setCurrentView('dashboard')} />
      ) : (
        <Dashboard onBackToLanding={() => setCurrentView('landing')} />
      )}
    </div>
  );
};

export default App;
