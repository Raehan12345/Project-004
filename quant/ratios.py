

def extract_ratios(info):
    return {
        "pe": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "margin": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth")
    }