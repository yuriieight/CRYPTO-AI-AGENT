import { useState, useEffect, useCallback } from 'react';
import {
  Search, TrendingUp, TrendingDown, BarChart2,
  BookOpen, RefreshCw, ChevronRight, X,
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { stocksAPI } from '../services/api';

// ── Types ──────────────────────────────────────────────────────────────────

interface Stock {
  symbol:      string;
  name:        string;
  sector:      string;
  price:       number | null;
  change_pct:  number | null;
  market_cap_fmt?: string;
  pe_ratio?:   number | null;
  volume?:     number | null;
}

interface Sector {
  sector:     string;
  change_pct: number;
  etf?:       string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const pct = (v: number | null | undefined) => {
  if (v == null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
};
const usd = (v: number | null | undefined, decimals = 2) => {
  if (v == null) return '—';
  return `$${v.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};
const colorClass = (v: number | null | undefined) =>
  v == null ? 'text-[#4a6080]' : v >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]';

const CHART_GRID  = 'rgba(26,45,74,0.6)';
const AXIS_STROKE = '#4a6080';
const TOOLTIP_STYLE = {
  contentStyle: { background: '#0d1628', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8 },
  labelStyle:   { color: '#c8d8e8' },
  itemStyle:    { color: '#00d4ff' },
};

const PERIODS = [
  { label: '1M',  value: '1mo',  interval: '1d'  },
  { label: '3M',  value: '3mo',  interval: '1d'  },
  { label: '6M',  value: '6mo',  interval: '1d'  },
  { label: '1Y',  value: '1y',   interval: '1wk' },
  { label: '5Y',  value: '5y',   interval: '1mo' },
];

// ── Main Component ─────────────────────────────────────────────────────────

export const Stocks: React.FC = () => {
  const [tab, setTab]               = useState<'market' | 'sectors' | 'compare'>('market');
  const [stocks, setStocks]         = useState<Stock[]>([]);
  const [sectors, setSectors]       = useState<Sector[]>([]);
  const [loading, setLoading]       = useState(true);
  const [selected, setSelected]     = useState<string | null>(null);
  const [searchQ, setSearchQ]       = useState('');
  const [searchRes, setSearchRes]   = useState<any[]>([]);
  const [searchLoading, setSearchL] = useState(false);

  useEffect(() => { loadMarket(); }, []);

  const loadMarket = async () => {
    setLoading(true);
    try {
      const [stocksRes, sectorsRes] = await Promise.all([
        stocksAPI.getTop(15),
        stocksAPI.getSectors(),
      ]);
      setStocks(stocksRes.data || []);
      setSectors(sectorsRes.data.sectors || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!searchQ.trim()) { setSearchRes([]); return; }
    const t = setTimeout(async () => {
      setSearchL(true);
      try {
        const res = await stocksAPI.search(searchQ, 8);
        setSearchRes(res.data.results || []);
      } finally {
        setSearchL(false);
      }
    }, 400);
    return () => clearTimeout(t);
  }, [searchQ]);

  const openStock = (symbol: string) => {
    setSelected(symbol);
    setSearchQ('');
    setSearchRes([]);
  };

  const TABS = [
    { id: 'market',   label: 'Ринок' },
    { id: 'sectors',  label: 'Сектори' },
    { id: 'compare',  label: 'Порівняння' },
  ] as const;

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="glass p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="section-title text-lg">Фондовий Ринок</h1>
            <p className="text-xs text-[#4a6080] mt-0.5">Акції NYSE / Nasdaq · Дані: Yahoo Finance & Alpha Vantage</p>
          </div>

          {/* Search */}
          <div className="relative w-full md:w-72">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a6080]" />
            <input
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
              placeholder="Пошук: AAPL, Tesla, …"
              className="cyber-input pl-9"
            />
            {searchLoading && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin" />
            )}
            {searchRes.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#0d1628] border border-[#1a2d4a] rounded-xl shadow-xl z-20 overflow-hidden">
                {searchRes.map(r => (
                  <button
                    key={r.symbol}
                    onClick={() => openStock(r.symbol)}
                    className="w-full px-4 py-2.5 text-left flex justify-between items-center
                               border-b border-[#0f1b2a] last:border-0
                               hover:bg-[#00d4ff08] transition-colors"
                  >
                    <span className="font-mono font-bold text-[#e8f4ff] text-sm">{r.symbol}</span>
                    <span className="text-xs text-[#4a6080] truncate max-w-[150px]">{r.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-[#0a1020] p-1 rounded-lg w-fit">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all duration-150 ${
                tab === t.id
                  ? 'bg-[#00d4ff] text-[#070b14]'
                  : 'text-[#4a6080] hover:text-[#c8d8e8]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      {selected && <StockDetail symbol={selected} onClose={() => setSelected(null)} />}

      {tab === 'market'  && <MarketTable stocks={stocks} loading={loading} onSelect={openStock} onRefresh={loadMarket} />}
      {tab === 'sectors' && <SectorView sectors={sectors} loading={loading} />}
      {tab === 'compare' && <CompareView />}
    </div>
  );
};


// ── Market Table ───────────────────────────────────────────────────────────

const MarketTable: React.FC<{
  stocks: Stock[]; loading: boolean;
  onSelect: (s: string) => void; onRefresh: () => void;
}> = ({ stocks, loading, onSelect, onRefresh }) => (
  <div className="glass overflow-hidden">
    <div className="flex items-center justify-between px-5 py-4 border-b border-[#1a2d4a]">
      <h2 className="section-title">Топ Акції</h2>
      <button
        onClick={onRefresh}
        className="flex items-center gap-1.5 text-xs border border-[#1a2d4a] text-[#4a6080]
                   hover:text-[#00d4ff] hover:border-[#00d4ff44] px-3 py-1.5 rounded-lg transition-all"
      >
        <RefreshCw size={12} /> Оновити
      </button>
    </div>

    {loading ? (
      <div className="flex justify-center items-center h-64"><div className="cyber-spinner" /></div>
    ) : (
      <div className="overflow-x-auto">
        <table className="w-full cyber-table">
          <thead>
            <tr>
              {['Компанія', 'Сектор', 'Ціна', 'Зміна за день', 'P/E', 'Кап-ція', ''].map((h, i) => (
                <th key={i} className={h === 'Компанія' || h === 'Сектор' || h === '' ? '' : 'text-right'}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stocks.map(s => (
              <tr key={s.symbol} onClick={() => onSelect(s.symbol)} className="cursor-pointer">
                <td>
                  <span className="font-mono font-bold text-[#e8f4ff]">{s.symbol}</span>
                  <p className="text-xs text-[#4a6080] truncate max-w-[160px]">{s.name}</p>
                </td>
                <td>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-[#0a1020] border border-[#1a2d4a] text-[#4a6080]">
                    {s.sector}
                  </span>
                </td>
                <td className="text-right font-mono font-semibold text-[#c8d8e8]">{usd(s.price)}</td>
                <td className={`text-right font-mono font-bold ${colorClass(s.change_pct)}`}>{pct(s.change_pct)}</td>
                <td className="text-right font-mono text-[#4a6080]">{s.pe_ratio ? s.pe_ratio.toFixed(1) : '—'}</td>
                <td className="text-right font-mono text-[#4a6080]">{s.market_cap_fmt ?? '—'}</td>
                <td className="text-[#2a4060]"><ChevronRight size={14} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
);


// ── Sector View ────────────────────────────────────────────────────────────

const SectorView: React.FC<{ sectors: Sector[]; loading: boolean }> = ({ sectors, loading }) => {
  if (loading) return (
    <div className="flex justify-center items-center h-48"><div className="cyber-spinner" /></div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="glass p-5">
        <h3 className="section-title mb-4">Динаміка секторів S&P 500</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={sectors} layout="vertical" margin={{ left: 130, right: 30, top: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={CHART_GRID} />
            <XAxis type="number" tickFormatter={v => `${v > 0 ? '+' : ''}${(+v).toFixed(1)}%`}
              stroke={AXIS_STROKE} fontSize={11} />
            <YAxis type="category" dataKey="sector" stroke={AXIS_STROKE} fontSize={11} width={125} />
            <Tooltip {...TOOLTIP_STYLE} formatter={(v: any) => [`${(+v).toFixed(2)}%`, 'Зміна']} />
            <ReferenceLine x={0} stroke="#1a2d4a" strokeWidth={1} />
            <Bar dataKey="change_pct" name="Зміна %"
              fill="#00d4ff" radius={[0, 4, 4, 0]}
              label={{ position: 'right', formatter: (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`, fontSize: 10, fill: '#4a6080' }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-2">
        <h3 className="section-title mb-2">Деталі</h3>
        {sectors.map(s => (
          <div key={s.sector} className="glass-hover px-4 py-3 flex items-center justify-between">
            <div>
              <p className="font-medium text-[#c8d8e8] text-sm">{s.sector}</p>
              {s.etf && <p className="text-xs text-[#4a6080]">ETF: {s.etf}</p>}
            </div>
            <div className={`flex items-center gap-1.5 font-mono font-bold ${colorClass(s.change_pct)}`}>
              {s.change_pct >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {pct(s.change_pct)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


// ── Compare View ───────────────────────────────────────────────────────────

const CompareView: React.FC = () => {
  const [input, setInput]     = useState('AAPL,MSFT,GOOGL');
  const [period, setPeriod]   = useState('1y');
  const [data, setData]       = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const COLORS = ['#00d4ff', '#00ff88', '#fbbf24', '#ff3366', '#a78bfa', '#fb923c', '#ec4899', '#84cc16'];

  const run = useCallback(async () => {
    const syms = input.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
    if (!syms.length) return;
    setLoading(true); setError('');
    try {
      const res = await stocksAPI.compare(syms, period);
      setData(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [input, period]);

  const chartData = (() => {
    if (!data?.series) return [];
    const series = data.series as Record<string, { date: string; value: number }[]>;
    const symbols = Object.keys(series);
    if (!symbols.length) return [];
    const byDate: Record<string, any> = {};
    symbols.forEach(sym => {
      series[sym].forEach(({ date, value }) => {
        if (!byDate[date]) byDate[date] = { date };
        byDate[date][sym] = value;
      });
    });
    return Object.values(byDate).sort((a: any, b: any) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  })();

  const symbols = data?.symbols ?? [];

  return (
    <div className="space-y-4">
      <div className="glass p-5">
        <h3 className="section-title mb-4">Порівняння прибутковості</h3>
        <div className="flex gap-3 flex-wrap items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="label mb-2 block">Тікери (через кому)</label>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="AAPL,MSFT,GOOGL"
              className="cyber-input"
            />
          </div>
          <div>
            <label className="label mb-2 block">Период</label>
            <select value={period} onChange={e => setPeriod(e.target.value)} className="cyber-input w-auto">
              {[['1mo','1 міс'],['3mo','3 міс'],['6mo','6 міс'],['1y','1 рік'],['2y','2 роки'],['5y','5 років']].map(([v,l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
          <button onClick={run} disabled={loading} className="btn-primary h-10 px-6">
            {loading ? 'Завантаження…' : 'Порівняти'}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-[#ff3366]">{error}</p>}
        <p className="mt-2 text-xs text-[#4a6080]">
          Нормалізована прибутковість (100 = початок). Макс 8 тікерів.
        </p>
      </div>

      {chartData.length > 0 && (
        <div className="glass p-5">
          <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
            <h3 className="section-title">Нормалізована прибутковість (база = 100)</h3>
            <div className="flex flex-wrap gap-3">
              {symbols.map((sym: string, i: number) => {
                const last = chartData[chartData.length - 1]?.[sym];
                const ret  = last != null ? (last - 100).toFixed(1) : null;
                return (
                  <div key={sym} className="flex items-center gap-1.5 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i] }} />
                    <span className="font-mono font-semibold text-[#c8d8e8]">{sym}</span>
                    {ret != null && (
                      <span className={+ret >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'} style={{ fontFamily: 'monospace' }}>
                        {+ret >= 0 ? '+' : ''}{ret}%
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
              <XAxis dataKey="date"
                tickFormatter={v => new Date(v).toLocaleDateString('uk-UA', { month: 'short', year: '2-digit' })}
                stroke={AXIS_STROKE} fontSize={11} />
              <YAxis tickFormatter={v => `${v}`} stroke={AXIS_STROKE} fontSize={11} />
              <Tooltip {...TOOLTIP_STYLE}
                formatter={(v: any, name: string) => [`${(+v).toFixed(2)}`, name]}
                labelFormatter={l => new Date(l).toLocaleDateString('uk-UA')}
              />
              <ReferenceLine y={100} stroke="#1a2d4a" strokeDasharray="4 4" />
              <Legend wrapperStyle={{ color: '#4a6080', fontSize: 12 }} />
              {symbols.map((sym: string, i: number) => (
                <Line key={sym} type="monotone" dataKey={sym}
                  stroke={COLORS[i]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};


// ── Stock Detail Panel ─────────────────────────────────────────────────────

const StockDetail: React.FC<{ symbol: string; onClose: () => void }> = ({ symbol, onClose }) => {
  const [quote, setQuote]       = useState<any>(null);
  const [history, setHistory]   = useState<any[]>([]);
  const [fundamentals, setFund] = useState<any>(null);
  const [loading, setLoading]   = useState(true);
  const [period, setPeriod]     = useState(PERIODS[2]);
  const [section, setSection]   = useState<'chart' | 'fundamentals'>('chart');

  useEffect(() => { loadAll(); }, [symbol]);
  useEffect(() => { loadHistory(); }, [period, symbol]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [qRes, fRes] = await Promise.all([
        stocksAPI.getQuote(symbol),
        stocksAPI.getFundamentals(symbol),
      ]);
      setQuote(qRes.data);
      setFund(fRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await stocksAPI.getHistory(symbol, period.value, period.interval);
      setHistory(res.data.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const isUp = (quote?.change_pct ?? 0) >= 0;
  const accentColor = isUp ? '#00ff88' : '#ff3366';

  return (
    <div className="glass overflow-hidden animate-fade-up">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#1a2d4a]" style={{ borderLeftWidth: 3, borderLeftColor: accentColor }}>
        <div className="flex justify-between items-start">
          <div>
            {loading ? (
              <div className="h-7 w-32 bg-[#1a2d4a] rounded animate-pulse mb-2" />
            ) : (
              <>
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="font-mono font-bold text-2xl text-[#e8f4ff]">{symbol}</h2>
                  {quote?.exchange && (
                    <span className="badge-gray">{quote.exchange}</span>
                  )}
                </div>
                <p className="text-sm text-[#4a6080]">{quote?.name}</p>
                {quote?.sector && (
                  <p className="text-xs text-[#00d4ff] mt-0.5">{quote.sector} · {quote.industry}</p>
                )}
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#4a6080] hover:text-[#c8d8e8] hover:bg-[#1a2d4a] transition-all"
          >
            <X size={16} />
          </button>
        </div>

        {!loading && quote && (
          <div className="mt-3 flex flex-wrap items-end gap-6">
            <div>
              <p className="font-mono font-bold text-3xl text-[#e8f4ff]">{usd(quote.price)}</p>
              <p className={`font-mono font-semibold text-sm ${colorClass(quote.change_pct)}`}>
                {quote.change != null ? `${quote.change >= 0 ? '+' : ''}${usd(quote.change)}` : ''}
                &nbsp;({pct(quote.change_pct)})
              </p>
            </div>
            <div className="flex gap-4 text-xs text-[#4a6080] flex-wrap font-mono">
              <span>Відкр. <b className="text-[#c8d8e8]">{usd(quote.open)}</b></span>
              <span>Макс. <b className="text-[#00ff88]">{usd(quote.high)}</b></span>
              <span>Мін. <b className="text-[#ff3366]">{usd(quote.low)}</b></span>
              <span>Кап. <b className="text-[#c8d8e8]">{quote.market_cap_fmt ?? '—'}</b></span>
              <span>P/E <b className="text-[#c8d8e8]">{quote.pe_ratio?.toFixed(1) ?? '—'}</b></span>
              <span>EPS <b className="text-[#c8d8e8]">{usd(quote.eps)}</b></span>
              <span>Дохідн. <b className="text-[#c8d8e8]">{quote.dividend_yield ? `${quote.dividend_yield}%` : '—'}</b></span>
            </div>
          </div>
        )}
      </div>

      {/* Section tabs */}
      <div className="flex gap-1 px-5 pt-3 bg-[#0a1020]">
        {(['chart', 'fundamentals'] as const).map(s => (
          <button key={s} onClick={() => setSection(s)}
            className={`px-4 py-2 text-xs font-semibold rounded-t-lg border-b-2 transition-all ${
              section === s
                ? 'border-[#00d4ff] text-[#00d4ff] bg-[#0d1628]'
                : 'border-transparent text-[#4a6080] hover:text-[#c8d8e8]'
            }`}>
            {s === 'chart' ? 'Графік' : 'Фундаментал'}
          </button>
        ))}
      </div>

      <div className="p-5">
        {section === 'chart' && (
          <ChartSection
            symbol={symbol}
            history={history}
            period={period}
            onPeriodChange={setPeriod}
            isUp={isUp}
          />
        )}
        {section === 'fundamentals' && fundamentals && (
          <FundamentalsSection data={fundamentals} />
        )}
      </div>
    </div>
  );
};


// ── Chart Section ──────────────────────────────────────────────────────────

const ChartSection: React.FC<{
  symbol: string; history: any[]; period: typeof PERIODS[number];
  onPeriodChange: (p: typeof PERIODS[number]) => void; isUp: boolean;
}> = ({ history, period, onPeriodChange, isUp }) => {
  const color  = isUp ? '#00ff88' : '#ff3366';
  const gradId = `stock-grad-${isUp ? 'up' : 'dn'}`;
  const minP   = history.length ? Math.min(...history.map(d => d.close)) * 0.998 : 0;
  const maxP   = history.length ? Math.max(...history.map(d => d.close)) * 1.002 : 1;

  return (
    <div>
      <div className="flex gap-1 mb-4">
        {PERIODS.map(p => (
          <button key={p.value} onClick={() => onPeriodChange(p)}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
              period.value === p.value
                ? 'bg-[#00d4ff] text-[#070b14]'
                : 'bg-[#0a1020] text-[#4a6080] hover:text-[#c8d8e8]'
            }`}>
            {p.label}
          </button>
        ))}
      </div>

      {history.length === 0 ? (
        <div className="flex justify-center items-center h-48 text-[#4a6080]">Немає даних</div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={history} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={color} stopOpacity={0.2} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
            <XAxis dataKey="timestamp"
              tickFormatter={v => {
                const d = new Date(v);
                return period.value.includes('y') || period.value === '6mo'
                  ? d.toLocaleDateString('uk-UA', { month: 'short', year: '2-digit' })
                  : d.toLocaleDateString('uk-UA', { month: 'short', day: 'numeric' });
              }}
              stroke={AXIS_STROKE} fontSize={11} />
            <YAxis domain={[minP, maxP]}
              tickFormatter={v => `$${v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(0)}`}
              stroke={AXIS_STROKE} fontSize={11} />
            <Tooltip {...TOOLTIP_STYLE}
              formatter={(v: any) => [usd(+v), 'Ціна закриття']}
              labelFormatter={l => new Date(l).toLocaleDateString('uk-UA')}
            />
            <Area type="monotone" dataKey="close" stroke={color} strokeWidth={2}
              fill={`url(#${gradId})`} dot={false} name="Ціна" />
          </AreaChart>
        </ResponsiveContainer>
      )}

      {history.length > 0 && (
        <div className="mt-2">
          <p className="label mb-1">Обсяг торгів</p>
          <ResponsiveContainer width="100%" height={60}>
            <BarChart data={history} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
              <Bar dataKey="volume" fill="#1a3a5c" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};


// ── Fundamentals Section ───────────────────────────────────────────────────

const FundamentalsSection: React.FC<{ data: any }> = ({ data }) => {
  const groups = [
    {
      title: 'Оцінка',
      icon: <BarChart2 size={13} className="text-[#00d4ff]" />,
      rows: [
        ['P/E (trailing)',    data.pe_ratio?.toFixed(2)       ?? '—'],
        ['P/E (forward)',     data.forward_pe?.toFixed(2)     ?? '—'],
        ['PEG Ratio',         data.peg_ratio?.toFixed(2)      ?? '—'],
        ['Price/Book',        data.price_to_book?.toFixed(2)  ?? '—'],
        ['Price/Sales',       data.price_to_sales?.toFixed(2) ?? '—'],
        ['EV/EBITDA',         data.ev_to_ebitda?.toFixed(2)   ?? '—'],
      ],
    },
    {
      title: 'Розмір',
      icon: <BookOpen size={13} className="text-[#a78bfa]" />,
      rows: [
        ['Ринкова кап.',      data.market_cap_fmt    ?? '—'],
        ['Виручка',           data.total_revenue_fmt ?? '—'],
        ['Чистий прибуток',   data.net_income_fmt    ?? '—'],
        ['EBITDA',            data.ebitda_fmt        ?? '—'],
        ['EPS (trailing)',    data.eps_trailing?.toFixed(2) ?? '—'],
        ['EPS (forward)',     data.eps_forward?.toFixed(2)  ?? '—'],
      ],
    },
    {
      title: 'Маржинальність',
      icon: <TrendingUp size={13} className="text-[#00ff88]" />,
      rows: [
        ['Валова маржа',      data.gross_margin_pct     != null ? `${data.gross_margin_pct}%`     : '—'],
        ['Операційна маржа',  data.operating_margin_pct != null ? `${data.operating_margin_pct}%` : '—'],
        ['Чиста маржа',       data.profit_margin_pct    != null ? `${data.profit_margin_pct}%`    : '—'],
        ['ROE',               data.roe != null ? `${(data.roe * 100).toFixed(2)}%` : '—'],
        ['ROA',               data.roa != null ? `${(data.roa * 100).toFixed(2)}%` : '—'],
        ['Зростання EPS',     data.earnings_growth_pct  != null ? `${data.earnings_growth_pct}%`  : '—'],
      ],
    },
    {
      title: 'Ризик / Баланс',
      icon: <TrendingDown size={13} className="text-[#fbbf24]" />,
      rows: [
        ['Beta',              data.beta?.toFixed(2)           ?? '—'],
        ['Debt/Equity',       data.debt_to_equity?.toFixed(2) ?? '—'],
        ['Current Ratio',     data.current_ratio?.toFixed(2)  ?? '—'],
        ['Quick Ratio',       data.quick_ratio?.toFixed(2)    ?? '—'],
        ['Готівка',           data.total_cash ?? '—'],
        ['Борг',              data.total_debt ?? '—'],
      ],
    },
    {
      title: 'Дивіденди',
      icon: <BarChart2 size={13} className="text-[#a78bfa]" />,
      rows: [
        ['Річний дивіденд',   data.dividend_rate  != null ? `$${data.dividend_rate}` : '—'],
        ['Дохідність',        data.dividend_yield != null ? `${data.dividend_yield}%` : '—'],
        ['Payout Ratio',      data.payout_ratio   != null ? `${(data.payout_ratio * 100).toFixed(1)}%` : '—'],
      ],
    },
    {
      title: 'Аналітики',
      icon: <TrendingUp size={13} className="text-[#00d4ff]" />,
      rows: [
        ['Цільова ціна',      data.analyst_target  != null ? usd(data.analyst_target)  : '—'],
        ['Рекомендація',      data.recommendation?.toUpperCase() ?? '—'],
        ['К-сть аналітиків',  data.analyst_count ?? '—'],
        ['52-тижн. макс.',    data['52w_high']    != null ? usd(data['52w_high']) : '—'],
        ['52-тижн. мін.',     data['52w_low']     != null ? usd(data['52w_low'])  : '—'],
      ],
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {groups.map(g => (
        <div key={g.title} className="bg-[#0a1020] rounded-xl p-4 border border-[#1a2d4a]">
          <h4 className="text-xs font-semibold text-[#c8d8e8] mb-3 flex items-center gap-1.5 uppercase tracking-widest">
            {g.icon} {g.title}
          </h4>
          <div className="space-y-1.5">
            {g.rows.map(([label, value]) => (
              <div key={label} className="flex justify-between text-xs">
                <span className="text-[#4a6080]">{label}</span>
                <span className="font-mono font-semibold text-[#e8f4ff]">{value}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
