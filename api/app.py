"""Analytics API over the warehouse + live sentiment scoring.

Endpoints
---------
* ``GET  /health``                  — liveness
* ``POST /predict``                 — score sentiment for a piece of text
* ``GET  /analytics/overview``      — headline KPIs from the star schema
* ``GET  /analytics/by-category``   — sentiment/rating per category
* ``GET  /analytics/daily``         — daily review counts & avg rating
* ``GET  /analytics/suspicious``    — flagged (possible fake) reviews

Run:  uvicorn api.app:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ml.sentiment import score

app = FastAPI(title="E-Commerce Review Intelligence API", version="2.0.0")


class TextIn(BaseModel):
    text: str


def _query(sql: str, params=None):
    from config.clients import pg_conn

    conn = pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(body: TextIn):
    return {"text": body.text, **score(body.text)}


@app.get("/analytics/overview")
def overview():
    rows = _query(
        """SELECT COUNT(*)                                   AS total_reviews,
                  ROUND(AVG(rating)::numeric, 3)             AS avg_rating,
                  ROUND(AVG(sentiment_stars)::numeric, 3)    AS avg_sentiment,
                  SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END) AS suspicious_reviews
             FROM fact_reviews"""
    )
    return rows[0] if rows else {}


@app.get("/analytics/by-category")
def by_category():
    return _query(
        """SELECT c.category_name,
                  COUNT(*)                                AS reviews,
                  ROUND(AVG(f.rating)::numeric, 3)        AS avg_rating,
                  ROUND(AVG(f.sentiment_stars)::numeric,3) AS avg_sentiment
             FROM fact_reviews f
             JOIN dim_category c ON c.category_id = f.category_id
             GROUP BY c.category_name
             ORDER BY reviews DESC"""
    )


@app.get("/analytics/daily")
def daily():
    return _query(
        """SELECT d.full_date,
                  COUNT(*)                         AS reviews,
                  ROUND(AVG(f.rating)::numeric, 3) AS avg_rating
             FROM fact_reviews f
             JOIN dim_date d ON d.date_id = f.date_id
             GROUP BY d.full_date
             ORDER BY d.full_date"""
    )


@app.get("/analytics/suspicious")
def suspicious(limit: int = 50):
    return _query(
        """SELECT review_id, product_id, rating, sentiment_stars, sentiment_label
             FROM fact_reviews
             WHERE is_suspicious = TRUE
             LIMIT %s""",
        (limit,),
    )
