"""
Stock Market Service
─────────────────────
Primary data source : yfinance (Yahoo Finance) — free, no rate limits for basic use
Secondary source    : Alpha Vantage (ALPHA_VANTAGE_KEY) — sector performance, fundamentals

Endpoints provided
  • quote(symbol)                — real-time price + key stats
  • get_ohlcv(symbol, period, interval) — historical OHLCV
  • search(query)               — symbol/name search
  • get_top_stocks()            — curated S&P 500 / Nasdaq watchlist
  • get_fundamentals(symbol)    — valuation, profitability, dividends
  • get_sector_performance()    — S&P 500 sectors via Alpha Vantage
  • compare(symbols)            — multi-symbol performance comparison
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

# ── Popular stocks watchlist ────────────────────────────────────────────────

TOP_STOCKS = [
    # Tech
    {"symbol": "AAPL",  "name": "Apple Inc.",            "sector": "Technology"},
    {"symbol": "MSFT",  "name": "Microsoft Corp.",        "sector": "Technology"},
    {"symbol": "NVDA",  "name": "NVIDIA Corp.",           "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.",          "sector": "Technology"},
    {"symbol": "META",  "name": "Meta Platforms Inc.",    "sector": "Technology"},
    {"symbol": "AMZN",  "name": "Amazon.com Inc.",        "sector": "Consumer Cyclical"},
    {"symbol": "TSLA",  "name": "Tesla Inc.",             "sector": "Consumer Cyclical"},
    # Finance
    {"symbol": "JPM",   "name": "JPMorgan Chase & Co.",  "sector": "Financial Services"},
    {"symbol": "BAC",   "name": "Bank of America Corp.", "sector": "Financial Services"},
    {"symbol": "GS",    "name": "Goldman Sachs Group",   "sector": "Financial Services"},
    # Healthcare
    {"symbol": "JNJ",   "name": "Johnson & Johnson",     "sector": "Healthcare"},
    {"symbol": "PFE",   "name": "Pfizer Inc.",            "sector": "Healthcare"},
    # Energy
    {"symbol": "XOM",   "name": "Exxon Mobil Corp.",     "sector": "Energy"},
    # ETFs
    {"symbol": "SPY",   "name": "SPDR S&P 500 ETF",      "sector": "ETF"},
    {"symbol": "QQQ",   "name": "Invesco QQQ Trust",     "sector": "ETF"},
]

# Sector ETFs used to compute sector performance when Alpha Vantage is unavailable
SECTOR_ETFS = {
    "Technology":           "XLK",
    "Financial Services":   "XLF",
    "Healthcare":           "XLV",
    "Energy":               "XLE",
    "Consumer Cyclical":    "XLY",
    "Consumer Defensive":   "XLP",
    "Industrials":          "XLI",
    "Materials":            "XLB",
    "Real Estate":          "XLRE",
    "Utilities":            "XLU",
    "Communication Svcs":   "XLC",
}


def _safe_float(value, default=None):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _fmt_large(value: Optional[float]) -> Optional[str]:
    """Format large numbers: 3 804 000 000 000 → '$3.80T'"""
    if value is None:
        return None
    if abs(value) >= 1e12:
        return f"${value / 1e12:.2f}T"
    if abs(value) >= 1e9:
        return f"${value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


class StockService:
    """Async wrapper around yfinance with Alpha Vantage fallback."""

    # ── Quote ───────────────────────────────────────────────────────────────

    async def get_quote(self, symbol: str) -> Dict:
        """Real-time quote with key stats."""
        return await asyncio.get_event_loop().run_in_executor(None, self._quote_sync, symbol.upper())

    def _quote_sync(self, symbol: str) -> Dict:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info

        price   = _safe_float(fi.last_price)
        prev    = _safe_float(fi.previous_close)
        change  = (price - prev) if (price and prev) else None
        pct     = (change / prev * 100) if (change is not None and prev) else None

        # Extra info from .info (slower but richer)
        try:
            info = ticker.info
        except Exception:
            info = {}

        return {
            "symbol":        symbol,
            "name":          info.get("longName") or info.get("shortName") or symbol,
            "price":         round(price, 4) if price else None,
            "prev_close":    round(prev, 4) if prev else None,
            "change":        round(change, 4) if change is not None else None,
            "change_pct":    round(pct, 2) if pct is not None else None,
            "open":          round(_safe_float(fi.open), 4) if fi.open else None,
            "high":          round(_safe_float(fi.day_high), 4) if fi.day_high else None,
            "low":           round(_safe_float(fi.day_low), 4) if fi.day_low else None,
            "volume":        int(fi.shares) if hasattr(fi, "shares") and fi.shares else info.get("volume"),
            "market_cap":    _safe_float(fi.market_cap),
            "market_cap_fmt":_fmt_large(_safe_float(fi.market_cap)),
            "currency":      info.get("currency", "USD"),
            "exchange":      info.get("exchange") or info.get("fullExchangeName"),
            "sector":        info.get("sector"),
            "industry":      info.get("industry"),
            "52w_high":      _safe_float(info.get("fiftyTwoWeekHigh")),
            "52w_low":       _safe_float(info.get("fiftyTwoWeekLow")),
            "pe_ratio":      _safe_float(info.get("trailingPE")),
            "eps":           _safe_float(info.get("trailingEps")),
            "dividend_yield":round(_safe_float(info.get("dividendYield"), 0) * 100, 2),
        }

    # ── OHLCV history ───────────────────────────────────────────────────────

    async def get_ohlcv(self, symbol: str, period: str = "6mo",
                        interval: str = "1d") -> List[Dict]:
        """Historical OHLCV.

        period   : 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max
        interval : 1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk 1mo 3mo
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._ohlcv_sync, symbol.upper(), period, interval
        )

    def _ohlcv_sync(self, symbol: str, period: str, interval: str) -> List[Dict]:
        import yfinance as yf
        df = yf.download(symbol, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return []

        result = []
        for ts, row in df.iterrows():
            # yfinance may return MultiIndex columns when downloading one ticker
            def _get(col):
                val = row.get(col) if hasattr(row, "get") else None
                if val is None and isinstance(row.index, object):
                    try:
                        val = row[col]
                    except Exception:
                        pass
                return _safe_float(val)

            result.append({
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "open":      round(_get("Open")  or 0, 4),
                "high":      round(_get("High")  or 0, 4),
                "low":       round(_get("Low")   or 0, 4),
                "close":     round(_get("Close") or 0, 4),
                "volume":    int(_get("Volume") or 0),
            })
        return result

    # ── Search ──────────────────────────────────────────────────────────────

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search stocks/ETFs by symbol or name prefix (local watchlist first,
        then yfinance lookup for exact symbol match)."""
        q = query.upper().strip()
        # 1. Match against our TOP_STOCKS list
        matches = [
            s for s in TOP_STOCKS
            if q in s["symbol"].upper() or q in s["name"].upper()
        ][:limit]

        if len(matches) < limit and len(q) >= 1:
            # 2. Try direct yfinance lookup for the exact ticker
            try:
                extra = await asyncio.get_event_loop().run_in_executor(
                    None, self._lookup_ticker, q
                )
                if extra and not any(m["symbol"] == extra["symbol"] for m in matches):
                    matches.append(extra)
            except Exception:
                pass

        return matches[:limit]

    def _lookup_ticker(self, symbol: str) -> Optional[Dict]:
        import yfinance as yf
        try:
            t = yf.Ticker(symbol)
            info = t.info
            name = info.get("longName") or info.get("shortName")
            if not name:
                return None
            return {
                "symbol": symbol,
                "name":   name,
                "sector": info.get("sector", ""),
            }
        except Exception:
            return None

    # ── Top stocks ──────────────────────────────────────────────────────────

    async def get_top_stocks(self, limit: int = 15) -> List[Dict]:
        """Enriched watchlist with live quotes (batched)."""
        symbols = [s["symbol"] for s in TOP_STOCKS[:limit]]
        quotes  = await asyncio.gather(
            *[self.get_quote(sym) for sym in symbols],
            return_exceptions=True
        )
        result = []
        for base, quote in zip(TOP_STOCKS[:limit], quotes):
            if isinstance(quote, Exception):
                result.append({**base, "price": None, "change_pct": None, "error": str(quote)})
            else:
                result.append({**base, **quote})
        return result

    # ── Fundamentals ─────────────────────────────────────────────────────────

    async def get_fundamentals(self, symbol: str) -> Dict:
        return await asyncio.get_event_loop().run_in_executor(
            None, self._fundamentals_sync, symbol.upper()
        )

    def _fundamentals_sync(self, symbol: str) -> Dict:
        import yfinance as yf
        t    = yf.Ticker(symbol)
        info = t.info

        # Income & valuation
        rev       = _safe_float(info.get("totalRevenue"))
        net_inc   = _safe_float(info.get("netIncomeToCommon"))
        ebitda    = _safe_float(info.get("ebitda"))
        mktcap    = _safe_float(info.get("marketCap"))
        book_val  = _safe_float(info.get("bookValue"))
        shares    = _safe_float(info.get("sharesOutstanding"))

        # Margins
        gm   = _safe_float(info.get("grossMargins"))
        om   = _safe_float(info.get("operatingMargins"))
        pm   = _safe_float(info.get("profitMargins"))

        # Growth
        rev_g  = _safe_float(info.get("revenueGrowth"))
        earn_g = _safe_float(info.get("earningsGrowth"))

        # Analyst targets
        target    = _safe_float(info.get("targetMeanPrice"))
        rec       = info.get("recommendationKey", "")
        num_anal  = info.get("numberOfAnalystOpinions", 0)

        return {
            "symbol": symbol,
            "name":   info.get("longName") or symbol,
            # Valuation
            "pe_ratio":           _safe_float(info.get("trailingPE")),
            "forward_pe":         _safe_float(info.get("forwardPE")),
            "peg_ratio":          _safe_float(info.get("pegRatio")),
            "price_to_book":      _safe_float(info.get("priceToBook")),
            "price_to_sales":     _safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_to_ebitda":       _safe_float(info.get("enterpriseToEbitda")),
            # Size
            "market_cap":         mktcap,
            "market_cap_fmt":     _fmt_large(mktcap),
            "total_revenue":      rev,
            "total_revenue_fmt":  _fmt_large(rev),
            "net_income":         net_inc,
            "net_income_fmt":     _fmt_large(net_inc),
            "ebitda":             ebitda,
            "ebitda_fmt":         _fmt_large(ebitda),
            # Per share
            "eps_trailing":       _safe_float(info.get("trailingEps")),
            "eps_forward":        _safe_float(info.get("forwardEps")),
            "book_value_ps":      book_val,
            "shares_outstanding": shares,
            "shares_fmt":         _fmt_large(shares),
            # Margins (%)
            "gross_margin_pct":   round(gm * 100, 2) if gm else None,
            "operating_margin_pct":round(om * 100, 2) if om else None,
            "profit_margin_pct":  round(pm * 100, 2) if pm else None,
            # Growth (%)
            "revenue_growth_pct": round(rev_g * 100, 2) if rev_g else None,
            "earnings_growth_pct":round(earn_g * 100, 2) if earn_g else None,
            # Returns
            "roe":  _safe_float(info.get("returnOnEquity")),
            "roa":  _safe_float(info.get("returnOnAssets")),
            "roic": _safe_float(info.get("returnOnCapital")),
            # Dividend
            "dividend_rate":  _safe_float(info.get("dividendRate")),
            "dividend_yield": round(_safe_float(info.get("dividendYield"), 0) * 100, 2),
            "payout_ratio":   _safe_float(info.get("payoutRatio")),
            "ex_dividend_date": str(info.get("exDividendDate", "")),
            # Balance sheet health
            "debt_to_equity":  _safe_float(info.get("debtToEquity")),
            "current_ratio":   _safe_float(info.get("currentRatio")),
            "quick_ratio":     _safe_float(info.get("quickRatio")),
            "total_cash":      _fmt_large(_safe_float(info.get("totalCash"))),
            "total_debt":      _fmt_large(_safe_float(info.get("totalDebt"))),
            # Analyst
            "analyst_target":  target,
            "recommendation":  rec,
            "analyst_count":   num_anal,
            # Technicals
            "beta":            _safe_float(info.get("beta")),
            "52w_high":        _safe_float(info.get("fiftyTwoWeekHigh")),
            "52w_low":         _safe_float(info.get("fiftyTwoWeekLow")),
            "avg_volume":      info.get("averageVolume"),
        }

    # ── Sector performance ───────────────────────────────────────────────────

    async def get_sector_performance(self) -> List[Dict]:
        """Returns 1-day % change for each S&P 500 sector.
        Tries Alpha Vantage first; falls back to sector ETFs via yfinance."""
        try:
            av = await self._alpha_vantage_sectors()
            if av:
                return av
        except Exception as e:
            logger.warning(f"Alpha Vantage sectors failed: {e}")

        return await self._etf_sectors()

    async def _alpha_vantage_sectors(self) -> List[Dict]:
        import aiohttp
        from app.core.config import settings
        key = getattr(settings, "ALPHA_VANTAGE_KEY", "")
        if not key:
            return []

        url = "https://www.alphavantage.co/query"
        params = {"function": "SECTOR", "apikey": key}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()

        day = data.get("Rank A: Real-Time Performance", {})
        if not day:
            return []

        result = []
        for sector, pct_str in day.items():
            try:
                pct = float(pct_str.replace("%", ""))
            except ValueError:
                continue
            result.append({"sector": sector, "change_pct": pct, "source": "alphavantage"})
        return sorted(result, key=lambda x: x["change_pct"], reverse=True)

    async def _etf_sectors(self) -> List[Dict]:
        """Fallback: compute sector % change via sector ETFs."""
        async def _one(name, etf):
            try:
                import yfinance as yf
                t = yf.Ticker(etf)
                fi = t.fast_info
                price = _safe_float(fi.last_price)
                prev  = _safe_float(fi.previous_close)
                pct   = (price - prev) / prev * 100 if price and prev else 0.0
                return {"sector": name, "etf": etf, "change_pct": round(pct, 2), "source": "etf"}
            except Exception:
                return {"sector": name, "etf": etf, "change_pct": 0.0, "source": "etf"}

        tasks = [_one(name, etf) for name, etf in SECTOR_ETFS.items()]
        results = await asyncio.gather(*tasks)
        return sorted(results, key=lambda x: x["change_pct"], reverse=True)

    # ── Compare ──────────────────────────────────────────────────────────────

    async def compare(self, symbols: List[str], period: str = "1y") -> Dict:
        """Compare normalized price performance of multiple tickers."""
        async def _one(sym):
            ohlcv = await self.get_ohlcv(sym, period=period, interval="1d")
            return sym, ohlcv

        all_ohlcv = await asyncio.gather(*[_one(s.upper()) for s in symbols],
                                         return_exceptions=True)

        series = {}
        for item in all_ohlcv:
            if isinstance(item, Exception):
                continue
            sym, data = item
            if not data:
                continue
            base = data[0]["close"]
            series[sym] = [
                {"date": d["timestamp"], "value": round(d["close"] / base * 100, 2)}
                for d in data if d["close"]
            ]

        return {
            "symbols":  symbols,
            "period":   period,
            "series":   series,
            "note":     "Normalized to 100 at start of period",
        }


# Singleton
stock_service = StockService()
