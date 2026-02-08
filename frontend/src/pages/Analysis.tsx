import React, { useState, useEffect } from 'react';
import { analysisAPI } from '../services/api';
import { TrendingUp, TrendingDown, Activity, Zap, ShieldAlert, BarChart2 } from 'lucide-react';

export const Analysis: React.FC<{ symbol: string }> = ({ symbol }) => {
  const [indicators, setIndicators] = useState<any>(null);
  const [signals, setSignals]       = useState<any>(null);
  const [trend, setTrend]           = useState<any>(null);
  const [loading, setLoading]       = useState(true);

  useEffect(() => { loadAnalysis(); }, [symbol]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const [indRes, sigRes, trendRes] = await Promise.all([
        analysisAPI.getIndicators(symbol),
        analysisAPI.getSignals(symbol),
        analysisAPI.getTrend(symbol),
      ]);
      setIndicators(indRes.data);
      setSignals(sigRes.data);
      setTrend(trendRes.data);
    } catch (e) {
      console.error('Analysis error:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="cyber-spinner" />
      </div>
    );
  }

  const trendType: string = trend?.trend?.trend || '';
  const isUp    = trendType.includes('uptrend');
  const isDown  = trendType.includes('downtrend');
  const signal  = signals?.signals?.signal;
  const isBuy   = signal === 'buy';
  const isSell  = signal === 'sell';

  const strength: number = trend?.trend?.strength ?? 0;
  const strengthColor = strength > 70 ? '#00ff88' : strength > 40 ? '#fbbf24' : '#ff3366';

  return (
    <div className="space-y-4">

      {/* ── Trend + signal overview ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Trend */}
        {trend && (
          <div className="glass p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-[#00d4ff]" />
              <h3 className="section-title">Аналіз Тренду</h3>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Trend badge */}
              <div>
                <p className="label mb-2">Тренд</p>
                <span className={`badge text-sm px-3 py-1.5 ${isUp ? 'badge-green' : isDown ? 'badge-red' : 'badge-yellow'}`}>
                  {isUp ? <TrendingUp size={14} /> : isDown ? <TrendingDown size={14} /> : <Activity size={14} />}
                  {trendType.replace(/_/g, ' ').toUpperCase() || 'N/A'}
                </span>
              </div>

              {/* RSI */}
              <div>
                <p className="label mb-2">RSI</p>
                <p className="font-mono font-bold text-2xl text-[#e8f4ff]">
                  {trend.trend?.rsi?.toFixed(1)}
                </p>
                <p className="text-xs mt-0.5" style={{
                  color: (trend.trend?.rsi > 70) ? '#ff3366' : (trend.trend?.rsi < 30) ? '#00ff88' : '#4a6080'
                }}>
                  {trend.trend?.rsi > 70 ? '⬤ Перекуплено' : trend.trend?.rsi < 30 ? '⬤ Перепродано' : '⬤ Нейтрально'}
                </p>
              </div>

              {/* Strength */}
              <div>
                <p className="label mb-2">Сила тренду</p>
                <div className="flex items-center gap-2">
                  <div className="progress-track flex-1">
                    <div className="progress-fill-cyan" style={{ width: `${strength}%`, background: `linear-gradient(90deg, ${strengthColor}, ${strengthColor}99)` }} />
                  </div>
                  <span className="font-mono font-bold text-sm" style={{ color: strengthColor }}>{strength}</span>
                </div>
              </div>

              {/* MACD */}
              <div>
                <p className="label mb-2">MACD</p>
                <p className={`font-mono font-bold text-2xl ${(trend.trend?.macd ?? 0) > 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                  {trend.trend?.macd?.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Signal */}
        {signals && (
          <div className="glass p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-[#fbbf24]" />
              <h3 className="section-title">Торговий Сигнал</h3>
            </div>

            <div className="flex items-center gap-4">
              {/* Big signal badge */}
              <div
                className={`w-20 h-20 rounded-xl flex flex-col items-center justify-center shrink-0 border-2 ${
                  isBuy  ? 'border-[#00ff88] bg-[#00ff8812] shadow-[0_0_20px_rgba(0,255,136,0.15)]' :
                  isSell ? 'border-[#ff3366] bg-[#ff336612] shadow-[0_0_20px_rgba(255,51,102,0.15)]' :
                  'border-[#1a2d4a] bg-[#0a1020]'
                }`}
              >
                {isBuy  ? <TrendingUp size={28} className="text-[#00ff88]" /> :
                 isSell ? <TrendingDown size={28} className="text-[#ff3366]" /> :
                 <Activity size={28} className="text-[#4a6080]" />}
                <span className={`font-mono font-bold text-sm mt-1 ${
                  isBuy ? 'text-[#00ff88]' : isSell ? 'text-[#ff3366]' : 'text-[#4a6080]'
                }`}>
                  {signal?.toUpperCase() ?? '—'}
                </span>
              </div>

              {/* Strength bars */}
              <div className="flex-1 space-y-1.5">
                <p className="label mb-2">Сила сигналу</p>
                <div className="flex gap-1">
                  {[...Array(10)].map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 h-6 rounded-sm transition-all"
                      style={{
                        background: i < (signals.signals?.strength ?? 0)
                          ? (isBuy ? '#00ff88' : isSell ? '#ff3366' : '#00d4ff')
                          : '#0f1b30',
                        opacity: i < (signals.signals?.strength ?? 0) ? 1 - i * 0.06 : 0.3,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Reasoning */}
            <div className="bg-[#0a1020] rounded-lg p-3 border border-[#1a2d4a]">
              <p className="text-xs text-[#4a6080] mb-1">Аналіз</p>
              <p className="text-sm text-[#c8d8e8] leading-relaxed">{signals.signals?.reasoning}</p>
            </div>
          </div>
        )}
      </div>

      {/* ── Price levels ────────────────────────────────────────────────── */}
      {signals && (
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert size={18} className="text-[#7c3aed]" />
            <h3 className="section-title">Рівні Ціни</h3>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: 'Вхід',         value: signals.signals?.entry_price,       color: '#00d4ff', bg: '#00d4ff12', icon: '→' },
              { label: 'Стоп-Лосс',    value: signals.signals?.stop_loss,         color: '#ff3366', bg: '#ff336612', icon: '↓' },
              { label: 'Тейк-Профіт',  value: signals.signals?.take_profit,       color: '#00ff88', bg: '#00ff8812', icon: '↑' },
              { label: 'Ризик/Профіт', value: null, rr: signals.signals?.risk_reward_ratio, color: '#a78bfa', bg: '#7c3aed12', icon: '⚖' },
            ].map(item => (
              <div key={item.label} className="rounded-xl p-4 border" style={{ background: item.bg, borderColor: `${item.color}30` }}>
                <p className="label mb-2">{item.icon} {item.label}</p>
                <p className="font-mono font-bold text-xl" style={{ color: item.color }}>
                  {item.rr != null
                    ? `1:${item.rr.toFixed(2)}`
                    : `$${item.value?.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? '—'}`
                  }
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Technical Indicators grid ───────────────────────────────────── */}
      {indicators && (
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={18} className="text-[#00d4ff]" />
            <h3 className="section-title">Технічні Індикатори</h3>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {Object.entries(indicators.indicators || {}).map(([key, val]: [string, any]) => {
              const n = typeof val === 'number' ? val : null;
              return (
                <div key={key} className="bg-[#0a1020] rounded-lg p-3 border border-[#1a2d4a] hover:border-[#00d4ff33] transition-colors">
                  <p className="label mb-1 truncate">{key}</p>
                  <p className="font-mono font-semibold text-sm text-[#e8f4ff]">
                    {n != null ? n.toFixed(key === 'RSI' ? 1 : 2) : String(val)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
