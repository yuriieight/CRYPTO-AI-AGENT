"""
Research Database Service
─────────────────────────
All CRUD operations on the SQLite research database.
"""

from sqlalchemy import select, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from app.db.research_db import (
    PriceSnapshot, MLRunHistory, BacktestRecord,
    ResearchNote, WatchlistItem, PortfolioAsset,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# Price Snapshots
# ══════════════════════════════════════════════════════════════════════════

async def save_price_snapshot(db: AsyncSession, symbol: str, asset_type: str,
                               price: float, change_pct: float = None,
                               volume: float = None, market_cap: float = None,
                               extra: dict = None) -> PriceSnapshot:
    snap = PriceSnapshot(
        symbol=symbol.upper(), asset_type=asset_type,
        price=price, change_pct=change_pct,
        volume=volume, market_cap=market_cap, extra=extra or {},
        recorded_at=datetime.utcnow(),
    )
    db.add(snap)
    await db.flush()
    return snap


async def get_price_history(db: AsyncSession, symbol: str,
                             days: int = 30, limit: int = 500) -> List[Dict]:
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.symbol == symbol.upper(),
               PriceSnapshot.recorded_at >= since)
        .order_by(PriceSnapshot.recorded_at)
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "timestamp":  r.recorded_at.isoformat(),
            "price":      r.price,
            "change_pct": r.change_pct,
            "volume":     r.volume,
        }
        for r in rows
    ]


async def get_tracked_symbols(db: AsyncSession) -> List[str]:
    result = await db.execute(
        select(PriceSnapshot.symbol).distinct()
    )
    return [r[0] for r in result.all()]


# ══════════════════════════════════════════════════════════════════════════
# ML Run History
# ══════════════════════════════════════════════════════════════════════════

async def save_ml_run(db: AsyncSession, data: Dict) -> MLRunHistory:
    metrics  = data.get("training_metrics") or {}
    preds    = data.get("predictions") or []
    first    = preds[0] if preds else {}
    cur_price = data.get("current_price")

    run = MLRunHistory(
        symbol        = data["symbol"].upper(),
        timeframe     = data.get("timeframe", "1d"),
        model         = data.get("model", "ensemble"),
        periods       = data.get("periods", 7),
        mae           = metrics.get("mae"),
        rmse          = metrics.get("rmse"),
        r2            = metrics.get("r2"),
        mape          = metrics.get("mape"),
        feature_count = data.get("feature_count"),
        pred_price    = first.get("predicted_price"),
        pred_change   = first.get("change_pct"),
        confidence    = first.get("confidence"),
        current_price = cur_price,
        predictions   = preds,
        created_at    = datetime.utcnow(),
    )
    db.add(run)
    await db.flush()
    return run


async def get_ml_history(db: AsyncSession, symbol: str = None,
                          model: str = None, limit: int = 50) -> List[Dict]:
    q = select(MLRunHistory).order_by(desc(MLRunHistory.created_at)).limit(limit)
    if symbol:
        q = q.where(MLRunHistory.symbol == symbol.upper())
    if model:
        q = q.where(MLRunHistory.model == model)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id":           r.id,
            "symbol":       r.symbol,
            "timeframe":    r.timeframe,
            "model":        r.model,
            "periods":      r.periods,
            "metrics":      {"mae": r.mae, "rmse": r.rmse, "r2": r.r2, "mape": r.mape},
            "feature_count":r.feature_count,
            "pred_price":   r.pred_price,
            "pred_change":  r.pred_change,
            "confidence":   r.confidence,
            "current_price":r.current_price,
            "created_at":   r.created_at.isoformat(),
        }
        for r in rows
    ]


async def get_model_comparison_stats(db: AsyncSession, symbol: str = None) -> List[Dict]:
    """Aggregate avg metrics per model from stored runs."""
    q = select(
        MLRunHistory.model,
        func.count(MLRunHistory.id).label("runs"),
        func.avg(MLRunHistory.mae).label("avg_mae"),
        func.avg(MLRunHistory.rmse).label("avg_rmse"),
        func.avg(MLRunHistory.r2).label("avg_r2"),
        func.avg(MLRunHistory.mape).label("avg_mape"),
    ).group_by(MLRunHistory.model).order_by(func.avg(MLRunHistory.mae))
    if symbol:
        q = q.where(MLRunHistory.symbol == symbol.upper())
    result = await db.execute(q)
    return [
        {
            "model":    r.model,
            "runs":     r.runs,
            "avg_mae":  round(r.avg_mae or 0, 4),
            "avg_rmse": round(r.avg_rmse or 0, 4),
            "avg_r2":   round(r.avg_r2 or 0, 4),
            "avg_mape": round(r.avg_mape or 0, 2),
        }
        for r in result.all()
    ]


# ══════════════════════════════════════════════════════════════════════════
# Backtest Records
# ══════════════════════════════════════════════════════════════════════════

async def save_backtest(db: AsyncSession, data: Dict) -> BacktestRecord:
    pm = data.get("prediction_metrics") or {}
    rec = BacktestRecord(
        symbol          = data["symbol"].upper(),
        timeframe       = data.get("timeframe", "1d"),
        model           = data.get("model", "gradient_boosting"),
        initial_capital = data.get("initial_capital", 10000),
        final_capital   = data.get("final_capital"),
        total_return_pct= data.get("total_return_pct"),
        win_rate        = data.get("win_rate"),
        total_trades    = data.get("total_trades"),
        profit_factor   = data.get("profit_factor"),
        sharpe_ratio    = data.get("sharpe_ratio"),
        max_drawdown_pct= data.get("max_drawdown_pct"),
        avg_win         = data.get("avg_win"),
        avg_loss        = data.get("avg_loss"),
        pred_mae        = pm.get("mae"),
        pred_r2         = pm.get("r2"),
        equity_curve    = data.get("equity_curve", [])[:50],   # trim to 50 pts
        recent_trades   = data.get("recent_trades", [])[-10:],
        created_at      = datetime.utcnow(),
    )
    db.add(rec)
    await db.flush()
    return rec


async def get_backtest_history(db: AsyncSession, symbol: str = None,
                                limit: int = 30) -> List[Dict]:
    q = select(BacktestRecord).order_by(desc(BacktestRecord.created_at)).limit(limit)
    if symbol:
        q = q.where(BacktestRecord.symbol == symbol.upper())
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id":               r.id,
            "symbol":           r.symbol,
            "timeframe":        r.timeframe,
            "model":            r.model,
            "initial_capital":  r.initial_capital,
            "final_capital":    r.final_capital,
            "total_return_pct": r.total_return_pct,
            "win_rate":         r.win_rate,
            "total_trades":     r.total_trades,
            "profit_factor":    r.profit_factor,
            "sharpe_ratio":     r.sharpe_ratio,
            "max_drawdown_pct": r.max_drawdown_pct,
            "pred_mae":         r.pred_mae,
            "pred_r2":          r.pred_r2,
            "equity_curve":     r.equity_curve,
            "created_at":       r.created_at.isoformat(),
        }
        for r in rows
    ]


# ══════════════════════════════════════════════════════════════════════════
# Research Notes
# ══════════════════════════════════════════════════════════════════════════

async def create_note(db: AsyncSession, symbol: str, asset_type: str,
                       title: str, content: str, tags: str = "",
                       price_at: float = None) -> ResearchNote:
    note = ResearchNote(
        symbol=symbol.upper(), asset_type=asset_type,
        title=title, content=content,
        tags=tags, price_at=price_at,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(note)
    await db.flush()
    return note


async def update_note(db: AsyncSession, note_id: int, title: str = None,
                       content: str = None, tags: str = None) -> Optional[ResearchNote]:
    result = await db.execute(select(ResearchNote).where(ResearchNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return None
    if title   is not None: note.title   = title
    if content is not None: note.content = content
    if tags    is not None: note.tags    = tags
    note.updated_at = datetime.utcnow()
    await db.flush()
    return note


async def delete_note(db: AsyncSession, note_id: int) -> bool:
    result = await db.execute(delete(ResearchNote).where(ResearchNote.id == note_id))
    return result.rowcount > 0


async def get_notes(db: AsyncSession, symbol: str = None,
                     limit: int = 50) -> List[Dict]:
    q = select(ResearchNote).order_by(desc(ResearchNote.created_at)).limit(limit)
    if symbol:
        q = q.where(ResearchNote.symbol == symbol.upper())
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id":         r.id,
            "symbol":     r.symbol,
            "asset_type": r.asset_type,
            "title":      r.title,
            "content":    r.content,
            "tags":       r.tags,
            "price_at":   r.price_at,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rows
    ]


# ══════════════════════════════════════════════════════════════════════════
# Watchlist
# ══════════════════════════════════════════════════════════════════════════

async def get_watchlist(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(WatchlistItem).order_by(WatchlistItem.added_at)
    )
    rows = result.scalars().all()
    return [
        {
            "id":         r.id,
            "symbol":     r.symbol,
            "name":       r.name,
            "asset_type": r.asset_type,
            "track_price":r.track_price,
            "notes":      r.notes,
            "added_at":   r.added_at.isoformat(),
        }
        for r in rows
    ]


async def add_to_watchlist(db: AsyncSession, symbol: str, name: str = None,
                            asset_type: str = "crypto", track_price: bool = True,
                            notes: str = None) -> Dict:
    # Upsert
    stmt = sqlite_insert(WatchlistItem).values(
        symbol=symbol.upper(), name=name, asset_type=asset_type,
        track_price=track_price, notes=notes, added_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["symbol"],
        set_={"name": name, "asset_type": asset_type,
              "track_price": track_price, "notes": notes},
    )
    await db.execute(stmt)
    await db.flush()
    return {"symbol": symbol.upper(), "added": True}


async def remove_from_watchlist(db: AsyncSession, symbol: str) -> bool:
    result = await db.execute(
        delete(WatchlistItem).where(WatchlistItem.symbol == symbol.upper())
    )
    return result.rowcount > 0


# ══════════════════════════════════════════════════════════════════════════
# Portfolio (persistent)
# ══════════════════════════════════════════════════════════════════════════

async def get_portfolio(db: AsyncSession, user_id: str) -> List[Dict]:
    result = await db.execute(
        select(PortfolioAsset)
        .where(PortfolioAsset.user_id == user_id)
        .order_by(PortfolioAsset.purchase_date)
    )
    rows = result.scalars().all()
    return [
        {
            "symbol":         r.symbol,
            "asset_type":     r.asset_type,
            "amount":         r.amount,
            "purchase_price": r.purchase_price,
            "purchase_date":  r.purchase_date.isoformat(),
            "notes":          r.notes,
        }
        for r in rows
    ]


async def upsert_portfolio_asset(db: AsyncSession, user_id: str, symbol: str,
                                  amount: float, purchase_price: float,
                                  asset_type: str = "crypto",
                                  notes: str = None) -> bool:
    result = await db.execute(
        select(PortfolioAsset)
        .where(PortfolioAsset.user_id == user_id,
               PortfolioAsset.symbol  == symbol.upper())
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Weighted average price
        total = existing.amount + amount
        wavg  = (existing.amount * existing.purchase_price +
                 amount * purchase_price) / total if total > 0 else purchase_price
        existing.amount = total
        existing.purchase_price = round(wavg, 8)
        if notes is not None:
            existing.notes = notes
    else:
        db.add(PortfolioAsset(
            user_id=user_id, symbol=symbol.upper(),
            asset_type=asset_type, amount=amount,
            purchase_price=purchase_price,
            purchase_date=datetime.utcnow(), notes=notes,
        ))
    await db.flush()
    return True


async def update_portfolio_asset(db: AsyncSession, user_id: str, symbol: str,
                                  amount: float, purchase_price: float) -> bool:
    result = await db.execute(
        select(PortfolioAsset)
        .where(PortfolioAsset.user_id == user_id,
               PortfolioAsset.symbol  == symbol.upper())
    )
    asset = result.scalar_one_or_none()
    if not asset:
        return False
    asset.amount = amount
    asset.purchase_price = purchase_price
    await db.flush()
    return True


async def delete_portfolio_asset(db: AsyncSession, user_id: str,
                                  symbol: str) -> bool:
    result = await db.execute(
        delete(PortfolioAsset)
        .where(PortfolioAsset.user_id == user_id,
               PortfolioAsset.symbol  == symbol.upper())
    )
    return result.rowcount > 0
