"""


Endpoints
─────────
GET /analysis/indicators/{symbol}   — Comprehensive technical indicators
GET /analysis/signals/{symbol}      — ML-powered trading signals
GET /analysis/trend/{symbol}        — Multi-factor trend analysis
GET /analysis/statistical/{symbol}  — Statistical time-series analysis
                                      (ADF, Hurst, autocorrelation,
                                       return distribution, VaR, ratios)
"""

from fastapi import APIRouter, HTTPException
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Technical indicators ───────────────────────────────────────────────────

@router.get("/indicators/{symbol:path}")
async def get_indicators(symbol: str, timeframe: str = "1d"):
    """Comprehensive technical indicators with extended set of metrics."""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service
        import pandas as pd

        historical = await binance_service.get_ohlcv(symbol, timeframe, 150)
        if not historical:
            raise HTTPException(status_code=404, detail="No data available")

        df = pd.DataFrame(historical)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = ml_service.calculate_technical_indicators(df)
        df = df.dropna(subset=["RSI"])

        if len(df) == 0:
            raise HTTPException(status_code=404, detail="Insufficient data")

        latest = df.iloc[-1]

        # Bollinger Band width (normalized squeeze indicator)
        bb_width = (float(latest["BB_upper"]) - float(latest["BB_lower"])) / (
            float(latest["BB_middle"]) + 1e-10
        )
        # Price position within Bollinger Bands (0 = lower band, 1 = upper)
        bb_pos = (float(latest["close"]) - float(latest["BB_lower"])) / (
            float(latest["BB_upper"]) - float(latest["BB_lower"]) + 1e-10
        )

        close = df["close"]
        # Stochastic %K (14-period)
        low14  = df["low"].rolling(14, min_periods=1).min().iloc[-1]
        high14 = df["high"].rolling(14, min_periods=1).max().iloc[-1]
        stoch_k = (float(latest["close"]) - float(low14)) / (
            float(high14) - float(low14) + 1e-10
        ) * 100

        # Williams %R (14-period)
        williams_r = (float(high14) - float(latest["close"])) / (
            float(high14) - float(low14) + 1e-10
        ) * -100

        # Rate of Change (different periods)
        roc_5  = float(close.pct_change(5).iloc[-1]) * 100
        roc_20 = float(close.pct_change(20).iloc[-1]) * 100

        # On-Balance Volume (last value)
        import numpy as np
        obv = float((np.sign(close.diff()) * df["volume"]).cumsum().iloc[-1])

        return {
            "symbol":   symbol,
            "timeframe": timeframe,
            "indicators": {
                # Trend
                "RSI":         round(float(latest["RSI"]), 2),
                "MACD":        round(float(latest["MACD"]), 6),
                "Signal_Line": round(float(latest["Signal_Line"]), 6),
                "MACD_Hist":   round(float(latest["MACD"]) - float(latest["Signal_Line"]), 6),
                # Moving Averages
                "SMA_7":       round(float(latest["SMA_7"]), 4),
                "SMA_25":      round(float(latest["SMA_25"]), 4),
                "SMA_99":      round(float(latest["SMA_99"]), 4),
                "EMA_12":      round(float(latest["EMA_12"]), 4),
                "EMA_26":      round(float(latest["EMA_26"]), 4),
                # Bollinger Bands
                "BB_upper":    round(float(latest["BB_upper"]), 4),
                "BB_middle":   round(float(latest["BB_middle"]), 4),
                "BB_lower":    round(float(latest["BB_lower"]), 4),
                "BB_width":    round(bb_width * 100, 2),
                "BB_position": round(bb_pos, 3),
                # Oscillators
                "Momentum":    round(float(latest["Momentum"]), 4),
                "ROC":         round(float(latest["ROC"]), 4),
                "ROC_5d":      round(roc_5, 2),
                "ROC_20d":     round(roc_20, 2),
                "Stoch_K":     round(stoch_k, 2),
                "Williams_R":  round(williams_r, 2),
                # Volume
                "Volume_SMA":  round(float(latest["Volume_SMA"]), 2),
                "Volume_Now":  round(float(df["volume"].iloc[-1]), 2),
                "OBV":         round(obv, 2),
            },
            "current_price": round(float(latest["close"]), 4),
            "price":         round(float(latest["close"]), 4),
            "timestamp":     str(latest["timestamp"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Trading signals ────────────────────────────────────────────────────────

@router.get("/signals/{symbol:path}")
async def get_signals(symbol: str, timeframe: str = "1d"):
    """ML-powered trading signals with entry/exit levels and reasoning."""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(symbol, timeframe, 150)
        if not historical:
            raise HTTPException(status_code=404, detail="No data")

        analysis = ml_service.analyze_trend(historical)
        signals  = ml_service.get_trading_signals(analysis)
        ticker   = await binance_service.get_ticker(symbol)

        return {
            "symbol":        symbol,
            "timeframe":     timeframe,
            "current_price": ticker["price"],
            "signals":       signals,
            "analysis":      analysis,
        }
    except Exception as e:
        logger.error(f"Signals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Trend analysis ─────────────────────────────────────────────────────────

@router.get("/trend/{symbol:path}")
async def get_trend(symbol: str, timeframe: str = "1d"):
    """Multi-indicator trend analysis with signal details."""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(symbol, timeframe, 150)
        if not historical:
            raise HTTPException(status_code=404, detail="No data")

        trend = ml_service.analyze_trend(historical)

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            "trend":     trend,
        }
    except Exception as e:
        logger.error(f"Trend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Statistical analysis ───────────────────────────────────────────────────

@router.get("/statistical/{symbol:path}")
async def get_statistical_analysis(symbol: str, timeframe: str = "1d", limit: int = 200):
    """
    Full statistical time-series analysis for diploma research:

    • ADF stationarity test (unit-root hypothesis)
    • Hurst exponent (trend persistence vs mean reversion)
    • Autocorrelation + Ljung-Box test (weak-form market efficiency)
    • Return distribution: skewness, kurtosis, Jarque-Bera normality
    • Historical VaR (95% / 99%) and Expected Shortfall
    • Volatility regime classification (low / normal / high)
    • Sortino, Calmar, Omega risk-adjusted performance ratios
    """
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import statistical_analyzer
        from datetime import datetime

        historical = await binance_service.get_ohlcv(symbol, timeframe, limit)
        if not historical:
            raise HTTPException(status_code=404, detail="No historical data")
        if len(historical) < 30:
            raise HTTPException(status_code=422, detail="Need at least 30 candles")

        result = statistical_analyzer.analyze(historical)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        return {
            "symbol":       symbol,
            "timeframe":    timeframe,
            "generated_at": datetime.now().isoformat(),
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Statistical analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
