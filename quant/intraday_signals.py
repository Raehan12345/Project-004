# quant/intraday_signals.py
import numpy as np
import pandas as pd
import yfinance as yf

def get_intraday_signal(quote_client, ticker):
    try:
        raw_sym = ticker.split('.')[0]
        tiger_sym = raw_sym.zfill(5) if ".HK" in ticker else raw_sym
        
        try:
            bars = quote_client.get_bars([tiger_sym], period='15m', limit=200)
            if bars is None or bars.empty: 
                raise ValueError("Empty Bars")
            bars = bars.sort_values('time')
            current_price = float(bars['close'].iloc[-1])
            
            quote = quote_client.get_stock_briefs([tiger_sym])
            if quote is None or quote.empty: 
                raise ValueError("Empty Quote")
            
            prev_close = float(quote['prev_close'].iloc[0])
            if prev_close == 0:
                prev_close = current_price
                
            change_pct = (current_price - prev_close) / prev_close
            
            returns = bars['close'].pct_change(fill_method=None).dropna()
            volatility = returns.std() 
            dynamic_dip_threshold = -2 * volatility 
            
            bars['datetime'] = pd.to_datetime(bars['time'], unit='ms')
            latest_day = bars['datetime'].dt.date.iloc[-1]
            today_data = bars[bars['datetime'].dt.date == latest_day].copy()
            
            if not today_data.empty:
                today_data['Typical_Price'] = (today_data['high'] + today_data['low'] + today_data['close']) / 3
                today_data['Volume_Price'] = today_data['Typical_Price'] * today_data['volume']
                
                total_vol = today_data['volume'].sum()
                vwap = today_data['Volume_Price'].sum() / total_vol if total_vol > 0 else current_price
                
                recent_volume = today_data['volume'].iloc[-1]
                avg_volume = today_data['volume'].mean()
                
                is_breakout = (current_price > vwap) and (recent_volume > (avg_volume * 1.5))
            else:
                is_breakout = False
                
        except Exception:
            # fallback to Yahoo Finance
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d", interval="15m")
            if hist.empty: return "NO_DATA"

            current_price = hist['Close'].iloc[-1]
            prev_close = stock.info.get('previousClose', current_price)
            
            returns = hist['Close'].pct_change(fill_method=None).dropna()
            volatility = returns.std() 
            change_pct = (current_price - prev_close) / prev_close
            
            dynamic_dip_threshold = -2 * volatility 
            
            latest_day = hist.index[-1].date()
            today_data = hist[hist.index.date == latest_day].copy()
            
            if not today_data.empty:
                today_data['Typical_Price'] = (today_data['High'] + today_data['Low'] + today_data['Close']) / 3
                today_data['Volume_Price'] = today_data['Typical_Price'] * today_data['Volume']
                total_vol = today_data['Volume'].sum()
                vwap = today_data['Volume_Price'].sum() / total_vol if total_vol > 0 else current_price
                
                recent_volume = today_data['Volume'].iloc[-1]
                avg_volume = today_data['Volume'].mean()
                is_breakout = (current_price > vwap) and (recent_volume > (avg_volume * 1.5))
            else:
                is_breakout = False

        print(f"[{ticker}] LIVE Px: {current_price:.2f} | Chg: {change_pct:.2%} | DipReq: {dynamic_dip_threshold:.2%} | Breakout: {is_breakout}")

        if change_pct < dynamic_dip_threshold:
            return "BUY_DIP"
        elif is_breakout and change_pct > 0:
            return "BUY_MOMENTUM"
            
        return "MONITOR"

    except Exception as e:
        print(f"Signal error for {ticker}: {e}")
        return "ERROR"