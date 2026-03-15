FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
      dbt-trino \
      openmetadata-ingestion==1.11.7 \
      collate-dbt-artifacts-parser \
      cachetools \
      fastapi \
      python-multipart \
      uvicorn

COPY kube/components/fq/dbt /app/dbt
COPY docker/gex/run-dbt.sh /app/run-dbt.sh
COPY docker/gex/app.py /app/app.py
COPY docker/gex/src /app/src

RUN chmod +x /app/run-dbt.sh

ENV DBT_PROJECT_DIR=/app/dbt
ENV DBT_PROFILES_DIR=/app/dbt
ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
