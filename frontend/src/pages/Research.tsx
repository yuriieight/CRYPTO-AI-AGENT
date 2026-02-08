import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts';
import { researchAPI } from '../services/api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface WatchlistItem {
  id: number; symbol: string; name: string | null;
  asset_type: string; track_price: boolean; notes: string | null;
  added_at: string;
}

interface PricePoint { timestamp: string; price: number; change_pct: number | null; volume: number | null; }

interface MlRow {
  id: number; symbol: string; model: string; timeframe: string;
  metrics: { mae: number | null; rmse: number | null; r2: number | null; mape: number | null };
  pred_price: number | null; pred_change: number | null;
  current_price: number | null; created_at: string;
}

interface BacktestRow {
  id: number; symbol: string; model: string; timeframe: string;
  initial_capital: number; final_capital: number | null;
  total_return_pct: number | null; win_rate: number | null;
  total_trades: number | null; sharpe_ratio: number | null;
  max_drawdown_pct: number | null; pred_mae: number | null; pred_r2: number | null;
  created_at: string;
}

interface Note {
  id: number; symbol: string; asset_type: string;
  title: string; content: string; tags: string;
  price_at: number | null; created_at: string; updated_at: string;
}

interface MlStat {
  model: string; runs: number;
  avg_mae: number; avg_rmse: number; avg_r2: number; avg_mape: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt = (n: number | null | undefined, dec = 2) =>
  n == null ? '—' : n.toFixed(dec);

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString('uk-UA', { dateStyle: 'short', timeStyle: 'short' });

const pct = (n: number | null | undefined) =>
  n == null ? '—' : `${n > 0 ? '+' : ''}${n.toFixed(2)}%`;

const CHART_GRID = 'rgba(26,45,74,0.6)';
const AXIS_STROKE = '#4a6080';
const TOOLTIP_STYLE = {
  contentStyle: { background: '#0d1628', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8 },
  labelStyle:   { color: '#c8d8e8' },
  itemStyle:    { color: '#00d4ff' },
};

// ── Tab config ────────────────────────────────────────────────────────────────

type Tab = 'watchlist' | 'prices' | 'ml' | 'backtest' | 'notes';

const TABS: { id: Tab; label: string }[] = [
  { id: 'watchlist', label: 'Watchlist' },
  { id: 'prices',    label: 'Price History' },
  { id: 'ml',        label: 'ML History' },
  { id: 'backtest',  label: 'Backtest History' },
  { id: 'notes',     label: 'Research Notes' },
];

// ── Shared table styles ───────────────────────────────────────────────────────

const TH = 'text-[10px] font-semibold text-[#4a6080] uppercase tracking-widest py-2 pr-3';
const TD = 'py-1.5 pr-3 text-xs border-b border-[#0f1b2a]';

// ── Watchlist tab ─────────────────────────────────────────────────────────────

function WatchlistTab() {
  const [items, setItems]     = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [newSym, setNewSym]   = useState('');
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState<'crypto' | 'stock'>('crypto');
  const [saving, setSaving]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await researchAPI.getWatchlist();
      setItems(r.data.items);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = async () => {
    if (!newSym.trim()) return;
    setSaving(true);
    try {
      await researchAPI.addToWatchlist({
        symbol: newSym.trim().toUpperCase(),
        name: newName || undefined,
        asset_type: newType,
        track_price: true,
      });
      setNewSym(''); setNewName('');
      await load();
    } catch { /* silent */ }
    setSaving(false);
  };

  const remove = async (symbol: string) => {
    try {
      await researchAPI.removeFromWatchlist(symbol);
      setItems(prev => prev.filter(i => i.symbol !== symbol));
    } catch { /* silent */ }
  };

  const snapshot = async (symbol: string, type: string) => {
    try { await researchAPI.saveSnapshot(symbol, type); }
    catch { /* silent */ }
  };

  return (
    <div className="space-y-4">
      <div className="glass p-4 space-y-3">
        <h3 className="label">Add to Watchlist</h3>
        <div className="flex gap-2 flex-wrap">
          <input
            className="cyber-input w-32"
            placeholder="Symbol (BTC)"
            value={newSym}
            onChange={e => setNewSym(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && add()}
          />
          <input
            className="cyber-input flex-1 min-w-28"
            placeholder="Name (optional)"
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
          <select
            className="cyber-input w-auto"
            value={newType}
            onChange={e => setNewType(e.target.value as 'crypto' | 'stock')}
          >
            <option value="crypto">Crypto</option>
            <option value="stock">Stock</option>
          </select>
          <button className="btn-primary" onClick={add} disabled={saving}>
            {saving ? 'Adding…' : 'Add'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-32"><div className="cyber-spinner" /></div>
      ) : items.length === 0 ? (
        <div className="text-center text-[#4a6080] py-12 text-sm">Watchlist порожній. Додайте символи вище.</div>
      ) : (
        <div className="glass overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#1a2d4a]">
                <th className={`${TH} text-left`}>Symbol</th>
                <th className={`${TH} text-left`}>Name</th>
                <th className={`${TH} text-left`}>Type</th>
                <th className={`${TH} text-left`}>Added</th>
                <th className={`${TH} text-right`}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} className="hover:bg-[#00d4ff04] transition-colors">
                  <td className={`${TD} font-mono text-[#00d4ff]`}>{item.symbol}</td>
                  <td className={`${TD} text-[#c8d8e8]`}>{item.name ?? '—'}</td>
                  <td className={TD}>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      item.asset_type === 'crypto'
                        ? 'badge-purple'
                        : 'badge-green'
                    }`}>
                      {item.asset_type}
                    </span>
                  </td>
                  <td className={`${TD} text-[#4a6080]`}>{fmtDate(item.added_at)}</td>
                  <td className={`${TD} text-right`}>
                    <div className="flex justify-end gap-3">
                      <button
                        onClick={() => snapshot(item.symbol, item.asset_type)}
                        className="text-xs text-[#4a6080] hover:text-[#00d4ff] transition-colors"
                      >
                        Snapshot
                      </button>
                      <button
                        onClick={() => remove(item.symbol)}
                        className="text-xs text-[#4a6080] hover:text-[#ff3366] transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Price History tab ─────────────────────────────────────────────────────────

function PricesTab() {
  const [tracked, setTracked]   = useState<string[]>([]);
  const [symbol, setSymbol]     = useState('');
  const [days, setDays]         = useState(30);
  const [data, setData]         = useState<PricePoint[]>([]);
  const [loading, setLoading]   = useState(false);

  useEffect(() => {
    researchAPI.getTracked()
      .then(r => {
        setTracked(r.data.symbols);
        if (r.data.symbols.length) setSymbol(r.data.symbols[0]);
      })
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const r = await researchAPI.getPriceHistory(symbol, days);
      setData(r.data.data);
    } catch { /* silent */ }
    setLoading(false);
  }, [symbol, days]);

  useEffect(() => { load(); }, [load]);

  const chartData = data.map(d => ({
    time:   new Date(d.timestamp).toLocaleDateString('uk-UA'),
    price:  d.price,
    change: d.change_pct,
  }));

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap items-center">
        <select className="cyber-input w-auto" value={symbol} onChange={e => setSymbol(e.target.value)}>
          {tracked.length === 0 && <option value="">No tracked symbols</option>}
          {tracked.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <div className="flex gap-1 bg-[#0a1020] rounded-lg p-1">
          {[7, 14, 30, 90].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                days === d ? 'bg-[#00d4ff] text-[#070b14]' : 'text-[#4a6080] hover:text-[#c8d8e8]'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
        <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">Refresh</button>
        <span className="text-[#4a6080] text-xs">{data.length} snapshots</span>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-48"><div className="cyber-spinner" /></div>
      ) : data.length === 0 ? (
        <div className="text-center text-[#4a6080] py-16 text-sm">
          Немає даних. Використайте Watchlist → Snapshot для запису цін.
        </div>
      ) : (
        <div className="glass p-4">
          <h3 className="section-title mb-3">Ціна — {symbol}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
              <XAxis dataKey="time" stroke={AXIS_STROKE} tick={{ fontSize: 10 }} />
              <YAxis stroke={AXIS_STROKE} tick={{ fontSize: 10 }} />
              <Tooltip {...TOOLTIP_STYLE} />
              <Area type="monotone" dataKey="price" stroke="#00d4ff" fill="url(#priceGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ── ML History tab ────────────────────────────────────────────────────────────

function MlTab() {
  const [rows, setRows]           = useState<MlRow[]>([]);
  const [stats, setStats]         = useState<MlStat[]>([]);
  const [filterSym, setFilterSym] = useState('');
  const [loading, setLoading]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [h, s] = await Promise.all([
        researchAPI.getMlHistory(filterSym || undefined, undefined, 100),
        researchAPI.getMlStats(filterSym || undefined),
      ]);
      setRows(h.data.rows);
      setStats(s.data.stats);
    } catch { /* silent */ }
    setLoading(false);
  }, [filterSym]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <input
          className="cyber-input w-36"
          placeholder="Filter symbol"
          value={filterSym}
          onChange={e => setFilterSym(e.target.value.toUpperCase())}
        />
        <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">Refresh</button>
        <span className="text-[#4a6080] text-xs">{rows.length} runs stored</span>
      </div>

      {stats.length > 0 && (
        <div className="glass p-4 space-y-4">
          <h3 className="section-title">Model Comparison (avg MAE — lower is better)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats} layout="vertical" margin={{ left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} horizontal={false} />
              <XAxis type="number" stroke={AXIS_STROKE} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="model" stroke={AXIS_STROKE} tick={{ fontSize: 10 }} width={100} />
              <Tooltip {...TOOLTIP_STYLE} />
              <Bar dataKey="avg_mae" fill="#00d4ff" name="Avg MAE" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#1a2d4a]">
                  {['Model','Runs','Avg MAE','Avg RMSE','Avg R²','Avg MAPE'].map(h => (
                    <th key={h} className={`${TH} ${h === 'Model' ? 'text-left' : 'text-right'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stats.map(s => (
                  <tr key={s.model} className="hover:bg-[#00d4ff04] transition-colors">
                    <td className={`${TD} font-mono text-[#00d4ff]`}>{s.model}</td>
                    <td className={`${TD} text-right text-[#c8d8e8]`}>{s.runs}</td>
                    <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(s.avg_mae, 4)}</td>
                    <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(s.avg_rmse, 4)}</td>
                    <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(s.avg_r2, 4)}</td>
                    <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(s.avg_mape, 2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-32"><div className="cyber-spinner" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center text-[#4a6080] py-12 text-sm">
          Немає ML-запусків. Запустіть прогнози — вони з'являться тут.
        </div>
      ) : (
        <div className="glass overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#1a2d4a]">
                {['Symbol','Model','TF','MAE','RMSE','R²','MAPE','Pred Δ%','Date'].map(h => (
                  <th key={h} className={`${TH} ${['Symbol','Model','TF'].includes(h) ? 'text-left' : 'text-right'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id} className="hover:bg-[#00d4ff04] transition-colors">
                  <td className={`${TD} font-mono text-[#00d4ff]`}>{r.symbol}</td>
                  <td className={`${TD} text-[#c8d8e8]`}>{r.model}</td>
                  <td className={`${TD} text-[#4a6080]`}>{r.timeframe}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.metrics.mae, 4)}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.metrics.rmse, 4)}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.metrics.r2, 4)}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.metrics.mape, 2)}%</td>
                  <td className={`${TD} text-right font-mono font-semibold ${(r.pred_change ?? 0) >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                    {pct(r.pred_change)}
                  </td>
                  <td className={`${TD} text-right text-[#4a6080]`}>{fmtDate(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Backtest History tab ──────────────────────────────────────────────────────

function BacktestTab() {
  const [rows, setRows]           = useState<BacktestRow[]>([]);
  const [filterSym, setFilterSym] = useState('');
  const [loading, setLoading]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await researchAPI.getBacktestHistory(filterSym || undefined, 50);
      setRows(r.data.rows);
    } catch { /* silent */ }
    setLoading(false);
  }, [filterSym]);

  useEffect(() => { load(); }, [load]);

  const chartData = rows.slice(0, 20).reverse().map((r, i) => ({
    name:    `#${i + 1} ${r.symbol}/${r.model.slice(0, 4)}`,
    return:  r.total_return_pct ?? 0,
    winRate: r.win_rate != null ? r.win_rate * 100 : 0,
  }));

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <input
          className="cyber-input w-36"
          placeholder="Filter symbol"
          value={filterSym}
          onChange={e => setFilterSym(e.target.value.toUpperCase())}
        />
        <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">Refresh</button>
        <span className="text-[#4a6080] text-xs">{rows.length} backtests stored</span>
      </div>

      {rows.length > 0 && (
        <div className="glass p-4">
          <h3 className="section-title mb-3">Recent Backtest Returns</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
              <XAxis dataKey="name" stroke={AXIS_STROKE} tick={{ fontSize: 9 }} />
              <YAxis stroke={AXIS_STROKE} tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <Tooltip {...TOOLTIP_STYLE} formatter={(v: any) => [`${Number(v).toFixed(2)}%`]} />
              <Bar dataKey="return" name="Total Return %" fill="#00ff88" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-32"><div className="cyber-spinner" /></div>
      ) : rows.length === 0 ? (
        <div className="text-center text-[#4a6080] py-12 text-sm">Немає записів. Запустіть бектест.</div>
      ) : (
        <div className="glass overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#1a2d4a]">
                {['Symbol','Model','Return','Win Rate','Trades','Sharpe','Max DD','MAE','Date'].map(h => (
                  <th key={h} className={`${TH} ${['Symbol','Model'].includes(h) ? 'text-left' : 'text-right'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id} className="hover:bg-[#00d4ff04] transition-colors">
                  <td className={`${TD} font-mono text-[#00d4ff]`}>{r.symbol}</td>
                  <td className={`${TD} text-[#c8d8e8]`}>{r.model}</td>
                  <td className={`${TD} text-right font-mono font-semibold ${(r.total_return_pct ?? 0) >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                    {pct(r.total_return_pct)}
                  </td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>
                    {r.win_rate != null ? `${(r.win_rate * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{r.total_trades ?? '—'}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.sharpe_ratio)}</td>
                  <td className={`${TD} text-right font-mono text-[#ff3366]`}>{pct(r.max_drawdown_pct)}</td>
                  <td className={`${TD} text-right font-mono text-[#c8d8e8]`}>{fmt(r.pred_mae, 4)}</td>
                  <td className={`${TD} text-right text-[#4a6080]`}>{fmtDate(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Research Notes tab ────────────────────────────────────────────────────────

function NotesTab() {
  const [notes, setNotes]         = useState<Note[]>([]);
  const [filterSym, setFilterSym] = useState('');
  const [loading, setLoading]     = useState(false);
  const [editId, setEditId]       = useState<number | null>(null);
  const [form, setForm]           = useState({ symbol: '', title: '', content: '', tags: '' });
  const [saving, setSaving]       = useState(false);
  const [editForm, setEditForm]   = useState({ title: '', content: '', tags: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await researchAPI.getNotes(filterSym || undefined, 100);
      setNotes(r.data.notes);
    } catch { /* silent */ }
    setLoading(false);
  }, [filterSym]);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!form.symbol || !form.title || !form.content) return;
    setSaving(true);
    try {
      await researchAPI.createNote({
        symbol: form.symbol.toUpperCase(),
        title: form.title,
        content: form.content,
        tags: form.tags,
      });
      setForm({ symbol: '', title: '', content: '', tags: '' });
      await load();
    } catch { /* silent */ }
    setSaving(false);
  };

  const startEdit = (note: Note) => {
    setEditId(note.id);
    setEditForm({ title: note.title, content: note.content, tags: note.tags });
  };

  const saveEdit = async () => {
    if (!editId) return;
    try { await researchAPI.updateNote(editId, editForm); setEditId(null); await load(); }
    catch { /* silent */ }
  };

  const del = async (id: number) => {
    try { await researchAPI.deleteNote(id); setNotes(prev => prev.filter(n => n.id !== id)); }
    catch { /* silent */ }
  };

  return (
    <div className="space-y-4">
      <div className="glass p-4 space-y-3">
        <h3 className="label">New Note</h3>
        <div className="flex gap-2 flex-wrap">
          <input className="cyber-input w-28" placeholder="Symbol" value={form.symbol}
            onChange={e => setForm(f => ({ ...f, symbol: e.target.value }))} />
          <input className="cyber-input flex-1 min-w-40" placeholder="Title" value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          <input className="cyber-input w-48" placeholder="Tags (comma separated)" value={form.tags}
            onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />
        </div>
        <textarea
          className="cyber-input resize-none"
          rows={3}
          placeholder="Note content…"
          value={form.content}
          onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
        />
        <button className="btn-primary" onClick={create} disabled={saving}>
          {saving ? 'Saving…' : 'Save Note'}
        </button>
      </div>

      <div className="flex gap-2 items-center">
        <input className="cyber-input w-36" placeholder="Filter symbol" value={filterSym}
          onChange={e => setFilterSym(e.target.value.toUpperCase())} />
        <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">Refresh</button>
        <span className="text-[#4a6080] text-xs">{notes.length} notes</span>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-32"><div className="cyber-spinner" /></div>
      ) : notes.length === 0 ? (
        <div className="text-center text-[#4a6080] py-12 text-sm">Нотатки відсутні.</div>
      ) : (
        <div className="space-y-3">
          {notes.map(note => (
            <div key={note.id} className="glass p-4">
              {editId === note.id ? (
                <div className="space-y-2">
                  <input className="cyber-input" value={editForm.title}
                    onChange={e => setEditForm(f => ({ ...f, title: e.target.value }))} />
                  <textarea className="cyber-input resize-none" rows={3} value={editForm.content}
                    onChange={e => setEditForm(f => ({ ...f, content: e.target.value }))} />
                  <input className="cyber-input" placeholder="Tags" value={editForm.tags}
                    onChange={e => setEditForm(f => ({ ...f, tags: e.target.value }))} />
                  <div className="flex gap-2">
                    <button onClick={saveEdit} className="btn-primary text-xs px-3 py-1">Save</button>
                    <button onClick={() => setEditId(null)} className="btn-ghost text-xs px-3 py-1">Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[#00d4ff] text-xs">{note.symbol}</span>
                      <span className="text-[#4a6080] text-xs">{fmtDate(note.created_at)}</span>
                      {note.tags && (
                        <span className="badge-purple text-[10px]">{note.tags}</span>
                      )}
                    </div>
                    <div className="flex gap-3 shrink-0">
                      <button onClick={() => startEdit(note)} className="text-xs text-[#4a6080] hover:text-[#00d4ff] transition-colors">Edit</button>
                      <button onClick={() => del(note.id)} className="text-xs text-[#4a6080] hover:text-[#ff3366] transition-colors">Delete</button>
                    </div>
                  </div>
                  <h4 className="font-semibold text-[#e8f4ff] text-sm">{note.title}</h4>
                  <p className="text-[#c8d8e8] text-sm mt-1 whitespace-pre-wrap leading-relaxed">{note.content}</p>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Research page ────────────────────────────────────────────────────────

export default function Research() {
  const [tab, setTab] = useState<Tab>('watchlist');

  return (
    <div className="space-y-4">
      <div>
        <h1 className="section-title text-xl">Research Hub</h1>
        <p className="text-[#4a6080] text-xs mt-1">
          Відстеження цін, порівняння ML-моделей, перегляд бектестів, нотатки.
        </p>
      </div>

      <div className="flex gap-1 bg-[#0a1020] rounded-lg p-1 flex-wrap w-fit">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold transition-all ${
              tab === t.id
                ? 'bg-[#00d4ff] text-[#070b14]'
                : 'text-[#4a6080] hover:text-[#c8d8e8]'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div>
        {tab === 'watchlist' && <WatchlistTab />}
        {tab === 'prices'    && <PricesTab />}
        {tab === 'ml'        && <MlTab />}
        {tab === 'backtest'  && <BacktestTab />}
        {tab === 'notes'     && <NotesTab />}
      </div>
    </div>
  );
}
