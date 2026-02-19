# analysis/sector_pe.py

SECTOR_MEDIAN_PE = {
    "Financial Services": 10,
    "Banks": 10,
    "Real Estate": 12,
    "REIT": 12,
    "Industrials": 14,
    "Consumer Defensive": 15,
    "Consumer Cyclical": 18,
    "Technology": 22,
    "Communication Services": 20,
    "Energy": 10,
    "Utilities": 14,
}

def get_sector_median_pe(sector):
    return SECTOR_MEDIAN_PE.get(sector, 15)
