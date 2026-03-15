FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
      dbt-trino \
      openmetadata-ingestion==1.11.7 \
      cachetools \
      fastapi \
      uvicorn

COPY kube/components/fq/dbt /app/dbt
COPY docker/dbt-runner/run-dbt.sh /app/run-dbt.sh
COPY docker/dbt-runner/runner_api.py /app/runner_api.py

RUN chmod +x /app/run-dbt.sh

ENV DBT_PROJECT_DIR=/app/dbt
ENV DBT_PROFILES_DIR=/app/dbt

EXPOSE 8080

CMD ["uvicorn", "runner_api:app", "--host", "0.0.0.0", "--port", "8080"]
