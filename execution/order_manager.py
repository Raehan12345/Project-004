import pandas as pd
import yfinance as yf
import csv
import os
from datetime import datetime
from tigeropen.common.util.order_utils import market_order, limit_order

def log_trade(ticker, action, quantity, price, signal_type):
    file_name = "trade_log.csv"
    file_exists = os.path.isfile(file_name)
    
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Ticker", "Action", "Quantity", "ExecutionPrice", "SignalType"])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, ticker, action, quantity, price, signal_type])

def get_current_quantity(positions, ticker):
    try:
        search_symbol = ticker.split('.')[0].upper()
        
        for pos in positions:
            pos_symbol = pos.contract.symbol.split('.')[0].upper()
            if pos_symbol == search_symbol:
                return pos.quantity
        return 0
    except Exception as e:
        print(f"Position check failed for {ticker}: {e}")
        return 0

def get_hkex_tick_size(price):
    if price <= 0.25: return 0.001
    if price <= 0.50: return 0.005
    if price <= 10.00: return 0.01
    if price <= 20.00: return 0.02
    if price <= 100.00: return 0.05
    if price <= 200.00: return 0.10
    if price <= 500.00: return 0.20
    if price <= 1000.00: return 0.50
    if price <= 2000.00: return 1.00
    if price <= 5000.00: return 2.00
    return 5.00

def execute_trade(trade_client, quote_client, account_id, ticker, target_weight, current_qty, signal_type="UNKNOWN"):
    try:
        assets = trade_client.get_assets()
        portfolio_value = assets[0].segments['S'].equity_with_loan
        
        raw_sym = ticker.split('.')[0]
        tiger_sym = raw_sym.zfill(5) if ".HK" in ticker else raw_sym
        
        try:
            quote = quote_client.get_stock_briefs([tiger_sym])
            if quote is None or quote.empty:
                raise ValueError("Empty Quote")
            latest_price = float(quote['latest_price'].iloc[0])
        except Exception:
            latest_price = yf.Ticker(ticker).fast_info['last_price']
            
        contracts = trade_client.get_contracts(tiger_sym, sec_type='STK')
        if not contracts:
            contracts = trade_client.get_contracts(ticker, sec_type='STK')
            if not contracts:
                contracts = trade_client.get_contracts(raw_sym, sec_type='STK')

        if not contracts:
            print(f"ERROR: Could not resolve contract for {ticker}")
            return
            
        contract = contracts[0]
        
        lot_size = getattr(contract, 'lot_size', 1)
        if not lot_size or lot_size <= 0:
            lot_size = 100 if ".SI" in ticker else 1
        lot_size = int(lot_size)
        
        target_qty = int((portfolio_value * target_weight) / latest_price)
        target_qty = (target_qty // lot_size) * lot_size

        needed_qty = target_qty - current_qty
        
        if needed_qty == 0:
            if target_weight > 0 and target_qty == 0:
                print(f"SKIPPING: {ticker} allocation is too small to afford 1 Board Lot (Lot Size: {lot_size}).")
            return
            
        action = 'BUY' if needed_qty > 0 else 'SELL'
        abs_qty = abs(needed_qty)

        abs_qty = (abs_qty // lot_size) * lot_size
        
        if abs_qty <= 0:
            return

        print(f"EXECUTION LOGIC: {action} {ticker} | Target: {target_qty} | Delta: {needed_qty} | Lot: {lot_size}")

        if ".HK" in ticker:
            raw_limit = latest_price * 1.01 if action == 'BUY' else latest_price * 0.99
            tick_size = get_hkex_tick_size(latest_price)
            limit_px = round(round(raw_limit / tick_size) * tick_size, 3)
            
            primary_order = limit_order(
                account=account_id, 
                contract=contract, 
                action=action, 
                quantity=int(abs_qty),
                limit_price=limit_px
            )
        else:
            primary_order = market_order(
                account=account_id, 
                contract=contract, 
                action=action, 
                quantity=int(abs_qty)
            )
            
        trade_client.place_order(primary_order)
        print(f"SUCCESS: {action} order for {abs_qty} shares of {ticker} transmitted.")

        log_trade(ticker, action, int(abs_qty), latest_price, signal_type)

    except Exception as e:
        print(f"EXECUTION FAILURE for {ticker}: {e}")