# analysis/liquidity.py

def liquidity_cap(avg_daily_value):
    if avg_daily_value is None:
        return 0.05  # conservative default

    if avg_daily_value >= 50_000_000:
        return 0.20
    elif avg_daily_value >= 20_000_000:
        return 0.15
    elif avg_daily_value >= 10_000_000:
        return 0.10
    elif avg_daily_value >= 5_000_000:
        return 0.07
    else:
        return 0.04
