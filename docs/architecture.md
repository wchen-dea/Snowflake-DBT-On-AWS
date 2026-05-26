# Project Architecture

This document provides a high-level overview of the Snowflake-DBT-On-AWS platform architecture, including core components, data flow, and deployment topology.

## Architecture Diagram

> **Diagram:**
>
> ![Platform Architecture](docs/images/architecture_diagram.png)
>
> *(If viewing locally, see `docs/images/architecture_diagram.png`. If not present, use the Mermaid diagram below as a reference.)*

```mermaid
graph TD
    A[Source Data (CSV, API)] --> B[MinIO (S3-compatible)]
    B --> C[Spark (Bronze/Silver)]
    C --> D[DuckDB (Warehouse)]
    D --> E[dbt-runner]
    E --> D
    D --> F[DuckDB UI]
    E --> G[Airflow]
    G --> C
    G --> E
    G --> D
    G --> B
    subgraph Docker Compose
      B
      C
      D
      E
      F
      G
    end
```

## Core Components

- **MinIO**: S3-compatible object storage for raw and processed data (Bronze/Silver/Gold layers).
- **Spark**: Handles large-scale data ingestion and transformation (Bronze/Silver processing).
- **DuckDB**: Local analytical database for warehouse storage (used in local/dev mode).
- **dbt-runner**: Executes dbt models, writing results to DuckDB.
- **DuckDB UI**: Web-based UI for querying and inspecting the DuckDB warehouse.
- **Airflow**: Orchestrates all ETL/ELT workflows and dependencies.
- **Postgres**: Metadata database for Airflow.
- **Terraform/K8S**: Infrastructure as code and cloud deployment (for prod/Snowflake targets).

## Data Flow

1. **Ingestion**: Source data (CSV, API) is loaded into MinIO (Bronze layer).
2. **Processing**: Spark jobs transform Bronze data to Silver, writing back to MinIO.
3. **Warehouse**: dbt-runner reads from MinIO/Silver and writes models to DuckDB (local) or Snowflake (cloud).
4. **Orchestration**: Airflow DAGs coordinate all steps, triggering Spark, dbt, and data quality checks.
5. **Exploration**: DuckDB UI provides a web interface for analysts to query the warehouse.

## Deployment Topology

- All core services run as containers in Docker Compose for local development.
- In production, Spark, Airflow, and dbt can be deployed on Kubernetes, with Snowflake as the warehouse.

---

For more details, see:
- [README.md](../README.md)
- [docker/README.md](../docker/README.md)
- [dbt/README.md](../dbt/README.md)
- [dags/README.md](../dags/README.md)
