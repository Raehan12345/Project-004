# quant/technical.py

import yfinance as yf
import pandas as pd
import numpy as np

def get_technical_signals(ticker):
    """
    Calculates institutional trend regimes and RSI overlays.
    Returns a dictionary with trend status and a quantitative technical score.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch 1 year of daily price data
        hist = stock.history(period="1y")
        
        # Require sufficient data for a 200-day moving average
        if len(hist) < 200:
            return {"trend": "Insufficient Data", "rsi": 50, "tech_score": 0}
        
        close = hist['Close']
        current_price = close.iloc[-1]
        
        # Calculate Moving Averages
        ma50 = close.rolling(window=50).mean().iloc[-1]
        ma200 = close.rolling(window=200).mean().iloc[-1]
        
        # Calculate 14-day RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Handle division by zero for RSI
        rs = np.where(loss == 0, 100, gain / loss)
        rsi_series = 100 - (100 / (1 + rs))
        rsi = rsi_series[-1]
        
        # Regime Classification
        tech_score = 0
        if current_price > ma50 and ma50 > ma200:
            trend = "Strong Bullish"
            tech_score += 2
        elif current_price < ma50 and ma50 < ma200:
            trend = "Strong Bearish"
            tech_score -= 2
        elif current_price > ma200:
            trend = "Weak Bullish"
            tech_score += 1
        else:
            trend = "Weak Bearish"
            tech_score -= 1
            
        # Mean Reversion Overlay (RSI)
        if rsi < 30:
            tech_score += 1  # Bonus for being oversold
        elif rsi > 70:
            tech_score -= 1  # Penalty for being overbought
            
        return {
            "trend": trend,
            "rsi": round(rsi, 2),
            "tech_score": tech_score
        }
        
    except Exception as e:
        print(f"Technical data error for {ticker}: {e}")
        return {"trend": "Error", "rsi": 50, "tech_score": 0}