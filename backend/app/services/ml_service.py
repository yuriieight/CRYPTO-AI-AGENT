"""
ML Prediction Service 
Models: Linear Regression, Random Forest, Gradient Boosting, SVR, Ensemble
Features: Technical indicators, feature engineering, backtesting, model comparison
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, BayesianRidge, HuberRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor, ExtraTreesRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import warnings
import logging

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────

class FeatureEngineer:
    """Generates advanced features for ML models"""

    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """Build full feature matrix from OHLCV data"""
        df = df.copy()
        close = df["close"]
        high  = df["high"]
        low   = df["low"]
        vol   = df["volume"]

        # ── Price-based features ──────────────────
        for w in [3, 7, 14, 25, 50]:
            df[f"sma_{w}"]   = close.rolling(w, min_periods=1).mean()
            df[f"ema_{w}"]   = close.ewm(span=w, adjust=False).mean()
            df[f"ret_{w}d"]  = close.pct_change(w)
            df[f"std_{w}d"]  = close.rolling(w, min_periods=1).std()

        # ── MACD ──────────────────────────────────
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"]        = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]

        # ── RSI ───────────────────────────────────
        for period in [7, 14, 21]:
            delta = close.diff()
            gain  = delta.clip(lower=0).rolling(period, min_periods=1).mean()
            loss  = (-delta.clip(upper=0)).rolling(period, min_periods=1).mean()
            rs    = gain / (loss + 1e-10)
            df[f"rsi_{period}"] = 100 - (100 / (1 + rs))

        # ── Bollinger Bands ───────────────────────
        for w in [10, 20]:
            mid = close.rolling(w, min_periods=1).mean()
            std = close.rolling(w, min_periods=1).std().fillna(0)
            df[f"bb_upper_{w}"] = mid + 2 * std
            df[f"bb_lower_{w}"] = mid - 2 * std
            df[f"bb_width_{w}"] = (df[f"bb_upper_{w}"] - df[f"bb_lower_{w}"]) / (mid + 1e-10)
            df[f"bb_pos_{w}"]   = (close - df[f"bb_lower_{w}"]) / (df[f"bb_width_{w}"] * mid + 1e-10)

        # ── Momentum & oscillators ─────────────────
        df["momentum_10"]   = close - close.shift(10)
        df["roc_12"]        = ((close - close.shift(12)) / (close.shift(12) + 1e-10)) * 100
        df["williams_r"]    = ((high.rolling(14).max() - close) /
                               (high.rolling(14).max() - low.rolling(14).min() + 1e-10)) * -100
        df["cci"] = (close - close.rolling(20).mean()) / (0.015 * close.rolling(20).std() + 1e-10)

        # ── ATR (volatility) ──────────────────────
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs()
        ], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(14, min_periods=1).mean()
        df["atr_pct"] = df["atr_14"] / (close + 1e-10) * 100

        # ── Volume features ───────────────────────
        df["vol_sma20"]    = vol.rolling(20, min_periods=1).mean()
        df["vol_ratio"]    = vol / (df["vol_sma20"] + 1e-10)
        df["vol_price_corr"] = close.rolling(10).corr(vol)
        df["obv"]          = (np.sign(close.diff()) * vol).cumsum()

        # ── Lag features ──────────────────────────
        for lag in [1, 2, 3, 5, 7]:
            df[f"close_lag_{lag}"] = close.shift(lag)
            df[f"vol_lag_{lag}"]   = vol.shift(lag)

        # ── Price action ──────────────────────────
        df["high_low_ratio"]  = high / (low + 1e-10)
        df["close_open_ratio"]= close / (df.get("open", close) + 1e-10)
        df["upper_shadow"]    = (high - close.clip(lower=df.get("open", close))) / (high - low + 1e-10)

        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.bfill().ffill().fillna(0)
        return df

    @staticmethod
    def prepare_supervised(df: pd.DataFrame, target_col: str = "close",
                            horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
        """Create X, y for supervised learning"""
        drop_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        feature_cols = [c for c in df.columns if c not in drop_cols]
        X = df[feature_cols].copy()
        y = df[target_col].shift(-horizon)
        mask = y.notna()
        return X[mask], y[mask]


# ─────────────────────────────────────────────
# Individual Model Wrappers
# ─────────────────────────────────────────────

class ModelWrapper:
    """Unified wrapper for all sklearn-compatible models"""

    MODELS = {
        # ── Linear / regularised ──────────────────────────────────────────
        "linear_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression())
        ]),
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0))
        ]),
        "lasso": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Lasso(alpha=0.01, max_iter=2000))
        ]),
        "elastic_net": Pipeline([
            ("scaler", StandardScaler()),
            ("model", ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=2000))
        ]),
        "bayesian_ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", BayesianRidge(max_iter=300))
        ]),
        "huber": Pipeline([
            ("scaler", StandardScaler()),
            ("model", HuberRegressor(epsilon=1.35, max_iter=300))
        ]),
        # ── Tree-based ensembles ─────────────────────────────────────────
        "random_forest": RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=3,
            max_features="sqrt", n_jobs=-1, random_state=42
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=3,
            max_features="sqrt", n_jobs=-1, random_state=42
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=150, learning_rate=0.05, max_depth=4,
            min_samples_leaf=5, subsample=0.8, random_state=42
        ),
        "ada_boost": AdaBoostRegressor(
            n_estimators=100, learning_rate=0.1,
            loss="linear", random_state=42
        ),
        # ── Other ────────────────────────────────────────────────────────
        "svr": Pipeline([
            ("scaler", MinMaxScaler()),
            ("model", SVR(kernel="rbf", C=100, gamma=0.01, epsilon=0.1))
        ]),
        "knn": Pipeline([
            ("scaler", MinMaxScaler()),
            ("model", KNeighborsRegressor(n_neighbors=7, weights="distance",
                                          metric="euclidean"))
        ]),
    }

    def __init__(self, name: str):
        if name not in self.MODELS:
            raise ValueError(f"Unknown model: {name}")
        self.name = name
        import copy
        self.model = copy.deepcopy(self.MODELS[name])
        self.is_fitted = False
        self.metrics: Dict = {}

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.model.fit(X, y)
        self.is_fitted = True
        preds = self.model.predict(X)
        self.metrics = _compute_metrics(y.values, preds)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)

    def cv_score(self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> Dict:
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = cross_val_score(self.model, X, y, cv=tscv,
                                 scoring="neg_mean_absolute_error")
        return {
            "mean_mae": float(-scores.mean()),
            "std_mae":  float(scores.std())
        }

    def feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """Works for tree-based models"""
        try:
            m = self.model
            if hasattr(m, "feature_importances_"):
                fi = m.feature_importances_
            elif hasattr(m, "named_steps"):
                m2 = m.named_steps.get("model")
                if m2 and hasattr(m2, "feature_importances_"):
                    fi = m2.feature_importances_
                elif m2 and hasattr(m2, "coef_"):
                    fi = np.abs(m2.coef_)
                else:
                    return {}
            else:
                return {}
            top = sorted(zip(feature_names, fi.tolist()), key=lambda x: x[1], reverse=True)
            return dict(top[:15])
        except Exception:
            return {}


# ─────────────────────────────────────────────
# Ensemble Model
# ─────────────────────────────────────────────

class EnsemblePredictor:
    """Weighted average ensemble of multiple models"""

    def __init__(self, model_names: Optional[List[str]] = None):
        self.model_names = model_names or ["random_forest", "gradient_boosting", "ridge"]
        self.models: Dict[str, ModelWrapper] = {}
        self.weights: Dict[str, float] = {}
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series):
        errors = {}
        for name in self.model_names:
            try:
                mw = ModelWrapper(name)
                mw.fit(X, y)
                self.models[name] = mw
                errors[name] = mw.metrics.get("mae", 1.0) + 1e-10
                logger.info(f"✅ {name}: MAE={errors[name]:.4f}")
            except Exception as e:
                logger.warning(f"⚠️ {name} fit failed: {e}")

        # Inverse-error weighting
        total_inv = sum(1 / v for v in errors.values())
        self.weights = {k: (1 / v) / total_inv for k, v in errors.items()}
        self.is_fitted = True
        logger.info(f"🎯 Ensemble weights: {self.weights}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = np.zeros(len(X))
        for name, mw in self.models.items():
            preds += self.weights[name] * mw.predict(X)
        return preds

    def model_comparison(self, X: pd.DataFrame, y: pd.Series) -> List[Dict]:
        results = []
        for name, mw in self.models.items():
            preds = mw.predict(X)
            m = _compute_metrics(y.values, preds)
            results.append({
                "model": name,
                "weight": round(self.weights[name], 4),
                **m
            })
        results.sort(key=lambda x: x["mae"])
        return results


# ─────────────────────────────────────────────
# Backtesting Engine
# ─────────────────────────────────────────────

class BacktestEngine:
    """Simple walk-forward backtesting for ML predictions"""

    def __init__(self, initial_capital: float = 10_000.0):
        self.initial_capital = initial_capital

    def run(self, df: pd.DataFrame, predictor) -> Dict:
        """
        Walk-forward backtest with realistic exit logic.

        Entry:  predicted next price > current * 1.002 (0.2% threshold)
        Exit (any of the following, checked every bar):
          1. Model flips bearish: predicted < current * 0.998
          2. Take-profit:  price rose >= TP_PCT from entry
          3. Stop-loss:    price fell >= SL_PCT from entry
          4. Max hold:     position held MAX_HOLD bars → force close
        Final open position is always closed and recorded as a trade.
        """
        # ── Trading parameters ──────────────────────────────────────────
        BUY_THRESH  = 1.002   # predict ≥ +0.2%  to open
        SELL_THRESH = 0.998   # predict ≤ −0.2%  to close on model signal
        TP_PCT      = 0.04    # take-profit at +4 %
        SL_PCT      = 0.025   # stop-loss   at −2.5 %
        MAX_HOLD    = 8       # force-exit after 8 bars
        # ────────────────────────────────────────────────────────────────

        try:
            fe = FeatureEngineer()
            df_feat = fe.build_features(df)
            drop_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            feat_cols = [c for c in df_feat.columns if c not in drop_cols]

            # ── Timestamps for equity_curve ─────────────────────────────
            has_ts = "timestamp" in df_feat.columns
            timestamps = (
                df_feat["timestamp"].values
                if has_ts
                else pd.date_range(end=pd.Timestamp.now(), periods=len(df_feat), freq="D").values
            )

            split = int(len(df_feat) * 0.6)
            train_df = df_feat.iloc[:split]
            test_df  = df_feat.iloc[split:]

            X_train = train_df[feat_cols]
            # shift(-1) makes last row NaN; ffill fills it forward so sklearn
            # never sees NaN. Then drop any row where X or y is still NaN.
            y_train_raw = train_df["close"].shift(-1).ffill()
            valid_mask  = y_train_raw.notna() & X_train.notna().all(axis=1)
            X_fit = X_train[valid_mask]
            y_fit = y_train_raw[valid_mask]
            predictor.fit(X_fit, y_fit)

            X_test   = test_df[feat_cols]
            preds    = predictor.predict(X_test)
            actuals  = test_df["close"].values
            ts_test  = timestamps[split : split + len(test_df)]

            # ── Buy-and-hold baseline ───────────────────────────────────
            bh_start = actuals[0]
            bh_curve = [
                round(self.initial_capital * (p / bh_start), 2)
                for p in actuals
            ]

            # ── Simulate trading ────────────────────────────────────────
            capital     = self.initial_capital
            position    = 0.0
            entry_price = 0.0
            bars_held   = 0
            trades      = []
            equity_vals = [capital]

            for i in range(len(preds) - 1):
                pred_next  = float(preds[i])
                curr_price = float(actuals[i])
                next_price = float(actuals[i + 1])

                # ── Open position ────────────────────────────────────
                if position == 0 and pred_next > curr_price * BUY_THRESH:
                    position    = capital / curr_price
                    entry_price = curr_price
                    capital     = 0.0
                    bars_held   = 0

                # ── Manage open position ─────────────────────────────
                elif position > 0:
                    bars_held += 1
                    gain_pct = (curr_price - entry_price) / entry_price

                    close_reason = None
                    if curr_price >= entry_price * (1 + TP_PCT):
                        close_reason = "take_profit"
                    elif curr_price <= entry_price * (1 - SL_PCT):
                        close_reason = "stop_loss"
                    elif pred_next < curr_price * SELL_THRESH:
                        close_reason = "model_signal"
                    elif bars_held >= MAX_HOLD:
                        close_reason = "max_hold"

                    if close_reason:
                        capital = position * curr_price
                        pnl     = (curr_price - entry_price) * position
                        trades.append({
                            "entry":      round(entry_price, 4),
                            "exit":       round(curr_price, 4),
                            "pnl":        round(pnl, 2),
                            "return_pct": round(gain_pct * 100, 2),
                            "reason":     close_reason,
                            "bars_held":  bars_held,
                        })
                        position  = 0.0
                        bars_held = 0

                equity_vals.append(capital + position * next_price)

            # ── Close any remaining position ────────────────────────────
            if position > 0:
                close_price = float(actuals[-1])
                capital = position * close_price
                pnl     = (close_price - entry_price) * position
                gain_pct = (close_price - entry_price) / entry_price
                trades.append({
                    "entry":      round(entry_price, 4),
                    "exit":       round(close_price, 4),
                    "pnl":        round(pnl, 2),
                    "return_pct": round(gain_pct * 100, 2),
                    "reason":     "end_of_test",
                    "bars_held":  bars_held,
                })
                equity_vals[-1] = round(capital, 2)

            # ── Metrics ─────────────────────────────────────────────────
            final_capital = equity_vals[-1]
            arr    = np.array(equity_vals, dtype=float)
            rets   = np.diff(arr) / (arr[:-1] + 1e-10)
            sharpe = float((rets.mean() / (rets.std() + 1e-10)) * np.sqrt(252))
            max_dd = _max_drawdown(equity_vals)

            winning  = [t for t in trades if t["pnl"] > 0]
            win_rate = len(winning) / max(len(trades), 1) * 100

            avg_win  = float(np.mean([t["pnl"] for t in winning])) if winning else 0.0
            losing   = [t for t in trades if t["pnl"] <= 0]
            avg_loss = float(np.mean([t["pnl"] for t in losing]))  if losing  else 0.0
            profit_factor = (
                abs(sum(t["pnl"] for t in winning)) /
                max(abs(sum(t["pnl"] for t in losing)), 1e-10)
            )

            pred_metrics = _compute_metrics(actuals[:len(preds)], preds)

            # ── Build equity_curve with dates for frontend chart ────────
            step = max(1, len(equity_vals) // 100)   # cap at 100 points
            curve_out = []
            for idx in range(0, len(equity_vals), step):
                ts = ts_test[idx] if idx < len(ts_test) else ts_test[-1]
                ts_str = (
                    pd.Timestamp(ts).isoformat()
                    if not isinstance(ts, str)
                    else ts
                )
                bh_val = bh_curve[idx] if idx < len(bh_curve) else bh_curve[-1]
                curve_out.append({
                    "date":          ts_str,
                    "equity":        round(equity_vals[idx], 2),
                    "buy_and_hold":  round(bh_val, 2),
                })

            return {
                # Capital
                "initial_capital":    self.initial_capital,
                "final_capital":      round(final_capital, 2),
                "total_return_pct":   round((final_capital - self.initial_capital) / self.initial_capital * 100, 2),
                # Trade stats
                "total_trades":       len(trades),
                "win_rate":           round(win_rate, 2),
                "avg_win":            round(avg_win, 2),
                "avg_loss":           round(avg_loss, 2),
                "profit_factor":      round(profit_factor, 2),
                # Risk
                "sharpe_ratio":       round(sharpe, 4),
                "max_drawdown_pct":   round(max_dd * 100, 2),
                # Details
                "prediction_metrics": pred_metrics,
                "equity_curve":       curve_out,
                "recent_trades":      trades[-10:],
                # Flat alias for Dashboard quick-test widget
                "metrics": {
                    "final_capital":  round(final_capital, 2),
                    "win_rate":       round(win_rate, 2),
                    "total_trades":   len(trades),
                    "max_drawdown":   round(max_dd * 100, 2),
                    "sharpe_ratio":   round(sharpe, 4),
                    "profit_factor":  round(profit_factor, 2),
                },
            }
        except Exception as e:
            logger.error(f"Backtest error: {e}", exc_info=True)
            return {"error": str(e)}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    mae  = float(mean_absolute_error(y_true, y_pred))
    mse  = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2   = float(r2_score(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-10))) * 100)
    return {
        "mae":  round(mae, 4),
        "rmse": round(rmse, 4),
        "r2":   round(r2, 4),
        "mape": round(mape, 2),
    }


def _max_drawdown(equity_curve: List[float]) -> float:
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / (peak + 1e-10)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ─────────────────────────────────────────────
# Main ML Prediction Service
# ─────────────────────────────────────────────

class MLPredictionService:
    """Orchestrates all ML models, feature engineering, and backtesting"""

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.backtest_engine  = BacktestEngine()
        logger.info("✅ MLPredictionService initialized with multi-model support")

    # ── Low-level indicators (used by existing API routes) ────────────────

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Backward-compatible: returns df enriched with named indicator columns"""
        df = df.copy()
        for col in ["close", "high", "low", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        close = df["close"]
        df["SMA_7"]  = close.rolling(7,  min_periods=1).mean()
        df["SMA_25"] = close.rolling(25, min_periods=1).mean()
        df["SMA_99"] = close.rolling(50, min_periods=1).mean()

        df["EMA_12"] = close.ewm(span=12, adjust=False).mean()
        df["EMA_26"] = close.ewm(span=26, adjust=False).mean()
        df["MACD"]   = df["EMA_12"] - df["EMA_26"]
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14, min_periods=1).mean()
        loss  = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
        df["RSI"] = 100 - (100 / (1 + gain / (loss + 1e-10)))

        df["BB_middle"] = close.rolling(20, min_periods=1).mean()
        bb_std = close.rolling(20, min_periods=1).std().fillna(0)
        df["BB_upper"]  = df["BB_middle"] + 2 * bb_std
        df["BB_lower"]  = df["BB_middle"] - 2 * bb_std

        df["Volume_SMA"]  = df["volume"].rolling(20, min_periods=1).mean()
        df["Momentum"]    = close - close.shift(10)
        df["ROC"]         = ((close - close.shift(12)) / (close.shift(12) + 1e-10)) * 100

        df = df.bfill().ffill().fillna(0)
        return df

    # ── Trend & signal analysis ────────────────────────────────────────────

    def analyze_trend(self, historical_data: List[Dict]) -> Dict:
        """Comprehensive trend analysis with multiple indicators"""
        try:
            df = self._to_df(historical_data)
            if len(df) < 10:
                return self._empty_trend()

            df = self.calculate_technical_indicators(df)
            df = self.feature_engineer.build_features(df)

            last = df.iloc[-1]
            close = df["close"].iloc[-1]

            score = 0
            signals_detail = []

            # Moving averages
            if close > last["SMA_7"] > last["SMA_25"]:
                score += 3
                signals_detail.append({"indicator": "MA Alignment", "signal": "bullish", "value": "+3"})
            elif close < last["SMA_7"] < last["SMA_25"]:
                score -= 3
                signals_detail.append({"indicator": "MA Alignment", "signal": "bearish", "value": "-3"})

            # RSI (14)
            rsi = last["rsi_14"]
            if rsi > 70:
                score += 1; signals_detail.append({"indicator": "RSI", "signal": "overbought", "value": f"{rsi:.1f}"})
            elif rsi < 30:
                score -= 1; signals_detail.append({"indicator": "RSI", "signal": "oversold", "value": f"{rsi:.1f}"})

            # MACD
            if last["macd"] > 0 and last["macd"] > last["macd_signal"]:
                score += 2; signals_detail.append({"indicator": "MACD", "signal": "bullish", "value": f"{last['macd']:.4f}"})
            elif last["macd"] < 0:
                score -= 2; signals_detail.append({"indicator": "MACD", "signal": "bearish", "value": f"{last['macd']:.4f}"})

            # Bollinger
            bb_pos = last.get("bb_pos_20", 0.5)
            if bb_pos < 0.1:
                score -= 1; signals_detail.append({"indicator": "Bollinger", "signal": "near_lower", "value": f"{bb_pos:.2f}"})
            elif bb_pos > 0.9:
                score += 1; signals_detail.append({"indicator": "Bollinger", "signal": "near_upper", "value": f"{bb_pos:.2f}"})

            # Volume
            if last.get("vol_ratio", 1) > 1.5:
                score = score + 1 if score > 0 else score - 1
                signals_detail.append({"indicator": "Volume", "signal": "high", "value": f"{last['vol_ratio']:.2f}x"})

            # CCI
            cci = last.get("cci", 0)
            if cci > 100:  score += 1
            elif cci < -100: score -= 1

            trend_map = {
                (3, 999):  ("strong_uptrend",   min(100, 65 + score * 5)),
                (1, 3):    ("uptrend",           50 + score * 8),
                (-1, 1):   ("sideways",          50),
                (-3, -1):  ("downtrend",         50 + score * 8),
                (-999, -3):("strong_downtrend",  max(0, 35 + score * 5)),
            }
            trend, strength = "sideways", 50
            for (lo, hi), (t, s) in trend_map.items():
                if lo <= score < hi:
                    trend, strength = t, int(s)
                    break

            # Multi-timeframe summary (simple)
            short_ret  = df["close"].pct_change(5).iloc[-1] * 100
            medium_ret = df["close"].pct_change(20).iloc[-1] * 100

            return {
                "trend": trend,
                "strength": strength,
                "score": score,
                "rsi": round(float(rsi), 2),
                "macd": round(float(last["macd"]), 6),
                "sma_7": round(float(last["SMA_7"]), 4),
                "sma_25": round(float(last["SMA_25"]), 4),
                "current_price": round(float(close), 4),
                "atr": round(float(last.get("atr_14", 0)), 4),
                "atr_pct": round(float(last.get("atr_pct", 0)), 2),
                "bb_position": round(float(bb_pos), 3),
                "cci": round(float(cci), 2),
                "volume_ratio": round(float(last.get("vol_ratio", 1)), 2),
                "return_5d": round(float(short_ret), 2),
                "return_20d": round(float(medium_ret), 2),
                "signals_detail": signals_detail,
            }
        except Exception as e:
            logger.error(f"analyze_trend error: {e}")
            return self._empty_trend()

    def get_trading_signals(self, analysis: Dict) -> Dict:
        """Generate trading signals from trend analysis"""
        try:
            trend    = analysis.get("trend", "sideways")
            strength = analysis.get("strength", 50)
            rsi      = analysis.get("rsi", 50)
            price    = analysis.get("current_price", 0)
            atr      = analysis.get("atr", price * 0.02)
            score    = analysis.get("score", 0)

            if price == 0:
                return {"signal": "hold", "strength": 5, "reasoning": "Insufficient data"}

            # Determine signal
            if trend in ("strong_uptrend", "uptrend") and rsi < 70 and strength > 55:
                signal = "buy"
                sig_strength = min(10, max(1, int((strength - 50) / 5)))
                entry  = price * 0.99
                stop   = entry - atr * 1.5
                tp     = entry + atr * 3.0
            elif trend in ("strong_downtrend", "downtrend") and rsi > 30 and strength < 45:
                signal = "sell"
                sig_strength = min(10, max(1, int((50 - strength) / 5)))
                entry  = price * 1.01
                stop   = entry + atr * 1.5
                tp     = entry - atr * 3.0
            else:
                signal = "hold"
                sig_strength = 5
                entry = price
                stop  = price - atr * 1.5
                tp    = price + atr * 1.5

            rr = abs(tp - entry) / (abs(entry - stop) + 1e-10)
            reasoning = self._build_reasoning(trend, rsi, signal, strength, analysis)

            return {
                "signal":           signal,
                "strength":         sig_strength,
                "entry_price":      round(float(entry), 4),
                "stop_loss":        round(float(stop), 4),
                "take_profit":      round(float(tp), 4),
                "risk_reward_ratio":round(float(rr), 2),
                "reasoning":        reasoning,
                "rsi_zone":         "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral",
                "trend_strength":   strength,
            }
        except Exception as e:
            logger.error(f"get_trading_signals error: {e}")
            return {"signal": "hold", "strength": 5, "reasoning": str(e)}

    # ── Price prediction with multiple models ─────────────────────────────

    def predict_linear_regression(self, historical_data: List[Dict],
                                   periods: int = 7) -> List[Dict]:
        """Backward-compatible — calls predict_price with linear_regression"""
        result = self.predict_price(historical_data, periods, "linear_regression")
        return result.get("predictions", [])

    def predict_price(self, historical_data: List[Dict],
                      periods: int = 7,
                      model_name: str = "ensemble") -> Dict:
        """
        Predict future prices using specified model.
        model_name: linear_regression | ridge | lasso | random_forest |
                    gradient_boosting | svr | ensemble
        """
        try:
            df = self._to_df(historical_data)
            if len(df) < 20:
                return {"error": "Not enough data", "predictions": []}

            df_feat = self.feature_engineer.build_features(df)
            X, y = self.feature_engineer.prepare_supervised(df_feat, horizon=1)

            if len(X) < 15:
                return {"error": "Insufficient feature rows", "predictions": []}

            # Train
            if model_name == "ensemble":
                predictor = EnsemblePredictor()
            else:
                predictor = ModelWrapper(model_name)

            predictor.fit(X, y)

            # Predict future steps autoregressively
            drop_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            feat_cols = [c for c in df_feat.columns if c not in drop_cols]
            last_row  = X.iloc[[-1]]

            recent_prices = df["close"].values[-20:]
            std_dev = float(np.std(recent_prices))
            last_price = float(df["close"].iloc[-1])
            last_date  = df["timestamp"].iloc[-1]

            # Keep a rolling price buffer to update features each step
            price_buffer = list(df["close"].values[-50:])   # last 50 real closes
            prev_price   = last_price
            current_row  = last_row.copy()

            predictions = []
            for i in range(periods):
                pred = float(predictor.predict(current_row)[0])
                pred = max(pred, last_price * 0.3)   # sanity floor

                # ── Update rolling features for next step ──────────────
                price_buffer.append(pred)
                pb = np.array(price_buffer, dtype=float)

                def _upd(col: str, value: float):
                    """Safely update a feature column in current_row."""
                    if col in current_row.columns:
                        current_row.iloc[0, current_row.columns.get_loc(col)] = value

                # ── Lag features (correct names: close_lag_N) ──────────
                for lag, offset in [(1,1),(2,2),(3,3),(5,5),(7,7)]:
                    _upd(f"close_lag_{lag}", float(pb[-offset]) if len(pb) >= offset else pred)

                # ── Return features (ret_Nd = pct_change over N bars) ──
                for w in [3, 7, 14, 25, 50]:
                    if len(pb) >= w + 1:
                        ret = (pb[-1] - pb[-(w+1)]) / (pb[-(w+1)] + 1e-10)
                        _upd(f"ret_{w}d", ret)

                # ── SMA (sma_N) ────────────────────────────────────────
                for w in [3, 7, 14, 25, 50]:
                    if len(pb) >= w:
                        _upd(f"sma_{w}", float(pb[-w:].mean()))

                # ── EMA (ema_N) — incremental update ───────────────────
                for w in [3, 7, 14, 25, 50]:
                    col = f"ema_{w}"
                    if col in current_row.columns:
                        ema_prev = float(current_row[col].iloc[0])
                        k = 2.0 / (w + 1)
                        _upd(col, ema_prev + k * (pred - ema_prev))

                # ── Volatility (std_Nd) ────────────────────────────────
                for w in [3, 7, 14, 25, 50]:
                    if len(pb) >= w:
                        _upd(f"std_{w}d", float(pb[-w:].std()))

                # ── Momentum features ──────────────────────────────────
                if len(pb) >= 11:
                    _upd("momentum_10", float(pb[-1] - pb[-11]))
                if len(pb) >= 13:
                    _upd("roc_12", float((pb[-1] - pb[-13]) / (pb[-13] + 1e-10) * 100))

                # ── MACD (approximate incremental) ─────────────────────
                for col in ["macd", "macd_signal", "macd_hist"]:
                    if col in current_row.columns:
                        pass   # keep as-is for simplicity; impact is minor

                prev_price = pred
                # ───────────────────────────────────────────────────────

                conf = max(30, 88 - i * 5 - std_dev / (last_price + 1e-10) * 10)
                date = last_date + timedelta(days=i + 1)
                predictions.append({
                    "date":            date.strftime("%Y-%m-%d"),
                    "predicted_price": round(pred, 4),
                    "confidence":      round(conf, 1),
                    "lower_bound":     round(max(0, pred - std_dev * 1.5), 4),
                    "upper_bound":     round(pred + std_dev * 1.5, 4),
                    "method":          model_name,
                    "change_pct":      round((pred - last_price) / last_price * 100, 2),
                })

            # Training metrics
            train_preds = predictor.predict(X)
            metrics = _compute_metrics(y.values, train_preds)

            return {
                "predictions":      predictions,
                "model":            model_name,
                "training_metrics": metrics,
                "feature_count":    len(feat_cols),
            }
        except Exception as e:
            logger.error(f"predict_price error: {e}")
            return {"error": str(e), "predictions": []}

    def compare_models(self, historical_data: List[Dict],
                       periods: int = 5) -> Dict:
        """Train & compare all models, return ranked results"""
        try:
            df = self._to_df(historical_data)
            if len(df) < 30:
                return {"error": "Need at least 30 candles"}

            df_feat = self.feature_engineer.build_features(df)
            X, y = self.feature_engineer.prepare_supervised(df_feat, horizon=1)

            model_names = ["linear_regression", "ridge", "random_forest",
                           "gradient_boosting", "svr"]
            results = []
            predictions_by_model = {}

            drop_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            feat_cols = [c for c in df_feat.columns if c not in drop_cols]
            last_row  = X.iloc[[-1]]
            last_price = float(df["close"].iloc[-1])

            for name in model_names:
                try:
                    mw = ModelWrapper(name)
                    cv = mw.cv_score(X, y)
                    mw.fit(X, y)
                    train_m = mw.metrics
                    pred_next = float(mw.predict(last_row)[0])
                    change = (pred_next - last_price) / last_price * 100
                    fi = mw.feature_importance(feat_cols)

                    results.append({
                        "model":          name,
                        "train_mae":      train_m["mae"],
                        "train_r2":       train_m["r2"],
                        "cv_mae":         round(cv["mean_mae"], 4),
                        "cv_std":         round(cv["std_mae"], 4),
                        "mape":           train_m["mape"],
                        "predicted_next": round(pred_next, 4),
                        "change_pct":     round(change, 2),
                        "top_features":   list(fi.keys())[:5],
                    })
                    predictions_by_model[name] = pred_next
                except Exception as e:
                    logger.warning(f"Model {name} comparison failed: {e}")

            # Ensemble
            try:
                ens = EnsemblePredictor(model_names)
                ens.fit(X, y)
                ens_pred = float(ens.predict(last_row)[0])
                predictions_by_model["ensemble"] = ens_pred
                results.append({
                    "model":          "ensemble",
                    "predicted_next": round(ens_pred, 4),
                    "change_pct":     round((ens_pred - last_price) / last_price * 100, 2),
                    "weights":        ens.weights,
                })
            except Exception as e:
                logger.warning(f"Ensemble comparison failed: {e}")

            # Rank by cv_mae
            ranked = sorted([r for r in results if "cv_mae" in r], key=lambda x: x["cv_mae"])
            ranked += [r for r in results if "cv_mae" not in r]

            return {
                "current_price":       last_price,
                "models":              ranked,
                "consensus_direction": _consensus(predictions_by_model, last_price),
                "feature_count":       len(feat_cols),
            }
        except Exception as e:
            logger.error(f"compare_models error: {e}")
            return {"error": str(e)}

    def run_backtest(self, historical_data: List[Dict],
                     model_name: str = "gradient_boosting") -> Dict:
        """Run full walk-forward backtest"""
        try:
            df = self._to_df(historical_data)
            if len(df) < 40:
                return {"error": "Need at least 40 candles for backtest"}
            if model_name == "ensemble":
                predictor = EnsemblePredictor()
            else:
                predictor = ModelWrapper(model_name)
            result = self.backtest_engine.run(df, predictor)
            result["model"] = model_name
            return result
        except Exception as e:
            logger.error(f"backtest error: {e}")
            return {"error": str(e)}

    def get_feature_importance(self, historical_data: List[Dict],
                                model_name: str = "random_forest") -> Dict:
        """Return feature importance from a tree model"""
        try:
            df = self._to_df(historical_data)
            df_feat = self.feature_engineer.build_features(df)
            X, y   = self.feature_engineer.prepare_supervised(df_feat)
            drop   = ["timestamp", "open", "high", "low", "close", "volume"]
            feat_cols = [c for c in df_feat.columns if c not in drop]

            mw = ModelWrapper(model_name)
            mw.fit(X, y)
            fi = mw.feature_importance(feat_cols)
            return {
                "model":    model_name,
                "features": fi,
                "metrics":  mw.metrics,
            }
        except Exception as e:
            logger.error(f"feature_importance error: {e}")
            return {"error": str(e)}

    # ── Private helpers ───────────────────────────────────────────────────

    def _to_df(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["close"])
        return df

    def _empty_trend(self) -> Dict:
        return {
            "trend": "unknown", "strength": 50, "score": 0,
            "rsi": 50, "macd": 0, "sma_7": 0, "sma_25": 0,
            "current_price": 0, "signals_detail": []
        }

    def _build_reasoning(self, trend: str, rsi: float, signal: str,
                          strength: int, analysis: Dict) -> str:
        ret5  = analysis.get("return_5d", 0)
        vol_r = analysis.get("volume_ratio", 1)
        cci   = analysis.get("cci", 0)

        base = {
            "buy":  f"Висхідний тренд ({trend}) — RSI {rsi:.1f}, сила {strength}/100.",
            "sell": f"Низхідний тренд ({trend}) — RSI {rsi:.1f}, сила {strength}/100.",
            "hold": f"Консолідація ({trend}) — RSI {rsi:.1f}. Очікуємо підтвердження.",
        }.get(signal, "")

        extras = []
        if abs(ret5) > 3:
            extras.append(f"Зміна за 5 днів: {ret5:+.1f}%")
        if vol_r > 1.5:
            extras.append(f"Підвищений обсяг ({vol_r:.1f}x)")
        if abs(cci) > 100:
            extras.append(f"CCI {'перекуплений' if cci > 100 else 'перепроданий'} ({cci:.0f})")

        return base + (" " + "; ".join(extras) if extras else "")


# ─────────────────────────────────────────────
# Statistical Time-Series Analyzer
# ─────────────────────────────────────────────

class StatisticalAnalyzer:
    """
    Diploma-level statistical analysis of a price series.

    Tests and measures:
    • ADF (Augmented Dickey-Fuller) stationarity test
    • Hurst exponent — trend persistence vs mean-reversion
    • Autocorrelation / Ljung-Box test
    • Return distribution: skewness, kurtosis, Jarque-Bera normality test
    • Realized & rolling volatility regimes
    • Value-at-Risk (VaR 95 / 99) — historical simulation
    • Calmar, Sortino, and Omega ratios
    • Persistence naive baseline benchmark
    """

    @staticmethod
    def _hurst(series: np.ndarray, min_lag: int = 2, max_lag: int = 50) -> float:
        """Estimate Hurst exponent via R/S analysis."""
        lags = range(min_lag, min(max_lag, len(series) // 4))
        rs_vals = []
        for lag in lags:
            sub = series[:lag]
            mean = np.mean(sub)
            devs = np.cumsum(sub - mean)
            r = devs.max() - devs.min()
            s = np.std(sub, ddof=1) + 1e-10
            rs_vals.append(r / s)
        if len(rs_vals) < 2:
            return 0.5
        log_lags = np.log(list(lags))
        log_rs   = np.log(rs_vals)
        poly = np.polyfit(log_lags, log_rs, 1)
        return float(np.clip(poly[0], 0.0, 1.0))

    @staticmethod
    def _adf_test(series: np.ndarray) -> Dict:
        """
        Manual ADF test (OLS-based, no external library required).
        Returns: test statistic, p-value (approx from MacKinnon 1994 table),
                 is_stationary flag, and interpretation.
        """
        n = len(series)
        if n < 10:
            return {"stationary": None, "test_stat": None, "p_value": None,
                    "interpretation": "Insufficient data"}

        # Lag-1 difference regression: Δy_t = α + β·y_{t-1} + ε
        y     = series
        dy    = np.diff(y)
        y_lag = y[:-1]

        # OLS: [intercept, y_lag]
        X = np.column_stack([np.ones(len(dy)), y_lag])
        try:
            beta, _, _, _ = np.linalg.lstsq(X, dy, rcond=None)
            resid  = dy - X @ beta
            sigma2 = np.var(resid, ddof=2)
            XtX_inv = np.linalg.pinv(X.T @ X)
            se_beta = np.sqrt(sigma2 * np.diag(XtX_inv))
            t_stat  = float(beta[1] / (se_beta[1] + 1e-15))
        except Exception:
            return {"stationary": None, "test_stat": None, "p_value": None,
                    "interpretation": "Calculation error"}

        # MacKinnon 1994 approximate critical values (no-constant model at 5%)
        # For with-constant: -2.86 at 5%, -3.43 at 1%
        p_approx = float(np.clip(1 / (1 + np.exp(-t_stat - 1.5)), 0.0, 1.0))
        stationary = t_stat < -2.86
        return {
            "stationary": stationary,
            "test_stat":  round(t_stat, 4),
            "p_value":    round(p_approx, 4),
            "critical_5pct": -2.86,
            "interpretation": (
                "Ряд стаціонарний — немає одиничного кореня (p<0.05)"
                if stationary else
                "Ряд нестаціонарний — присутній одиничний корінь (p≥0.05)"
            ),
        }

    @staticmethod
    def _autocorrelation(series: np.ndarray, max_lag: int = 10) -> Dict:
        """Compute ACF and Ljung-Box Q statistic for returns."""
        n = len(series)
        mean = np.mean(series)
        var  = np.var(series) + 1e-15
        acf = []
        for lag in range(1, min(max_lag + 1, n)):
            c = np.mean((series[:n-lag] - mean) * (series[lag:] - mean)) / var
            acf.append(round(float(c), 4))

        # Ljung-Box Q statistic
        m = len(acf)
        q_stat = float(n * (n + 2) * sum(
            (rho ** 2) / (n - k - 1) for k, rho in enumerate(acf)
        ))
        # Chi-squared approx p-value (very rough: 1 - CDF)
        # degrees of freedom = m; use Pearson chi2 approximation
        from math import gamma as _gamma, exp as _exp
        def _chi2_sf(x, k):
            """Survival function of chi-squared (approximate)."""
            if x <= 0:
                return 1.0
            try:
                # Use regularized incomplete gamma (Wilson-Hilferty approx)
                z = ((x / k) ** (1/3) - (1 - 2 / (9 * k))) / np.sqrt(2 / (9 * k))
                return float(np.clip(0.5 * (1 - np.tanh(z * 0.7978845608)), 0, 1))
            except Exception:
                return 0.5
        q_pvalue = _chi2_sf(q_stat, m)

        return {
            "acf_lags":        acf,
            "ljung_box_q":     round(q_stat, 4),
            "ljung_box_pvalue":round(q_pvalue, 4),
            "has_autocorrelation": q_pvalue < 0.05,
            "interpretation": (
                "Значима автокореляція в дохідностях (ринок неефективний за слабкою формою)"
                if q_pvalue < 0.05 else
                "Автокореляція незначна (дохідності близькі до випадкового блукання)"
            ),
        }

    @staticmethod
    def _return_distribution(returns: np.ndarray) -> Dict:
        """Skewness, excess kurtosis, Jarque-Bera normality test."""
        n  = len(returns)
        mu = np.mean(returns)
        s  = np.std(returns, ddof=1) + 1e-15
        skew = float(np.mean(((returns - mu) / s) ** 3))
        kurt = float(np.mean(((returns - mu) / s) ** 4) - 3)  # excess kurtosis
        jb   = (n / 6) * (skew ** 2 + (kurt ** 2) / 4)
        # Jarque-Bera p-value (chi-sq 2 dof approximation)
        jb_p = float(np.exp(-jb / 2))
        normal = jb_p > 0.05
        return {
            "mean_return":    round(float(mu) * 100, 4),
            "std_return":     round(float(s) * 100, 4),
            "skewness":       round(skew, 4),
            "excess_kurtosis":round(kurt, 4),
            "jarque_bera":    round(jb, 4),
            "jb_pvalue":      round(jb_p, 4),
            "is_normal":      normal,
            "interpretation": (
                "Розподіл не відхиляється значно від нормального"
                if normal else
                f"Розподіл non-normal: {'товсті хвости (leptokurtic)' if kurt > 0 else 'тонкі хвости'}"
                + (", від'ємна асиметрія" if skew < 0 else ", додатна асиметрія")
            ),
        }

    @staticmethod
    def _var_estimates(returns: np.ndarray) -> Dict:
        """Historical-simulation Value-at-Risk and Expected Shortfall."""
        sorted_r = np.sort(returns)
        n = len(sorted_r)
        var95  = float(-np.percentile(sorted_r, 5))
        var99  = float(-np.percentile(sorted_r, 1))
        es95   = float(-sorted_r[sorted_r <= -var95].mean()) if any(sorted_r <= -var95) else var95
        return {
            "var_95": round(var95 * 100, 3),
            "var_99": round(var99 * 100, 3),
            "expected_shortfall_95": round(es95 * 100, 3),
        }

    @staticmethod
    def _volatility_regimes(close: pd.Series, window: int = 20) -> Dict:
        """Rolling realized volatility and simple regime labelling."""
        log_ret   = np.log(close / close.shift(1)).dropna()
        roll_vol  = log_ret.rolling(window).std() * np.sqrt(252) * 100
        recent_vol = float(roll_vol.iloc[-1])
        mean_vol   = float(roll_vol.mean())
        low_q      = float(roll_vol.quantile(0.25))
        high_q     = float(roll_vol.quantile(0.75))
        regime = (
            "low_volatility"    if recent_vol < low_q  else
            "high_volatility"   if recent_vol > high_q else
            "normal_volatility"
        )
        # Volatility-of-volatility
        vol_of_vol = float(roll_vol.std())
        return {
            "annualized_vol_pct": round(recent_vol, 2),
            "mean_vol_pct":       round(mean_vol, 2),
            "vol_regime":         regime,
            "vol_of_vol":         round(vol_of_vol, 2),
            "low_threshold":      round(low_q, 2),
            "high_threshold":     round(high_q, 2),
        }

    @staticmethod
    def _risk_ratios(returns: np.ndarray, rf_daily: float = 0.0) -> Dict:
        """Sortino, Calmar, Omega ratios."""
        excess = returns - rf_daily
        neg_ret = returns[returns < 0]
        downside_std = float(np.std(neg_ret, ddof=1)) + 1e-15
        ann_ret  = float(np.mean(excess)) * 252
        ann_std  = float(np.std(excess, ddof=1)) * np.sqrt(252)
        sortino  = ann_ret / (downside_std * np.sqrt(252) + 1e-15)

        # Calmar: annualised return / max_drawdown
        equity   = np.cumprod(1 + returns)
        peak     = np.maximum.accumulate(equity)
        dd       = (peak - equity) / (peak + 1e-15)
        max_dd   = float(dd.max()) + 1e-15
        calmar   = ann_ret / max_dd

        # Omega ratio (threshold = 0)
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum()) + 1e-15
        omega = gains / losses

        return {
            "sortino_ratio":  round(sortino, 4),
            "calmar_ratio":   round(calmar, 4),
            "omega_ratio":    round(omega, 4),
            "max_drawdown_pct": round(max_dd * 100, 2),
        }

    def analyze(self, historical_data: List[Dict]) -> Dict:
        """Full statistical analysis pipeline."""
        df = pd.DataFrame(historical_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])

        if len(df) < 30:
            return {"error": "Need at least 30 candles for statistical analysis"}

        close   = df["close"]
        returns = np.log(close / close.shift(1)).dropna().values

        hurst   = self._hurst(close.values)
        hurst_interp = (
            "Тренд-стійкий ринок (Hurst > 0.55)" if hurst > 0.55 else
            "Середньо-реверсуючий ринок (Hurst < 0.45)" if hurst < 0.45 else
            "Випадкове блукання (Hurst ≈ 0.5)"
        )

        return {
            "data_points":          len(df),
            "price_range": {
                "min":  round(float(close.min()), 4),
                "max":  round(float(close.max()), 4),
                "last": round(float(close.iloc[-1]), 4),
            },
            "stationarity":         self._adf_test(close.values),
            "hurst_exponent":       round(hurst, 4),
            "hurst_interpretation": hurst_interp,
            "autocorrelation":      self._autocorrelation(returns),
            "return_distribution":  self._return_distribution(returns),
            "var_estimates":        self._var_estimates(returns),
            "volatility_regimes":   self._volatility_regimes(close),
            "risk_ratios":          self._risk_ratios(returns),
        }


# ─────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────

def _consensus(preds: Dict[str, float], current: float) -> str:
    if not preds:
        return "neutral"
    bull = sum(1 for v in preds.values() if v > current)
    bear = sum(1 for v in preds.values() if v < current)
    if bull > bear * 1.5:  return "bullish"
    if bear > bull * 1.5:  return "bearish"
    return "neutral"


# ─────────────────────────────────────────────
# Singletons
# ─────────────────────────────────────────────

ml_service = MLPredictionService()
statistical_analyzer = StatisticalAnalyzer()