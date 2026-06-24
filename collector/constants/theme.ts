export type ColorScheme = {
  background: string;
  surface: string;
  border: string;
  accent: string;
  accentDark: string;
  text: string;
  subtext: string;
  positive: string;
  negative: string;
};

export const darkColors: ColorScheme = {
  background: '#0d1117',
  surface: '#161b22',
  border: '#30363d',
  accent: '#06b6d4',
  accentDark: '#0891b2',
  text: '#ffffff',
  subtext: '#8b949e',
  positive: '#10b981',
  negative: '#ef4444',
};

export const lightColors: ColorScheme = {
  background: '#ffffff',
  surface: '#f3f4f6',
  border: '#e5e7eb',
  accent: '#0891b2',
  accentDark: '#0e7490',
  text: '#111827',
  subtext: '#6b7280',
  positive: '#059669',
  negative: '#dc2626',
};

// Keep legacy export so nothing breaks before migration
export const colors = darkColors;
