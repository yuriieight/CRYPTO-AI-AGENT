import React, { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, TrendingDown, Target, RefreshCw } from 'lucide-react';
import { predictionsAPI } from '../services/api';
import { DynamicChart } from '../components/ChartTypes';

const MODELS = [
  { value: 'ensemble',          label: 'Ансамбль' },
  { value: 'gradient_boosting', label: 'Gradient Boosting' },
  { value: 'random_forest',     label: 'Random Forest' },
  { value: 'extra_trees',       label: 'Extra Trees' },
  { value: 'ada_boost',         label: 'AdaBoost' },
  { value: 'bayesian_ridge',    label: 'Bayesian Ridge' },
  { value: 'ridge',             label: 'Ridge' },
  { value: 'lasso',             label: 'Lasso' },
  { value: 'elastic_net',       label: 'Elastic Net' },
  { value: 'huber',             label: 'Huber' },
  { value: 'svr',               label: 'SVR' },
  { value: 'knn',               label: 'KNN' },
];

const TIMEFRAMES = [
  { value: '1h', label: '1 Год' },
  { value: '4h', label: '4 Год' },
  { value: '1d', label: '1 День' },
  { value: '1w', label: '1 Тиж' },
];

export const Predictions: React.FC<{ symbol: string }> = ({ symbol }) => {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [analysis, setAnalysis]       = useState<any>(null);
  const [metrics, setMetrics]         = useState<any>(null);
  const [loading, setLoading]         = useState(false);
  const [periods, setPeriods]         = useState(7);
  const [timeframe, setTimeframe]     = useState('1d');
  const [model, setModel]             = useState('ensemble');

  useEffect(() => { loadPredictions(); }, [symbol, periods, timeframe, model]);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const res = await predictionsAPI.predictPrice(symbol, timeframe, periods, model);
      setPredictions(res.data.predictions || []);
      setAnalysis(res.data.trend_analysis);
      setMetrics(res.data.training_metrics ?? null);
    } catch (e) {
      console.error('Predictions error:', e);
    } finally {
      setLoading(false);
    }
  };

  const isUp = (analysis?.trend ?? '').includes('uptrend');
  const isDown = (analysis?.trend ?? '').includes('downtrend');
  const strength: number = analysis?.strength ?? 0;
  const strengthColor = strength > 70 ? '#00ff88' : strength > 40 ? '#fbbf24' : '#ff3366';

  return (
    <div className="space-y-4">

      {/* ── Controls ───────────────────────────────────────────────────── */}
      <div className="glass p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">

          <div>
            <label className="label mb-2 block">Модель ML</label>
            <select value={model} onChange={e => setModel(e.target.value)} className="cyber-input">
              {MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          <div>
            <label className="label mb-2 block">Таймфрейм</label>
            <div className="flex gap-1 bg-[#0a1020] rounded-lg p-1">
              {TIMEFRAMES.map(tf => (
                <button
                  key={tf.value}
                  onClick={() => setTimeframe(tf.value)}
                  className={`flex-1 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    timeframe === tf.value ? 'bg-[#00d4ff] text-[#070b14]' : 'text-[#4a6080] hover:text-[#c8d8e8]'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label mb-2 block">Горизонт (днів): <span className="text-[#00d4ff] font-mono">{periods}</span></label>
            <input
              type="range" min="1" max="30" value={periods}
              onChange={e => setPeriods(parseInt(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
              style={{ accentColor: '#00d4ff' }}
            />
          </div>

          <button onClick={loadPredictions} disabled={loading} className="btn-primary h-10 flex items-center justify-center gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Завантаження...' : 'Оновити'}
          </button>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="mt-4 flex flex-wrap gap-4 pt-4 border-t border-[#1a2d4a]">
            <span className="label">Навчання ({model}):</span>
            {[
              { k: 'MAE',  v: metrics.mae },
              { k: 'RMSE', v: metrics.rmse },
              { k: 'R²',   v: metrics.r2 },
              { k: 'MAPE', v: metrics.mape, suffix: '%' },
            ].map(({ k, v, suffix = '' }) => (
              <div key={k} className="flex items-center gap-1.5">
                <span className="label">{k}</span>
                <span className="font-mono text-xs text-[#00d4ff]">{v}{suffix}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Trend summary ───────────────────────────────────────────────── */}
      {analysis && (
        <div className="glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <Target size={18} className="text-[#00d4ff]" />
            <h3 className="section-title">Аналіз Тренду</h3>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="label mb-2">Тренд</p>
              <span className={`badge text-sm px-3 py-1.5 ${isUp ? 'badge-green' : isDown ? 'badge-red' : 'badge-yellow'}`}>
                {isUp ? <TrendingUp size={12} /> : isDown ? <TrendingDown size={12} /> : null}
                {(analysis.trend ?? '').replace(/_/g, ' ').toUpperCase() || 'N/A'}
              </span>
            </div>

            <div>
              <p className="label mb-2">Сила</p>
              <div className="flex items-center gap-2">
                <div className="progress-track flex-1">
                  <div style={{ width: `${strength}%`, height: '100%', borderRadius: 9999, background: `linear-gradient(90deg, ${strengthColor}, ${strengthColor}99)`, transition: 'width 0.4s' }} />
                </div>
                <span className="font-mono text-sm font-bold" style={{ color: strengthColor }}>{strength}</span>
              </div>
            </div>

            <div>
              <p className="label mb-2">RSI</p>
              <p className="font-mono font-bold text-2xl text-[#e8f4ff]">{analysis.rsi?.toFixed(1)}</p>
            </div>

            <div>
              <p className="label mb-2">Поточна Ціна</p>
              <p className="font-mono font-bold text-2xl text-[#00d4ff]">${analysis.current_price?.toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Chart + table ───────────────────────────────────────────────── */}
      {predictions.length > 0 && (
        <div className="glass p-5 space-y-5">
          <h3 className="section-title">Прогноз — {symbol} · {periods} днів</h3>

          {loading ? (
            <div className="flex justify-center items-center h-64"><div className="cyber-spinner" /></div>
          ) : (
            <>
              <DynamicChart
                data={predictions.map(p => ({ timestamp: p.date, close: p.predicted_price, volume: 0 }))}
                type="area" color="#00d4ff" height={300}
              />

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full cyber-table text-xs">
                  <thead>
                    <tr>
                      <th>Дата</th>
                      <th className="text-right">Прогноз</th>
                      <th className="text-right">Мін</th>
                      <th className="text-right">Макс</th>
                      <th className="text-right">Зміна %</th>
                      <th className="text-right">Впевненість</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((pred, i) => {
                      const chg = pred.change_pct ?? 0;
                      const conf: number = pred.confidence ?? 0;
                      const confColor = conf > 70 ? '#00ff88' : conf > 40 ? '#fbbf24' : '#ff3366';
                      return (
                        <tr key={i}>
                          <td className="font-mono text-[#4a6080]">{pred.date}</td>
                          <td className="text-right font-mono font-bold text-[#e8f4ff]">
                            ${pred.predicted_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="text-right font-mono text-[#4a6080]">
                            ${pred.lower_bound?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="text-right font-mono text-[#4a6080]">
                            ${pred.upper_bound?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="text-right">
                            <span className={chg >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'} style={{ fontFamily: 'monospace' }}>
                              {chg >= 0 ? '+' : ''}{chg.toFixed(2)}%
                            </span>
                          </td>
                          <td className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-14 progress-track">
                                <div style={{ width: `${conf}%`, height: '100%', borderRadius: 9999, background: confColor, transition: 'width 0.3s' }} />
                              </div>
                              <span className="font-mono text-xs" style={{ color: confColor }}>{conf}%</span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Disclaimer ──────────────────────────────────────────────────── */}
      <div className="flex items-start gap-3 px-4 py-3 rounded-xl border border-[#fbbf2430] bg-[#fbbf2408]">
        <AlertTriangle size={16} className="text-[#fbbf24] shrink-0 mt-0.5" />
        <p className="text-xs text-[#4a6080] leading-relaxed">
          <span className="text-[#fbbf24] font-semibold">Застереження:</span> Прогнози ML базуються на історичних даних і не є фінансовою порадою.
          Ринок криптовалют надзвичайно волатильний. Інвестуйте відповідально.
        </p>
      </div>
    </div>
  );
};
