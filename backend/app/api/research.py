"""
Research Router
────────────────
All endpoints for the database-backed research features.

Price tracking
  POST   /research/snapshot/{symbol}     — save current price to DB
  GET    /research/price-history/{symbol}— stored price history
  GET    /research/tracked               — all tracked symbols

ML History
  GET    /research/ml-history            — all/filtered ML runs
  GET    /research/ml-stats              — per-model aggregated metrics
  POST   /research/ml-run               — save a new ML run result

Backtest History
  GET    /research/backtest-history      — all/filtered backtest runs
  POST   /research/backtest-run          — save a backtest result

Research Notes
  GET    /research/notes                 — all/filtered notes
  POST   /research/notes                 — create note
  PUT    /research/notes/{id}            — update note
  DELETE /research/notes/{id}            — delete note

Watchlist
  GET    /research/watchlist             — get watchlist
  POST   /research/watchlist             — add symbol
  DELETE /research/watchlist/{symbol}    — remove symbol
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.research_db import get_db
import app.services.db_service as svc

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic request models ────────────────────────────────────────────────

class NoteCreate(BaseModel):
    symbol:     str
    asset_type: str  = "crypto"
    title:      str
    content:    str
    tags:       str  = ""
    price_at:   Optional[float] = None


class NoteUpdate(BaseModel):
    title:   Optional[str] = None
    content: Optional[str] = None
    tags:    Optional[str] = None


class WatchlistAdd(BaseModel):
    symbol:      str
    name:        Optional[str] = None
    asset_type:  str  = "crypto"
    track_price: bool = True
    notes:       Optional[str] = None


class MLRunPayload(BaseModel):
    symbol:        str
    timeframe:     str  = "1d"
    model:         str  = "ensemble"
    periods:       int  = 7
    current_price: Optional[float] = None
    training_metrics: Optional[dict] = None
    predictions:   Optional[list]  = None
    feature_count: Optional[int]   = None


class BacktestPayload(BaseModel):
    symbol:           str
    timeframe:        str   = "1d"
    model:            str   = "gradient_boosting"
    initial_capital:  float = 10000.0
    final_capital:    Optional[float] = None
    total_return_pct: Optional[float] = None
    win_rate:         Optional[float] = None
    total_trades:     Optional[int]   = None
    profit_factor:    Optional[float] = None
    sharpe_ratio:     Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    avg_win:          Optional[float] = None
    avg_loss:         Optional[float] = None
    prediction_metrics: Optional[dict] = None
    equity_curve:     Optional[list]  = None
    recent_trades:    Optional[list]  = None


# ── Price snapshots ────────────────────────────────────────────────────────

@router.post("/snapshot/{symbol}")
async def save_snapshot(
    symbol: str,
    asset_type: str = Query("crypto"),
    db: AsyncSession = Depends(get_db),
):
    """Fetch current price and save a snapshot to the database."""
    try:
        symbol = symbol.upper()
        if asset_type == "stock":
            from app.services.stock_service import stock_service
            q = await stock_service.get_quote(symbol)
            price      = q.get("price")
            change_pct = q.get("change_pct")
            volume     = None
            market_cap = q.get("market_cap")
            extra      = {"pe_ratio": q.get("pe_ratio"), "name": q.get("name")}
        else:
            from app.services.binance_service import binance_service
            t = await binance_service.get_ticker(symbol)
            price      = t.get("price")
            change_pct = t.get("change_percent_24h")
            volume     = t.get("volume_24h")
            market_cap = None
            extra      = {}

        if price is None:
            raise HTTPException(status_code=404, detail="Could not fetch price")

        snap = await svc.save_price_snapshot(
            db, symbol, asset_type, price, change_pct, volume, market_cap, extra
        )
        return {
            "saved": True, "symbol": symbol,
            "price": price, "recorded_at": snap.recorded_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Snapshot error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price-history/{symbol}")
async def price_history(
    symbol: str,
    days:  int = Query(30, ge=1, le=365),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_price_history(db, symbol, days, limit)
    return {"symbol": symbol.upper(), "days": days, "data": data, "count": len(data)}


@router.get("/tracked")
async def tracked_symbols(db: AsyncSession = Depends(get_db)):
    symbols = await svc.get_tracked_symbols(db)
    return {"symbols": symbols}


# ── ML run history ─────────────────────────────────────────────────────────

@router.post("/ml-run")
async def save_ml_run(payload: MLRunPayload, db: AsyncSession = Depends(get_db)):
    run = await svc.save_ml_run(db, payload.model_dump())
    return {"saved": True, "id": run.id, "created_at": run.created_at.isoformat()}


@router.get("/ml-history")
async def ml_history(
    symbol: Optional[str] = None,
    model:  Optional[str] = None,
    limit:  int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows = await svc.get_ml_history(db, symbol, model, limit)
    return {"rows": rows, "count": len(rows)}


@router.get("/ml-stats")
async def ml_stats(
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Per-model aggregated accuracy metrics from all stored runs."""
    stats = await svc.get_model_comparison_stats(db, symbol)
    return {"stats": stats}


# ── Backtest history ───────────────────────────────────────────────────────

@router.post("/backtest-run")
async def save_backtest(payload: BacktestPayload, db: AsyncSession = Depends(get_db)):
    rec = await svc.save_backtest(db, payload.model_dump())
    return {"saved": True, "id": rec.id, "created_at": rec.created_at.isoformat()}


@router.get("/backtest-history")
async def backtest_history(
    symbol: Optional[str] = None,
    limit:  int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    rows = await svc.get_backtest_history(db, symbol, limit)
    return {"rows": rows, "count": len(rows)}


# ── Research notes ─────────────────────────────────────────────────────────

@router.get("/notes")
async def get_notes(
    symbol: Optional[str] = None,
    limit:  int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    notes = await svc.get_notes(db, symbol, limit)
    return {"notes": notes, "count": len(notes)}


@router.post("/notes")
async def create_note(body: NoteCreate, db: AsyncSession = Depends(get_db)):
    note = await svc.create_note(
        db, body.symbol, body.asset_type, body.title,
        body.content, body.tags, body.price_at,
    )
    return {
        "saved": True, "id": note.id,
        "created_at": note.created_at.isoformat(),
    }


@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    body: NoteUpdate,
    db: AsyncSession = Depends(get_db),
):
    note = await svc.update_note(db, note_id, body.title, body.content, body.tags)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"updated": True, "id": note_id}


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    ok = await svc.delete_note(db, note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True}


# ── Watchlist ──────────────────────────────────────────────────────────────

@router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    items = await svc.get_watchlist(db)
    return {"items": items, "count": len(items)}


@router.post("/watchlist")
async def add_watchlist(body: WatchlistAdd, db: AsyncSession = Depends(get_db)):
    result = await svc.add_to_watchlist(
        db, body.symbol, body.name, body.asset_type,
        body.track_price, body.notes,
    )
    return result


@router.delete("/watchlist/{symbol}")
async def remove_watchlist(symbol: str, db: AsyncSession = Depends(get_db)):
    ok = await svc.remove_from_watchlist(db, symbol)
    if not ok:
        raise HTTPException(status_code=404, detail="Symbol not in watchlist")
    return {"removed": True, "symbol": symbol.upper()}
