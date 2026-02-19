# analysis/valuation_score.py

def valuation_score(pe, sector_median_pe):
    if pe is None or pe <= 0 or sector_median_pe is None or sector_median_pe <= 0:
        return 0.5  # neutral if data missing

    ratio = pe / sector_median_pe

    if ratio < 0.6:
        return 1.0      # deeply undervalued
    elif ratio < 0.8:
        return 0.8
    elif ratio < 1.0:
        return 0.6
    elif ratio < 1.3:
        return 0.4
    else:
        return 0.1      # expensive
