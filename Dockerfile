FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 / pyarrow wheels are already bundled; keep image lean.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8501

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
