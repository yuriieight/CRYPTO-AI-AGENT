import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Zap, TrendingUp, TrendingDown, ChevronDown, ChevronUp, Brain } from 'lucide-react';
import { aiAPI, predictionsAPI, marketAPI } from '../services/api';

/* ── Types ───────────────────────────────────────────────────────────────── */
interface Prediction {
  date: string;
  predicted_price: number;
  lower_bound: number;
  upper_bound: number;
  change_pct: number;
  confidence: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  predictions?: Prediction[];
  predictionMeta?: { symbol: string; model: string; currentPrice: number };
}

/* ── Quick questions ─────────────────────────────────────────────────────── */
const QUICK_QUESTIONS = [
  'Надай прогноз BTC на 5 днів',
  'Прогноз ETH на тиждень',
  'Поясни технічний аналіз',
  'Як управляти ризиками?',
];

/* ── Crypto symbol map ───────────────────────────────────────────────────── */
const SYMBOL_MAP: Record<string, string> = {
  bitcoin: 'BTC/USDT', btc: 'BTC/USDT',
  ethereum: 'ETH/USDT', eth: 'ETH/USDT',
  bnb: 'BNB/USDT', binance: 'BNB/USDT',
  xrp: 'XRP/USDT', ripple: 'XRP/USDT',
  ada: 'ADA/USDT', cardano: 'ADA/USDT',
  sol: 'SOL/USDT', solana: 'SOL/USDT',
  dot: 'DOT/USDT', polkadot: 'DOT/USDT',
  doge: 'DOGE/USDT', dogecoin: 'DOGE/USDT',
  avax: 'AVAX/USDT', avalanche: 'AVAX/USDT',
  matic: 'MATIC/USDT', polygon: 'MATIC/USDT',
};

/* ── Intent / symbol detection ───────────────────────────────────────────── */
const PREDICTION_KEYWORDS = [
  // Ukrainian
  'прогноз', 'передбач', 'передбачення', 'передбач',
  'прогнозу', 'наступні дні', 'на кілька днів', 'на тиждень',
  'ціна завтра', 'що буде з ціною', 'куди піде', 'зростання ціни',
  // English
  'predict', 'forecast', 'price prediction', 'next days', 'next week',
  'will it go', 'future price', 'price target',
];

function detectPredictionIntent(message: string): boolean {
  const lower = message.toLowerCase();
  return PREDICTION_KEYWORDS.some(kw => lower.includes(kw));
}

function extractPeriods(message: string): number {
  // Look for explicit numbers like "3 дні", "7 days", "5 днів"
  const match = message.match(/(\d+)\s*(дн|day|тиж|week)/i);
  if (match) {
    const n = parseInt(match[1]);
    const unit = match[2].toLowerCase();
    if (unit.startsWith('тиж') || unit.startsWith('week')) return Math.min(n * 7, 14);
    return Math.min(Math.max(n, 1), 14);
  }
  // "на тиждень" / "a week"
  if (/тиждень|тижн|a week|one week/i.test(message)) return 7;
  return 5; // default
}

function extractSymbol(message: string, fallback: string): string {
  const lower = message.toLowerCase();
  for (const [key, symbol] of Object.entries(SYMBOL_MAP)) {
    if (lower.includes(key)) return symbol;
  }
  return fallback;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PREDICTION CARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
function PredictionCard({ predictions, meta }: {
  predictions: Prediction[];
  meta: { symbol: string; model: string; currentPrice: number };
}) {
  const [expanded, setExpanded] = useState(false);
  const shown = expanded ? predictions : predictions.slice(0, 3);

  const totalChange = predictions.length > 0
    ? ((predictions[predictions.length - 1].predicted_price - meta.currentPrice) / meta.currentPrice) * 100
    : 0;
  const isUp = totalChange >= 0;

  return (
    <div
      className="mt-3 rounded-xl overflow-hidden text-xs"
      style={{ border: '1px solid var(--c-border)', background: 'var(--c-bg-2)' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2.5"
        style={{ borderBottom: '1px solid var(--c-border)', background: 'var(--c-bg-1)' }}
      >
        <div className="flex items-center gap-2">
          <Brain size={13} style={{ color: 'var(--c-accent)' }} />
          <span className="font-semibold uppercase tracking-widest" style={{ color: 'var(--c-text-3)' }}>
            ML Прогноз
          </span>
          <span className="font-mono font-bold" style={{ color: 'var(--c-accent)' }}>
            {meta.symbol}
          </span>
          <span
            className="px-1.5 py-0.5 rounded-full font-semibold"
            style={{ background: 'var(--c-accent-dim)', color: 'var(--c-accent)', fontSize: '9px' }}
          >
            {meta.model}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="flex items-center gap-1 font-mono font-bold"
            style={{ color: isUp ? '#00ff88' : '#ff3366' }}
          >
            {isUp ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {isUp ? '+' : ''}{totalChange.toFixed(2)}% за {predictions.length}д
          </span>
        </div>
      </div>

      {/* Current price row */}
      <div
        className="flex items-center gap-3 px-3 py-2 font-mono"
        style={{ borderBottom: '1px solid var(--c-border)', color: 'var(--c-text-3)' }}
      >
        <span>Поточна:</span>
        <span className="font-bold" style={{ color: 'var(--c-text-2)' }}>
          ${meta.currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </div>

      {/* Table */}
      <table className="w-full">
        <thead>
          <tr style={{ color: 'var(--c-text-3)' }}>
            <th className="px-3 py-2 text-left font-semibold uppercase tracking-widest"
              style={{ fontSize: '10px', borderBottom: '1px solid var(--c-border)' }}>
              Дата
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-widest"
              style={{ fontSize: '10px', borderBottom: '1px solid var(--c-border)' }}>
              Прогноз
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-widest hidden sm:table-cell"
              style={{ fontSize: '10px', borderBottom: '1px solid var(--c-border)' }}>
              Діапазон
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-widest"
              style={{ fontSize: '10px', borderBottom: '1px solid var(--c-border)' }}>
              Зміна
            </th>
            <th className="px-3 py-2 text-right font-semibold uppercase tracking-widest"
              style={{ fontSize: '10px', borderBottom: '1px solid var(--c-border)' }}>
              Впевн.
            </th>
          </tr>
        </thead>
        <tbody>
          {shown.map((p, i) => {
            const up = p.change_pct >= 0;
            const confColor = p.confidence >= 65 ? '#00ff88' : p.confidence >= 40 ? '#fbbf24' : '#ff3366';
            const isLast = i === shown.length - 1;
            return (
              <tr key={p.date} style={{ borderBottom: isLast && !expanded ? 'none' : '1px solid var(--c-bg-3)' }}>
                <td className="px-3 py-2 font-mono" style={{ color: 'var(--c-text-3)' }}>
                  {p.date}
                </td>
                <td className="px-3 py-2 text-right font-mono font-bold" style={{ color: 'var(--c-text-1)' }}>
                  ${p.predicted_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-3 py-2 text-right font-mono hidden sm:table-cell" style={{ color: 'var(--c-text-3)', fontSize: '10px' }}>
                  ${p.lower_bound.toLocaleString('en-US', { maximumFractionDigits: 0 })} –{' '}
                  ${p.upper_bound.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </td>
                <td className="px-3 py-2 text-right font-mono font-semibold"
                  style={{ color: up ? '#00ff88' : '#ff3366' }}>
                  {up ? '+' : ''}{p.change_pct.toFixed(2)}%
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <div className="w-10 h-1 rounded-full overflow-hidden" style={{ background: 'var(--c-border)' }}>
                      <div style={{ width: `${p.confidence}%`, height: '100%', background: confColor, borderRadius: 9999 }} />
                    </div>
                    <span className="font-mono" style={{ color: confColor }}>{p.confidence}%</span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {predictions.length > 3 && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="flex items-center justify-center gap-1 w-full py-2 transition-colors"
          style={{
            borderTop: '1px solid var(--c-border)',
            color: 'var(--c-text-3)',
            background: 'transparent',
            fontSize: '11px',
          }}
          onMouseEnter={e => (e.currentTarget.style.color = 'var(--c-accent)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'var(--c-text-3)')}
        >
          {expanded
            ? <><ChevronUp size={12} /> Згорнути</>
            : <><ChevronDown size={12} /> Показати всі {predictions.length} днів</>
          }
        </button>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN CHAT COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
export const Chat: React.FC<{ selectedSymbol?: string }> = ({ selectedSymbol = 'BTC/USDT' }) => {
  const [messages,     setMessages]     = useState<Message[]>([]);
  const [input,        setInput]        = useState('');
  const [loading,      setLoading]      = useState(false);
  const [fetchingData, setFetchingData] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef       = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  /* ── Gather context ──────────────────────────────────────────────────── */
  const gatherContext = async (message: string): Promise<{
    context: Record<string, unknown>;
    predictions?: Prediction[];
    predMeta?: { symbol: string; model: string; currentPrice: number };
  }> => {
    const isPrediction = detectPredictionIntent(message);
    const symbol       = extractSymbol(message, selectedSymbol);
    const periods      = extractPeriods(message);
    const context: Record<string, unknown> = {};

    try {
      // Always fetch live ticker for the detected symbol
      const tickerRes = await marketAPI.getTicker(symbol);
      if (tickerRes.data) {
        context.market_data = { ...tickerRes.data, symbol };
      }
    } catch { /* non-critical */ }

    if (!isPrediction) return { context };

    try {
      setFetchingData(true);
      const predRes = await predictionsAPI.predictPrice(symbol, '1d', periods, 'ensemble');
      const data    = predRes.data;

      const predictions: Prediction[] = (data.predictions || []).map((p: any) => ({
        date:            p.date,
        predicted_price: p.predicted_price,
        lower_bound:     p.lower_bound   ?? p.predicted_price * 0.97,
        upper_bound:     p.upper_bound   ?? p.predicted_price * 1.03,
        change_pct:      p.change_pct    ?? 0,
        confidence:      p.confidence    ?? 50,
      }));

      context.predictions = predictions.map(p => ({
        date:            p.date,
        predicted_price: p.predicted_price,
        change_pct:      p.change_pct,
        confidence:      p.confidence,
      }));

      if (data.trend_analysis) {
        context.trend_analysis = data.trend_analysis;
      }

      const currentPrice = (context.market_data as any)?.price
        ?? predictions[0]?.predicted_price
        ?? 0;

      return {
        context,
        predictions,
        predMeta: { symbol, model: 'Ensemble', currentPrice },
      };
    } catch {
      return { context };
    } finally {
      setFetchingData(false);
    }
  };

  /* ── Submit ──────────────────────────────────────────────────────────── */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    const userMsg: Message = { role: 'user', content: userText };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setLoading(true);

    try {
      // Gather live context (+ predictions if requested)
      const { context, predictions, predMeta } = await gatherContext(userText);

      // Call AI with enriched context
      const history = newMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content }));
      const response = await aiAPI.chat(userText, history, context);

      const assistantMsg: Message = {
        role:            'assistant',
        content:         response.data.response,
        predictions:     predictions,
        predictionMeta:  predMeta,
      };
      setMessages([...newMessages, assistantMsg]);
    } catch {
      setMessages([...newMessages, {
        role:    'assistant',
        content: 'Вибачте, виникла помилка. Спробуйте ще раз.',
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleQuickQuestion = (q: string) => {
    setInput(q);
    inputRef.current?.focus();
  };

  /* ── Render ──────────────────────────────────────────────────────────── */
  return (
    <div className="flex flex-col h-[calc(100dvh-9rem)] min-h-[500px] max-h-[900px]">
      <div className="glass flex flex-col h-full overflow-hidden">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-5 py-4 shrink-0"
          style={{ borderBottom: '1px solid var(--c-border)' }}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00d4ff] to-[#7c3aed] flex items-center justify-center shadow-[0_0_12px_rgba(0,212,255,0.3)]">
            <Bot size={16} className="text-white" />
          </div>
          <div>
            <h2 className="section-title leading-none">AI Асистент</h2>
            <p className="mt-0.5 uppercase tracking-widest" style={{ fontSize: '10px', color: 'var(--c-text-3)' }}>
              Crypto Intelligence · ML Predictions
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2 text-xs" style={{ color: 'var(--c-text-3)' }}>
            <span className="glow-dot" />
            <span className="hidden sm:inline">Онлайн</span>
          </div>
        </div>

        {/* ── Messages ───────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-8">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, rgba(0,212,255,0.1), rgba(124,58,237,0.1))',
                  border: '1px solid var(--c-border)',
                }}
              >
                <Zap size={32} style={{ color: 'var(--c-accent)' }} />
              </div>
              <div>
                <p className="font-semibold mb-1" style={{ color: 'var(--c-text-2)' }}>Почніть розмову</p>
                <p className="text-sm" style={{ color: 'var(--c-text-3)' }}>
                  Запитайте прогноз, аналіз або задайте будь-яке питання
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {QUICK_QUESTIONS.map(q => (
                  <button
                    key={q}
                    onClick={() => handleQuickQuestion(q)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
                    style={{
                      border: '1px solid var(--c-border)',
                      color: 'var(--c-text-3)',
                      background: 'var(--c-bg-2)',
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.color = 'var(--c-accent)';
                      (e.currentTarget as HTMLElement).style.borderColor = 'var(--c-border-hover)';
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.color = 'var(--c-text-3)';
                      (e.currentTarget as HTMLElement).style.borderColor = 'var(--c-border)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 animate-fade-up ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                      style={{
                        background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(124,58,237,0.12))',
                        border: '1px solid var(--c-border)',
                      }}
                    >
                      <Bot size={14} style={{ color: 'var(--c-accent)' }} />
                    </div>
                  )}

                  <div className={`max-w-[82%] ${msg.role === 'user' ? '' : 'flex-1'}`}>
                    <div
                      className="rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
                      style={
                        msg.role === 'user'
                          ? {
                              background: 'linear-gradient(135deg, rgba(0,212,255,0.1), rgba(124,58,237,0.1))',
                              border: '1px solid rgba(0,212,255,0.2)',
                              color: 'var(--c-text-1)',
                            }
                          : {
                              background: 'var(--c-bg-1)',
                              border: '1px solid var(--c-border)',
                              color: 'var(--c-text-2)',
                            }
                      }
                    >
                      {msg.content}
                    </div>

                    {/* Prediction card */}
                    {msg.predictions && msg.predictions.length > 0 && msg.predictionMeta && (
                      <PredictionCard
                        predictions={msg.predictions}
                        meta={msg.predictionMeta}
                      />
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                      style={{
                        background: 'rgba(0,212,255,0.1)',
                        border: '1px solid rgba(0,212,255,0.25)',
                      }}
                    >
                      <User size={14} style={{ color: 'var(--c-accent)' }} />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading / fetching state */}
              {(loading || fetchingData) && (
                <div className="flex gap-3 justify-start animate-fade-up">
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                    style={{
                      background: 'linear-gradient(135deg, rgba(0,212,255,0.12), rgba(124,58,237,0.12))',
                      border: '1px solid var(--c-border)',
                    }}
                  >
                    <Bot size={14} style={{ color: 'var(--c-accent)' }} />
                  </div>
                  <div
                    className="rounded-xl px-4 py-3"
                    style={{ background: 'var(--c-bg-1)', border: '1px solid var(--c-border)' }}
                  >
                    {fetchingData ? (
                      <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--c-text-3)' }}>
                        <div className="cyber-spinner !w-3.5 !h-3.5 !border-[1.5px]" />
                        Завантаження ML прогнозів...
                      </div>
                    ) : (
                      <div className="flex gap-1.5 items-center h-4">
                        {[0, 0.15, 0.3].map((delay, i) => (
                          <div
                            key={i}
                            className="w-1.5 h-1.5 rounded-full animate-bounce"
                            style={{ backgroundColor: 'var(--c-accent)', animationDelay: `${delay}s` }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* ── Input ──────────────────────────────────────────────────── */}
        <form
          onSubmit={handleSubmit}
          className="px-4 py-4 shrink-0"
          style={{ borderTop: '1px solid var(--c-border)' }}
        >
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Запитайте прогноз, аналіз або будь-яке питання..."
              className="cyber-input flex-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary flex items-center gap-2 px-5 shrink-0"
            >
              <Send size={15} />
              <span className="hidden sm:inline">Надіслати</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
