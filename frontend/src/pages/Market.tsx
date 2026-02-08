import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart2, RefreshCw } from 'lucide-react';
import { marketAPI } from '../services/api';
import { DynamicChart, ChartTypeSelector } from '../components/ChartTypes';

export const Market: React.FC<{ symbol: string }> = ({ symbol }) => {
  const [chartType, setChartType] = useState('candlestick');
  const [timeframe, setTimeframe] = useState('1d');
  const [data, setData]           = useState<any[]>([]);
  const [ticker, setTicker]       = useState<any>(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => { loadMarketData(); }, [symbol, timeframe]);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      const [histRes, tickRes] = await Promise.all([
        marketAPI.getHistory(symbol, timeframe, 100),
        marketAPI.getTicker(symbol),
      ]);
      setData(histRes.data || []);
      setTicker(tickRes.data);
    } catch (e) {
      console.error('Market data error:', e);
    } finally {
      setLoading(false);
    }
  };

  const TIMEFRAMES = [
    { value: '1h', label: '1Г' },
    { value: '4h', label: '4Г' },
    { value: '1d', label: '1Д' },
    { value: '1w', label: '1Т' },
  ];

  const up = (ticker?.change_percent_24h ?? 0) >= 0;

  return (
    <div className="space-y-4">

      {/* ── Ticker header ──────────────────────────────────────────────── */}
      {ticker && (
        <div className="glass p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">

            {/* Left: symbol + price */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="label">Торгова Пара</span>
                <span className={`badge ${up ? 'badge-green' : 'badge-red'}`}>
                  {up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                  {up ? '+' : ''}{ticker.change_percent_24h?.toFixed(2)}%
                </span>
              </div>
              <h2 className="font-mono font-bold text-2xl text-[#e8f4ff]">{symbol}</h2>
              <p className={`font-mono font-bold text-4xl mt-1 ${up ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                ${ticker.price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
            </div>

            {/* Right: 24h stats */}
            <div className="grid grid-cols-3 gap-4 sm:gap-6">
              {[
                { label: 'Макс 24г', value: `$${ticker.high_24h?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, color: '#00ff88' },
                { label: 'Мін 24г',  value: `$${ticker.low_24h?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,  color: '#ff3366' },
                { label: 'Обсяг',    value: `$${(ticker.volume_24h / 1e6).toFixed(2)}M`,                                   color: '#00d4ff' },
              ].map(stat => (
                <div key={stat.label}>
                  <p className="label mb-1">{stat.label}</p>
                  <p className="font-mono font-semibold text-sm sm:text-base" style={{ color: stat.color }}>
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Chart card ─────────────────────────────────────────────────── */}
      <div className="glass p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div className="flex items-center gap-2">
            <BarChart2 size={18} className="text-[#00d4ff]" />
            <h3 className="section-title">Графік Ціни</h3>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Timeframe pills */}
            <div className="flex gap-1 bg-[#0a1020] rounded-lg p-1">
              {TIMEFRAMES.map(tf => (
                <button
                  key={tf.value}
                  onClick={() => setTimeframe(tf.value)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition-all duration-150 ${
                    timeframe === tf.value
                      ? 'bg-[#00d4ff] text-[#070b14]'
                      : 'text-[#4a6080] hover:text-[#c8d8e8]'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <ChartTypeSelector currentType={chartType} onTypeChange={setChartType} />

            <button
              onClick={loadMarketData}
              className="p-2 rounded-lg border border-[#1a2d4a] text-[#4a6080] hover:text-[#00d4ff] hover:border-[#00d4ff44] transition-all"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-96">
            <div className="cyber-spinner" />
          </div>
        ) : (
          <DynamicChart data={data} type={chartType as any} height={420} color="#00d4ff" />
        )}
      </div>
    </div>
  );
};
