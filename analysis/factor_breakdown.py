def factor_breakdown(ratios, rules):
    breakdown = {}

    breakdown["Valuation (P/E)"] = (
        "PASS" if ratios["pe"] and ratios["pe"] < rules["pe_max"] else "FAIL"
    )
    breakdown["Profitability (ROE)"] = (
        "PASS" if ratios["roe"] and ratios["roe"] > rules["roe_min"] else "FAIL"
    )
    breakdown["Leverage"] = (
        "PASS" if ratios["debt_to_equity"]
        and ratios["debt_to_equity"] < rules["debt_to_equity_max"]
        else "FAIL"
    )
    breakdown["Margins"] = (
        "PASS" if ratios["margin"] and ratios["margin"] > rules["margin_min"] else "FAIL"
    )
    breakdown["Growth"] = (
        "PASS" if ratios["revenue_growth"]
        and ratios["revenue_growth"] > rules["growth_min"]
        else "FAIL"
    )

    return breakdown
