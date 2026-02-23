# analysis/liquidity.py

def liquidity_cap(avg_daily_value):
    if avg_daily_value is None:
        return 0.03  # More conservative default for unknown liquidity

    # Tier 1: High Liquidity (Blue Chips / Large Mid-Caps)
    if avg_daily_value >= 10_000_000:
        return 0.20
    
    # Tier 2: Standard Mid-Cap Liquidity
    elif avg_daily_value >= 5_000_000:
        return 0.15
    
    # Tier 3: Lower Mid-Cap 
    elif avg_daily_value >= 1_000_000:
        return 0.10
    
    # Tier 4: Small-Cap / Tight Liquidity
    elif avg_daily_value >= 500_000:
        return 0.06
    
    # Tier 5: Illiquid / Micro-Cap
    else:
        return 0.02