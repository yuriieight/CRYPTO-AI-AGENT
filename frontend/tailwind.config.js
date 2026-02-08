/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg:       '#070b14',
          surface:  '#0d1628',
          card:     '#0f1b30',
          border:   '#1a2d4a',
          cyan:     '#00d4ff',
          purple:   '#7c3aed',
          green:    '#00ff88',
          red:      '#ff3366',
          yellow:   '#fbbf24',
          muted:    '#4a6080',
          text:     '#c8d8e8',
          heading:  '#e8f4ff',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      animation: {
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'scan-line':  'scanLine 4s linear infinite',
        'fade-up':    'fadeUp 0.4s ease-out',
        'shimmer':    'shimmer 2s linear infinite',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(0,212,255,0.2)' },
          '50%':      { boxShadow: '0 0 20px rgba(0,212,255,0.5)' },
        },
        scanLine: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition:  '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
