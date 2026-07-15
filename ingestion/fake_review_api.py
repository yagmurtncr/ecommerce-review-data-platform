"""A tiny 'source' API that serves synthetic reviews.

Stands in for a third-party review feed. The stream producer polls this API (or
generates directly) to simulate reviews arriving continuously.

Run:  uvicorn ingestion.fake_review_api:app --port 8010
"""
from __future__ import annotations

from fastapi import FastAPI, Query

from ingestion.synthetic_reviews import generate

app = FastAPI(title="Fake Review Source API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reviews")
def reviews(n: int = Query(20, ge=1, le=1000), seed: int = 0):
    """Return a batch of freshly generated synthetic reviews."""
    return {"count": n, "items": generate(n, seed=seed)}
