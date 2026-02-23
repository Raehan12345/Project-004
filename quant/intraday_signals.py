# quant/intraday_signals.py
import numpy as np
import yfinance as yf

def get_intraday_signal(quote_client, ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch 5 days of 15m data to calculate 'normal' volatility
        hist = stock.history(period="5d", interval="15m")
        if hist.empty: return "NO_DATA"

        current_price = hist['Close'].iloc[-1]
        prev_close = stock.info.get('previousClose')
        
        # 1. Calculate Standard Deviation of returns
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() 
        
        # 2. Calculate the current move
        change_pct = (current_price - prev_close) / prev_close
        
        # 3. Dynamic Threshold: Only buy if the dip is > 2 standard deviations
        # This scales automatically: AAPL might trigger at -1.2%, TSLA at -3.5%
        dynamic_threshold = -2 * volatility 
        
        print(f"📊 {ticker} | Price: {current_price:.2f} | Change: {change_pct:.2%} | Threshold: {dynamic_threshold:.2%}")

        if change_pct < dynamic_threshold:
            return "BUY_NOW"
        return "MONITOR"

    except Exception as e:
        return "ERROR"