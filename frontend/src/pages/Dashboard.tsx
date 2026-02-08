import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, DollarSign, Activity,
  Play, Brain, BarChart2, AlertCircle, Layers,
} from 'lucide-react';
import { marketAPI, portfolioAPI, predictionsAPI } from '../services/api';

interface DashboardStats {
  totalAssets: number;
  portfolioValue: number;
  profitLoss: number;
  roi: number;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats]         = useState<DashboardStats>({ totalAssets:0, portfolioValue:0, profitLoss:0, roi:0 });
  const [topCryptos, setTopCryptos] = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);
  const [runningBacktest, setRunning]  = useState<Record<string, boolean>>({});
  const [backtestResults, setResults]  = useState<Record<string, any>>({});
  const [backtestErrors, setErrors]    = useState<Record<string, string>>({});

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [perfRes, cryptoRes] = await Promise.all([
        portfolioAPI.getPerformance('demo-user'),
        marketAPI.getTopCryptos(10),
      ]);
      setStats({
        totalAssets:    perfRes.data.assets?.length || 0,
        portfolioValue: perfRes.data.current_value  || 0,
        profitLoss:     perfRes.data.profit_loss     || 0,
        roi:            perfRes.data.profit_loss_percent || 0,
      });
      setTopCryptos(cryptoRes.data || []);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickBacktest = async (symbol: string) => {
    setRunning(prev => ({ ...prev, [symbol]: true }));
    setErrors(prev  => ({ ...prev, [symbol]: '' }));
    setResults(prev => ({ ...prev, [symbol]: null }));
    try {
      const formattedSymbol = symbol.includes('/') ? symbol : `${symbol}/USDT`;
      const { data } = await predictionsAPI.runBacktest(formattedSymbol, '1d', 'gradient_boosting');
      setResults(prev => ({ ...prev, [symbol]: {
        win_rate:         data.win_rate         ?? 0,
        final_capital:    data.final_capital     ?? 1000,
        total_trades:     data.total_trades      ?? 0,
        max_drawdown:     data.max_drawdown_pct  ?? 0,
        sharpe_ratio:     data.sharpe_ratio      ?? 0,
        profit_factor:    data.profit_factor     ?? 0,
        total_return_pct: data.total_return_pct  ?? 0,
      }}));
    } catch (err: any) {
      setErrors(prev => ({ ...prev, [symbol]: err.message }));
    } finally {
      setRunning(prev => ({ ...prev, [symbol]: false }));
    }
  };

  const statCards = [
    {
      label: 'Всього Активів',
      value: String(stats.totalAssets),
      icon: <Layers size={18} className="text-[#00d4ff]" />,
      accent: '#00d4ff',
    },
    {
      label: 'Вартість Портфеля',
      value: `$${stats.portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      icon: <DollarSign size={18} className="text-[#00ff88]" />,
      accent: '#00ff88',
    },
    {
      label: 'Прибуток / Збиток',
      value: `${stats.profitLoss >= 0 ? '+' : ''}$${Math.abs(stats.profitLoss).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      icon: stats.profitLoss >= 0
        ? <TrendingUp size={18} className="text-[#00ff88]" />
        : <TrendingDown size={18} className="text-[#ff3366]" />,
      accent: stats.profitLoss >= 0 ? '#00ff88' : '#ff3366',
    },
    {
      label: 'ROI',
      value: `${stats.roi >= 0 ? '+' : ''}${stats.roi.toFixed(2)}%`,
      icon: stats.roi >= 0
        ? <TrendingUp size={18} className="text-[#00ff88]" />
        : <TrendingDown size={18} className="text-[#ff3366]" />,
      accent: stats.roi >= 0 ? '#00ff88' : '#ff3366',
    },
  ];

  return (
    <div className="space-y-6">

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(card => (
          <div
            key={card.label}
            className="glass-hover p-5 group"
            style={{ borderColor: `${card.accent}22` }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="label">{card.label}</span>
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: `${card.accent}18` }}
              >
                {card.icon}
              </div>
            </div>
            <p
              className="font-mono font-bold text-xl sm:text-2xl"
              style={{ color: card.accent }}
            >
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* ── Market table ───────────────────────────────────────────────── */}
      <div className="glass overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1a2d4a]">
          <div className="flex items-center gap-3">
            <Activity size={18} className="text-[#00d4ff]" />
            <h2 className="section-title">Топ Криптовалют</h2>
          </div>
          <span className="badge-cyan">
            <Brain size={12} /> AI Аналітика
          </span>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="cyber-spinner" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full cyber-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Пара</th>
                  <th className="text-right">Ціна</th>
                  <th className="text-right">24г %</th>
                  <th className="text-right">Обсяг</th>
                  <th className="text-right pr-5">AI Бектест</th>
                </tr>
              </thead>
              <tbody>
                {topCryptos.map((c, idx) => {
                  const up = c.change_percent_24h >= 0;
                  return (
                    <tr key={c.symbol}>
                      <td className="font-mono text-[#2a4060] w-10">{idx + 1}</td>

                      <td>
                        <span className="font-mono font-bold text-[#e8f4ff]">{c.symbol}</span>
                      </td>

                      <td className="text-right">
                        <span className="font-mono font-semibold text-[#c8d8e8]">
                          ${c.price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                        </span>
                      </td>

                      <td className="text-right">
                        <span className={`badge ${up ? 'badge-green' : 'badge-red'}`}>
                          {up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                          {up ? '+' : ''}{c.change_percent_24h?.toFixed(2)}%
                        </span>
                      </td>

                      <td className="text-right font-mono text-[#4a6080] text-xs">
                        ${(c.volume_24h / 1e6).toFixed(1)}M
                      </td>

                      <td className="text-right pr-5 min-w-[180px]">
                        {runningBacktest[c.symbol] ? (
                          <div className="flex justify-end items-center gap-2 text-[#00d4ff] text-xs">
                            <div className="cyber-spinner !w-4 !h-4 !border-[1.5px]" />
                            Обчислення...
                          </div>
                        ) : backtestErrors[c.symbol] ? (
                          <div className="flex flex-col items-end gap-1">
                            <span className="badge-red"><AlertCircle size={10} /> Помилка</span>
                            <button
                              onClick={() => setErrors(p => ({ ...p, [c.symbol]: '' }))}
                              className="text-[10px] text-[#4a6080] hover:text-[#00d4ff] underline"
                            >Повторити</button>
                          </div>
                        ) : backtestResults[c.symbol] ? (
                          <BacktestResult result={backtestResults[c.symbol]} />
                        ) : (
                          <button
                            onClick={() => handleQuickBacktest(c.symbol)}
                            className="ml-auto flex items-center gap-1.5 text-xs border border-[#1a3a5c] text-[#00d4ff]
                                       hover:bg-[#00d4ff] hover:text-[#070b14] px-3 py-1.5 rounded-lg
                                       font-semibold transition-all duration-150"
                          >
                            <Play size={11} /> Тест
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

/* ── Backtest result mini-widget ─────────────────────────────────────────── */
function BacktestResult({ result }: { result: any }) {
  const isUp = result.total_return_pct >= 0;
  return (
    <div className="flex flex-col items-end gap-1 text-xs animate-fade-up">
      <div className="flex items-center gap-2">
        <span className="text-[#4a6080]">Win</span>
        <span className="font-mono font-bold text-[#c8d8e8]">{result.win_rate?.toFixed(1)}%</span>
        <span className="text-[#2a4060]">({result.total_trades} угод)</span>
      </div>
      <div className={`font-mono font-bold ${isUp ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
        <BarChart2 size={10} className="inline mr-1" />
        {isUp ? '+' : ''}{result.total_return_pct?.toFixed(2)}%
      </div>
      <div className="text-[#2a4060] flex gap-2">
        <span>Sharpe {result.sharpe_ratio?.toFixed(2)}</span>
        <span>DD {result.max_drawdown?.toFixed(1)}%</span>
      </div>
    </div>
  );
}
