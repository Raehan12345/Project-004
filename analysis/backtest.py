# analysis/backtest.py

import pandas as pd
import yfinance as yf

def get_monthly_returns(tickers, start, end):
    prices = yf.download(
        tickers,
        start=start,
        end=end,
        interval="1mo",
        auto_adjust=True,
        progress=False,
    )["Close"]

    returns = prices.pct_change().dropna()
    return returns


def run_backtest(df, start="2021-01-01", end="2024-01-01"):
    tickers = df["Ticker"].tolist()

    monthly_returns = get_monthly_returns(tickers, start, end)

    # align columns
    monthly_returns = monthly_returns[tickers]

    portfolio_returns = []

    for date, row in monthly_returns.iterrows():
        weights = df.set_index("Ticker")["TargetWeight"]
        port_ret = (row * weights).sum()
        portfolio_returns.append(port_ret)

    return pd.Series(portfolio_returns, index=monthly_returns.index)
