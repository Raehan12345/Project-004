# analysis/portfolio.py
import pandas as pd

def allocate_portfolio(df, max_sector_weight=0.30):
    """
    Upgraded: Risk-Parity Allocation with Sector Concentration Limits.
    Prevents the portfolio from over-allocating to a single industry.
    """
    scores = df["AdjPortfolioScore"].clip(lower=0)
    risk_weights = df["VolMultiplier"]
    composite_score = scores * risk_weights
    
    total = composite_score.sum()
    if total == 0:
        return pd.Series([0.0] * len(df))

    raw_weights = composite_score / total
    capped_weights = pd.Series(0.0, index=df.index)
    
    # Track accumulated weight per sector
    sector_exposure = {}

    for idx, row in df.sort_values("AdjPortfolioScore", ascending=False).iterrows():
        sector = row["Sector"]
        cap = row["LiquidityCap"]
        proposed_weight = raw_weights.loc[idx]
        
        # Apply Liquidity Cap
        weight = min(proposed_weight, cap)
        
        # Apply Sector Cap
        current_sector_weight = sector_exposure.get(sector, 0.0)
        if current_sector_weight + weight > max_sector_weight:
            # Only allow the remainder up to the 30% cap
            weight = max(0, max_sector_weight - current_sector_weight)
            
        capped_weights.loc[idx] = weight
        sector_exposure[sector] = current_sector_weight + weight

    # Re-normalize to ensure 100% capital deployment after all caps
    if capped_weights.sum() > 0:
        return capped_weights / capped_weights.sum()
        
    return capped_weights