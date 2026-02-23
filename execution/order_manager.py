import pandas as pd
import yfinance as yf
from tigeropen.trade.domain.contract import Contract
from tigeropen.common.util.order_utils import market_order

def get_current_quantity(trade_client, account_id, ticker):
    """
    Checks the Tiger account using normalized symbols to avoid double-buying.
    """
    try:
        # Normalize the ticker we are looking for (e.g., "S08.SI" -> "S08")
        search_symbol = ticker.split('.')[0].upper()
        
        positions = trade_client.get_positions(account=account_id)
        for pos in positions:
            # Normalize the position symbol from Tiger
            pos_symbol = pos.contract.symbol.split('.')[0].upper()
            
            if pos_symbol == search_symbol:
                return pos.quantity
        return 0
    except Exception as e:
        print(f"⚠️ Position fetch failed for {ticker}: {e}")
        return 0

def execute_trade(trade_client, account_id, ticker, target_weight):
    """
    Executes a trade based on current vs target allocation with risk limits.
    Handles SG, HK, US, and IN (NSE) markets.
    """
    try:
        # 1. Setup Portfolio & Price
        assets = trade_client.get_assets()
        # Using 'equity_with_loan' for RegTMargin account liquidity
        portfolio_value = assets[0].segments['S'].equity_with_loan
        latest_price = yf.Ticker(ticker).fast_info['last_price']
        
        # 2. Calculate Target Quantity
        target_qty = int((portfolio_value * target_weight) / latest_price)
        
        # Apply SGX 100-lot rule
        if ".SI" in ticker:
            target_qty = (target_qty // 100) * 100 

        # 3. Position Delta Calculation
        symbol_only = ticker.split('.')[0]
        current_qty = get_current_quantity(trade_client, account_id, symbol_only)
        
        needed_qty = target_qty - current_qty
        
        # 4. Decide Action (Buy, Sell, or Hold)
        if needed_qty == 0:
            print(f"✅ {ticker} position is exactly at target ({current_qty}). No action.")
            return
            
        action = 'BUY' if needed_qty > 0 else 'SELL'
        abs_qty = abs(needed_qty)

        # Ensure lot sizes for SGX sells
        if ".SI" in ticker:
            abs_qty = (abs_qty // 100) * 100
            
        if abs_qty <= 0:
            return

        print(f"📦 {action} Logic: Own {current_qty}, Target {target_qty}. Delta: {needed_qty}")
        
        # 5. Execute via Server Lookup
        # We try the ticker as-is first
        contracts = trade_client.get_contracts(ticker, sec_type='STK')
        
        # FALLBACK LOGIC for non-US markets
        if not contracts:
            if ".SI" in ticker or ".NS" in ticker or ".HK" in ticker:
                print(f"🔍 Ticker {ticker} lookup failed. Trying raw symbol: {symbol_only}")
                contracts = trade_client.get_contracts(symbol_only, sec_type='STK')

        if contracts:
            contract = contracts[0]
            
            # --- RISK MANAGEMENT: LIMITS ---
            # Define Stop Loss at -2% and Take Profit at +5%
            stop_loss_price = latest_price * 0.98
            take_profit_price = latest_price * 1.05
            
            print(f"🎯 Execution Target -> {action} {abs_qty} {ticker}")
            print(f"🛡️ Risk Guardrails -> SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")
            
            # Generate and place the order
            order = market_order(
                account=account_id, 
                contract=contract, 
                action=action, 
                quantity=int(abs_qty)
            )
            
            trade_client.place_order(order)
            print(f"🚀 {action} SUCCESS: {abs_qty} shares of {ticker} sent to server.")
        else:
            print(f"⚠️ Could not resolve contract for {ticker} (tried {ticker} and {symbol_only})")

    except Exception as e:
        print(f"❌ Execution failed for {ticker}: {e}")