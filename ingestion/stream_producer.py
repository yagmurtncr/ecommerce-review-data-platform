"""Stream ingestion: push synthetic reviews into Kafka continuously.

Simulates a real-time feed of customer reviews. The Spark structured-streaming
job (``spark/streaming_sentiment.py``) consumes this topic, scores sentiment and
writes results back to ``reviews.scored``.

Run:  python -m ingestion.stream_producer --rate 5
"""
from __future__ import annotations

import argparse
import time

from config import settings
from config.clients import kafka_producer
from ingestion.synthetic_reviews import generate


def run(rate_per_sec: float, total: int | None, seed: int = 0):
    producer = kafka_producer()
    sent = 0
    batch_seed = seed
    try:
        while total is None or sent < total:
            for review in generate(max(1, int(rate_per_sec)), seed=batch_seed):
                producer.send(settings.KAFKA_TOPIC_REVIEWS, key=review["review_id"], value=review)
                sent += 1
            producer.flush()
            batch_seed += 1
            if sent % 50 == 0:
                print(f"produced {sent} reviews -> {settings.KAFKA_TOPIC_REVIEWS}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print(f"\nstopped. total produced: {sent}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Stream synthetic reviews into Kafka")
    ap.add_argument("--rate", type=float, default=5, help="reviews per second")
    ap.add_argument("--total", type=int, default=None, help="stop after N (default: run forever)")
    args = ap.parse_args()
    run(args.rate, args.total)
