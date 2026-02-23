# execution/order_manager.py
import pandas as pd
import yfinance as yf
import csv
import os
from datetime import datetime
from tigeropen.common.util.order_utils import market_order, trail_order

#trade logging
def log_trade(ticker, action, quantity, price, signal_type, trail_pct="N/A"):
    file_name = "trade_log.csv"
    file_exists = os.path.isfile(file_name)
    
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Ticker", "Action", "Quantity", "ExecutionPrice", "SignalType", "TrailingStopPct"])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, ticker, action, quantity, price, signal_type, trail_pct])

#positions
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

def get_atr(ticker, period=14):
    try:
        data = yf.Ticker(ticker).history(period="30d")
        if len(data) < period: 
            return None
            
        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift()).abs()
        low_close = (data['Low'] - data['Close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean().iloc[-1]
    except Exception as e:
        print(f"ATR calculation failed for {ticker}: {e}")
        return None

def execute_trade(trade_client, account_id, ticker, target_weight, current_qty, signal_type="UNKNOWN"):
    try:
        assets = trade_client.get_assets()
        portfolio_value = assets[0].segments['S'].equity_with_loan
        stock = yf.Ticker(ticker)
        latest_price = stock.fast_info['last_price']
        
        target_qty = int((portfolio_value * target_weight) / latest_price)
        if ".SI" in ticker:
            target_qty = (target_qty // 100) * 100

        needed_qty = target_qty - current_qty
        
        if needed_qty == 0:
            return
            
        action = 'BUY' if needed_qty > 0 else 'SELL'
        abs_qty = abs(needed_qty)

        if ".SI" in ticker:
            abs_qty = (abs_qty // 100) * 100
            
        if abs_qty <= 0:
            return

        print(f"EXECUTION LOGIC: {action} {ticker} | Target: {target_qty} | Delta: {needed_qty}")

        symbol_only = ticker.split('.')[0]
        contracts = trade_client.get_contracts(ticker, sec_type='STK')
        if not contracts:
            if ".SI" in ticker or ".NS" in ticker or ".HK" in ticker:
                contracts = trade_client.get_contracts(symbol_only, sec_type='STK')

        if contracts:
            contract = contracts[0]
            
            primary_order = market_order(
                account=account_id, 
                contract=contract, 
                action=action, 
                quantity=int(abs_qty)
            )
            trade_client.place_order(primary_order)
            print(f"SUCCESS: {action} order for {abs_qty} shares of {ticker} transmitted.")
            
            trail_pct = "N/A"
            
            if action == 'BUY':
                atr = get_atr(ticker)
                if atr:
                    trail_pct = round(((2 * atr) / latest_price) * 100, 2)
                    trail_pct = min(trail_pct, 20.0)
                    
                    stop_order = trail_order(
                        account=account_id,
                        contract=contract,
                        action='SELL',
                        quantity=int(abs_qty),
                        trailing_percent=trail_pct
                    )
                    trade_client.place_order(stop_order)
                    print(f"RISK MANAGEMENT: Server-side trailing stop attached at {trail_pct}% distance.")

            log_trade(ticker, action, int(abs_qty), latest_price, signal_type, trail_pct)

        else:
            print(f"ERROR: Could not resolve contract for {ticker}")

    except Exception as e:
        print(f"EXECUTION FAILURE for {ticker}: {e}")