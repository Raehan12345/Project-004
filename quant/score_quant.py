from quant.sector_rules import SECTOR_RULES, DEFAULT_RULES

def score_quant(ratios, sector):
    rules = SECTOR_RULES.get(sector, DEFAULT_RULES)
    score = 0

    if ratios["pe"] and ratios["pe"] < rules["pe_max"]:
        score += 1
    if ratios["roe"] and ratios["roe"] > rules["roe_min"]:
        score += 1
    if ratios["debt_to_equity"] and ratios["debt_to_equity"] < rules["debt_to_equity_max"]:
        score += 1
    if ratios["margin"] and ratios["margin"] > rules["margin_min"]:
        score += 1
    if ratios["revenue_growth"] and ratios["revenue_growth"] > rules["growth_min"]:
        score += 1

    return score