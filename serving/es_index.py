"""Index scored reviews into Elasticsearch with dense-vector embeddings.

Powers semantic ("find similar reviews") search on top of the platform. The
index mapping stores the review text, rating, sentiment and a 768-dim cosine
``dense_vector`` embedding.

Run:  python -m serving.es_index --csv data/samples/reviews.csv
"""
from __future__ import annotations

import argparse

import pandas as pd

from config import settings
from config.clients import es_client
from ml.sentiment import score_batch
from serving.embedding_utils import EMBED_DIM, get_embedding

MAPPING = {
    "properties": {
        "review_id": {"type": "keyword"},
        "review_text": {"type": "text"},
        "category": {"type": "keyword"},
        "rating": {"type": "integer"},
        "sentiment_stars": {"type": "integer"},
        "sentiment_label": {"type": "keyword"},
        "embedding": {"type": "dense_vector", "dims": EMBED_DIM, "index": True, "similarity": "cosine"},
    }
}


def ensure_index(es):
    if not es.indices.exists(index=settings.ES_INDEX_REVIEWS):
        es.indices.create(index=settings.ES_INDEX_REVIEWS, mappings=MAPPING)
        print(f"created index {settings.ES_INDEX_REVIEWS}")


def index_csv(csv_path: str, embed: bool = True):
    es = es_client()
    ensure_index(es)
    df = pd.read_csv(csv_path)
    scored = score_batch(df["review_text"].astype(str).tolist())
    n = 0
    for (_, row), s in zip(df.iterrows(), scored):
        doc = {
            "review_id": row["review_id"],
            "review_text": row["review_text"],
            "category": row.get("category"),
            "rating": int(row["rating"]),
            "sentiment_stars": s["stars"],
            "sentiment_label": s["label"],
        }
        if embed:
            doc["embedding"] = get_embedding(str(row["review_text"]))
        es.index(index=settings.ES_INDEX_REVIEWS, id=row["review_id"], document=doc)
        n += 1
    es.indices.refresh(index=settings.ES_INDEX_REVIEWS)
    print(f"indexed {n} reviews into {settings.ES_INDEX_REVIEWS}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Index scored reviews into Elasticsearch")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    ap.add_argument("--no-embed", action="store_true", help="skip embeddings (no model needed)")
    args = ap.parse_args()
    index_csv(args.csv, embed=not args.no_embed)
