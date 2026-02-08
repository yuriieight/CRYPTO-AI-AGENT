"""
Stock Market Router
────────────────────
GET  /stocks/top                     — Top stocks watchlist with live prices
GET  /stocks/quote/{symbol}          — Real-time quote
GET  /stocks/history/{symbol}        — OHLCV history
GET  /stocks/search?q=               — Search by symbol / company name
GET  /stocks/fundamentals/{symbol}   — Full fundamental analysis
GET  /stocks/sectors                 — S&P 500 sector performance
GET  /stocks/compare?symbols=        — Normalized multi-ticker comparison
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Top stocks ─────────────────────────────────────────────────────────────

@router.get("/top")
async def get_top_stocks(limit: int = Query(default=15, ge=1, le=30)):
    """Watchlist of popular stocks with live price and daily change."""
    try:
        from app.services.stock_service import stock_service
        return await stock_service.get_top_stocks(limit)
    except Exception as e:
        logger.error(f"Top stocks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Quote ──────────────────────────────────────────────────────────────────

@router.get("/quote/{symbol:path}")
async def get_quote(symbol: str):
    """Real-time quote with key statistics."""
    try:
        from app.services.stock_service import stock_service
        result = await stock_service.get_quote(symbol)
        if result.get("price") is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quote error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── History ────────────────────────────────────────────────────────────────

@router.get("/history/{symbol:path}")
async def get_history(
    symbol: str,
    period:   str = Query(default="6mo",
                          description="1d 5d 1mo 3mo 6mo 1y 2y 5y ytd max"),
    interval: str = Query(default="1d",
                          description="1m 5m 15m 1h 1d 1wk 1mo"),
):
    """Historical OHLCV data from Yahoo Finance."""
    try:
        from app.services.stock_service import stock_service
        data = await stock_service.get_ohlcv(symbol, period, interval)
        if not data:
            raise HTTPException(status_code=404, detail=f"No history for {symbol}")
        return {
            "symbol":       symbol.upper(),
            "period":       period,
            "interval":     interval,
            "data":         data,
            "count":        len(data),
            "generated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Search ─────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_stocks(
    q:     str = Query(..., min_length=1, description="Symbol or company name"),
    limit: int = Query(default=10, ge=1, le=20),
):
    """Search stocks by ticker symbol or company name."""
    try:
        from app.services.stock_service import stock_service
        results = await stock_service.search(q, limit)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Search error for '{q}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Fundamentals ───────────────────────────────────────────────────────────

@router.get("/fundamentals/{symbol:path}")
async def get_fundamentals(symbol: str):
    """
    Comprehensive fundamental analysis:
    valuation ratios, margins, growth, balance sheet, dividends, analyst targets.
    """
    try:
        from app.services.stock_service import stock_service
        result = await stock_service.get_fundamentals(symbol)
        return {**result, "generated_at": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Fundamentals error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Sector performance ─────────────────────────────────────────────────────

@router.get("/sectors")
async def get_sectors():
    """
    Real-time S&P 500 sector performance.
    Primary: Alpha Vantage API.
    Fallback: sector ETF % change from Yahoo Finance.
    """
    try:
        from app.services.stock_service import stock_service
        sectors = await stock_service.get_sector_performance()
        return {
            "sectors":      sectors,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Sectors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Compare ────────────────────────────────────────────────────────────────

@router.get("/compare")
async def compare_stocks(
    symbols: str = Query(..., description="Comma-separated tickers, e.g. AAPL,MSFT,GOOGL"),
    period:  str = Query(default="1y", description="1mo 3mo 6mo 1y 2y 5y"),
):
    """
    Normalized cumulative return comparison (rebased to 100 at start of period).
    Useful for diplom-level portfolio analysis charts.
    """
    try:
        from app.services.stock_service import stock_service
        sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not sym_list:
            raise HTTPException(status_code=422, detail="No symbols provided")
        if len(sym_list) > 8:
            raise HTTPException(status_code=422, detail="Max 8 symbols at once")

        result = await stock_service.compare(sym_list, period)
        return {**result, "generated_at": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
