# Setup Guide

This guide reflects the current repository layout and local-first workflow.

For a high-level overview of the platform, see [architecture.md](architecture.md).

## Prerequisites

- Docker Desktop
- Python 3.11+
- `uv`
- Terraform 1.5+ (for cloud provisioning)
- Snowflake account (for `dev`/`prod` dbt targets)

## Install Python Dependencies

From repository root:

```bash
uv sync --frozen --group dev
```

## Start Local Platform

```bash
make up
```

Equivalent command:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

## Validate Services

- Airflow: `http://localhost:8080`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Spark Master UI: `http://localhost:8181`
- DuckDB UI: `http://localhost:4213`

## Run dbt Commands

```bash
uv run dbt deps --project-dir dbt --profiles-dir .
uv run dbt debug --project-dir dbt --profiles-dir .
uv run dbt run --project-dir dbt --profiles-dir .
uv run dbt test --project-dir dbt --profiles-dir .
```

Select target when needed:

```bash
export DBT_TARGET=local   # or dev / prod
```

## Trigger DAGs (Optional)

Use Airflow UI or run from container shell.

Important DAG IDs:

- `s3_to_snowflake_ingest`
- `banking_processing_dag`
- `dbt_datavault_dag`

## Terraform Environments (Cloud)

```bash
cd terraform/env/dev
terraform init
terraform plan
terraform apply
```

Repeat for `terraform/env/prod` with production controls.

## Troubleshooting

For container-level troubleshooting and DuckDB UI issues, see `docker/README.md`.
