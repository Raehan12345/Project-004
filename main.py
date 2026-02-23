# main.py
import pandas as pd
import yfinance as yf
from execution.broker_api import get_tiger_client
from quant.screener_engine import run_full_screener
from quant.intraday_signals import get_intraday_signal
from execution.order_manager import execute_trade, get_current_quantity
from quant.earnings_blackout import is_earnings_blackout

def run_trading_floor():
    print("\n--- STARTING ---")
    
    run_full_screener()
    df = pd.read_csv("stock_screen_results.csv")
    
    trade_client, quote_client, account_id = get_tiger_client()
    assets = trade_client.get_assets()
    portfolio_value = assets[0].segments['S'].equity_with_loan
    
    weights = {}
    ticker_map = {}
    for _, row in df.iterrows():
        sym = row['Ticker'].split('.')[0]
        weights[sym] = row['TargetWeight']
        ticker_map[sym] = row['Ticker']
    
    # Phase 3: Diagnostic Health Check
    print("\n--- PORTFOLIO CHECK: Target vs. Actual ---")
    print(f"{'Ticker':<12} | {'Target Qty':<12} | {'Actual Qty':<12} | {'Status'}")
    print("-" * 55)

    current_positions = trade_client.get_positions(account=account_id)

    for ticker in df['Ticker'].tolist():
        raw_sym = ticker.split('.')[0]
        tiger_sym = raw_sym.zfill(5) if ".HK" in ticker else raw_sym
        
        try:
            quote = quote_client.get_stock_briefs([tiger_sym])
            if quote is None or quote.empty:
                raise ValueError("Empty Quote")
            latest_price = float(quote['latest_price'].iloc[0])
        except Exception:
            latest_price = yf.Ticker(ticker).fast_info['last_price']
            
        # Dynamically fetch the lot size for the diagnostic check
        try:
            contracts = trade_client.get_contracts(tiger_sym, sec_type='STK')
            if contracts:
                lot_size = getattr(contracts[0], 'lot_size', 100 if ".SI" in ticker else 1)
                lot_size = int(lot_size) if lot_size else (100 if ".SI" in ticker else 1)
            else:
                lot_size = 100 if ".SI" in ticker else 1
        except Exception:
            lot_size = 100 if ".SI" in ticker else 1
        
        target_qty = int((portfolio_value * weights[raw_sym]) / latest_price)
        target_qty = (target_qty // lot_size) * lot_size
        
        actual_qty = get_current_quantity(current_positions, ticker)
        
        status = "MATCH" if actual_qty == target_qty else "MISMATCH"
        print(f"{ticker:<12} | {target_qty:<12} | {actual_qty:<12} | {status}")

    # --- Phase 4: Intraday Scan & Entry/Trim ---
    print("\n--- Entry & Scaling ---")
    
    current_positions = trade_client.get_positions(account=account_id)
    
    for ticker in df['Ticker'].tolist():
        raw_sym = ticker.split('.')[0]
        actual_qty = get_current_quantity(current_positions, ticker)
        
        if actual_qty == 0:
            if is_earnings_blackout(ticker):
                print(f"SKIPPING CORE INITIALIZATION: {ticker} is in a 48-hour Earnings Blackout.")
                continue
                
            execute_trade(trade_client, quote_client, account_id, ticker, (weights[raw_sym] * 0.5), actual_qty, signal_type="CORE_INIT")
            continue
            
        signal = get_intraday_signal(quote_client, ticker)
        
        if signal in ["BUY_DIP", "BUY_MOMENTUM"]:
            if is_earnings_blackout(ticker):
                print(f"SKIPPING SCALING: {ticker} triggered a buy signal, but is in an Earnings Blackout.")
                continue
                
            trigger_type = "Mean Reversion Dip" if signal == "BUY_DIP" else "VWAP Momentum Breakout"
            print(f"SCALING TRIGGER: {ticker} hit {trigger_type}. Reconciling full delta...")
            execute_trade(trade_client, quote_client, account_id, ticker, weights[raw_sym], actual_qty, signal_type=signal)
            
    # Phase 5: Portfolio Cleanup
    print("\n--- Validating Exits ---")
    
    current_positions = trade_client.get_positions(account=account_id)
    top_symbols = list(weights.keys()) 

    for pos in current_positions:
        raw_symbol = pos.contract.symbol.split('.')[0]
        quantity = pos.quantity
        
        if quantity > 0 and raw_symbol not in top_symbols:
            print(f"EXIT TRIGGER: {raw_symbol} removed from Target Universe. Liquidating.")
            
            full_ticker = ticker_map.get(raw_symbol)
            if not full_ticker:
                if raw_symbol.isdigit(): 
                    full_ticker = f"{raw_symbol.zfill(5)}.HK"
                elif len(raw_symbol) <= 4 and raw_symbol.isalpha(): 
                    full_ticker = raw_symbol
                else: 
                    full_ticker = f"{raw_symbol}.SI"
            
            execute_trade(trade_client, quote_client, account_id, full_ticker, 0, quantity, signal_type="CLEANUP_LIQUIDATION")
        else:
            if quantity > 0:
                print(f"HOLD: {raw_symbol} maintains Model Ranking.")

    print("\n--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    run_trading_floor()