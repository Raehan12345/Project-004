def turnaround_flag(ratios):
    if (
        ratios.get("revenue_growth", 0) < 0.05 and
        ratios.get("margin", 0) < 0.05 and
        ratios.get("debt_to_equity", 0) > 100
    ):
        return True
    return False
