from fastapi import APIRouter

# Create main router
api_router = APIRouter()

# Import and include all sub-routers
try:
    from .market import router as market_router
    api_router.include_router(market_router, prefix="/market", tags=["market"])
    print("✅ Market router loaded")
except Exception as e:
    print(f"❌ Market router error: {e}")

try:
    from .analysis import router as analysis_router
    api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
    print("✅ Analysis router loaded")
except Exception as e:
    print(f"❌ Analysis router error: {e}")

try:
    from .portfolio import router as portfolio_router
    api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
    print("✅ Portfolio router loaded")
except Exception as e:
    print(f"❌ Portfolio router error: {e}")

try:
    from .ai_chat import router as ai_chat_router
    api_router.include_router(ai_chat_router, prefix="/ai", tags=["ai"])
    print("✅ AI Chat router loaded")
except Exception as e:
    print(f"❌ AI Chat router error: {e}")

try:
    from .predictions import router as predictions_router
    api_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
    print("✅ Predictions router loaded")
except Exception as e:
    print(f"❌ Predictions router error: {e}")

try:
    from .news import router as news_router
    api_router.include_router(news_router, prefix="/news", tags=["news"])
    print("✅ News router loaded")
except Exception as e:
    print(f"❌ News router error: {e}")

try:
    from .stocks import router as stocks_router
    api_router.include_router(stocks_router, prefix="/stocks", tags=["stocks"])
    print("✅ Stocks router loaded")
except Exception as e:
    print(f"❌ Stocks router error: {e}")

try:
    from .users import router as users_router
    api_router.include_router(users_router, prefix="/users", tags=["users"])
    print("✅ Users router loaded")
except Exception as e:
    print(f"❌ Users router error: {e}")

try:
    from .research import router as research_router
    api_router.include_router(research_router, prefix="/research", tags=["research"])
    print("✅ Research router loaded")
except Exception as e:
    print(f"❌ Research router error: {e}")
