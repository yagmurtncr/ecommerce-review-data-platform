"""Load reviews into the PostgreSQL star schema.

Creates the schema (if missing), enriches each review with sentiment + anomaly
flags, then upserts the conformed dimensions and the ``fact_reviews`` table.

Run:  python -m warehouse.load_to_warehouse --csv data/samples/reviews.csv
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from config.clients import pg_conn
from ml.anomaly_detection import detect

DDL_PATH = os.path.join(os.path.dirname(__file__), "ddl", "star_schema.sql")


def _date_id(d: pd.Timestamp) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def load(csv_path: str):
    df = pd.read_csv(csv_path)
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df = df.dropna(subset=["review_id", "review_date"])

    enriched = detect(df)                       # adds sentiment_stars, is_suspicious, ...
    enriched["review_length"] = enriched["review_text"].astype(str).str.len()
    enriched["word_count"] = enriched["review_text"].astype(str).str.split().str.len()
    from ml.sentiment import score_batch
    labels = [s["label"] for s in score_batch(enriched["review_text"].astype(str).tolist())]
    enriched["sentiment_label"] = labels

    conn = pg_conn()
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute(open(DDL_PATH, encoding="utf-8").read())

    # dim_date
    dates = enriched["review_date"].dt.normalize().drop_duplicates()
    for d in dates:
        cur.execute(
            """INSERT INTO dim_date(date_id, full_date, year, month, day, weekday, is_weekend)
               VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (date_id) DO NOTHING""",
            (_date_id(d), d.date(), d.year, d.month, d.day, d.weekday() + 1, d.weekday() >= 5),
        )

    # dim_category
    for cat in sorted(enriched["category"].dropna().unique()):
        cur.execute("INSERT INTO dim_category(category_name) VALUES (%s) ON CONFLICT (category_name) DO NOTHING", (cat,))
    cur.execute("SELECT category_name, category_id FROM dim_category")
    cat_id = dict(cur.fetchall())

    # dim_product
    prod = enriched[["product_id", "product_name", "category"]].drop_duplicates("product_id")
    for _, r in prod.iterrows():
        cur.execute(
            """INSERT INTO dim_product(product_id, product_name, category_id)
               VALUES (%s,%s,%s) ON CONFLICT (product_id) DO NOTHING""",
            (r["product_id"], r["product_name"], cat_id.get(r["category"])),
        )

    # dim_customer
    cust = enriched.groupby("customer_id").agg(first_seen=("review_date", "min"),
                                               review_count=("review_id", "count")).reset_index()
    for _, r in cust.iterrows():
        cur.execute(
            """INSERT INTO dim_customer(customer_id, first_seen, review_count)
               VALUES (%s,%s,%s)
               ON CONFLICT (customer_id) DO UPDATE SET review_count = EXCLUDED.review_count""",
            (r["customer_id"], r["first_seen"].date(), int(r["review_count"])),
        )

    # fact_reviews
    for _, r in enriched.iterrows():
        cur.execute(
            """INSERT INTO fact_reviews(review_id, product_id, customer_id, date_id, category_id,
                   rating, sentiment_stars, sentiment_label, review_length, word_count, is_suspicious)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (review_id) DO NOTHING""",
            (r["review_id"], r["product_id"], r["customer_id"], _date_id(r["review_date"]),
             cat_id.get(r["category"]), int(r["rating"]), int(r["sentiment_stars"]),
             r["sentiment_label"], int(r["review_length"]), int(r["word_count"]), bool(r["is_suspicious"])),
        )

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM fact_reviews")
    print(f"Loaded warehouse. fact_reviews rows: {cur.fetchone()[0]}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Load reviews into the PostgreSQL star schema")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    args = ap.parse_args()
    load(args.csv)
