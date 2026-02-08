import React, { useState, useEffect } from 'react';
import { Newspaper, Clock, Brain, RefreshCw, ExternalLink, Activity } from 'lucide-react';
import { newsAPI } from '../services/api';

export const News: React.FC<{ symbol: string }> = ({ symbol }) => {
  const [news, setNews]           = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(true);

  useEffect(() => { loadNews(); loadAnalysis(); }, [symbol]);

  const loadNews = async () => {
    try {
      setLoading(true);
      const cleanSymbol = symbol.split('/')[0];
      const newsRes = await newsAPI.getNews(cleanSymbol, 20);
      setNews(newsRes.data || []);
    } catch (e) {
      console.error('News error:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysis = async () => {
    try {
      setAnalyzing(true);
      const cleanSymbol = symbol.split('/')[0];
      const { data } = await newsAPI.getAiAnalysis(cleanSymbol, 15);
      if (!data.error) setAiAnalysis(data);
    } catch {
      // non-critical
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRefresh = () => { loadNews(); loadAnalysis(); };

  const formatDate = (dateString: string) => {
    try {
      const date  = new Date(dateString);
      const diffMs = Date.now() - date.getTime();
      const mins   = Math.floor(diffMs / 60000);
      if (mins < 60)    return `${mins}хв тому`;
      const hrs = Math.floor(mins / 60);
      if (hrs  < 24)    return `${hrs}год тому`;
      const days = Math.floor(hrs / 24);
      if (days < 7)     return `${days}д тому`;
      return date.toLocaleDateString('uk-UA');
    } catch {
      return 'Нещодавно';
    }
  };

  const sentimentColor = (idx: number) =>
    idx >= 60 ? '#00ff88' : idx <= 40 ? '#ff3366' : '#fbbf24';

  return (
    <div className="space-y-4">

      {/* ── AI Sentiment block ─────────────────────────────────────────── */}
      {analyzing ? (
        <div className="glass p-5 animate-pulse space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-[#1a2d4a]" />
            <div className="h-4 w-48 rounded bg-[#1a2d4a]" />
          </div>
          <div className="space-y-2">
            <div className="h-3 rounded bg-[#1a2d4a] w-full" />
            <div className="h-3 rounded bg-[#1a2d4a] w-5/6" />
            <div className="h-3 rounded bg-[#1a2d4a] w-4/6" />
          </div>
        </div>
      ) : aiAnalysis ? (
        <div className="glass p-5 space-y-4 relative overflow-hidden">
          {/* Decorative glow */}
          <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-[#7c3aed10] blur-2xl pointer-events-none" />

          <div className="flex flex-wrap items-start justify-between gap-3 relative">
            <div className="flex items-center gap-2">
              <Brain size={18} className="text-[#a78bfa]" />
              <h3 className="section-title">AI Аналіз Новин — {aiAnalysis.symbol}</h3>
            </div>
            <div className="text-right">
              <p className="label mb-1">Сентимент Індекс</p>
              <span
                className="font-mono font-bold text-2xl"
                style={{ color: sentimentColor(aiAnalysis.sentiment_index) }}
              >
                {aiAnalysis.sentiment_index}
                <span className="text-sm text-[#4a6080] font-normal"> / 100</span>
              </span>
            </div>
          </div>

          <div className="bg-[#0a1020] rounded-lg p-4 border border-[#1a2d4a] relative">
            <p className="text-sm text-[#c8d8e8] leading-relaxed">{aiAnalysis.ai_summary}</p>
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold mb-1.5">
              <span className="text-[#ff3366]">Песимізм</span>
              <span className="badge-purple">{aiAnalysis.overall_sentiment}</span>
              <span className="text-[#00ff88]">Оптимізм</span>
            </div>
            <div className="progress-track h-2">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${aiAnalysis.sentiment_index}%`,
                  background: `linear-gradient(90deg, #ff3366, #fbbf24, #00ff88)`,
                }}
              />
            </div>
            <div className="mt-2 flex items-center gap-1 justify-end text-[#4a6080]">
              <Activity size={10} />
              <span className="text-[10px]">
                Проаналізовано {aiAnalysis.articles_analyzed} статей · FinBERT & LLM
              </span>
            </div>
          </div>
        </div>
      ) : null}

      {/* ── News list ──────────────────────────────────────────────────── */}
      <div className="glass overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1a2d4a]">
          <div className="flex items-center gap-2">
            <Newspaper size={18} className="text-[#00d4ff]" />
            <h2 className="section-title">Останні Новини</h2>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading || analyzing}
            className="flex items-center gap-1.5 text-xs border border-[#1a2d4a] text-[#4a6080]
                       hover:text-[#00d4ff] hover:border-[#00d4ff44] px-3 py-1.5 rounded-lg
                       transition-all duration-150 disabled:opacity-40"
          >
            <RefreshCw size={12} className={(loading || analyzing) ? 'animate-spin' : ''} />
            Оновити
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="cyber-spinner" />
          </div>
        ) : news.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-[#4a6080] gap-2">
            <Newspaper size={32} className="opacity-30" />
            <p className="text-sm">Новини відсутні</p>
          </div>
        ) : (
          <div className="divide-y divide-[#1a2d4a]">
            {news.map((article, idx) => (
              <div key={idx} className="px-5 py-4 hover:bg-[#00d4ff04] transition-colors group">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <h3 className="font-semibold text-[#c8d8e8] group-hover:text-[#00d4ff] transition-colors mb-1.5 leading-snug text-sm sm:text-base">
                    {article.title}
                  </h3>
                </a>
                {article.description && (
                  <p className="text-xs sm:text-sm text-[#4a6080] leading-relaxed mb-3 line-clamp-2">
                    {article.description}
                  </p>
                )}
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-3 text-xs text-[#4a6080]">
                    <span className="px-2 py-0.5 rounded-md bg-[#0a1020] border border-[#1a2d4a] font-medium">
                      {article.source}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={11} />
                      {formatDate(article.published_at)}
                    </span>
                  </div>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-[#00d4ff] hover:text-[#00b8e0] transition-colors font-medium"
                  >
                    Читати <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
