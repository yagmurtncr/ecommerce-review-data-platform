# E-Commerce Review Intelligence Platform — common tasks.

.PHONY: help up down seed batch stream dq topics anomalies api dashboard test

help:
	@echo "up         - start the full local stack (docker compose)"
	@echo "down       - stop the stack"
	@echo "seed       - generate a synthetic reviews CSV"
	@echo "batch      - run the batch pipeline (ingest -> DQ -> warehouse)"
	@echo "stream     - stream synthetic reviews into Kafka"
	@echo "dq         - run the data-quality suite"
	@echo "topics     - run TF-IDF topic analysis"
	@echo "anomalies  - run fake-review / anomaly detection"
	@echo "api        - run the analytics API locally"
	@echo "dashboard  - run the Streamlit dashboard locally"

up:
	docker compose up -d

down:
	docker compose down

seed:
	python -m ingestion.synthetic_reviews -n 5000 -o data/samples/reviews.csv

# End-to-end batch path (assumes the stack is up).
batch: seed
	python -m ingestion.batch_ingest --csv data/samples/reviews.csv
	python -m dq.checks --csv data/samples/reviews.csv
	python -m warehouse.load_to_warehouse --csv data/samples/reviews.csv

stream:
	python -m ingestion.stream_producer --rate 5

dq:
	python -m dq.checks --csv data/samples/reviews.csv

topics:
	python -m ml.topic_model --csv data/samples/reviews.csv --k 6

anomalies:
	python -m ml.anomaly_detection --csv data/samples/reviews.csv

api:
	uvicorn api.app:app --reload --port 8000

dashboard:
	streamlit run dashboard/streamlit_app.py

test:
	python -m dq.checks --csv data/samples/reviews.csv
