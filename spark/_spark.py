"""Shared SparkSession builder wired for MinIO (S3A) access."""
from __future__ import annotations

from config import settings


def build_spark(app_name: str):
    from pyspark.sql import SparkSession

    endpoint = ("https://" if settings.MINIO_SECURE else "http://") + settings.MINIO_ENDPOINT
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.hadoop.fs.s3a.endpoint", endpoint)
        .config("spark.hadoop.fs.s3a.access.key", settings.MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", settings.MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(settings.MINIO_SECURE).lower())
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
