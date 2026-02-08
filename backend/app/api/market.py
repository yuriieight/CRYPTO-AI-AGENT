from fastapi import APIRouter, HTTPException, Query
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/top")
async def get_top_cryptos(limit: int = Query(default=10, ge=1, le=100)):
    """Get top cryptocurrencies"""
    try:
        from app.services.binance_service import binance_service
        cryptos = await binance_service.get_top_cryptos(limit)
        return cryptos
    except Exception as e:
        logger.error(f"Market top error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol:path}")
async def get_ticker(symbol: str):
    """Get ticker for symbol - accepts paths like BTC/USDT"""
    try:
        from app.services.binance_service import binance_service
        ticker = await binance_service.get_ticker(symbol)
        return ticker
    except Exception as e:
        logger.error(f"Ticker error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol:path}")
async def get_historical_data(
    symbol: str,
    timeframe: str = "1d",
    limit: int = 100
):
    """Get historical OHLCV data - accepts paths like BTC/USDT"""
    try:
        from app.services.binance_service import binance_service
        data = await binance_service.get_ohlcv(symbol, timeframe, limit)
        return data
    except Exception as e:
        logger.error(f"History error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orderbook/{symbol:path}")
async def get_order_book(symbol: str, limit: int = 20):
    """Get order book"""
    try:
        from app.services.binance_service import binance_service
        orderbook = await binance_service.get_order_book(symbol, limit)
        return orderbook
    except Exception as e:
        logger.error(f"Orderbook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
