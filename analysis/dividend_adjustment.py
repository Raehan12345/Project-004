# analysis/dividend_adjustment.py

def dividend_adjustment(dividend_yield):
    if dividend_yield is None or dividend_yield <= 0:
        return 0.0

    if dividend_yield >= 0.06:
        return 0.3   # very attractive income
    elif dividend_yield >= 0.04:
        return 0.2
    elif dividend_yield >= 0.025:
        return 0.1
    else:
        return 0.0
