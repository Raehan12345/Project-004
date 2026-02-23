# analysis/portfolio.py
import pandas as pd
from analysis.correlation import apply_correlation_penalty

def allocate_portfolio(df, max_sector_weight=0.30):
    scores = df["AdjPortfolioScore"].clip(lower=0)
    risk_weights = df["VolMultiplier"]
    composite_score = scores * risk_weights
    
    total = composite_score.sum()
    if total == 0:
        return pd.Series([0.0] * len(df))

    raw_weights = composite_score / total
    capped_weights = pd.Series(0.0, index=df.index)
    sector_exposure = {}

    for idx, row in df.sort_values("AdjPortfolioScore", ascending=False).iterrows():
        sector = row["Sector"]
        cap = row["LiquidityCap"]
        proposed_weight = raw_weights.loc[idx]
        
        weight = min(proposed_weight, cap)
        current_sector_weight = sector_exposure.get(sector, 0.0)
        
        if current_sector_weight + weight > max_sector_weight:
            weight = max(0, max_sector_weight - current_sector_weight)
            
        capped_weights.loc[idx] = weight
        sector_exposure[sector] = current_sector_weight + weight

    # Normalize before correlation
    if capped_weights.sum() > 0:
        capped_weights = capped_weights / capped_weights.sum()
        
    # Apply the Statistical Correlation Penalty
    final_weights = apply_correlation_penalty(df, capped_weights)
    
    return final_weights