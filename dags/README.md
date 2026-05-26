# Airflow DAGs

This directory contains orchestration pipelines for ingestion, processing, and dbt execution.

## DAG Inventory

| File | DAG ID | Schedule | Responsibility |
| --- | --- | --- | --- |
| `ingestion_dag.py` | `s3_to_snowflake_ingest` | `0 2 * * *` | Run ingestion and load/check raw data in local (DuckDB) or cloud (Snowflake) mode |
| `processing_dag.py` | `banking_processing_dag` | `0 3 * * *` | Run Spark Bronze/Silver processing and dbt orchestration handoff |
| `dbt_dag.py` | `dbt_datavault_dag` | `0 4 * * *` | Run dbt Data Vault model execution and validation |

## Runtime Notes

- DAG behavior changes by `DBT_TARGET` (`local`, `dev`, `prod`).
- Local mode uses MinIO + DuckDB.
- Non-local modes expect a valid Airflow Snowflake connection (`SNOWFLAKE_CONN_ID`, default `snowflake_default`).

## Local Operations

- Start stack: `make up`
- Open Airflow UI: `http://localhost:8080`
- Trigger a DAG manually from the UI or CLI in the webserver container.
