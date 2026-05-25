import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("🚀 Starting Crypto AI Agent...")
    
    try:
        from app.db.database import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database OK")
    except Exception as e:
        logger.warning(f"⚠️ Database: {e}")

    try:
        from app.db.research_db import init_db
        await init_db()
        logger.info("✅ Research DB (SQLite) OK")
    except Exception as e:
        logger.warning(f"⚠️ Research DB: {e}")
    
    logger.info("📊 Server: http://localhost:8000")
    
    yield
    
    logger.info("👋 Shutting down...")
    try:
        from app.db.database import engine
        await engine.dispose()
    except:
        pass


# Create app
app = FastAPI(
    title="Crypto AI Agent",
    description="AI-powered crypto trading platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crypto-ai-agent"}

@app.get("/")
async def root():
    return {
        "message": "Crypto AI Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Include API routes
from app.api import api_router
app.include_router(api_router, prefix="/api/v1")

logger.info("✅ All routes registered")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
