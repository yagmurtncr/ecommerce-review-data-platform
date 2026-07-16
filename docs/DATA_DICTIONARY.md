# Data Dictionary

Field-level reference for the review record as it flows through the platform.

## Raw / Bronze (`review`)

| Field | Type | Description |
|-------|------|-------------|
| `review_id` | string | Unique review identifier (primary key) |
| `product_id` | string | Product identifier |
| `product_name` | string | Human-readable product name |
| `category` | string | One of: Electronics, Home & Kitchen, Books, Fashion, Beauty |
| `customer_id` | string | Reviewer identifier |
| `rating` | int (1–5) | Star rating given by the customer |
| `review_text` | string | Free-text review body |
| `topic` | string | Seed topic (quality, shipping, price, packaging, customer_service, return) |
| `review_date` | date (ISO) | Date the review was posted |

## Silver (added by `spark/bronze_to_silver.py`)

| Field | Type | Description |
|-------|------|-------------|
| `review_length` | int | Character length of `review_text` |
| `word_count` | int | Number of tokens in `review_text` |
| `review_year` / `review_month` | int | Derived from `review_date` |

## Warehouse — `fact_reviews` (grain: one review)

| Field | Type | Description |
|-------|------|-------------|
| `review_id` | text (PK) | Review identifier |
| `product_id` | text (FK → dim_product) | Product |
| `customer_id` | text (FK → dim_customer) | Customer |
| `date_id` | int (FK → dim_date, yyyymmdd) | Review date |
| `category_id` | int (FK → dim_category) | Category |
| `rating` | smallint (1–5) | Customer rating |
| `sentiment_stars` | smallint (1–5) | Model-predicted sentiment |
| `sentiment_label` | text | positive / neutral / negative |
| `review_length` / `word_count` | int | Text features |
| `is_suspicious` | boolean | Flagged by anomaly / fake-review detection |

## Dimensions

- **`dim_product`** — `product_id` (PK), `product_name`, `category_id`
- **`dim_customer`** — `customer_id` (PK), `first_seen`, `review_count`
- **`dim_date`** — `date_id` (PK), `full_date`, `year`, `month`, `day`, `weekday`, `is_weekend`
- **`dim_category`** — `category_id` (PK), `category_name`

## Streaming (`reviews.scored` topic)

| Field | Type | Description |
|-------|------|-------------|
| `review_id` | string | Review identifier |
| `category` | string | Product category |
| `rating` | int | Customer rating |
| `sentiment_stars` | int | Model-predicted sentiment |
| `sentiment_label` | string | positive / neutral / negative |
