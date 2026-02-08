import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const marketAPI = {
  getTopCryptos: (limit = 10) => api.get(`/market/top?limit=${limit}`),
  getTicker: (symbol: string) => api.get(`/market/ticker/${symbol}`),
  getHistory: (symbol: string, timeframe = '1d', limit = 100) => 
    api.get(`/market/history/${symbol}?timeframe=${timeframe}&limit=${limit}`),
  getOrderBook: (symbol: string, limit = 20) => 
    api.get(`/market/orderbook/${symbol}?limit=${limit}`),
};

export const analysisAPI = {
  getIndicators:   (symbol: string, timeframe = '1d') =>
    api.get(`/analysis/indicators/${symbol}?timeframe=${timeframe}`),
  getSignals:      (symbol: string, timeframe = '1d') =>
    api.get(`/analysis/signals/${symbol}?timeframe=${timeframe}`),
  getTrend:        (symbol: string, timeframe = '1d') =>
    api.get(`/analysis/trend/${symbol}?timeframe=${timeframe}`),
  getStatistical:  (symbol: string, timeframe = '1d', limit = 200) =>
    api.get(`/analysis/statistical/${symbol}?timeframe=${timeframe}&limit=${limit}`),
};

export const portfolioAPI = {
  get: (userId: string) => api.get(`/portfolio/${userId}`),
  getPerformance: (userId: string) => api.get(`/portfolio/${userId}/performance`),
  addAsset: (userId: string, symbol: string, amount: number, price: number) =>
    api.post('/portfolio/add', { user_id: userId, symbol, amount, purchase_price: price }),
  updateAsset: (userId: string, symbol: string, amount: number, price: number) =>
    api.put('/portfolio/update', { user_id: userId, symbol, amount, purchase_price: price }),
  removeAsset: (userId: string, symbol: string) =>
    api.delete(`/portfolio/remove/${userId}/${encodeURIComponent(symbol)}`),
};

export const predictionsAPI = {
  predictPrice:       (symbol: string, timeframe = '1d', periods = 7, model = 'ensemble') =>
    api.post('/predictions/price', { symbol, timeframe, periods, model }),
  getSignals:         (symbol: string, timeframe = '1d') =>
    api.get(`/predictions/signals/${symbol}?timeframe=${timeframe}`),
  getIndicators:      (symbol: string, timeframe = '1d') =>
    api.get(`/predictions/indicators/${symbol}?timeframe=${timeframe}`),
  compareModels:      (symbol: string, timeframe = '1d', periods = 3) =>
    api.get(`/predictions/compare/${symbol}?timeframe=${timeframe}&periods=${periods}`),
  runBacktest:        (symbol: string, timeframe = '1d', model = 'gradient_boosting') =>
    api.post('/predictions/backtest', { symbol, timeframe, model }),
  getFeatureImportance: (symbol: string, timeframe = '1d', model = 'random_forest') =>
    api.get(`/predictions/features/${symbol}?timeframe=${timeframe}&model=${model}`),
};

export const newsAPI = {
  getNews:        (symbol: string, limit = 20) => api.get(`/news/${symbol}?limit=${limit}`),
  analyzeNews:    (symbol: string, articles: any[]) => api.post(`/news/analyze?symbol=${symbol}`, articles),
  getAiAnalysis:  (symbol: string, limit = 15) => api.get(`/news/analyze/${symbol}?limit=${limit}`),
};

export const aiAPI = {
  chat: (message: string, history?: any[], context?: any) =>
    api.post('/ai/chat', { message, conversation_history: history, context, stream: false }),
  getSentiment: (symbol: string) => api.post(`/ai/sentiment/${symbol}`, {}),
};

export const stocksAPI = {
  getTop:          (limit = 15) =>
    api.get(`/stocks/top?limit=${limit}`),
  getQuote:        (symbol: string) =>
    api.get(`/stocks/quote/${symbol}`),
  getHistory:      (symbol: string, period = '6mo', interval = '1d') =>
    api.get(`/stocks/history/${symbol}?period=${period}&interval=${interval}`),
  search:          (q: string, limit = 10) =>
    api.get(`/stocks/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  getFundamentals: (symbol: string) =>
    api.get(`/stocks/fundamentals/${symbol}`),
  getSectors:      () =>
    api.get('/stocks/sectors'),
  compare:         (symbols: string[], period = '1y') =>
    api.get(`/stocks/compare?symbols=${symbols.join(',')}&period=${period}`),
};

export const researchAPI = {
  // Price snapshots
  saveSnapshot:    (symbol: string, assetType = 'crypto') =>
    api.post(`/research/snapshot/${symbol}?asset_type=${assetType}`),
  getPriceHistory: (symbol: string, days = 30, limit = 500) =>
    api.get(`/research/price-history/${symbol}?days=${days}&limit=${limit}`),
  getTracked:      () => api.get('/research/tracked'),

  // ML run history
  saveMlRun:       (payload: any) => api.post('/research/ml-run', payload),
  getMlHistory:    (symbol?: string, model?: string, limit = 50) => {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    if (model)  params.append('model', model);
    params.append('limit', String(limit));
    return api.get(`/research/ml-history?${params}`);
  },
  getMlStats:      (symbol?: string) =>
    api.get(`/research/ml-stats${symbol ? `?symbol=${symbol}` : ''}`),

  // Backtest history
  saveBacktest:      (payload: any) => api.post('/research/backtest-run', payload),
  getBacktestHistory: (symbol?: string, limit = 30) => {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    params.append('limit', String(limit));
    return api.get(`/research/backtest-history?${params}`);
  },

  // Notes
  getNotes:   (symbol?: string, limit = 50) => {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    params.append('limit', String(limit));
    return api.get(`/research/notes?${params}`);
  },
  createNote: (payload: { symbol: string; asset_type?: string; title: string; content: string; tags?: string; price_at?: number }) =>
    api.post('/research/notes', payload),
  updateNote: (id: number, payload: { title?: string; content?: string; tags?: string }) =>
    api.put(`/research/notes/${id}`, payload),
  deleteNote: (id: number) => api.delete(`/research/notes/${id}`),

  // Watchlist
  getWatchlist:    () => api.get('/research/watchlist'),
  addToWatchlist:  (payload: { symbol: string; name?: string; asset_type?: string; track_price?: boolean; notes?: string }) =>
    api.post('/research/watchlist', payload),
  removeFromWatchlist: (symbol: string) => api.delete(`/research/watchlist/${symbol}`),
};

export default api;
