#scraper for yahoofinance news

import feedparser

def get_headlines(ticker, limit=10):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    feed = feedparser.parse(url)

    headlines = []
    for entry in feed.entries[:limit]:
        headlines.append(entry.title)

    return headlines

