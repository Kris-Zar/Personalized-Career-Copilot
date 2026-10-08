import React from 'react';
import { NavLink } from 'react-router-dom';

const TABS = [
  { path: '/profile', label: '01 · Profile', icon: '👤' },
  { path: '/goal', label: '02 · Goal Discovery', icon: '🎯' },
  { path: '/assessment', label: '03 · Assessment', icon: '📝' },
  { path: '/results', label: '04 · Results', icon: '📊' },
  { path: '/roadmap', label: '05 · Roadmap', icon: '🗺️' },
  { path: '/dashboard', label: '06 · Dashboard', icon: '🚀' },
];

export const TopNavigation: React.FC = () => {
  return (
    <nav className="nav-tabs">
      {TABS.map((tab) => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
        >
          <span>{tab.icon}</span>
          <span>{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};
