# analysis/cointegration.py
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import itertools
import os

def load_tickers(filepath=r"C:\Users\raeha\OneDrive\Desktop\SCRAPE\tickers.txt"):
    """Reads the universe of tickers from the text file."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
        
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]

def find_cointegrated_pairs(tickers, period="2y"):
    """
    Scans the provided ticker universe for cointegrated pairs 
    and calculates their historical hedge ratios.
    """
    print(f"Downloading historical data for {len(tickers)} tickers for the past {period}...")
    
    # Download daily close prices
    data = yf.download(tickers, period=period, progress=False)['Close']
    
    # Drop columns that have completely missing data
    data = data.dropna(axis=1, how='all')
    
    # Forward fill temporary gaps, then drop remaining NAs to align timelines
    data = data.ffill().dropna()
    
    valid_tickers = data.columns.tolist()
    print(f"Data cleaned. Proceeding with {len(valid_tickers)} valid tickers.")
    
    # Generate all possible unique combinations of tickers
    pairs = list(itertools.combinations(valid_tickers, 2))
    print(f"Testing {len(pairs)} possible combinations for cointegration...")
    
    results = []
    
    for asset1, asset2 in pairs:
        try:
            series1 = data[asset1]
            series2 = data[asset2]
            
            # The Engle-Granger two-step cointegration test
            score, pvalue, _ = coint(series1, series2)
            
            # A p-value < 0.05 indicates strong statistical evidence of cointegration
            if pvalue < 0.05:
                # Calculate the Hedge Ratio using Ordinary Least Squares (OLS)
                # Equation: Asset1 = (Hedge_Ratio * Asset2) + Constant
                X = sm.add_constant(series2)
                model = sm.OLS(series1, X).fit()
                hedge_ratio = model.params.iloc[1]
                
                results.append({
                    'Asset_1': asset1,
                    'Asset_2': asset2,
                    'P_Value': round(pvalue, 5),
                    'Hedge_Ratio': round(hedge_ratio, 4)
                })
                print(f"Valid Pair Discovered: {asset1} & {asset2} | P-Value: {pvalue:.4f}")
                
        except Exception as e:
            continue

    df_results = pd.DataFrame(results)
    
    if not df_results.empty:
        # Sort by the lowest p-value (strongest mean reversion probability)
        df_results = df_results.sort_values(by='P_Value')
        df_results.to_csv("cointegrated_pairs.csv", index=False)
        print(f"\nScan complete. {len(df_results)} valid pairs saved to cointegrated_pairs.csv")
    else:
        print("\nScan complete. No cointegrated pairs found in the current universe.")

if __name__ == "__main__":
    # The filepath is now handled by the default argument in load_tickers
    ticker_list = load_tickers() 
    if ticker_list:
        find_cointegrated_pairs(ticker_list)