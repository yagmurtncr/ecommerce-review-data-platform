"""Airflow DAG: nightly batch pipeline for the review platform.

    generate_reviews → batch_ingest(Bronze)
                          → bronze_to_silver(Spark)
                             → data_quality_gate
                                → silver_to_gold(Spark)
                                   → load_warehouse(PostgreSQL star schema)

The stream side (Kafka producer + Spark structured streaming) runs continuously
and is deployed separately from this batch DAG.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

default_args = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="reviews_batch_pipeline",
    description="Bronze→Silver→(DQ gate)→Gold→Warehouse for e-commerce reviews",
    default_args=default_args,
    schedule="0 2 * * *",          # nightly at 02:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["reviews", "batch", "data-engineering"],
) as dag:

    generate = BashOperator(
        task_id="generate_reviews",
        bash_command="python -m ingestion.synthetic_reviews -n 5000 -o data/samples/reviews.csv",
    )

    ingest = BashOperator(
        task_id="batch_ingest_bronze",
        bash_command="python -m ingestion.batch_ingest --csv data/samples/reviews.csv",
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command="spark-submit spark/bronze_to_silver.py",
    )

    dq_gate = BashOperator(
        task_id="data_quality_gate",
        bash_command="python -m dq.checks --csv data/samples/reviews.csv",  # non-zero exit fails the DAG
    )

    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command="spark-submit spark/silver_to_gold.py",
    )

    load_warehouse = BashOperator(
        task_id="load_warehouse",
        bash_command="python -m warehouse.load_to_warehouse --csv data/samples/reviews.csv",
    )

    generate >> ingest >> bronze_to_silver >> dq_gate >> silver_to_gold >> load_warehouse
