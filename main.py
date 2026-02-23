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
    
    # 3: Diagnostic Check
    print("\n--- PORTFOLIO CHECK: Target vs. Actual ---")
    print(f"{'Ticker':<12} | {'Target Qty':<12} | {'Actual Qty':<12} | {'Status'}")
    print("-" * 55)

    # API Opti: Fetch positions once
    current_positions = trade_client.get_positions(account=account_id)

    for ticker in df['Ticker'].tolist():
        symbol_only = ticker.split('.')[0]
        
        latest_price = yf.Ticker(ticker).fast_info['last_price']
        target_qty = int((portfolio_value * weights[symbol_only]) / latest_price)
        if ".SI" in ticker: 
            target_qty = (target_qty // 100) * 100
        
        actual_qty = get_current_quantity(current_positions, ticker)
        
        status = "MATCH" if actual_qty == target_qty else "MISMATCH"
        print(f"{ticker:<12} | {target_qty:<12} | {actual_qty:<12} | {status}")

    # 4: Intraday Scan & Entry/Trim
    print("\n--- Entry & Scaling ---")
    
    # API Opti: Fetch positions once
    current_positions = trade_client.get_positions(account=account_id)
    
    for ticker in df['Ticker'].tolist():
        symbol_only = ticker.split('.')[0]
        actual_qty = get_current_quantity(current_positions, ticker)
        
        if actual_qty == 0:
            if is_earnings_blackout(ticker):
                print(f"SKIPPING CORE INITIALIZATION: {ticker} is in a 48-hour Earnings Blackout.")
                continue
                
            print(f"INITIALIZING CORE: {ticker} has 0 holdings. Deploying 50% baseline.")
            execute_trade(trade_client, account_id, ticker, (weights[symbol_only] * 0.5), actual_qty, signal_type="CORE_INIT")
            continue
            
        signal = get_intraday_signal(quote_client, ticker)
        
        if signal in ["BUY_DIP", "BUY_MOMENTUM"]:
            if is_earnings_blackout(ticker):
                print(f"SKIPPING SCALING: {ticker} triggered a buy signal, but is in an Earnings Blackout.")
                continue
                
            trigger_type = "Mean Reversion Dip" if signal == "BUY_DIP" else "VWAP Momentum Breakout"
            print(f"SCALING TRIGGER: {ticker} hit {trigger_type}. Reconciling full delta...")
            execute_trade(trade_client, account_id, ticker, weights[symbol_only], actual_qty, signal_type=signal)
            
    # 5: Portfolio Cleanup
    print("\n--- Validating Exits ---")
    
    # API Opti: Fetch positions once
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
            
            execute_trade(trade_client, account_id, full_ticker, 0, quantity, signal_type="CLEANUP_LIQUIDATION")
        else:
            if quantity > 0:
                print(f"HOLD: {raw_symbol} maintains Model Ranking.")

    print("\n--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    run_trading_floor()