# qual/score_qual.py

def score_qual(sentiment, event_count):
    if event_count == 0:
        return 0

    # High Conviction Signal: Multiple corroborating headlines with strong tone
    if abs(sentiment) >= 0.5 and event_count >= 3:
        return 3 if sentiment > 0 else -3

    # Direct Signal: Clear positive/negative trend
    if abs(sentiment) >= 0.3 and event_count >= 2:
        return 2 if sentiment > 0 else -2

    # Moderate Signal: Single headline or weak multi-headline trend
    if abs(sentiment) >= 0.15:
        return 1 if sentiment > 0 else -1

    # Noise
    return 0


