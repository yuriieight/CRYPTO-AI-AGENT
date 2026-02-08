
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Public REST Fallback (no API key, no clock issues)
# ─────────────────────────────────────────────

BINANCE_BASE = "https://api.binance.com"


async def _public_get(path: str, params: dict = None, timeout: int = 10) -> dict | list:
    """Simple async GET against Binance public REST API (no auth required)."""
    url = BINANCE_BASE + path
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout)
    ) as session:
        async with session.get(url, params=params or {}) as resp:
            resp.raise_for_status()
            return await resp.json()


# ─────────────────────────────────────────────
# Interval mapping
# ─────────────────────────────────────────────

CCXT_TO_BINANCE: Dict[str, str] = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
}


class BinanceService:
    """
    Binance market data service.

    Strategy:
      - Primary:  ccxt with adjustForTimeDifference (handles clock skew)
      - Fallback: direct public Binance REST (zero auth, zero clock issues)
    """

    def __init__(self):
        try:
            from app.core.config import settings
            api_key    = getattr(settings, "BINANCE_API_KEY", "")
            api_secret = getattr(settings, "BINANCE_API_SECRET", "")
        except Exception:
            api_key = api_secret = ""

        self.exchange = ccxt.binance({
            "apiKey":  api_key,
            "secret":  api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
                # ← KEY FIX: ccxt fetches server time and corrects the offset
                "adjustForTimeDifference": True,
                "recvWindow": 10000,        # 10 s window (Binance max = 60 s)
                "timeDifference": 0,        # will be auto-filled
            },
        })
        self._time_synced = False
        logger.info("✅ BinanceService initialized (adjustForTimeDifference=True)")

    # ── Time sync ────────────────────────────────────────────────────────

    async def _ensure_time_sync(self):
        """Force a server-time fetch so ccxt recalculates the offset."""
        if self._time_synced:
            return
        try:
            await self.exchange.load_time_difference()
            self._time_synced = True
            offset = self.exchange.options.get("timeDifference", 0)
            logger.info(f"⏱️  Clock offset with Binance: {offset} ms")
        except Exception as e:
            logger.warning(f"Time sync skipped: {e}")

    # ── Public helpers ───────────────────────────────────────────────────

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """BTC/USDT → BTCUSDT (REST) or keep BTC/USDT (ccxt)."""
        return symbol.replace("/", "")

    # ── Ticker ───────────────────────────────────────────────────────────

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker — tries ccxt first, falls back to public REST."""
        await self._ensure_time_sync()
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return self._format_ticker(symbol, ticker)
        except Exception as ccxt_err:
            logger.warning(f"ccxt ticker failed for {symbol}, using REST: {ccxt_err}")
            return await self._rest_ticker(symbol)

    async def _rest_ticker(self, symbol: str) -> Dict:
        """Public REST fallback for ticker."""
        sym = self._normalize_symbol(symbol)
        data = await _public_get("/api/v3/ticker/24hr", {"symbol": sym})
        price = float(data.get("lastPrice", 0))
        return {
            "symbol":            symbol,
            "price":             price,
            "change_24h":        float(data.get("priceChange", 0)),
            "change_percent_24h":float(data.get("priceChangePercent", 0)),
            "volume_24h":        float(data.get("quoteVolume", 0)),
            "high_24h":          float(data.get("highPrice", 0)),
            "low_24h":           float(data.get("lowPrice", 0)),
            "timestamp":         int(datetime.now().timestamp() * 1000),
        }

    @staticmethod
    def _format_ticker(symbol: str, t: dict) -> Dict:
        return {
            "symbol":            symbol,
            "price":             t.get("last", 0),
            "change_24h":        t.get("change", 0),
            "change_percent_24h":t.get("percentage", 0),
            "volume_24h":        t.get("quoteVolume", 0),
            "high_24h":          t.get("high", 0),
            "low_24h":           t.get("low", 0),
            "timestamp":         t.get("timestamp", int(datetime.now().timestamp() * 1000)),
        }

    # ── OHLCV ─────────────────────────────────────────────────────────────

    async def get_ohlcv(self, symbol: str, timeframe: str = "1d",
                         limit: int = 100) -> List[Dict]:
        """Get candlestick data — ccxt with REST fallback."""
        await self._ensure_time_sync()
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            return self._format_ohlcv(ohlcv)
        except Exception as ccxt_err:
            logger.warning(f"ccxt OHLCV failed for {symbol}, using REST: {ccxt_err}")
            return await self._rest_ohlcv(symbol, timeframe, limit)

    async def _rest_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """Public REST fallback for candlesticks."""
        interval = CCXT_TO_BINANCE.get(timeframe, "1d")
        sym      = self._normalize_symbol(symbol)
        candles  = await _public_get(
            "/api/v3/klines",
            {"symbol": sym, "interval": interval, "limit": min(limit, 1000)},
        )
        return [
            {
                "timestamp": datetime.fromtimestamp(c[0] / 1000).isoformat(),
                "open":      float(c[1]),
                "high":      float(c[2]),
                "low":       float(c[3]),
                "close":     float(c[4]),
                "volume":    float(c[5]),
            }
            for c in candles
        ]

    @staticmethod
    def _format_ohlcv(ohlcv: list) -> List[Dict]:
        return [
            {
                "timestamp": datetime.fromtimestamp(c[0] / 1000).isoformat(),
                "open":      c[1] or 0,
                "high":      c[2] or 0,
                "low":       c[3] or 0,
                "close":     c[4] or 0,
                "volume":    c[5] or 0,
            }
            for c in ohlcv
        ]

    # ── Top cryptos ───────────────────────────────────────────────────────

    async def get_top_cryptos(self, limit: int = 20) -> List[Dict]:
        """Get top USDT pairs by volume — REST fallback first (more reliable)."""
        try:
            return await self._rest_top_cryptos(limit)
        except Exception as rest_err:
            logger.warning(f"REST top cryptos failed: {rest_err}, trying ccxt...")
            return await self._ccxt_top_cryptos(limit)

    async def _rest_top_cryptos(self, limit: int) -> List[Dict]:
        """Public REST: fetch all 24h tickers, filter USDT pairs, sort by volume."""
        all_tickers = await _public_get("/api/v3/ticker/24hr")
        usdt = []
        for t in all_tickers:
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            price  = float(t.get("lastPrice",          0))
            volume = float(t.get("quoteVolume",         0))
            if price <= 0 or volume <= 0:
                continue
            usdt.append({
                "symbol":            sym[:-4] + "/USDT",
                "price":             price,
                "change_24h":        float(t.get("priceChange",        0)),
                "change_percent_24h":float(t.get("priceChangePercent", 0)),
                "volume_24h":        volume,
                "market_cap":        volume * price,
            })
        usdt.sort(key=lambda x: x["volume_24h"], reverse=True)
        return usdt[:limit]

    async def _ccxt_top_cryptos(self, limit: int) -> List[Dict]:
        await self._ensure_time_sync()
        markets = await self.exchange.fetch_tickers()
        usdt    = []
        for symbol, data in markets.items():
            if not symbol.endswith("/USDT"):
                continue
            price  = data.get("last")  or data.get("close") or 0
            volume = data.get("quoteVolume") or data.get("baseVolume") or 0
            if not price or not volume:
                continue
            usdt.append({
                "symbol":            symbol,
                "price":             float(price),
                "change_24h":        float(data.get("change",     0)),
                "change_percent_24h":float(data.get("percentage", 0)),
                "volume_24h":        float(volume),
                "market_cap":        float(volume) * float(price),
            })
        usdt.sort(key=lambda x: x["volume_24h"], reverse=True)
        return usdt[:limit]

    # ── Multiple tickers ──────────────────────────────────────────────────

    async def get_multiple_tickers(self, symbols: List[str]) -> List[Dict]:
        tasks   = [self.get_ticker(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    # ── Order book ────────────────────────────────────────────────────────

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        await self._ensure_time_sync()
        try:
            ob = await self.exchange.fetch_order_book(symbol, limit)
            return {
                "symbol":    symbol,
                "bids":      ob["bids"][:limit],
                "asks":      ob["asks"][:limit],
                "timestamp": ob.get("timestamp", int(datetime.now().timestamp() * 1000)),
            }
        except Exception as ccxt_err:
            logger.warning(f"ccxt orderbook failed, using REST: {ccxt_err}")
            return await self._rest_order_book(symbol, limit)

    async def _rest_order_book(self, symbol: str, limit: int) -> Dict:
        sym  = self._normalize_symbol(symbol)
        data = await _public_get("/api/v3/depth", {"symbol": sym, "limit": min(limit, 100)})
        bids = [[float(p), float(q)] for p, q in data.get("bids", [])[:limit]]
        asks = [[float(p), float(q)] for p, q in data.get("asks", [])[:limit]]
        return {
            "symbol":    symbol,
            "bids":      bids,
            "asks":      asks,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    # ── Cleanup ───────────────────────────────────────────────────────────

    async def close(self):
        try:
            await self.exchange.close()
        except Exception as e:
            logger.error(f"Error closing exchange: {e}")


# Singleton
binance_service = BinanceService()