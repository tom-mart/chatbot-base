'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

// Theme configuration with icons and descriptions
const THEME_CONFIG = [
  { name: 'light', icon: '☀️', description: 'Clean & bright' },
  { name: 'dark', icon: '🌙', description: 'Easy on eyes' },
  { name: 'cupcake', icon: '🧁', description: 'Sweet & soft' },
  { name: 'emerald', icon: '💚', description: 'Fresh & natural' },
  { name: 'corporate', icon: '💼', description: 'Professional' },
  { name: 'synthwave', icon: '🌆', description: 'Retro neon' },
  { name: 'cyberpunk', icon: '🤖', description: 'Futuristic' },
  { name: 'valentine', icon: '💝', description: 'Romantic pink' },
  { name: 'forest', icon: '🌲', description: 'Nature green' },
  { name: 'aqua', icon: '🌊', description: 'Ocean blue' },
  { name: 'pastel', icon: '🎨', description: 'Soft colors' },
  { name: 'dracula', icon: '🧛', description: 'Dark purple' },
  { name: 'autumn', icon: '🍂', description: 'Warm tones' },
  { name: 'business', icon: '📊', description: 'Minimal pro' },
  { name: 'night', icon: '🌃', description: 'Deep dark' },
  { name: 'sunset', icon: '🌅', description: 'Warm sunset' },
] as const;

const AVAILABLE_THEMES = THEME_CONFIG.map(t => t.name) as readonly string[];

type Theme = typeof AVAILABLE_THEMES[number];

interface ThemeConfig {
  name: string;
  icon: string;
  description: string;
}

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  availableThemes: readonly Theme[];
  themeConfig: typeof THEME_CONFIG;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('corporate');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Get saved theme or default to 'corporate'
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme && AVAILABLE_THEMES.includes(savedTheme)) {
      setThemeState(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      document.documentElement.setAttribute('data-theme', 'corporate');
    }
  }, []);

  useEffect(() => {
    if (mounted) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    }
  }, [theme, mounted]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, availableThemes: AVAILABLE_THEMES, themeConfig: THEME_CONFIG }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
