"""Market API router (stub)."""
from fastapi import APIRouter
from app.services.market_service_stub import get_price

router = APIRouter(prefix="/api/v1/market", tags=["market"])

@router.get("/price/{symbol}")
async def price(symbol: str):
    return await get_price(symbol)
