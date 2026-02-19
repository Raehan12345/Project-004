def risk_flags(ratios):
    flags = []

    if ratios["pe"] and ratios["pe"] > 30:
        flags.append("Valuation risk (high P/E)")

    if ratios["debt_to_equity"] and ratios["debt_to_equity"] > 150:
        flags.append("Balance sheet leverage")

    if ratios["revenue_growth"] and ratios["revenue_growth"] < 0.03:
        flags.append("Low growth profile")

    return flags
