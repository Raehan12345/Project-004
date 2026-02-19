ORDER_KEYWORDS = [
    "order",
    "contract",
    "award",
    "secured",
    "tender",
    "project",
    "win",
    "appointed",
    "framework agreement",
    "letter of award"
]

EVENT_KEYWORDS = {
    "earnings": [
        "earnings", "revenue", "profit", "guidance", "forecast", "outlook"
    ],
    "regulatory": [
        "lawsuit", "probe", "regulator", "antitrust", "investigation", "fine"
    ],
    "mna": [
        "acquire", "acquisition", "merger", "buyout", "takeover"
    ],
    "management": [
        "ceo", "cfo", "resigns", "steps down", "appoints", "succession"
    ],
    "product": [
        "launch", "releases", "unveils", "product", "service"
    ],
}

def classify_event(headline: str):
    h = headline.lower()

    for kw in ORDER_KEYWORDS:
        if kw in h:
            return "order_win"

    for event, keywords in EVENT_KEYWORDS.items():
        for kw in keywords:
            if kw in h:
                return event

    return "noise"

"""""
if __name__ == "__main__":
    test_headlines = [
        "ATTIKA secures new interior fit-out contract worth $15m",
        "Company reports decline in quarterly revenue",
        "CEO resigns amid restructuring",
        "New product launch announced",
        "Share price moves on market speculation",
    ]

    for h in test_headlines:
        print(f"{classify_event(h)} -> {h}")
"""""
