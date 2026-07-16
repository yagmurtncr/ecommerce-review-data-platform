"""Spark Structured Streaming: score sentiment on the live review stream.

Reads ``reviews.raw`` from Kafka, applies the sentiment model per micro-batch,
and writes enriched records to ``reviews.scored`` (and optionally MongoDB).

The heavy transformer is loaded once per executor; a lexicon fallback keeps the
job runnable even when the fine-tuned model is not present.

Run:  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
          spark/streaming_sentiment.py
"""
from __future__ import annotations

from pyspark.sql import functions as F
from pyspark.sql import types as T

from config import settings
from ml.sentiment import score_batch
from spark._spark import build_spark

OUT_SCHEMA = T.StructType([
    T.StructField("review_id", T.StringType()),
    T.StructField("category", T.StringType()),
    T.StructField("rating", T.IntegerType()),
    T.StructField("sentiment_stars", T.IntegerType()),
    T.StructField("sentiment_label", T.StringType()),
])


def _score_partition(rows):
    rows = list(rows)
    if not rows:
        return iter([])
    texts = [r["review_text"] for r in rows]
    scored = score_batch(texts)
    out = []
    for r, s in zip(rows, scored, strict=False):
        out.append((r["review_id"], r.get("category"), r.get("rating"),
                    s["stars"], s["label"]))
    return iter(out)


def main():
    spark = build_spark("streaming_sentiment")
    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
        .option("subscribe", settings.KAFKA_TOPIC_REVIEWS)
        .option("startingOffsets", "latest")
        .load()
    )

    review_schema = T.StructType([
        T.StructField("review_id", T.StringType()),
        T.StructField("category", T.StringType()),
        T.StructField("rating", T.IntegerType()),
        T.StructField("review_text", T.StringType()),
    ])
    parsed = raw.select(F.from_json(F.col("value").cast("string"), review_schema).alias("r")).select("r.*")

    def process(batch_df, batch_id):
        scored = (
            batch_df.rdd.mapPartitions(_score_partition)
            .toDF(["review_id", "category", "rating", "sentiment_stars", "sentiment_label"])
        )
        (scored.selectExpr(
            "review_id as key",
            "to_json(struct(*)) as value")
         .write.format("kafka")
         .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP)
         .option("topic", settings.KAFKA_TOPIC_SCORED)
         .save())

    (parsed.writeStream
        .foreachBatch(process)
        .option("checkpointLocation", "/tmp/ckpt/streaming_sentiment")
        .start()
        .awaitTermination())


if __name__ == "__main__":
    main()
