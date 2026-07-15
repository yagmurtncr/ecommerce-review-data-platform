"""Fake-review / anomaly detection.

Two complementary signals:

1. **Rating vs. sentiment mismatch** — e.g. 5 stars on clearly negative text.
2. **Near-duplicate spam** — the same review text posted by many customers.
3. **Statistical outliers** — IsolationForest over simple behavioural features
   (review length, word count, rating, duplicate-ness).

Run:  python -m ml.anomaly_detection --csv data/samples/reviews.csv
"""
from __future__ import annotations

import argparse

import pandas as pd

from ml.sentiment import score_batch


def detect(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["review_text"] = df["review_text"].astype(str)

    # 1) rating vs sentiment mismatch
    scored = score_batch(df["review_text"].tolist())
    df["sentiment_stars"] = [s["stars"] for s in scored]
    df["rating_sentiment_gap"] = (df["rating"] - df["sentiment_stars"]).abs()
    df["flag_mismatch"] = df["rating_sentiment_gap"] >= 3

    # 2) near-duplicate spam (same text used by >1 distinct customer)
    dup = (df.groupby("review_text")["customer_id"].nunique())
    df["text_customer_spread"] = df["review_text"].map(dup)
    df["flag_duplicate_spam"] = df["text_customer_spread"] >= 3

    # 3) IsolationForest over behavioural features
    from sklearn.ensemble import IsolationForest

    feats = df.assign(
        review_length=df["review_text"].str.len(),
        word_count=df["review_text"].str.split().str.len(),
    )[["rating", "review_length", "word_count", "rating_sentiment_gap", "text_customer_spread"]].fillna(0)
    iso = IsolationForest(contamination=0.05, random_state=42)
    df["flag_outlier"] = iso.fit_predict(feats) == -1

    df["is_suspicious"] = df[["flag_mismatch", "flag_duplicate_spam", "flag_outlier"]].any(axis=1)
    return df


def main():
    ap = argparse.ArgumentParser(description="Fake-review / anomaly detection")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    ap.add_argument("--out", default="data/samples/anomalies.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    result = detect(df)
    flagged = result[result["is_suspicious"]]
    flagged.to_csv(args.out, index=False)

    n = len(result)
    print(f"Scanned {n} reviews. Suspicious: {len(flagged)} ({len(flagged)/max(n,1):.1%})")
    print(f"  mismatch: {int(result['flag_mismatch'].sum())} | "
          f"duplicate-spam: {int(result['flag_duplicate_spam'].sum())} | "
          f"outlier: {int(result['flag_outlier'].sum())}")
    print(f"Wrote flagged rows -> {args.out}")


if __name__ == "__main__":
    main()
