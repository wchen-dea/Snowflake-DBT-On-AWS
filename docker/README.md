# Docker Stack

## Purpose

This directory contains container definitions for local development and deployment packaging.

## Highlights

- Containerized deployment path aligned with Kubernetes workloads
- Reproducible runtime for Airflow, Spark, and dbt
- Pre-installed connectors for Snowflake, S3, pandas, and PySpark
- Bind-mounted project integration for DAGs and Spark jobs in local development
- Minimal dependency footprint for a lighter, safer image baseline

## DuckDB Local UI

Use the official DuckDB Local UI service to inspect the local warehouse file used by dbt.

### Startup

1. Build and start the UI service:

```bash
docker compose -f docker/docker-compose.yml up -d --build duckdb-ui
```

2. Open the UI:

```text
http://localhost:4213
```

3. Check service status:

```bash
docker compose -f docker/docker-compose.yml ps duckdb-ui
```

### Troubleshooting

1. Inspect UI logs:

```bash
docker compose -f docker/docker-compose.yml logs --tail=100 duckdb-ui
```

Look for a line like `UI started at http://localhost:4213/`.

2. Recreate both dbt warehouse producer and UI (if schema/file changed):

```bash
docker compose -f docker/docker-compose.yml up -d --build dbt-runner duckdb-ui
```

3. Verify port mapping:

```bash
docker compose -f docker/docker-compose.yml ps duckdb-ui
```

Expected port mapping includes `0.0.0.0:4213->54213/tcp`.

4. If port 4213 is already in use, stop conflicting process or remap host port in `docker/docker-compose.yml` under `duckdb-ui.ports`.
