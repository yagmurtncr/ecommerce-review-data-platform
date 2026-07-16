from ingestion.synthetic_reviews import generate

REQUIRED = {"review_id", "product_id", "product_name", "category",
            "customer_id", "rating", "review_text", "topic", "review_date"}


def test_row_count_includes_anomalies():
    rows = generate(1000, seed=1, anomaly_rate=0.03)
    # base rows + injected anomalies
    assert 1000 < len(rows) <= 1000 + int(1000 * 0.03) + 1


def test_schema_and_rating_range():
    rows = generate(300, seed=2)
    for r in rows:
        assert REQUIRED <= set(r)
        assert 1 <= r["rating"] <= 5
        assert len(r["review_text"]) >= 3


def test_deterministic_given_seed():
    a = generate(200, seed=7)
    b = generate(200, seed=7)
    assert [r["review_id"] for r in a] == [r["review_id"] for r in b]
    assert [r["review_text"] for r in a] == [r["review_text"] for r in b]


def test_text_is_reasonably_diverse():
    rows = generate(1500, seed=3)
    texts = [r["review_text"] for r in rows]
    # legitimate reviews should be mostly unique (spam is the exception)
    assert len(set(texts)) / len(texts) > 0.7
