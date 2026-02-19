#scoring system for qualitative data

def score_qual(sentiment, event_count):
    if event_count == 0:
        return 0

    # strong signals
    if sentiment >= 0.4 and event_count >= 2:
        return 2
    if sentiment <= -0.4 and event_count >= 2:
        return -2

    # moderate signals
    if sentiment >= 0.15:
        return 1
    if sentiment <= -0.15:
        return -1

    return 0


