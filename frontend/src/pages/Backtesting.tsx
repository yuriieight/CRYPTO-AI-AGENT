import React, { useState } from 'react';
import { Play, TrendingUp, AlertTriangle, Activity, DollarSign, Percent } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { predictionsAPI } from '../services/api';

const MODELS = [
  { value: 'ensemble',          label: 'Ансамбль' },
  { value: 'gradient_boosting', label: 'Gradient Boosting' },
  { value: 'random_forest',     label: 'Random Forest' },
  { value: 'extra_trees',       label: 'Extra Trees' },
  { value: 'ada_boost',         label: 'AdaBoost' },
  { value: 'ridge',             label: 'Ridge' },
  { value: 'lasso',             label: 'Lasso' },
  { value: 'elastic_net',       label: 'Elastic Net' },
  { value: 'bayesian_ridge',    label: 'Bayesian Ridge' },
  { value: 'huber',             label: 'Huber' },
  { value: 'svr',               label: 'SVR' },
  { value: 'knn',               label: 'KNN' },
];

const SYMBOLS = [
  { value: 'BTC/USDT', label: 'Bitcoin (BTC)' },
  { value: 'ETH/USDT', label: 'Ethereum (ETH)' },
  { value: 'SOL/USDT', label: 'Solana (SOL)' },
  { value: 'BNB/USDT', label: 'BNB' },
  { value: 'XRP/USDT', label: 'XRP' },
];

const TIMEFRAMES = [
  { value: '1d', label: '1Д' },
  { value: '4h', label: '4Г' },
  { value: '1h', label: '1Г' },
];

export const Backtesting: React.FC = () => {
  const [loading, setLoading]   = useState(false);
  const [results, setResults]   = useState<any>(null);
  const [error, setError]       = useState<string | null>(null);
  const [symbol, setSymbol]     = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1d');
  const [model, setModel]       = useState('gradient_boosting');

  const runBacktest = async () => {
    setLoading(true); setError(null);
    try {
      const { data } = await predictionsAPI.runBacktest(symbol, timeframe, model);
      setResults(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Помилка бектестингу');
    } finally {
      setLoading(false);
    }
  };

  const r = results;
  const totalReturn = r?.total_return_pct ?? 0;
  const isProfit = totalReturn >= 0;

  return (
    <div className="space-y-4">

      {/* ── Controls ───────────────────────────────────────────────────── */}
      <div className="glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={18} className="text-[#00d4ff]" />
          <h2 className="section-title">Симуляція торгівлі (Walk-Forward Backtesting)</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div>
            <label className="label mb-2 block">Торгова пара</label>
            <select value={symbol} onChange={e => setSymbol(e.target.value)} className="cyber-input">
              {SYMBOLS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
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
            <label className="label mb-2 block">ML Модель</label>
            <select value={model} onChange={e => setModel(e.target.value)} className="cyber-input">
              {MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          <button onClick={runBacktest} disabled={loading} className="btn-primary h-10 flex items-center justify-center gap-2">
            {loading ? <div className="cyber-spinner !w-5 !h-5 !border-[1.5px]" /> : <Play size={15} />}
            {loading ? 'Симуляція...' : 'Запустити'}
          </button>
        </div>
      </div>

      {/* ── Error ──────────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl border border-[#ff336630] bg-[#ff336608] text-[#ff3366] text-sm">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* ── Results ────────────────────────────────────────────────────── */}
      {results && (
        <div className="space-y-4 animate-fade-up">

          {/* Primary metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { icon: <DollarSign size={16} />, label: 'Фінальний баланс', value: `$${(r.final_capital ?? 0).toFixed(2)}`, color: isProfit ? '#00ff88' : '#ff3366' },
              { icon: <TrendingUp size={16} />,  label: 'Загальний прибуток', value: `${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`, color: isProfit ? '#00ff88' : '#ff3366' },
              { icon: <Percent size={16} />,     label: `Win Rate · ${r.total_trades ?? 0} угод`, value: `${(r.win_rate ?? 0).toFixed(1)}%`, color: '#00d4ff' },
              { icon: <Activity size={16} />,    label: 'Max Drawdown', value: `-${(r.max_drawdown_pct ?? 0).toFixed(2)}%`, color: '#ff3366' },
            ].map(card => (
              <div key={card.label} className="glass-hover p-4" style={{ borderColor: `${card.color}22` }}>
                <div className="flex items-center gap-2 mb-2" style={{ color: card.color }}>
                  {card.icon}
                  <span className="label">{card.label}</span>
                </div>
                <p className="font-mono font-bold text-xl sm:text-2xl" style={{ color: card.color }}>
                  {card.value}
                </p>
              </div>
            ))}
          </div>

          {/* Secondary */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: 'Sharpe Ratio',  value: (r.sharpe_ratio  ?? 0).toFixed(3), color: '#00d4ff' },
              { label: 'Profit Factor', value: (r.profit_factor ?? 0).toFixed(2), color: '#a78bfa' },
              { label: 'Avg Win',       value: `$${(r.avg_win  ?? 0).toFixed(2)}`, color: '#00ff88' },
              { label: 'Avg Loss',      value: `$${(r.avg_loss ?? 0).toFixed(2)}`, color: '#ff3366' },
            ].map(card => (
              <div key={card.label} className="glass p-4">
                <p className="label mb-1">{card.label}</p>
                <p className="font-mono font-bold text-lg" style={{ color: card.color }}>{card.value}</p>
              </div>
            ))}
          </div>

          {/* Prediction accuracy */}
          {r.prediction_metrics && (
            <div className="glass p-5">
              <p className="section-title mb-3">Точність моделі — {model}</p>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { k: 'MAE',  v: r.prediction_metrics.mae?.toFixed(4) },
                  { k: 'RMSE', v: r.prediction_metrics.rmse?.toFixed(4) },
                  { k: 'R²',   v: r.prediction_metrics.r2?.toFixed(4) },
                  { k: 'MAPE', v: `${r.prediction_metrics.mape?.toFixed(2)}%` },
                ].map(({ k, v }) => (
                  <div key={k}>
                    <p className="label mb-1">{k}</p>
                    <p className="font-mono font-bold text-lg text-[#00d4ff]">{v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Equity curve */}
          {r.equity_curve?.length > 0 && (
            <div className="glass p-5">
              <h3 className="section-title mb-4">Крива капіталу (Equity Curve)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={r.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a2d4a" vertical={false} />
                  <XAxis dataKey="date"
                    tickFormatter={v => new Date(v).toLocaleDateString('uk-UA')}
                    stroke="#2a4060" tick={{ fontSize: 10, fill: '#4a6080' }} />
                  <YAxis domain={['auto', 'auto']}
                    tickFormatter={v => `$${v}`}
                    stroke="#2a4060" tick={{ fontSize: 10, fill: '#4a6080' }} />
                  <Tooltip
                    contentStyle={{ background: '#0d1628', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8 }}
                    labelStyle={{ color: '#4a6080' }}
                    formatter={(v: any) => [`$${parseFloat(v).toFixed(2)}`]}
                    labelFormatter={l => new Date(l).toLocaleDateString('uk-UA')}
                  />
                  <Legend wrapperStyle={{ color: '#4a6080', fontSize: 12 }} />
                  <Line type="monotone" dataKey="equity" name="AI Модель"
                    stroke="#00d4ff" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: '#00d4ff' }} />
                  {r.equity_curve[0]?.buy_and_hold !== undefined && (
                    <Line type="monotone" dataKey="buy_and_hold" name="Купив і тримай"
                      stroke="#4a6080" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Recent trades */}
          {r.recent_trades?.length > 0 && (
            <div className="glass overflow-hidden">
              <div className="px-5 py-4 border-b border-[#1a2d4a]">
                <h4 className="section-title">Останні угоди</h4>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full cyber-table text-xs">
                  <thead>
                    <tr>
                      <th>Вхід $</th>
                      <th>Вихід $</th>
                      <th className="text-right">P&L</th>
                      <th className="text-right">Повернення</th>
                      <th>Причина</th>
                      <th className="text-right">Барів</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.recent_trades.map((t: any, i: number) => (
                      <tr key={i}>
                        <td className="font-mono">${t.entry?.toFixed(2)}</td>
                        <td className="font-mono">${t.exit?.toFixed(2)}</td>
                        <td className={`text-right font-mono font-bold ${t.pnl >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                          {t.pnl >= 0 ? '+' : ''}${t.pnl?.toFixed(2)}
                        </td>
                        <td className={`text-right font-mono ${t.return_pct >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                          {t.return_pct >= 0 ? '+' : ''}{t.return_pct?.toFixed(2)}%
                        </td>
                        <td className="text-[#4a6080]">{t.reason}</td>
                        <td className="text-right font-mono text-[#4a6080]">{t.bars_held}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {!results && !loading && (
        <div className="glass flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#00d4ff12] border border-[#00d4ff30] flex items-center justify-center mb-4">
            <TrendingUp size={32} className="text-[#00d4ff]" />
          </div>
          <p className="text-[#4a6080] text-sm">Оберіть пару, таймфрейм і модель — потім натисніть <span className="text-[#00d4ff]">Запустити</span></p>
        </div>
      )}
    </div>
  );
};
