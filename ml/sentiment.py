"""Sentiment scoring with a graceful fallback.

Primary path: the fine-tuned **DistilBERT** classifier (1..5 stars) at
``SENTIMENT_MODEL_PATH``. If those weights are not available (e.g. a fresh
clone), a lightweight lexicon scorer keeps every downstream stage runnable so
the platform can be demoed end-to-end without the heavy model.
"""
from __future__ import annotations

from functools import lru_cache

from config import settings

_POS = {"excellent", "great", "perfect", "amazing", "love", "fast", "happy",
        "worth", "helpful", "smooth", "premium", "recommend", "quick", "easy"}
_NEG = {"poor", "broke", "cheap", "late", "delayed", "overpriced", "expensive",
        "damaged", "crushed", "rude", "terrible", "nightmare", "refused",
        "scratched", "unhelpful", "ignored", "never"}

_LABELS = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


def _label(stars: int) -> str:
    return _LABELS.get(int(stars), "neutral")


@lru_cache(maxsize=1)
def _load_model():
    """Return (tokenizer, model) or None if weights are unavailable."""
    import os

    if not os.path.isdir(settings.SENTIMENT_MODEL_PATH):
        return None  # no weights -> lexicon fallback, avoid heavy torch import
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(settings.SENTIMENT_MODEL_PATH)
        mdl = AutoModelForSequenceClassification.from_pretrained(settings.SENTIMENT_MODEL_PATH)
        mdl.eval()
        return tok, mdl
    except Exception:
        return None


def _lexicon_stars(text: str) -> int:
    words = {w.strip(".,!?").lower() for w in text.split()}
    score = len(words & _POS) - len(words & _NEG)
    if score >= 2:
        return 5
    if score == 1:
        return 4
    if score == 0:
        return 3
    if score == -1:
        return 2
    return 1


def score_batch(texts: list[str]) -> list[dict]:
    """Return [{'stars': int, 'label': str, 'model': str}, ...] for each text."""
    loaded = _load_model()
    if loaded is None:
        return [{"stars": (s := _lexicon_stars(t)), "label": _label(s), "model": "lexicon"} for t in texts]

    import torch
    tok, mdl = loaded
    enc = tok(texts, return_tensors="pt", truncation=True, padding=True, max_length=256)
    with torch.no_grad():
        logits = mdl(**enc).logits
    preds = torch.argmax(torch.softmax(logits, dim=1), dim=1).tolist()
    out = []
    for p in preds:
        stars = int(p) + 1
        out.append({"stars": stars, "label": _label(stars), "model": "distilbert"})
    return out


def score(text: str) -> dict:
    return score_batch([text])[0]


if __name__ == "__main__":
    for t in ["Fast shipping and great quality, love it!",
              "Terrible product, broke immediately and support ignored me."]:
        print(t, "->", score(t))
