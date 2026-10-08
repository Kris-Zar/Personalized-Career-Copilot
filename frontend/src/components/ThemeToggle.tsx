import React, { useEffect, useState } from 'react';

export const ThemeToggle: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('xcl_theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('xcl_theme', theme);
  }, [theme]);

  const toggle = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <button
      className="theme-toggle-btn"
      onClick={toggle}
      title="Toggle Light / Dark Theme"
    >
      {theme === 'light' ? '🌙 Velvet Purple Dark' : '☀️ Medium Red Light'}
    </button>
  );
};
