# quant/intraday_signals.py
import numpy as np
import yfinance as yf

def get_intraday_signal(quote_client, ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch 5 days of 15m data to capture volume and price
        hist = stock.history(period="5d", interval="15m")
        if hist.empty: return "NO_DATA"

        current_price = hist['Close'].iloc[-1]
        prev_close = stock.info.get('previousClose', current_price)
        
        # Volatility Calculation
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() 
        change_pct = (current_price - prev_close) / prev_close
        
        # 1. Mean Reversion Trigger (The Dip Buy)
        dynamic_dip_threshold = -2 * volatility 
        
        # 2. VWAP & Momentum Trigger (The Breakout Buy)
        # Calculate intraday VWAP for the most recent day
        latest_day = hist.index[-1].date()
        today_data = hist[hist.index.date == latest_day].copy()
        
        if not today_data.empty:
            today_data['Typical_Price'] = (today_data['High'] + today_data['Low'] + today_data['Close']) / 3
            today_data['Volume_Price'] = today_data['Typical_Price'] * today_data['Volume']
            vwap = today_data['Volume_Price'].sum() / today_data['Volume'].sum() if today_data['Volume'].sum() > 0 else current_price
            
            recent_volume = today_data['Volume'].iloc[-1]
            avg_volume = today_data['Volume'].mean()
            
            # Breakout logic: Price > VWAP and Volume is surging (1.5x average)
            is_breakout = (current_price > vwap) and (recent_volume > (avg_volume * 1.5))
        else:
            is_breakout = False

        print(f"[{ticker}] Px: {current_price:.2f} | Chg: {change_pct:.2%} | DipReq: {dynamic_dip_threshold:.2%} | Breakout: {is_breakout}")

        if change_pct < dynamic_dip_threshold:
            return "BUY_DIP"
        elif is_breakout and change_pct > 0:
            return "BUY_MOMENTUM"
            
        return "MONITOR"

    except Exception as e:
        print(f"Signal error for {ticker}: {e}")
        return "ERROR"