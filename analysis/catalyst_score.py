# analysis/catalyst_score.py

CATALYST_KEYWORDS = {
    # very strong catalysts
    "contract": 2.0,
    "contract win": 2.5,
    "award": 2.0,
    "acquisition": 2.0,
    "divestment": 2.0,
    "asset sale": 2.5,
    "strategic review": 2.5,
    "spin-off": 2.5,

    # moderate catalysts
    "government": 1.5,
    "policy": 1.5,
    "tender": 1.5,
    "regulatory approval": 1.5,
    "expansion": 1.0,
    "joint venture": 1.0,

    # softer / early signals
    "exploring": 0.5,
    "reviewing options": 0.5,
}

MAX_CATALYST_SCORE = 5.0


def catalyst_score(headlines):
    score = 0.0
    triggers = set()

    for h in headlines:
        h_lower = h.lower()
        for keyword, weight in CATALYST_KEYWORDS.items():
            if keyword in h_lower:
                score += weight
                triggers.add(keyword)

    return min(score, MAX_CATALYST_SCORE), list(triggers)
