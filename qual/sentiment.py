from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from qual.event_classifier import classify_event
from qual.event_weights import EVENT_WEIGHTS

analyzer = SentimentIntensityAnalyzer()

def sentiment_score(headlines):
    weighted_scores = []
    total_weight = 0.0
    event_count = 0

    for h in headlines:
        event = classify_event(h)
        weight = EVENT_WEIGHTS.get(event, 0.0)

        if weight == 0.0:
            continue

        sentiment = analyzer.polarity_scores(h)["compound"]
        weighted_scores.append(sentiment * weight)
        total_weight += weight
        event_count += 1

    if total_weight == 0:
        return 0.0, 0

    avg_sentiment = sum(weighted_scores) / total_weight
    return avg_sentiment, event_count

