GOV_SECTORS = ["Industrials", "Utilities", "Materials"]

def gov_spend_sensitivity(sector):
    if sector in GOV_SECTORS:
        return 1
    return 0