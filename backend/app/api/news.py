"""
News Router — Enhanced with NLP analysis, multi-article analysis, market sentiment
"""

from fastapi import APIRouter, HTTPException
from app.services.news_service import news_service
from pydantic import BaseModel
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class NewsArticle(BaseModel):
    title: str
    description: str
    url: str
    source: str
    published_at: str
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    topic: str = "general"


# ── Fetch news ─────────────────────────────────────────────────────────────

@router.get("/{symbol}")
async def get_crypto_news(symbol: str, limit: int = 20):
    """Fetch news with full NLP enrichment"""
    try:
        from app.services.news_service import news_service
        articles = await news_service.get_news(symbol, limit)
        return articles
    except Exception as e:
        logger.error(f"News error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Full NLP analysis ──────────────────────────────────────────────────────

@router.get("/analysis/{symbol}")
async def get_news_analysis(symbol: str, limit: int = 30):
    """Full NLP-powered news analysis with sentiment index, keywords, topics"""
    try:
        from app.services.news_service import news_service
        analysis = await news_service.get_analysis(symbol, limit)
        return analysis
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Analyze pre-fetched articles ───────────────────────────────────────────

@router.post("/analyze")
async def analyze_news(symbol: str, articles: List[NewsArticle]):
    """Analyze a list of submitted articles using NLP pipeline"""
    try:
        from app.services.news_service import news_service

        raw = [a.dict() for a in articles]
        result = news_service.analyze_articles(raw, symbol)
        return result
    except Exception as e:
        logger.error(f"Article analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Market-wide sentiment ──────────────────────────────────────────────────

@router.get("/sentiment/market")
async def get_market_sentiment():
    """Quick sentiment snapshot for top 5 cryptocurrencies"""
    try:
        from app.services.news_service import news_service
        symbols = ["BTC", "ETH", "BNB", "SOL", "XRP"]
        result  = await news_service.get_market_sentiment(symbols)
        return {"symbols": result}
    except Exception as e:
        logger.error(f"Market sentiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{symbol}")
async def analyze_market_news(symbol: str, limit: int = 15):
    """Get AI-powered analysis of current news narrative"""
    try:
        analysis = await news_service.get_news_analysis(symbol, limit)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))