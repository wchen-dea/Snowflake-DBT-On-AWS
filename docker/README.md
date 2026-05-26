# Docker Stack

This directory defines the local development stack and build images.

## Files

- `docker-compose.yml`: local multi-service platform
- `Dockerfile-airflow`: Airflow runtime image
- `Dockerfile-dbt`: dbt runner image
- `Dockerfile-spark`: Spark image for cloud-style jobs
- `Dockerfile-spark-local`: Spark local/compose image
- `Dockerfile-duckdb-ui`: DuckDB UI support image
- `duckdb_ui_server.py`: local DuckDB UI helper

## Core Local Services

- `minio` + `minio-init`
- `postgres`
- `spark-master` + `spark-worker`
- `dbt-runner`
- `duckdb-ui`
- `airflow-init`, `airflow-webserver`, `airflow-scheduler`

## Start and Stop

```bash
# Start local services
docker compose -f docker/docker-compose.yml up --build -d

# Stop local services
docker compose -f docker/docker-compose.yml down
```

Or use shortcuts:

```bash
# Start local services
make up

# Stop local services
make down
```

## Important Endpoints

- Airflow: `http://localhost:8080`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Spark Master UI: `http://localhost:8181`
- DuckDB UI: `http://localhost:4213`

## DuckDB UI Troubleshooting

```bash
# Check status
docker compose -f docker/docker-compose.yml ps duckdb-ui

# Inspect logs
docker compose -f docker/docker-compose.yml logs --tail=100 duckdb-ui

# Rebuild dbt + UI services
docker compose -f docker/docker-compose.yml up -d --build dbt-runner duckdb-ui
```

If schema or data appears stale, rebuild `dbt-runner` and `duckdb-ui` together.
