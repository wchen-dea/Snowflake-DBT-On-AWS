# Project Architecture

This document provides a high-level overview of the Snowflake-DBT-On-AWS platform architecture, including core components, data flow, and deployment topology.

## Architecture Diagram

```mermaid
flowchart TD
    SourceData --> MinIO
    MinIO --> Spark
    Spark --> DuckDB
    DuckDB --> dbtRunner
    dbtRunner --> DuckDB
    DuckDB --> DuckDBUI
    dbtRunner --> Airflow
    Airflow --> Spark
    Airflow --> dbtRunner
    Airflow --> DuckDB
    Airflow --> MinIO
    subgraph DockerCompose
      MinIO
      Spark
      DuckDB
      dbtRunner
      DuckDBUI
      Airflow
    end
    SourceData["Source Data (CSV, API)"]
    MinIO["MinIO (S3-compatible)"]
    Spark["Spark (Bronze/Silver)"]
    DuckDB["DuckDB (Warehouse)"]
    dbtRunner["dbt-runner"]
    DuckDBUI["DuckDB UI"]
    Airflow["Airflow"]
```

## Component Diagram

This diagram shows the main platform components and their relationships.

```mermaid
flowchart LR
    subgraph Storage
      MinIO["MinIO (S3-compatible)"]
      DuckDB["DuckDB (Warehouse)"]
      Snowflake["Snowflake (Cloud Warehouse)"]
    end
    subgraph Compute
      Spark["Spark"]
      dbtRunner["dbt-runner"]
    end
    subgraph Orchestration
      Airflow["Airflow"]
    end
    subgraph UI
      DuckDBUI["DuckDB UI"]
    end
    subgraph Infra
      Terraform["Terraform"]
      K8S["Kubernetes"]
    end
    SourceData["Source Data (CSV, API)"]
    Postgres["Postgres (Airflow Metadata)"]

    SourceData --> MinIO
    MinIO <--> Spark
    Spark <--> DuckDB
    Spark <--> MinIO
    dbtRunner <--> DuckDB
    dbtRunner <--> Snowflake
    dbtRunner <--> MinIO
    dbtRunner <--> Spark
    DuckDBUI <--> DuckDB
    Airflow <--> Spark
    Airflow <--> dbtRunner
    Airflow <--> DuckDB
    Airflow <--> MinIO
    Airflow <--> Postgres
    Terraform --> K8S
    K8S --> Airflow
    K8S --> Spark
    K8S --> dbtRunner
    K8S --> MinIO
    K8S --> DuckDB
    K8S --> DuckDBUI
```

## Data Flow Diagram

This diagram illustrates the step-by-step movement of data through the platform.

```mermaid
flowchart TD
    A["Source Data (CSV, API)"] --> B["MinIO (Bronze)"]
    B --> C["Spark (Bronze->Silver)"]
    C --> D["MinIO (Silver)"]
    D --> E["dbt-runner (Staging/Vault/Marts)"]
    E --> F["DuckDB (Warehouse)"]
    F --> G["DuckDB UI"]
    E --> H["Snowflake (Cloud, prod/dev)"]
    subgraph Orchestration
      Airflow
    end
    Airflow --> B
    Airflow --> C
    Airflow --> E
    Airflow --> F
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
