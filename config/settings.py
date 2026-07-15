"""Central, environment-driven configuration for the platform.

Every service reads its connection settings from here so nothing is hardcoded.
Defaults line up with the bundled ``docker-compose.yml`` for local development.
"""
from __future__ import annotations

import os


def _env(key: str, default: str) -> str:
    val = os.getenv(key)
    return val if val is not None and val != "" else default


# ── Kafka ───────────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP = _env("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC_REVIEWS = _env("KAFKA_TOPIC_REVIEWS", "reviews.raw")
KAFKA_TOPIC_SCORED = _env("KAFKA_TOPIC_SCORED", "reviews.scored")
KAFKA_GROUP_ID = _env("KAFKA_GROUP_ID", "review-platform")

# ── MinIO / S3 (data lake) ──────────────────────────────────────────────────
MINIO_ENDPOINT = _env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = _env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = _env("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = _env("MINIO_SECURE", "false").lower() == "true"
LAKE_BUCKET = _env("LAKE_BUCKET", "reviews-lake")
BRONZE_PREFIX = "bronze"
SILVER_PREFIX = "silver"
GOLD_PREFIX = "gold"

# ── PostgreSQL (analytical warehouse) ───────────────────────────────────────
PG_HOST = _env("PG_HOST", "localhost")
PG_PORT = int(_env("PG_PORT", "5432"))
PG_DB = _env("PG_DB", "reviews_dw")
PG_USER = _env("PG_USER", "dw")
PG_PASSWORD = _env("PG_PASSWORD", "dw")

def pg_dsn() -> str:
    return f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

def pg_jdbc() -> str:
    return f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

# ── MongoDB (document store for raw/scored reviews) ─────────────────────────
MONGO_HOST = _env("MONGO_HOST", "localhost")
MONGO_PORT = int(_env("MONGO_PORT", "27017"))
MONGO_USER = _env("MONGO_USERNAME", "mongoadmin")
MONGO_PASSWORD = _env("MONGO_PASSWORD", "secret")
MONGO_DB = _env("MONGO_DB_NAME", "reviews")

def mongo_uri() -> str:
    return (
        f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        f"{MONGO_DB}?authSource=admin"
    )

# ── Elasticsearch (search + serving) ────────────────────────────────────────
ES_URL = _env("ES_URL", "http://localhost:9200")
ES_INDEX_REVIEWS = _env("ES_INDEX_REVIEWS", "reviews")

# ── ML ──────────────────────────────────────────────────────────────────────
SENTIMENT_MODEL_PATH = _env("SENTIMENT_MODEL_PATH", "./final_model")
MLFLOW_TRACKING_URI = _env("MLFLOW_TRACKING_URI", "http://localhost:5000")
