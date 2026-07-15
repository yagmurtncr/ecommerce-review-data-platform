# Architecture

The platform ingests e-commerce reviews from **batch** and **streaming** sources,
lands them in a **Bronze → Silver → Gold** data lake, gates them with **data-quality
checks**, models them into a **PostgreSQL star schema**, enriches them with
**sentiment / topic / anomaly** models, and serves analytics through a **FastAPI +
Streamlit** layer. **Airflow** orchestrates the batch path; **Spark Structured
Streaming** handles the real-time path.

```mermaid
flowchart TB
    subgraph SRC["Sources"]
        CSV["CSV files"]
        API["Fake Review API"]
    end

    subgraph INGEST["Ingestion"]
        BATCH["batch_ingest"]
        STREAM["stream_producer"]
    end
    KAFKA(["Kafka · reviews.raw"])

    subgraph LAKE["Data Lake (MinIO / S3)"]
        BRONZE["🥉 Bronze — raw"]
        SILVER["🥈 Silver — clean & validated"]
        GOLD["🥇 Gold — marts"]
    end

    subgraph PROC["Processing (Spark)"]
        B2S["bronze to silver"]
        S2G["silver to gold"]
        SSTREAM["structured streaming<br/>sentiment"]
    end

    DQ{"Data-Quality Gate"}

    subgraph WH["Warehouse (PostgreSQL)"]
        STAR["⭐ star schema<br/>fact_reviews + dims"]
    end

    subgraph ML["Models"]
        SENT["Sentiment (DistilBERT)"]
        TOPIC["Topics (TF-IDF+KMeans)"]
        ANOM["Anomaly / fake-review"]
    end

    subgraph SERVE["Serving"]
        FASTAPI["FastAPI analytics API"]
        ES[("Elasticsearch<br/>vector search")]
        DASH["Streamlit dashboard"]
    end

    CSV --> BATCH --> BRONZE
    API --> STREAM --> KAFKA
    KAFKA --> SSTREAM --> ES
    BRONZE --> B2S --> SILVER
    SILVER --> DQ -->|pass| S2G --> GOLD
    GOLD --> STAR
    SILVER --> ML
    ML --> STAR
    STAR --> FASTAPI --> DASH
    ES --> FASTAPI
```

## Batch vs. streaming

| Path | Trigger | Tools | Output |
|------|---------|-------|--------|
| **Batch** | nightly (Airflow) | CSV → Bronze → Spark → DQ → Gold → Warehouse | star schema, Gold marts |
| **Streaming** | continuous | Kafka → Spark Structured Streaming → sentiment | `reviews.scored`, ES index |

## Medallion layers

- **Bronze** — raw, immutable, append-only, partitioned by ingest date (replayable)
- **Silver** — cleaned, de-duplicated, typed, validated; engineered features
  (`review_length`, `word_count`, `review_year/month`)
- **Gold** — aggregated marts (`daily_category_sentiment`, `product_summary`,
  `topic_distribution`) ready for BI and the warehouse

## Dimensional model (star schema)

`fact_reviews` (grain = one review) references conformed dimensions
`dim_product`, `dim_customer`, `dim_date`, `dim_category`. See
[`warehouse/ddl/star_schema.sql`](../warehouse/ddl/star_schema.sql).
