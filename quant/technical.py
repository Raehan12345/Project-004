# quant/technical.py

import yfinance as yf
import pandas as pd
import numpy as np

def get_technical_signals(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 1 year of daily price data
        hist = stock.history(period="1y")
        
        # require sufficient data for a 200-day moving average
        if len(hist) < 200:
            return {"trend": "Insufficient Data", "rsi": 50, "tech_score": 0}
        
        close = hist['Close']
        current_price = close.iloc[-1]
        
        # moving averages
        ma50 = close.rolling(window=50).mean().iloc[-1]
        ma200 = close.rolling(window=200).mean().iloc[-1]
        
        # 14 day RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # fix division by zero for RSI
        rs = np.where(loss == 0, 100, gain / loss)
        rsi_series = 100 - (100 / (1 + rs))
        rsi = rsi_series[-1]
        
        # regime classification
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
            
        # mean reversion overlay -RSI
        if rsi < 30:
            tech_score += 1  # oversold bonus
        elif rsi > 70:
            tech_score -= 1  # overbought penalty
            
        return {
            "trend": trend,
            "rsi": round(rsi, 2),
            "tech_score": tech_score
        }
        
    except Exception as e:
        print(f"Technical data error for {ticker}: {e}")
        return {"trend": "Error", "rsi": 50, "tech_score": 0}