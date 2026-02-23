# analysis/volatility.py
import yfinance as yf
import numpy as np

def get_volatility_multiplier(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="3mo")
        if len(hist) < 30:
            return 1.0
            
        # Fixed Pandas warning by explicitly declaring fill_method
        returns = hist['Close'].pct_change(fill_method=None).dropna()
        daily_vol = returns.rolling(window=30).std().iloc[-1]
        ann_vol = daily_vol * np.sqrt(252)
        
        if ann_vol > 0.60:
            return 0.5
        elif ann_vol > 0.40:
            return 0.75
        return 1.0
        
    except Exception as e:
        print(f"Volatility data error for {ticker}: {e}")
        return 1.0