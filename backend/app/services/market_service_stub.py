"""Market data service – Binance + yfinance."""
import httpx

BINANCE_BASE = "https://api.binance.com/api/v3"

async def get_price(symbol: str) -> dict:
    """Fetch current price from Binance ticker."""
    bn_symbol = symbol.replace("/", "")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BINANCE_BASE}/ticker/price", params={"symbol": bn_symbol})
        r.raise_for_status()
        data = r.json()
    return {"symbol": symbol, "price": float(data["price"])}
