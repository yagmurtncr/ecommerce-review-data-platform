-- ─────────────────────────────────────────────────────────────────────────
-- Analytical warehouse: star schema for e-commerce reviews
-- One fact table (grain = one review) + conformed dimensions.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_date (
    date_id     INTEGER PRIMARY KEY,          -- yyyymmdd
    full_date   DATE    NOT NULL,
    year        SMALLINT NOT NULL,
    month       SMALLINT NOT NULL,
    day         SMALLINT NOT NULL,
    weekday     SMALLINT NOT NULL,            -- 1=Mon .. 7=Sun
    is_weekend  BOOLEAN  NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_id   SERIAL PRIMARY KEY,
    category_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category_id   INTEGER REFERENCES dim_category(category_id)
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id   TEXT PRIMARY KEY,
    first_seen    DATE,
    review_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fact_reviews (
    review_id        TEXT PRIMARY KEY,
    product_id       TEXT     REFERENCES dim_product(product_id),
    customer_id      TEXT     REFERENCES dim_customer(customer_id),
    date_id          INTEGER  REFERENCES dim_date(date_id),
    category_id      INTEGER  REFERENCES dim_category(category_id),
    rating           SMALLINT CHECK (rating BETWEEN 1 AND 5),
    sentiment_stars  SMALLINT CHECK (sentiment_stars BETWEEN 1 AND 5),
    sentiment_label  TEXT,
    review_length    INTEGER,
    word_count       INTEGER,
    is_suspicious    BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_fact_reviews_date     ON fact_reviews(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_reviews_category ON fact_reviews(category_id);
CREATE INDEX IF NOT EXISTS idx_fact_reviews_product  ON fact_reviews(product_id);
