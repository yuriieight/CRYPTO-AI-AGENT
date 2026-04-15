/** Available UI color themes */
export const THEMES = {
  dark:     { bg: "#0f172a", card: "#1e293b", accent: "#3b82f6", text: "#f8fafc" },
  light:    { bg: "#f8fafc", card: "#ffffff", accent: "#2563eb", text: "#0f172a" },
  midnight: { bg: "#020617", card: "#0f172a", accent: "#818cf8", text: "#e2e8f0" },
  forest:   { bg: "#052e16", card: "#14532d", accent: "#4ade80", text: "#f0fdf4" },
  sunset:   { bg: "#1c0a00", card: "#431407", accent: "#fb923c", text: "#fff7ed" },
} as const;

export type ThemeName = keyof typeof THEMES;
