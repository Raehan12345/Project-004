def scenario_triggers(ratios):
    triggers = []

    if ratios["pe"] and ratios["pe"] > 30:
        triggers.append("BUY if P/E falls below 25")

    if ratios["revenue_growth"] and ratios["revenue_growth"] < 0.10:
        triggers.append("Upgrade if revenue growth re-accelerates >10%")

    return triggers
