# Snowflake-DBT-On-AWS

Banking data platform reference project using Airflow, Spark, dbt, Snowflake, Docker, and Terraform.

## Scope

- Orchestrate ingestion, processing, and dbt modeling with Airflow DAGs.
- Run local-first pipelines with Docker Compose (MinIO + Spark + Airflow + DuckDB + dbt + DuckDB UI).
- Support cloud targets with Snowflake (`dev` and `prod` dbt profiles).
- Keep infrastructure definitions in Terraform and Kubernetes manifests.

## Pipeline Flow

1. Raw banking sample data is stored under `spark_jobs/data/raw` and seeded to MinIO by `minio-init`.
2. Spark jobs process Bronze and Silver layers.
3. Airflow DAGs orchestrate ingestion (`s3_to_snowflake_ingest`) and processing (`banking_processing_dag`).
4. The `duckdb` service initializes and maintains the local DuckDB warehouse file in a shared volume.
5. dbt builds staging, vault, and marts models via `dbt_datavault_dag`, writing into the shared DuckDB warehouse.
6. `duckdb-ui` reads from the same warehouse volume for local data inspection.

## Repository Map

```text
.
|-- dags/                  # Airflow orchestration DAGs
|-- dbt/                   # dbt project (models, macros, packages)
|-- docker/                # Dockerfiles + docker-compose local stack
|-- docs/                  # Setup and documentation image guide
|-- infrastructure/        # K8S deployment specs and infra notes
|-- spark_jobs/            # PySpark jobs and sample raw data
|-- terraform/             # Terraform providers, vars, envs, modules
|-- Makefile               # Local stack convenience commands
|-- profiles.yml           # dbt profile targets (local/dev/prod)
`-- pyproject.toml         # Python dependencies and tooling
```

## Local Quick Start

### Prerequisites

- Docker Desktop
- Python 3.11+
- `uv` (recommended for local Python tooling)

### Start the platform

```bash
make up
```

Or with plain Docker Compose:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

### Access Local Services

- Airflow: `http://localhost:8080`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Spark Master UI: `http://localhost:8181`
- DuckDB UI: `http://localhost:4213`

### DuckDB Service Role

- Service name: `duckdb` (defined in `docker/docker-compose.yml`).
- Responsibility: initialize and keep the local warehouse file lifecycle managed inside Docker Compose.
- Shared storage: `dbt-warehouse-volume` is mounted by `duckdb`, `dbt-runner`, and `duckdb-ui`.
- Runtime dependency: `dbt-runner` and `duckdb-ui` wait for healthy `duckdb` before running.

### Run dbt from Repository Root

```bash
uv run dbt deps --project-dir dbt --profiles-dir .
uv run dbt run --project-dir dbt --profiles-dir .
uv run dbt test --project-dir dbt --profiles-dir .
```

## Cloud Deployment (Terraform)

Use environment entry points in `terraform/env`.

```bash
cd terraform/env/dev
terraform init
terraform plan
terraform apply
```

## Documentation Index

- `docs/SETUP.md`: setup details and runbook
- `docker/README.md`: container stack and DuckDB UI troubleshooting
- `dbt/README.md`: dbt model layout and run commands
- `dags/README.md`: DAG responsibilities and scheduling
- `spark_jobs/README.md`: Spark ingestion/transformation jobs
- `.github/workflows/README.md`: CI/CD workflow notes
- `CONTRIBUTING.md`: contribution process and validation commands
