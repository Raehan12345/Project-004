from openai import OpenAI

client = OpenAI()

def summarize_events(ticker, headlines):
    """
    Returns a concise analyst-style summary of material events.
    """
    prompt = f"""
You are a financial analyst.

Summarize the following recent news headlines for {ticker}.
Focus ONLY on material business events (earnings, guidance, regulation, M&A, management).
Ignore market noise and opinion pieces.

Keep the summary under 4 bullet points.
Be factual, neutral, and concise.

Headlines:
""" + "\n".join(f"- {h}" for h in headlines)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a buy-side equity research analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()