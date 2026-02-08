import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, TrendingUp, TrendingDown, Wallet, DollarSign, X } from 'lucide-react';
import { portfolioAPI } from '../services/api';

interface Asset {
  symbol: string;
  amount: number;
  purchase_price: number;
  current_price?: number;
  current_value?: number;
  invested?: number;
  profit_loss?: number;
  profit_loss_percent?: number;
}

export const Portfolio: React.FC = () => {
  const userId = 'demo-user';
  const [assets, setAssets]       = useState<Asset[]>([]);
  const [performance, setPerf]    = useState<any>({});
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Asset | null>(null);
  const [form, setForm]           = useState({ symbol: '', amount: '', purchase_price: '' });

  useEffect(() => { loadPortfolio(); }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const res = await portfolioAPI.getPerformance(userId);
      setAssets(res.data.assets || []);
      setPerf({
        total_invested:      res.data.total_invested       || 0,
        current_value:       res.data.current_value        || 0,
        profit_loss:         res.data.profit_loss          || 0,
        profit_loss_percent: res.data.profit_loss_percent  || 0,
      });
    } catch (e) {
      console.error('Portfolio error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editing) {
        await portfolioAPI.updateAsset(userId, editing.symbol, parseFloat(form.amount), parseFloat(form.purchase_price));
      } else {
        await portfolioAPI.addAsset(userId, form.symbol.toUpperCase() + '/USDT', parseFloat(form.amount), parseFloat(form.purchase_price));
      }
      closeModal();
      loadPortfolio();
    } catch (e) {
      console.error('Submit error:', e);
      alert('Помилка збереження');
    }
  };

  const handleEdit = (asset: Asset) => {
    setEditing(asset);
    setForm({ symbol: asset.symbol.replace('/USDT', ''), amount: String(asset.amount), purchase_price: String(asset.purchase_price) });
    setShowModal(true);
  };

  const handleDelete = async (symbol: string) => {
    if (!confirm(`Видалити ${symbol} з портфеля?`)) return;
    try { await portfolioAPI.removeAsset(userId, symbol); loadPortfolio(); }
    catch (e) { console.error('Delete error:', e); }
  };

  const closeModal = () => {
    setShowModal(false);
    setEditing(null);
    setForm({ symbol: '', amount: '', purchase_price: '' });
  };

  const isUp = (v: number) => v >= 0;

  const summaryCards = [
    {
      label: 'Всього Інвестовано',
      value: `$${performance.total_invested?.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? '0.00'}`,
      icon: <DollarSign size={18} className="text-[#00d4ff]" />,
      accent: '#00d4ff',
    },
    {
      label: 'Поточна Вартість',
      value: `$${performance.current_value?.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? '0.00'}`,
      icon: <Wallet size={18} className="text-[#a78bfa]" />,
      accent: '#a78bfa',
    },
    {
      label: 'Прибуток / Збиток',
      value: `${isUp(performance.profit_loss) ? '+' : ''}$${Math.abs(performance.profit_loss ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      icon: isUp(performance.profit_loss)
        ? <TrendingUp size={18} className="text-[#00ff88]" />
        : <TrendingDown size={18} className="text-[#ff3366]" />,
      accent: isUp(performance.profit_loss) ? '#00ff88' : '#ff3366',
    },
    {
      label: 'Прибутковість',
      value: `${isUp(performance.profit_loss_percent) ? '+' : ''}${(performance.profit_loss_percent ?? 0).toFixed(2)}%`,
      icon: isUp(performance.profit_loss_percent)
        ? <TrendingUp size={18} className="text-[#00ff88]" />
        : <TrendingDown size={18} className="text-[#ff3366]" />,
      accent: isUp(performance.profit_loss_percent) ? '#00ff88' : '#ff3366',
    },
  ];

  return (
    <div className="space-y-4">

      {/* ── Summary cards ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map(card => (
          <div key={card.label} className="glass-hover p-5" style={{ borderColor: `${card.accent}22` }}>
            <div className="flex items-center justify-between mb-3">
              <span className="label">{card.label}</span>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${card.accent}18` }}>
                {card.icon}
              </div>
            </div>
            <p className="font-mono font-bold text-xl sm:text-2xl" style={{ color: card.accent }}>
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* ── Assets table ───────────────────────────────────────────────── */}
      <div className="glass overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1a2d4a]">
          <h3 className="section-title">Ваші Активи</h3>
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center gap-1.5"
          >
            <Plus size={15} />
            Додати Актив
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full cyber-table">
            <thead>
              <tr>
                <th>Актив</th>
                <th className="text-right">Кількість</th>
                <th className="text-right">Серед. Ціна</th>
                <th className="text-right">Поточна Ціна</th>
                <th className="text-right">Вартість</th>
                <th className="text-right">П/З</th>
                <th className="text-right pr-5">Дії</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="flex justify-center"><div className="cyber-spinner" /></div>
                  </td>
                </tr>
              ) : assets.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-[#4a6080] text-sm">
                    Портфель порожній. Додайте ваш перший актив!
                  </td>
                </tr>
              ) : (
                assets.map(asset => {
                  const up = (asset.profit_loss ?? 0) >= 0;
                  return (
                    <tr key={asset.symbol}>
                      <td>
                        <span className="font-mono font-bold text-[#e8f4ff]">{asset.symbol}</span>
                      </td>
                      <td className="text-right font-mono text-[#c8d8e8] text-sm">
                        {asset.amount?.toFixed(4)}
                      </td>
                      <td className="text-right font-mono text-[#4a6080] text-sm">
                        ${asset.purchase_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-right font-mono text-[#c8d8e8] text-sm">
                        ${asset.current_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-right font-mono font-semibold text-[#e8f4ff] text-sm">
                        ${asset.current_value?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-right text-sm">
                        <div className={`font-mono font-semibold ${up ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
                          {up ? '+' : ''}{asset.profit_loss_percent?.toFixed(2)}%
                        </div>
                        <div className={`text-xs ${up ? 'text-[#00ff8880]' : 'text-[#ff336680]'}`}>
                          {up ? '+' : ''}${Math.abs(asset.profit_loss ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </div>
                      </td>
                      <td className="text-right pr-5">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleEdit(asset)}
                            className="p-1.5 rounded-lg border border-[#1a2d4a] text-[#4a6080] hover:text-[#00d4ff] hover:border-[#00d4ff44] transition-all"
                          >
                            <Edit2 size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(asset.symbol)}
                            className="p-1.5 rounded-lg border border-[#1a2d4a] text-[#4a6080] hover:text-[#ff3366] hover:border-[#ff336644] transition-all"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Add / Edit Modal ───────────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass w-full max-w-md animate-fade-up">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#1a2d4a]">
              <h3 className="section-title">
                {editing ? `Редагувати ${editing.symbol}` : 'Додати Актив'}
              </h3>
              <button
                onClick={closeModal}
                className="p-1.5 rounded-lg text-[#4a6080] hover:text-[#c8d8e8] hover:bg-[#1a2d4a] transition-all"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
              {!editing && (
                <div>
                  <label className="label mb-2 block">Символ (напр. BTC, ETH)</label>
                  <input
                    type="text"
                    value={form.symbol}
                    onChange={e => setForm({ ...form, symbol: e.target.value.toUpperCase() })}
                    className="cyber-input"
                    placeholder="BTC"
                    required
                  />
                </div>
              )}

              <div>
                <label className="label mb-2 block">Кількість</label>
                <input
                  type="number"
                  step="0.00000001"
                  value={form.amount}
                  onChange={e => setForm({ ...form, amount: e.target.value })}
                  className="cyber-input"
                  placeholder="0.5"
                  required
                />
              </div>

              <div>
                <label className="label mb-2 block">Ціна Покупки (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.purchase_price}
                  onChange={e => setForm({ ...form, purchase_price: e.target.value })}
                  className="cyber-input"
                  placeholder="45000"
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-ghost flex-1">
                  Скасувати
                </button>
                <button type="submit" className="btn-primary flex-1">
                  {editing ? 'Оновити' : 'Додати'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
