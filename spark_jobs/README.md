# Spark Jobs

## Purpose

This directory contains PySpark jobs for ingestion and transformation stages.

## Design

- Reusable shared helpers in `utils/` and `spark_utils.py`
- Modular job separation (Bronze ingestion vs Silver transforms)
- Cloud-ready I/O patterns for S3-backed data movement
- Orchestration-ready design for Airflow and Kubernetes execution

## Notes

Outputs from Silver transformations are intended to feed downstream dbt Data Vault models.
