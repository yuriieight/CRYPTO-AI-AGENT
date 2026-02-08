import { useState, useEffect } from 'react';
import {
  LineChart, Wallet, TrendingUp, MessageSquare,
  Home, Target, Newspaper, Activity, BarChart2, BookOpen, Zap,
} from 'lucide-react';
import { Dashboard }   from './pages/Dashboard';
import { Market }      from './pages/Market';
import { Analysis }    from './pages/Analysis';
import { Portfolio }   from './pages/Portfolio';
import { Predictions } from './pages/Predictions';
import { Backtesting } from './pages/Backtesting';
import { Chat }        from './pages/Chat';
import { News }        from './pages/News';
import { Stocks }      from './pages/Stocks';
import Research        from './pages/Research';

/* ── Tabs ────────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'dashboard',   label: 'Панель',      icon: Home },
  { id: 'market',      label: 'Ринок',        icon: LineChart },
  { id: 'analysis',    label: 'Аналіз',       icon: TrendingUp },
  { id: 'predictions', label: 'Прогнози',     icon: Target },
  { id: 'backtesting', label: 'Бектестинг',   icon: Activity },
  { id: 'stocks',      label: 'Акції',        icon: BarChart2 },
  { id: 'research',    label: 'Дослідження',  icon: BookOpen },
  { id: 'news',        label: 'Новини',       icon: Newspaper },
  { id: 'portfolio',   label: 'Портфель',     icon: Wallet },
  { id: 'chat',        label: 'AI Чат',       icon: MessageSquare },
];

const CRYPTOS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT',
  'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'DOGE/USDT',
  'AVAX/USDT', 'MATIC/USDT',
];

/* ── Themes ──────────────────────────────────────────────────────────────── */
const THEMES = [
  { id: 'cyber',    label: 'Кібер',   color: '#00d4ff' },
  { id: 'midnight', label: 'Ніч',     color: '#a78bfa' },
  { id: 'matrix',   label: 'Матриця', color: '#00ff88' },
  { id: 'ember',    label: 'Жар',     color: '#fbbf24' },
  { id: 'light',    label: 'Світло',  color: '#0ea5e9', light: true },
] as const;

type ThemeId = typeof THEMES[number]['id'];

/* ═══════════════════════════════════════════════════════════════════════════
   APP
   ═══════════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [activeTab,      setActiveTab]      = useState('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [theme,          setTheme]          = useState<ThemeId>(() => {
    return (localStorage.getItem('app-theme') as ThemeId) || 'cyber';
  });

  /* Apply theme to <html> so body bg + scrollbar also respond */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  return (
    <div className="min-h-screen bg-grid flex flex-col">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 h-14 flex items-center gap-4">

          {/* Logo */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00d4ff] to-[#7c3aed] flex items-center justify-center shadow-[0_0_12px_rgba(0,212,255,0.4)]">
              <Zap size={16} className="text-white" />
            </div>
            <div className="hidden sm:block">
              <span className="font-bold tracking-wide text-sm" style={{ color: 'var(--c-text-1)' }}>CRYPTO</span>
              <span className="font-bold tracking-wide text-sm" style={{ color: 'var(--c-accent)' }}> AI</span>
            </div>
          </div>

          {/* Live indicator */}
          <div className="hidden md:flex items-center gap-2 text-xs" style={{ color: 'var(--c-text-3)' }}>
            <span className="glow-dot" />
            <span className="font-mono tracking-widest text-[10px] uppercase">Live</span>
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Theme switcher */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg" style={{ border: '1px solid var(--c-border)' }}>
            {THEMES.map(t => (
              <button
                key={t.id}
                title={t.label}
                onClick={() => setTheme(t.id)}
                className="theme-dot"
                style={{
                  backgroundColor: t.color,
                  borderColor: theme === t.id ? 'var(--c-text-1)' : 'transparent',
                  boxShadow: theme === t.id ? `0 0 8px ${t.color}80` : 'none',
                }}
              />
            ))}
          </div>

          {/* Symbol selector */}
          <div className="flex items-center gap-2">
            <span className="hidden sm:block label">Пара</span>
            <select
              value={selectedSymbol}
              onChange={e => setSelectedSymbol(e.target.value)}
              className="cyber-input w-auto text-xs py-1.5 pr-8 font-mono cursor-pointer"
            >
              {CRYPTOS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </header>

      {/* ── Navigation ─────────────────────────────────────────────────── */}
      <nav className="app-nav">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="nav-scroll flex items-stretch">
            {TABS.map(tab => {
              const Icon   = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab-btn${active ? ' active' : ''}`}
                >
                  <Icon size={14} />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* ── Main Content ───────────────────────────────────────────────── */}
      <main className="flex-1 max-w-[1400px] mx-auto w-full px-4 sm:px-6 py-6 animate-fade-up">
        {activeTab === 'dashboard'   && <Dashboard />}
        {activeTab === 'market'      && <Market symbol={selectedSymbol} />}
        {activeTab === 'analysis'    && <Analysis symbol={selectedSymbol} />}
        {activeTab === 'predictions' && <Predictions symbol={selectedSymbol} />}
        {activeTab === 'backtesting' && <Backtesting />}
        {activeTab === 'stocks'      && <Stocks />}
        {activeTab === 'research'    && <Research />}
        {activeTab === 'news'        && <News symbol={selectedSymbol} />}
        {activeTab === 'portfolio'   && <Portfolio />}
        {activeTab === 'chat'        && <Chat selectedSymbol={selectedSymbol} />}
      </main>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="py-4 px-6 text-center" style={{ borderTop: '1px solid var(--c-border)' }}>
        <p className="text-xs font-mono" style={{ color: 'var(--c-text-4)' }}>
          © 2026 CRYPTO AI AGENT &nbsp;·&nbsp; Powered by ML &nbsp;·&nbsp;
          <span style={{ color: '#ff3366' }}>⚠ Не є фінансовою порадою</span>
        </p>
      </footer>
    </div>
  );
}
