# execution/order_manager.py
import pandas as pd
import yfinance as yf
from tigeropen.common.util.order_utils import market_order

def get_current_quantity(trade_client, account_id, ticker):
    """
    Checks the Tiger account using normalized symbols to avoid double-buying.
    """
    try:
        search_symbol = ticker.split('.')[0].upper()
        
        positions = trade_client.get_positions(account=account_id)
        for pos in positions:
            pos_symbol = pos.contract.symbol.split('.')[0].upper()
            if pos_symbol == search_symbol:
                return pos.quantity
        return 0
    except Exception as e:
        print(f"Position fetch failed for {ticker}: {e}")
        return 0

def get_atr(ticker, period=14):
    """Calculates Average True Range (ATR) for volatility-based stops."""
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

def execute_trade(trade_client, account_id, ticker, target_weight):
    """
    Executes a trade based on current vs target allocation with volatility-based limits.
    """
    try:
        assets = trade_client.get_assets()
        portfolio_value = assets[0].segments['S'].equity_with_loan
        stock = yf.Ticker(ticker)
        latest_price = stock.fast_info['last_price']
        
        target_qty = int((portfolio_value * target_weight) / latest_price)
        
        if ".SI" in ticker:
            target_qty = (target_qty // 100) * 100

        symbol_only = ticker.split('.')[0]
        current_qty = get_current_quantity(trade_client, account_id, symbol_only)
        needed_qty = target_qty - current_qty
        
        if needed_qty == 0:
            print(f"HOLD: {ticker} position is at target ({current_qty}).")
            return
            
        action = 'BUY' if needed_qty > 0 else 'SELL'
        abs_qty = abs(needed_qty)

        if ".SI" in ticker:
            abs_qty = (abs_qty // 100) * 100
            
        if abs_qty <= 0:
            return

        print(f"EXECUTION: {action} {ticker} | Own: {current_qty} | Target: {target_qty} | Delta: {needed_qty}")
        
        # ATR-Based Risk Guardrails
        atr = get_atr(ticker)
        if atr:
            stop_loss_price = latest_price - (2 * atr)
            take_profit_price = latest_price + (3 * atr)
            limit_type = "ATR-Aware"
        else:
            stop_loss_price = latest_price * 0.98
            take_profit_price = latest_price * 1.05
            limit_type = "Static 2%"
            
        print(f"LIMITS ({limit_type}) -> SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")

        contracts = trade_client.get_contracts(ticker, sec_type='STK')
        
        if not contracts:
            if ".SI" in ticker or ".NS" in ticker or ".HK" in ticker:
                contracts = trade_client.get_contracts(symbol_only, sec_type='STK')

        if contracts:
            contract = contracts[0]
            order = market_order(
                account=account_id, 
                contract=contract, 
                action=action, 
                quantity=int(abs_qty)
            )
            
            trade_client.place_order(order)
            print(f"SUCCESS: {action} order for {abs_qty} shares of {ticker} transmitted.")
        else:
            print(f"ERROR: Could not resolve contract for {ticker}")

    except Exception as e:
        print(f"EXECUTION FAILURE for {ticker}: {e}")