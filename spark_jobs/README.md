# Spark Jobs

PySpark workloads for ingestion and transformation stages.

For a high-level architecture diagram and component map, see [../docs/architecture.md](../docs/architecture.md).

## Files

- `bronze_ingestion.py`: ingest raw source data into Bronze layer outputs
- `silver_transform.py`: transform Bronze data into Silver-ready structures
- `utils/spark_utils.py`: shared Spark utility helpers
- `data/raw/`: local sample CSV seed data

## Execution Context

- Local mode runs against Spark standalone in Docker Compose.
- Storage interfaces use S3-compatible paths (MinIO local, AWS S3 cloud).
- Jobs are typically launched by Airflow DAGs in `dags/`.

## Operational Notes

- Keep Spark configs and package compatibility aligned with Dockerfiles.
- Any schema changes in Spark outputs should be coordinated with dbt staging models.
