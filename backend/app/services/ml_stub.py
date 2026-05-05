"""ML prediction service – ensemble of sklearn models."""
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model  import Ridge, Lasso
from sklearn.svm           import SVR
import numpy as np

MODELS = {
    "random_forest":  RandomForestRegressor(n_estimators=100, random_state=42),
    "gradient_boost": GradientBoostingRegressor(n_estimators=100, random_state=42),
    "ridge":          Ridge(alpha=1.0),
    "lasso":          Lasso(alpha=0.1),
    "svr":            SVR(kernel="rbf"),
}

def train_and_predict(X_train, y_train, X_test, model_name="random_forest"):
    model = MODELS[model_name]
    model.fit(X_train, y_train)
    return model.predict(X_test)

# fix: handle edge case when price series has fewer than 26 data points
def safe_predict(prices: list, model_name: str = "random_forest") -> list:
    if len(prices) < 30:
        raise ValueError(f"Need at least 30 data points, got {len(prices)}")
    X = [[p] for p in prices[:-1]]
    y = prices[1:]
    return train_and_predict(X[:int(len(X)*0.8)], y[:int(len(y)*0.8)],
                             X[int(len(X)*0.8):], model_name).tolist()
