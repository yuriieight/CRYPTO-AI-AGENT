from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Portfolio Schemas
class AssetBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: float
    purchase_price: float
    asset_type: str


class AssetResponse(AssetBase):
    id: int
    current_price: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: int
    total_value: float
    profit_loss: float
    profit_loss_percent: Optional[float] = None
    assets: List[AssetResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


# Market Data Schemas
class MarketDataResponse(BaseModel):
    symbol: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    market_cap: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None


class CandlestickData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoricalDataResponse(BaseModel):
    symbol: str
    data: List[CandlestickData]


# Analysis Schemas
class TechnicalIndicators(BaseModel):
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    moving_averages: Optional[Dict[str, float]] = None
    bollinger_bands: Optional[Dict[str, float]] = None
    volume_analysis: Optional[Dict[str, Any]] = None


class SentimentAnalysis(BaseModel):
    overall_sentiment: str
    sentiment_score: float  # -1 to 1
    sources: List[Dict[str, Any]]
    keywords: List[str]


class PredictionResponse(BaseModel):
    symbol: str
    current_price: float
    predictions: List[Dict[str, Any]]
    confidence: float
    model: str
    timeframe: str


class SignalResponse(BaseModel):
    symbol: str
    signal: str  # buy, sell, hold
    strength: float
    price: float
    reasoning: str
    indicators: TechnicalIndicators
    timestamp: datetime


# AI Chat Schemas
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    charts: Optional[List[Dict[str, Any]]] = None


# Watchlist Schemas
class WatchlistItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    asset_type: str
    notes: Optional[str] = None


class WatchlistResponse(WatchlistItem):
    id: int
    current_price: Optional[float] = None
    change_24h: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Analysis Request
class AnalysisRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1d"
    indicators: Optional[List[str]] = None
