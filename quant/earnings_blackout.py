# quant/earnings_blackout.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

def is_earnings_blackout(ticker, blackout_hours=48):
    try:
        stock = yf.Ticker(ticker)
        # Fetch upcoming and recent earnings dates
        earnings_dates = stock.get_earnings_dates(limit=5)
        
        if earnings_dates is None or earnings_dates.empty:
            return False
            
        now = datetime.now(timezone.utc)
        
        # Filter strictly for future earnings
        future_earnings = earnings_dates[earnings_dates.index > now]
        
        if not future_earnings.empty:
            # Isolate the absolute next earnings date
            next_date = future_earnings.index.min()
            time_to_earnings = next_date - now
            
            # Check if the event falls within the blackout threshold
            if timedelta(hours=0) <= time_to_earnings <= timedelta(hours=blackout_hours):
                formatted_date = next_date.strftime('%Y-%m-%d %H:%M UTC')
                print(f"BLACKOUT ACTIVE: {ticker} reports earnings on {formatted_date}.")
                return True
                
    except Exception as e:
        # If the API fails to fetch dates, default to False to avoid halting the entire system
        print(f"Earnings lookup failed for {ticker}: {e}")
        
    return False