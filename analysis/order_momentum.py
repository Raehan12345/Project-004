def order_momentum(headlines):
    count = 0
    for h in headlines:
        if "ORDER_WIN" in h:
            count += 1

    if count >= 3:
        return 2, "Strong order momentum"
    elif count >= 1:
        return 1, "Initial order recovery"
    return 0, None
