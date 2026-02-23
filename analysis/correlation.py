# analysis/correlation.py
import yfinance as yf
import pandas as pd

def apply_correlation_penalty(df, final_weights, threshold=0.80):
    tickers = df['Ticker'].tolist()
    
    try:
        data = yf.download(tickers, period="90d", interval="1d", progress=False)['Close']
        # Fixed Pandas warning by explicitly declaring fill_method
        returns = data.pct_change(fill_method=None).dropna()
        corr_matrix = returns.corr()
    except Exception as e:
        print(f"Correlation calculation failed: {e}. Bypassing penalty.")
        return final_weights

    adjusted_weights = final_weights.copy()
    
    sorted_indices = df.sort_values("AdjPortfolioScore", ascending=False).index

    for i in range(len(sorted_indices)):
        idx_primary = sorted_indices[i]
        ticker_primary = df.loc[idx_primary, 'Ticker']
        
        for j in range(i + 1, len(sorted_indices)):
            idx_secondary = sorted_indices[j]
            ticker_secondary = df.loc[idx_secondary, 'Ticker']
            
            try:
                correlation = corr_matrix.loc[ticker_primary, ticker_secondary]
                
                if correlation > threshold:
                    penalty_factor = 0.50
                    adjusted_weights.loc[idx_secondary] *= penalty_factor
                    print(f"CORRELATION PENALTY: {ticker_secondary} is {correlation:.2f} correlated to {ticker_primary}. Weight reduced.")
            except KeyError:
                continue

    if adjusted_weights.sum() > 0:
        return adjusted_weights / adjusted_weights.sum()
        
    return adjusted_weights