import React from 'react';
import { TopNavigation } from './TopNavigation';
import { ThemeToggle } from './ThemeToggle';
import { MomentumMeter } from './MomentumMeter';
import { PersonaBar } from './PersonaBar';

interface Props {
  children: React.ReactNode;
}

export const AppShell: React.FC<Props> = ({ children }) => {
  return (
    <div className="app-container">
      <header className="top-toolbar">
        <div className="top-bar-upper">
          <div className="brand-section">
            <div className="brand-dot"></div>
            <span className="brand-title">PathFinder</span>
            <span className="brand-badge">Adaptive Career Copilot</span>
          </div>

          <div className="toolbar-actions">
            <MomentumMeter />
            <ThemeToggle />
          </div>
        </div>

        <TopNavigation />
      </header>

      <PersonaBar />

      <main>{children}</main>
    </div>
  );
};
