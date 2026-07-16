# dbt — warehouse transformations

Turns the raw star schema (loaded by `warehouse/load_to_warehouse.py`) into
tested analytics models on PostgreSQL.

```
models/
├── staging/
│   ├── _sources.yml       # warehouse tables as dbt sources + column tests
│   └── stg_reviews.sql    # fact joined to product/category/date dims (view)
└── marts/
    ├── mart_category_sentiment.sql   # sentiment & rating per category (table)
    ├── mart_daily_trends.sql         # daily volume + 7-day rolling rating (table)
    └── _marts.yml                    # model docs + schema tests
```

## Run

```bash
cp profiles.example.yml ~/.dbt/profiles.yml   # or set DBT_PROFILES_DIR
pip install dbt-postgres

dbt deps
dbt run       # build staging views + mart tables
dbt test      # not_null / unique / accepted_values / relationships
dbt docs generate && dbt docs serve
```

## Why it's here

Demonstrates **ELT with dbt** on top of a dimensional model: sources, staging,
marts, and **data tests as governance** (referential integrity, accepted value
sets, uniqueness) — the transformation layer a data team would own.
