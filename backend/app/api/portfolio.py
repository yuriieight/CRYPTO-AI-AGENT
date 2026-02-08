from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.research_db import get_db
import app.services.db_service as svc

logger = logging.getLogger(__name__)
router = APIRouter()


class AddAssetRequest(BaseModel):
    user_id: str
    symbol: str
    amount: float
    purchase_price: float
    asset_type: str = "crypto"
    notes: Optional[str] = None


class UpdateAssetRequest(BaseModel):
    user_id: str
    symbol: str
    amount: float
    purchase_price: float


@router.post("/add")
async def add_asset(request: AddAssetRequest, db: AsyncSession = Depends(get_db)):
    """Add or update asset in portfolio (weighted-average price on re-add)."""
    try:
        await svc.upsert_portfolio_asset(
            db, request.user_id, request.symbol,
            request.amount, request.purchase_price,
            request.asset_type, request.notes,
        )
        assets = await svc.get_portfolio(db, request.user_id)
        total_invested = sum(a["amount"] * a["purchase_price"] for a in assets)
        return {"success": True, "assets": assets, "total_invested": total_invested}
    except Exception as e:
        logger.error(f"Add asset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update")
async def update_asset(request: UpdateAssetRequest, db: AsyncSession = Depends(get_db)):
    """Overwrite amount and purchase price for an existing asset."""
    try:
        ok = await svc.update_portfolio_asset(
            db, request.user_id, request.symbol,
            request.amount, request.purchase_price,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Asset not found")
        assets = await svc.get_portfolio(db, request.user_id)
        total_invested = sum(a["amount"] * a["purchase_price"] for a in assets)
        return {"success": True, "assets": assets, "total_invested": total_invested}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove/{user_id}/{symbol:path}")
async def remove_asset(user_id: str, symbol: str, db: AsyncSession = Depends(get_db)):
    """Remove asset from portfolio."""
    try:
        ok = await svc.delete_portfolio_asset(db, user_id, symbol)
        if not ok:
            raise HTTPException(status_code=404, detail="Asset not found")
        assets = await svc.get_portfolio(db, user_id)
        total_invested = sum(a["amount"] * a["purchase_price"] for a in assets)
        return {"success": True, "assets": assets, "total_invested": total_invested}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
async def get_portfolio(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all portfolio assets for a user."""
    try:
        assets = await svc.get_portfolio(db, user_id)
        total_invested = sum(a["amount"] * a["purchase_price"] for a in assets)
        return {
            "user_id": user_id,
            "assets": assets,
            "total_invested": total_invested,
        }
    except Exception as e:
        logger.error(f"Get portfolio error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/performance")
async def get_portfolio_performance(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get portfolio performance with live prices."""
    try:
        from app.services.binance_service import binance_service

        assets = await svc.get_portfolio(db, user_id)
        if not assets:
            return {
                "total_invested": 0, "current_value": 0,
                "profit_loss": 0, "profit_loss_percent": 0, "assets": [],
            }

        asset_performance = []
        total_current_value = 0.0
        total_invested = 0.0

        for asset in assets:
            try:
                ticker = await binance_service.get_ticker(asset["symbol"])
                current_price = ticker["price"]
                current_value = asset["amount"] * current_price
                invested = asset["amount"] * asset["purchase_price"]
                pl = current_value - invested
                pl_pct = (pl / invested * 100) if invested > 0 else 0

                asset_performance.append({
                    "symbol":           asset["symbol"],
                    "amount":           asset["amount"],
                    "purchase_price":   asset["purchase_price"],
                    "current_price":    current_price,
                    "invested":         invested,
                    "current_value":    current_value,
                    "profit_loss":      pl,
                    "profit_loss_percent": pl_pct,
                })
                total_current_value += current_value
                total_invested      += invested
            except Exception as e:
                logger.error(f"Price error for {asset['symbol']}: {e}")

        pl = total_current_value - total_invested
        pl_pct = (pl / total_invested * 100) if total_invested > 0 else 0
        return {
            "total_invested":      total_invested,
            "current_value":       total_current_value,
            "profit_loss":         pl,
            "profit_loss_percent": pl_pct,
            "assets":              asset_performance,
        }
    except Exception as e:
        logger.error(f"Performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
