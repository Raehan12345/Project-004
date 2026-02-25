# quant/stat_arb_signals.py
import pandas as pd
import numpy as np
import yfinance as yf
import os
import contextlib
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def calculate_pair_zscore_local(data, asset1, asset2, hedge_ratio):
    """
    Calculates the current Z-Score of a cointegrated pair using locally pre-downloaded data.
    """
    try:
        if asset1 not in data.columns or asset2 not in data.columns:
            return None
            
        pair_data = data[[asset1, asset2]].ffill().dropna()
        
        if pair_data.empty:
            return None
            
        spread = pair_data[asset1] - (hedge_ratio * pair_data[asset2])
        
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        if spread_std == 0:
            return 0
            
        current_spread = spread.iloc[-1]
        z_score = (current_spread - spread_mean) / spread_std
        
        return round(z_score, 3)
        
    except Exception:
        return None

def scan_stat_arb_signals(filepath="cointegrated_pairs.csv", max_entry_pairs=5):
    """
    Evaluates pairs for long-only relative value entries and exits.
    Returns a list of tickers to buy, and a list of tickers to liquidate.
    """
    if not os.path.exists(filepath):
        print("Pairs file not found. Run cointegration.py first.")
        return [], [], []

    df = pd.read_csv(filepath)
    df = df.sort_values(by='P_Value').reset_index(drop=True)
    
    universe_tickers = list(set(df['Asset_1'].tolist() + df['Asset_2'].tolist()))
    
    buy_list = []
    exit_list = []
    
    print(f"Bulk downloading 1-hour interval data for {len(universe_tickers)} unique assets...")
    
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            raw_data = yf.download(universe_tickers, period="60d", interval="1h", progress=False)
            
    if isinstance(raw_data.columns, pd.MultiIndex):
        if 'Close' in raw_data.columns.levels[0]:
            bulk_data = raw_data['Close']
        elif 'Adj Close' in raw_data.columns.levels[0]:
            bulk_data = raw_data['Adj Close']
        else:
            bulk_data = raw_data
    else:
        bulk_data = raw_data

    print(f"Data acquired. Scanning {len(df)} total pairs for active mean-reversion signals...\n")
    print("--- LIVE Z-SCORE HEARTBEAT (TOP 5 PAIRS) ---")
    
    for index, row in df.iterrows():
        a1 = row['Asset_1']
        a2 = row['Asset_2']
        hr = row['Hedge_Ratio']
        
        a1_exchange = a1.split('.')[-1] if '.' in a1 else ''
        a2_exchange = a2.split('.')[-1] if '.' in a2 else ''
        if a1_exchange != a2_exchange:
            continue
            
        zscore = calculate_pair_zscore_local(bulk_data, a1, a2, hr)
        
        if zscore is not None:
            if zscore >= 0.0:
                exit_list.append(a1)
            if zscore <= 0.0:
                exit_list.append(a2)
                
            if index < max_entry_pairs:
                print(f"[{a1} vs {a2}] Current Z-Score: {zscore} | Threshold: +/- 2.0")
                if zscore <= -2.0:
                    buy_list.append(a1)
                    print(f" >>> SIGNAL TRIGGERED: BUY {a1} (Undervalued)")
                elif zscore >= 2.0:
                    buy_list.append(a2)
                    print(f" >>> SIGNAL TRIGGERED: BUY {a2} (Undervalued)")
        else:
            if index < max_entry_pairs:
                print(f"[{a1} vs {a2}] Current Z-Score: DATA UNAVAILABLE")

    print("--------------------------------------------\n")

    buy_set = set(buy_list)
    exit_set = set(exit_list)
    
    final_exits = list(exit_set - buy_set)
    final_buys = list(buy_set)

    return final_buys, final_exits, universe_tickers

if __name__ == "__main__":
    buys, exits, universe = scan_stat_arb_signals("../cointegrated_pairs.csv")