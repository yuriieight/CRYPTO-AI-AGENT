"""Backtesting engine – ML strategy vs Buy&Hold."""
import numpy as np

def run_backtest(prices: list, signals: list, initial_capital: float = 10000.0) -> dict:
    capital   = initial_capital
    position  = 0.0
    trades    = 0
    peak      = initial_capital
    max_dd    = 0.0

    for i, (price, signal) in enumerate(zip(prices, signals)):
        if signal == 1 and position == 0:
            position = capital / price
            capital  = 0.0
            trades  += 1
        elif signal == -1 and position > 0:
            capital  = position * price
            position = 0.0
            trades  += 1
        portfolio_val = capital + position * price
        if portfolio_val > peak:
            peak = portfolio_val
        dd = (peak - portfolio_val) / peak
        if dd > max_dd:
            max_dd = dd

    final = capital + position * prices[-1]
    total_return = (final - initial_capital) / initial_capital * 100
    bh_return    = (prices[-1] - prices[0])  / prices[0] * 100

    returns = np.diff(prices) / prices[:-1]
    sharpe  = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0

    return {
        "total_return_pct": round(total_return, 2),
        "buy_hold_return_pct": round(bh_return, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "total_trades": trades,
    }
