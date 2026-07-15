"""Batch ingestion: land a CSV of reviews into the Bronze lake layer as-is.

Bronze = raw, immutable, append-only. No cleaning happens here on purpose; we
keep an exact copy of what arrived so the pipeline is fully replayable.

Run:  python -m ingestion.batch_ingest --csv data/samples/reviews.csv
"""
from __future__ import annotations

import argparse
import io
from datetime import datetime, timezone

from config import settings
from config.clients import minio_client


def ingest_csv(csv_path: str) -> str:
    with open(csv_path, "rb") as f:
        payload = f.read()

    # partition bronze by ingestion date for replayability
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    object_name = f"{settings.BRONZE_PREFIX}/reviews/ingest_date={day}/reviews_{ts}.csv"

    client = minio_client()
    client.put_object(
        settings.LAKE_BUCKET,
        object_name,
        data=io.BytesIO(payload),
        length=len(payload),
        content_type="text/csv",
    )
    print(f"Landed {csv_path} -> s3://{settings.LAKE_BUCKET}/{object_name} ({len(payload)} bytes)")
    return object_name


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Batch-ingest a review CSV into Bronze")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    args = ap.parse_args()
    ingest_csv(args.csv)
