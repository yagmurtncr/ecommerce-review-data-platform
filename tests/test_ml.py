import pandas as pd

from ml.anomaly_detection import detect
from ml.sentiment import score, score_batch


def test_sentiment_positive_vs_negative():
    pos = score("Fast shipping and great quality, love it!")
    neg = score("Terrible product, broke immediately and support ignored me.")
    assert pos["stars"] > neg["stars"]
    assert pos["label"] == "positive"
    assert neg["label"] == "negative"


def test_score_batch_shape():
    out = score_batch(["great", "poor cheap late"])
    assert len(out) == 2
    assert all({"stars", "label", "model"} <= set(o) for o in out)


def test_anomaly_flags_injected_mismatch():
    df = pd.DataFrame([
        # clean positive review, consistent rating
        {"review_id": "ok1", "product_id": "p1", "customer_id": "c1", "rating": 5,
         "review_text": "Amazing value, fast delivery and premium quality."},
        # 5 stars but clearly negative text -> mismatch
        {"review_id": "bad1", "product_id": "p1", "customer_id": "c2", "rating": 5,
         "review_text": "Terrible product, broke immediately and support ignored me."},
    ])
    res = detect(df)
    row = res[res["review_id"] == "bad1"].iloc[0]
    assert bool(row["flag_mismatch"]) is True
    assert bool(row["is_suspicious"]) is True
