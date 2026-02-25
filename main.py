# main.py
import pandas as pd
from execution.broker_api import get_tiger_client
from quant.stat_arb_signals import scan_stat_arb_signals
from execution.order_manager import execute_trade, get_current_quantity
from quant.earnings_blackout import is_earnings_blackout

def run_trading_floor():
    print("\n--- STARTING LONG-ONLY RELATIVE VALUE ENGINE ---")
    
    # 1. Generate real-time statistical signals
    buy_targets, exit_targets, universe_tickers = scan_stat_arb_signals("cointegrated_pairs.csv", max_entry_pairs=5)
    
    trade_client, quote_client, account_id = get_tiger_client()
    assets = trade_client.get_assets()
    portfolio_value = assets[0].segments['S'].equity_with_loan
    
    # Fixed allocation: Risk 15% of total portfolio value per trade
    fixed_weight = 0.15 
    
    print("\n--- Phase 1: Signal Execution (Entries) ---")
    current_positions = trade_client.get_positions(account=account_id)
    
    for ticker in buy_targets:
        if is_earnings_blackout(ticker):
            print(f"SKIPPING: {ticker} has a valid signal but is in an Earnings Blackout.")
            continue
            
        actual_qty = get_current_quantity(current_positions, ticker)
        
        if actual_qty == 0:
            print(f"SIGNAL ACTIVE: Initiating long position for undervalued asset {ticker}.")
            execute_trade(trade_client, quote_client, account_id, ticker, fixed_weight, actual_qty, signal_type="REL_VAL_BUY")
        else:
            print(f"HOLD: Target weight already achieved for {ticker}.")

    print("\n--- Phase 2: Validating Exits (Mean Reversion) ---")
    current_positions = trade_client.get_positions(account=account_id)
    
    for pos in current_positions:
        raw_symbol = pos.contract.symbol.split('.')[0]
        quantity = pos.quantity
        
        if quantity > 0:
            full_ticker = None
            for t in universe_tickers:
                if t.startswith(raw_symbol + "."):
                    full_ticker = t
                    break
            
            if not full_ticker:
                full_ticker = f"{raw_symbol.zfill(5)}.HK" if raw_symbol.isdigit() else f"{raw_symbol}.SI"
            
            if full_ticker not in universe_tickers:
                print(f"CLEANUP: {full_ticker} is no longer in the cointegrated universe. Liquidating.")
                execute_trade(trade_client, quote_client, account_id, full_ticker, 0, quantity, signal_type="UNIVERSE_CLEANUP")
            elif full_ticker in exit_targets:
                print(f"REVERSION CAPTURED: {full_ticker} spread has reverted to the mean. Liquidating.")
                execute_trade(trade_client, quote_client, account_id, full_ticker, 0, quantity, signal_type="REL_VAL_EXIT")
            else:
                print(f"HOLD: {full_ticker} spread has not yet reached the zero baseline.")

    print("\n--- CYCLE COMPLETE ---")

if __name__ == "__main__":
    run_trading_floor()