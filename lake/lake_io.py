"""Helpers for the Bronze / Silver / Gold data-lake layers on MinIO (S3).

Layer contract
--------------
* **bronze/** — raw, immutable, exactly as ingested (CSV/JSON)
* **silver/** — cleaned, validated, de-duplicated, typed (Parquet)
* **gold/**   — aggregated, model-ready & warehouse-ready marts (Parquet)

Spark reads/writes via ``s3a://`` paths (see :func:`s3a`). Light consumers
(API, dashboard) can read Gold Parquet directly with :func:`read_gold`.
"""
from __future__ import annotations

import pandas as pd

from config import settings

LAYER_PREFIX = {
    "bronze": settings.BRONZE_PREFIX,
    "silver": settings.SILVER_PREFIX,
    "gold": settings.GOLD_PREFIX,
}


def s3a(layer: str, *parts: str) -> str:
    """Build an ``s3a://`` path Spark can read/write for a lake layer."""
    prefix = LAYER_PREFIX[layer]
    tail = "/".join(p.strip("/") for p in parts)
    return f"s3a://{settings.LAKE_BUCKET}/{prefix}/{tail}".rstrip("/")


def _storage_options() -> dict:
    return {
        "key": settings.MINIO_ACCESS_KEY,
        "secret": settings.MINIO_SECRET_KEY,
        "client_kwargs": {"endpoint_url": ("https://" if settings.MINIO_SECURE else "http://") + settings.MINIO_ENDPOINT},
    }


def read_gold(name: str) -> pd.DataFrame:
    """Read a Gold Parquet mart into pandas (used by the API / dashboard)."""
    path = f"s3://{settings.LAKE_BUCKET}/{settings.GOLD_PREFIX}/{name}"
    return pd.read_parquet(path, storage_options=_storage_options())


def write_gold(df: pd.DataFrame, name: str) -> str:
    path = f"s3://{settings.LAKE_BUCKET}/{settings.GOLD_PREFIX}/{name}"
    df.to_parquet(path, index=False, storage_options=_storage_options())
    return path
