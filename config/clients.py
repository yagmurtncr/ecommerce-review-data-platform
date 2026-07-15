"""Thin client factories for the platform's backing services.

Keeping construction in one place means the rest of the codebase never worries
about connection strings or credentials.
"""
from __future__ import annotations

import json

from config import settings


# ── Kafka ───────────────────────────────────────────────────────────────────
def kafka_producer():
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
        acks="all",
        retries=3,
    )


def kafka_consumer(topic: str, group_id: str | None = None):
    from kafka import KafkaConsumer

    return KafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP,
        group_id=group_id or settings.KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )


# ── MinIO ───────────────────────────────────────────────────────────────────
def minio_client():
    from minio import Minio

    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    if not client.bucket_exists(settings.LAKE_BUCKET):
        client.make_bucket(settings.LAKE_BUCKET)
    return client


# ── PostgreSQL ──────────────────────────────────────────────────────────────
def pg_conn():
    import psycopg2

    return psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        dbname=settings.PG_DB,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD,
    )


# ── MongoDB ─────────────────────────────────────────────────────────────────
def mongo_db():
    from pymongo import MongoClient

    return MongoClient(settings.mongo_uri())[settings.MONGO_DB]


# ── Elasticsearch ───────────────────────────────────────────────────────────
def es_client():
    from elasticsearch import Elasticsearch

    return Elasticsearch(settings.ES_URL)
