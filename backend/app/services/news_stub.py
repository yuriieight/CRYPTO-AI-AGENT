"""News sentiment analysis using FinBERT."""
# Model: ProsusAI/finbert
# Labels: positive, negative, neutral
from transformers import pipeline

_pipe = None

def _get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = pipeline("text-classification",
                         model="ProsusAI/finbert",
                         top_k=None)
    return _pipe

def analyze_sentiment(text: str) -> dict:
    results = _get_pipe()(text[:512])[0]
    best = max(results, key=lambda x: x["score"])
    return {"label": best["label"], "score": round(best["score"], 4)}
