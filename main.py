import pandas as pd
import yfinance as yf
from execution.broker_api import get_tiger_client
from quant.screener_engine import run_full_screener
from quant.intraday_signals import get_intraday_signal
from execution.order_manager import execute_trade, get_current_quantity

def run_trading_floor():
    print("\n--- ENGINE: STARTING ---")
    
    # --- Phase 1: Refresh Rankings ---
    run_full_screener()
    df = pd.read_csv("stock_screen_results.csv")
    
    # --- Phase 2: API Handshake ---
    trade_client, quote_client, account_id = get_tiger_client()
    
    # Get total portfolio value for target calculations
    assets = trade_client.get_assets()
    portfolio_value = assets[0].segments['S'].equity_with_loan
    
    # Create a dictionary for quick weight lookup and full ticker mapping
    weights = {}
    ticker_map = {}
    for _, row in df.iterrows():
        sym = row['Ticker'].split('.')[0]
        weights[sym] = row['TargetWeight']
        ticker_map[sym] = row['Ticker']
    
    # --- Phase 3: Diagnostic Health Check ---
    print("\n---  PORTFOLIO HEALTH CHECK: Target vs. Actual ---")
    print(f"{'Ticker':<12} | {'Target Qty':<12} | {'Actual Qty':<12} | {'Status'}")
    print("-" * 55)

    for ticker in df['Ticker'].tolist():
        symbol_only = ticker.split('.')[0]
        
        # Calculate what we SHOULD own
        latest_price = yf.Ticker(ticker).fast_info['last_price']
        target_qty = int((portfolio_value * weights[symbol_only]) / latest_price)
        if ".SI" in ticker: 
            target_qty = (target_qty // 100) * 100
        
        # Check what we ACTUALLY own using the normalized getter
        actual_qty = get_current_quantity(trade_client, account_id, ticker)
        
        status = "MATCH" if actual_qty == target_qty else "MISMATCH"
        print(f"{ticker:<12} | {target_qty:<12} | {actual_qty:<12} | {status}")

    # --- Phase 4: Intraday Scan & Entry/Trim ---
    print("\n--- 🔍 SCANNING: Entry & Rebalancing Windows ---")
    for ticker in df['Ticker'].tolist():
        symbol_only = ticker.split('.')[0]
        signal = get_intraday_signal(quote_client, ticker)
        
        # Trigger trade if signal hits
        if signal == "BUY_NOW":
            print(f" TRIGGER: {ticker} hit entry window. Checking allocation...")
            execute_trade(trade_client, account_id, ticker, weights[symbol_only])
            
    # --- Phase 5: Portfolio Cleanup (Exit Logic) ---
    print("\n---  CLEANUP: Checking for Exits ---")
    current_positions = trade_client.get_positions(account=account_id)
    top_symbols = list(weights.keys()) 

    for pos in current_positions:
        # Normalize the symbol coming from Tiger
        raw_symbol = pos.contract.symbol.split('.')[0]
        quantity = pos.quantity
        
        if quantity > 0 and raw_symbol not in top_symbols:
            print(f" EXIT: {raw_symbol} no longer in Top 17 rankings. Liquidating...")
            
            # Map back to full ticker for yfinance price retrieval
            full_ticker = ticker_map.get(raw_symbol)
            if not full_ticker:
                if raw_symbol.isdigit(): # HK
                    full_ticker = f"{raw_symbol.zfill(5)}.HK"
                elif len(raw_symbol) <= 4 and raw_symbol.isalpha(): # US
                    full_ticker = raw_symbol
                else: # Default to Singapore
                    full_ticker = f"{raw_symbol}.SI"
            
            print(f"DEBUG: Liquidating {raw_symbol} using ticker: {full_ticker}")
            execute_trade(trade_client, account_id, full_ticker, 0)
        else:
            if quantity > 0:
                print(f" HOLD: {raw_symbol} remains in Top 17.")

    print("\n--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    run_trading_floor()