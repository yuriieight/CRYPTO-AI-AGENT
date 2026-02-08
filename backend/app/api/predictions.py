"""
Predictions Router — Extended with multi-model support, backtesting, and comparison
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    periods: int = 7
    # Available: linear_regression | ridge | lasso | elastic_net | bayesian_ridge | huber |
    #            random_forest | extra_trees | gradient_boosting | ada_boost |
    #            svr | knn | ensemble
    model: str = "ensemble"


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    model: str = "gradient_boosting"
    initial_capital: float = 10000.0


# ── Price prediction ───────────────────────────────────────────────────────

@router.post("/price")
async def predict_price(request: PredictionRequest):
    """Predict future prices using the selected ML model"""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(request.symbol, request.timeframe, 150)
        if not historical:
            raise HTTPException(status_code=404, detail="No historical data")

        result = ml_service.predict_price(historical, request.periods, request.model)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        trend = ml_service.analyze_trend(historical)

        response = {
            "symbol":          request.symbol,
            "model":           request.model,
            "timeframe":       request.timeframe,
            "periods":         request.periods,
            "predictions":     result["predictions"],
            "training_metrics":result.get("training_metrics", {}),
            "feature_count":   result.get("feature_count", 0),
            "trend_analysis":  trend,
            "generated_at":    datetime.now().isoformat(),
        }

        # Auto-save to research DB (fire-and-forget, non-blocking)
        try:
            from app.db.research_db import AsyncSessionLocal
            import app.services.db_service as svc
            async with AsyncSessionLocal() as db:
                ticker = await binance_service.get_ticker(request.symbol)
                await svc.save_ml_run(db, {
                    "symbol":           request.symbol,
                    "timeframe":        request.timeframe,
                    "model":            request.model,
                    "periods":          request.periods,
                    "current_price":    ticker.get("price"),
                    "training_metrics": result.get("training_metrics", {}),
                    "predictions":      result["predictions"],
                    "feature_count":    result.get("feature_count"),
                })
                await db.commit()
        except Exception as db_err:
            logger.warning(f"ML run save skipped: {db_err}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Model comparison ───────────────────────────────────────────────────────

@router.get("/compare/{symbol:path}")
async def compare_models(symbol: str, timeframe: str = "1d", periods: int = 3):
    """Train and compare all ML models side-by-side"""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(symbol, timeframe, 200)
        if not historical:
            raise HTTPException(status_code=404, detail="No data")

        comparison = ml_service.compare_models(historical, periods)
        if "error" in comparison:
            raise HTTPException(status_code=422, detail=comparison["error"])

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            **comparison,
            "generated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Backtesting ────────────────────────────────────────────────────────────

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run walk-forward backtest and return performance metrics"""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(request.symbol, request.timeframe, 300)
        if not historical or len(historical) < 40:
            raise HTTPException(status_code=404, detail="Need at least 40 candles for backtesting")

        result = ml_service.run_backtest(historical, request.model)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        response = {
            "symbol":    request.symbol,
            "timeframe": request.timeframe,
            **result,
            "generated_at": datetime.now().isoformat(),
        }

        # Auto-save to research DB
        try:
            from app.db.research_db import AsyncSessionLocal
            import app.services.db_service as svc
            async with AsyncSessionLocal() as db:
                await svc.save_backtest(db, {
                    "symbol":           request.symbol,
                    "timeframe":        request.timeframe,
                    "model":            request.model,
                    "initial_capital":  request.initial_capital,
                    **{k: result.get(k) for k in [
                        "final_capital", "total_return_pct", "win_rate",
                        "total_trades", "profit_factor", "sharpe_ratio",
                        "max_drawdown_pct", "avg_win", "avg_loss",
                        "prediction_metrics", "equity_curve", "recent_trades",
                    ]},
                })
                await db.commit()
        except Exception as db_err:
            logger.warning(f"Backtest save skipped: {db_err}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Feature importance ─────────────────────────────────────────────────────

@router.get("/features/{symbol:path}")
async def get_feature_importance(
    symbol: str,
    timeframe: str = "1d",
    model: str = "random_forest"
):
    """Return top feature importances from a tree-based model"""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service

        historical = await binance_service.get_ohlcv(symbol, timeframe, 200)
        if not historical:
            raise HTTPException(status_code=404, detail="No data")

        result = ml_service.get_feature_importance(historical, model)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            **result,
            "generated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature importance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Trading signals (ML-powered) ───────────────────────────────────────────

@router.get("/signals/{symbol:path}")
async def get_prediction_signals(symbol: str, timeframe: str = "1d"):
    """Get comprehensive ML-powered trading signals"""
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
            "current_price": ticker["price"],
            "signals":       signals,
            "analysis":      analysis,
            "generated_at":  datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Signals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Technical indicators (detailed) ───────────────────────────────────────

@router.get("/indicators/{symbol:path}")
async def get_prediction_indicators(symbol: str, timeframe: str = "1d"):
    """Get comprehensive technical indicators"""
    try:
        from app.services.binance_service import binance_service
        from app.services.ml_service import ml_service
        import pandas as pd

        historical = await binance_service.get_ohlcv(symbol, timeframe, 150)
        if not historical:
            raise HTTPException(status_code=404, detail="No data")

        df = pd.DataFrame(historical)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = ml_service.calculate_technical_indicators(df)
        df = df.dropna(subset=["RSI"])
        if len(df) == 0:
            raise HTTPException(status_code=422, detail="Insufficient data for indicators")

        latest = df.iloc[-1]

        return {
            "symbol":    symbol,
            "timeframe": timeframe,
            "indicators": {
                "RSI":         round(float(latest["RSI"]), 2),
                "MACD":        round(float(latest["MACD"]), 6),
                "Signal_Line": round(float(latest["Signal_Line"]), 6),
                "SMA_7":       round(float(latest["SMA_7"]), 4),
                "SMA_25":      round(float(latest["SMA_25"]), 4),
                "SMA_99":      round(float(latest["SMA_99"]), 4),
                "EMA_12":      round(float(latest["EMA_12"]), 4),
                "EMA_26":      round(float(latest["EMA_26"]), 4),
                "BB_upper":    round(float(latest["BB_upper"]), 4),
                "BB_middle":   round(float(latest["BB_middle"]), 4),
                "BB_lower":    round(float(latest["BB_lower"]), 4),
                "Momentum":    round(float(latest["Momentum"]), 4),
                "ROC":         round(float(latest["ROC"]), 4),
                "Volume_SMA":  round(float(latest["Volume_SMA"]), 2),
            },
            "current_price": round(float(latest["close"]), 4),
            "timestamp":     datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))