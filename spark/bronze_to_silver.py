"""Spark batch job: Bronze (raw CSV) -> Silver (clean, validated Parquet).

Transformations
---------------
* drop rows with null ``review_id`` / ``review_text``
* trim + collapse whitespace, drop reviews shorter than 3 chars
* de-duplicate on ``review_id`` (keep first)
* cast & validate ``rating`` to 1..5 (out-of-range -> dropped)
* parse ``review_date`` and drop future dates
* derive features: ``review_length``, ``word_count``, ``review_year/month``

Run:  spark-submit spark/bronze_to_silver.py
"""
from __future__ import annotations

from pyspark.sql import functions as F
from pyspark.sql import types as T

from lake.lake_io import s3a
from spark._spark import build_spark

SCHEMA = T.StructType([
    T.StructField("review_id", T.StringType()),
    T.StructField("product_id", T.StringType()),
    T.StructField("product_name", T.StringType()),
    T.StructField("category", T.StringType()),
    T.StructField("customer_id", T.StringType()),
    T.StructField("rating", T.IntegerType()),
    T.StructField("review_text", T.StringType()),
    T.StructField("topic", T.StringType()),
    T.StructField("review_date", T.StringType()),
])


def main():
    spark = build_spark("bronze_to_silver")

    raw = (
        spark.read.option("header", True).schema(SCHEMA)
        .csv(s3a("bronze", "reviews"))
    )

    clean = (
        raw
        .filter(F.col("review_id").isNotNull() & F.col("review_text").isNotNull())
        .withColumn("review_text", F.trim(F.regexp_replace("review_text", r"\s+", " ")))
        .filter(F.length("review_text") >= 3)
        .filter(F.col("rating").between(1, 5))
        .withColumn("review_date", F.to_date("review_date"))
        .filter(F.col("review_date").isNotNull())
        .filter(F.col("review_date") <= F.current_date())
        .dropDuplicates(["review_id"])
        .withColumn("review_length", F.length("review_text"))
        .withColumn("word_count", F.size(F.split(F.col("review_text"), r"\s+")))
        .withColumn("review_year", F.year("review_date"))
        .withColumn("review_month", F.month("review_date"))
    )

    (clean.write.mode("overwrite").partitionBy("category")
        .parquet(s3a("silver", "reviews")))

    print(f"Silver written: {clean.count()} rows (from {raw.count()} raw)")
    spark.stop()


if __name__ == "__main__":
    main()
