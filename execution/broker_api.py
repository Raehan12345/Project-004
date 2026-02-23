# execution/broker_api.py

from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key
from tigeropen.trade.trade_client import TradeClient
from tigeropen.quote.quote_client import QuoteClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_tiger_client():
    client_config = TigerOpenClientConfig(sandbox_debug=False)
    key_path = os.getenv("PRIVATE_KEY_PATH")
    client_config.private_key = read_private_key(key_path) 
    client_config.language = 'en_US'
    client_config.tiger_id = os.getenv("TIGER_ID")
    client_config.account = os.getenv("TIGER_ACCOUNT")
    
    trade_client = TradeClient(client_config)
    
    # Force grab permission on initialization
    quote_client = QuoteClient(client_config, is_grab_permission=True)
    
    # Manual grab to override any other active sessions (App/Desktop)
    try:
        quote_client.grab_quote_permission()
        print("✅ Market Data Permission Grabbed successfully.")
    except Exception as e:
        print(f"⚠️ Permission grab failed (you might need to close the Tiger App): {e}")
        
    return trade_client, quote_client, client_config.account

if __name__ == "__main__":
    try:
        print("--- Testing Tiger Brokers API Connection ---")
        trade_client, quote_client, account_id = get_tiger_client()
        
        # Fetch assets to verify connection
        assets = trade_client.get_assets()
        
        print("\n✅ Connection Successful!")
        if assets:
            # We look at the first asset object returned
            account_info = assets[0]
            print(f"Active Account: {account_info.account}")
            
            # Check for the Securities ('S') segment (Standard for SGX/HKEX)
            if 'S' in account_info.segments:
                sec_segment = account_info.segments['S']
                
                # Fetch available funds with fallback logic
                cash_balance = getattr(sec_segment, 'available_funds', 
                               getattr(sec_segment, 'cash', 
                               getattr(sec_segment, 'net_liquidation', "N/A")))
                
                print(f"Tradable Funds (S-Segment): {cash_balance}")
            else:
                print(f"Net Liquidation Value: {getattr(account_info, 'net_liquidation', 'N/A')}")
        else:
            print("⚠️ Connected, but no asset data was found. Is the account initialized?")
            
    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")