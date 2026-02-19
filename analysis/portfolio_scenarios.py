# analysis/portfolio_scenarios.py

PORTFOLIO_SCENARIOS = {
    "Rate Cut": {
        "REIT": 0.10,
        "Utilities": 0.05,
        "Banks": -0.05,
        "Financial Services": -0.05,
    },
    "China Slowdown": {
        "Industrials": -0.10,
        "Materials": -0.12,
        "Technology": -0.08,
        "Consumer Cyclical": -0.07,
    },
    "Energy Shock": {
        "Energy": 0.15,
        "Industrials": -0.05,
        "Consumer Defensive": -0.03,
    }
}

def portfolio_scenario_impact(df, scenario_name):
    rules = PORTFOLIO_SCENARIOS.get(scenario_name, {})
    impacts = []

    for _, row in df.iterrows():
        sector = row["Sector"]
        impacts.append(rules.get(sector, 0))

    return impacts
