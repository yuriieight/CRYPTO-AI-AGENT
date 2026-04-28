"""Quick smoke tests for all API endpoints."""
import httpx, pytest

BASE = "http://localhost:8000/api/v1"

@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as c:
        r = await c.get("http://localhost:8000/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_market_price():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/market/price/BTC%2FUSDT")
    assert r.status_code == 200
    assert "price" in r.json()

@pytest.mark.asyncio
async def test_top_coins():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/market/top")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
