import pandas as pd

from dq.checks import validate

SUITE = "dq/expectations.yaml"


def _clean_df():
    return pd.DataFrame([
        {"review_id": "r1", "category": "Books", "rating": 5,
         "review_text": "great book", "review_date": "2024-01-01"},
        {"review_id": "r2", "category": "Beauty", "rating": 3,
         "review_text": "it is ok", "review_date": "2024-02-01"},
    ])


def test_clean_data_passes():
    report = validate(_clean_df(), SUITE)
    assert report["success"] is True
    assert report["checks_passed"] == report["checks_total"]


def test_out_of_range_rating_fails():
    df = _clean_df()
    df.loc[0, "rating"] = 9            # invalid rating
    report = validate(df, SUITE)
    assert report["success"] is False
    failed = [r["name"] for r in report["results"] if not r["success"]]
    assert "rating_in_range" in failed


def test_duplicate_id_and_future_date_fail():
    df = _clean_df()
    df.loc[1, "review_id"] = "r1"                 # duplicate id
    df.loc[1, "review_date"] = "2999-01-01"       # future date
    report = validate(df, SUITE)
    failed = {r["name"] for r in report["results"] if not r["success"]}
    assert "review_id_unique" in failed
    assert "review_date_not_in_future" in failed


def test_unknown_category_fails():
    df = _clean_df()
    df.loc[0, "category"] = "Groceries"           # not in allowed set
    report = validate(df, SUITE)
    failed = {r["name"] for r in report["results"] if not r["success"]}
    assert "category_in_set" in failed
