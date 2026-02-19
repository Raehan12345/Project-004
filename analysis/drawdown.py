# analysis/drawdown.py

import pandas as pd

def drawdown(series: pd.Series):
    """
    Returns drawdown series and max drawdown.
    """
    cumulative = (1 + series).cumprod()
    peak = cumulative.cummax()
    dd = (cumulative - peak) / peak
    return dd, dd.min()
