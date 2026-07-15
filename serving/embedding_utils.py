"""CLS embeddings from the fine-tuned model, for Elasticsearch vector search.

Lazily loaded so importing this module never fails when the model weights are
absent (e.g. a fresh clone). ``get_embedding`` raises a clear error only if you
actually call it without a model available.
"""
from __future__ import annotations

import os
from functools import lru_cache

from config import settings

EMBED_DIM = 768


@lru_cache(maxsize=1)
def _load():
    import torch  # noqa: F401
    from transformers import AutoModel, AutoTokenizer

    if not os.path.isdir(settings.SENTIMENT_MODEL_PATH):
        raise RuntimeError(
            f"Model not found at {settings.SENTIMENT_MODEL_PATH}. "
            "Vector embeddings need the fine-tuned model; set SENTIMENT_MODEL_PATH."
        )
    tok = AutoTokenizer.from_pretrained(settings.SENTIMENT_MODEL_PATH)
    mdl = AutoModel.from_pretrained(settings.SENTIMENT_MODEL_PATH)
    mdl.eval()
    return tok, mdl


def get_embedding(text: str) -> list[float]:
    import torch

    tok, mdl = _load()
    inputs = tok(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        out = mdl(**inputs)
    return out.last_hidden_state[:, 0, :].squeeze().tolist()
