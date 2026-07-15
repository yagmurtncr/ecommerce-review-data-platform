"""Spark batch job: Silver -> Gold aggregated marts (Parquet).

Builds analytics-ready marts that back the dashboard, the API and the
warehouse loader:

* ``gold/daily_category_sentiment`` — reviews & avg rating per day/category
* ``gold/product_summary``          — per-product rating stats
* ``gold/topic_distribution``       — review counts per topic/category

Run:  spark-submit spark/silver_to_gold.py
"""
from __future__ import annotations

from pyspark.sql import functions as F

from lake.lake_io import s3a
from spark._spark import build_spark


def main():
    spark = build_spark("silver_to_gold")
    silver = spark.read.parquet(s3a("silver", "reviews"))

    daily = (
        silver.groupBy("review_date", "category")
        .agg(
            F.count("*").alias("review_count"),
            F.round(F.avg("rating"), 3).alias("avg_rating"),
            F.round(F.avg("review_length"), 1).alias("avg_review_length"),
        )
        .orderBy("review_date", "category")
    )
    daily.write.mode("overwrite").parquet(s3a("gold", "daily_category_sentiment"))

    product = (
        silver.groupBy("product_id", "product_name", "category")
        .agg(
            F.count("*").alias("review_count"),
            F.round(F.avg("rating"), 3).alias("avg_rating"),
            F.min("review_date").alias("first_review"),
            F.max("review_date").alias("last_review"),
        )
    )
    product.write.mode("overwrite").parquet(s3a("gold", "product_summary"))

    topics = (
        silver.groupBy("category", "topic")
        .agg(F.count("*").alias("review_count"), F.round(F.avg("rating"), 3).alias("avg_rating"))
    )
    topics.write.mode("overwrite").parquet(s3a("gold", "topic_distribution"))

    print("Gold marts written: daily_category_sentiment, product_summary, topic_distribution")
    spark.stop()


if __name__ == "__main__":
    main()
