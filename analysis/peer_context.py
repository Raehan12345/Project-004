def peer_context(ratios, sector_medians):
    context = {}

    context["pe_vs_peers"] = (
        "CHEAPER" if ratios["pe"] and ratios["pe"] < sector_medians["pe"] else "RICHER"
    )

    context["margin_vs_peers"] = (
        "STRONGER"
        if ratios["margin"] and ratios["margin"] > sector_medians["margin"]
        else "WEAKER"
    )

    return context

TECH_MEDIANS = {
    "pe": 28,
    "margin": 0.18
}
