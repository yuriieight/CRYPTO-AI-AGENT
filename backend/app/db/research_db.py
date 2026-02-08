"""
SQLite Research Database
─────────────────────────
File-based, zero-setup. Stores:
  • price_snapshots   — periodic price history (crypto + stocks)
  • ml_run_history    — every ML prediction run with full metrics
  • backtest_records  — backtest results per symbol/model
  • research_notes    — free-form analyst notes per symbol
  • watchlist         — persistent symbol watchlist
  • portfolio_assets  — portfolio (replaces in-memory dict)
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Text,
    Boolean, Index, UniqueConstraint
)
from datetime import datetime
import os

# ── Database file lives in the backend directory ──────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "crypto_research.db")
DB_PATH = os.path.abspath(DB_PATH)
SQLITE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(
    SQLITE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession,
    expire_on_commit=False, autocommit=False, autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ══════════════════════════════════════════════════════════════════════════
# Models
# ══════════════════════════════════════════════════════════════════════════

class PriceSnapshot(Base):
    """Periodic price snapshots — the raw material for price-history charts."""
    __tablename__ = "price_snapshots"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    symbol      = Column(String(20), nullable=False, index=True)
    asset_type  = Column(String(10), nullable=False, default="crypto")  # crypto | stock
    price       = Column(Float, nullable=False)
    change_pct  = Column(Float)
    volume      = Column(Float)
    market_cap  = Column(Float)
    extra       = Column(JSON)          # extra fields (high/low, pe_ratio, …)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_price_snap_sym_time", "symbol", "recorded_at"),
    )


class MLRunHistory(Base):
    """Each call to the ML prediction endpoint is stored here."""
    __tablename__ = "ml_run_history"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    symbol       = Column(String(20), nullable=False, index=True)
    timeframe    = Column(String(10), nullable=False)
    model        = Column(String(40), nullable=False)
    periods      = Column(Integer, nullable=False)
    # Training quality metrics
    mae          = Column(Float)
    rmse         = Column(Float)
    r2           = Column(Float)
    mape         = Column(Float)
    feature_count= Column(Integer)
    # First prediction (next period)
    pred_price   = Column(Float)
    pred_change  = Column(Float)       # % vs current price
    confidence   = Column(Float)
    current_price= Column(Float)
    # Full predictions JSON
    predictions  = Column(JSON)
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class BacktestRecord(Base):
    """Backtesting run results."""
    __tablename__ = "backtest_records"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    symbol          = Column(String(20), nullable=False, index=True)
    timeframe       = Column(String(10), nullable=False)
    model           = Column(String(40), nullable=False)
    initial_capital = Column(Float, default=10000.0)
    final_capital   = Column(Float)
    total_return_pct= Column(Float)
    win_rate        = Column(Float)
    total_trades    = Column(Integer)
    profit_factor   = Column(Float)
    sharpe_ratio    = Column(Float)
    max_drawdown_pct= Column(Float)
    avg_win         = Column(Float)
    avg_loss        = Column(Float)
    pred_mae        = Column(Float)
    pred_r2         = Column(Float)
    equity_curve    = Column(JSON)      # sampled points
    recent_trades   = Column(JSON)
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class ResearchNote(Base):
    """Free-form analyst notes attached to a symbol."""
    __tablename__ = "research_notes"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(10), default="crypto")
    title      = Column(String(200), nullable=False)
    content    = Column(Text, nullable=False)
    tags       = Column(String(200))   # comma-separated
    price_at   = Column(Float)         # price when note was written
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class WatchlistItem(Base):
    """Persistent watchlist (crypto + stocks)."""
    __tablename__ = "watchlist"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String(20), nullable=False, unique=True)
    name       = Column(String(100))
    asset_type = Column(String(10), default="crypto")
    track_price= Column(Boolean, default=True)   # auto-save PriceSnapshot
    notes      = Column(Text)
    added_at   = Column(DateTime, nullable=False, default=datetime.utcnow)


class PortfolioAsset(Base):
    """Portfolio — replaces the in-memory dict in portfolio.py."""
    __tablename__ = "portfolio_assets"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(String(50), nullable=False, index=True)
    symbol         = Column(String(20), nullable=False)
    asset_type     = Column(String(10), default="crypto")
    amount         = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date  = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes          = Column(Text)

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),
    )
