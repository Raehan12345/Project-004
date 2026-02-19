# analysis/portfolio.py
import pandas as pd

def allocate_portfolio(df):
    scores = df["AdjPortfolioScore"].clip(lower=0)
    total = scores.sum()

    if total == 0:
        return [0] * len(scores)

    raw_weights = scores / total

    capped_weights = []
    for _, row in df.iterrows():
        cap = row["LiquidityCap"]
        capped_weights.append(min(raw_weights.loc[row.name], cap))

    capped_weights = pd.Series(capped_weights)
    return capped_weights / capped_weights.sum()

