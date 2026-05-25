from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import all routers
from .market import router as market_router
from .analysis import router as analysis_router
from .portfolio import router as portfolio_router
from .ai_chat import router as ai_chat_router
from .predictions import router as predictions_router
from .news import router as news_router
from .users import router as users_router
from .stocks import router as stocks_router
from .research import router as research_router

# Include all routers
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(ai_chat_router, prefix="/ai", tags=["ai"])
api_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
api_router.include_router(news_router, prefix="/news", tags=["news"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(stocks_router, prefix="/stocks", tags=["stocks"])
api_router.include_router(research_router, prefix="/research", tags=["research"])

print("✅ All API routers loaded successfully")
