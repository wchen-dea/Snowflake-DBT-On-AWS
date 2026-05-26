"""
dbt Data Vault DAG
Runs dbt staging → vault → marts against the configured target.

Targets (set DBT_TARGET env var):
  local  — DuckDB + MinIO  (default, no cloud creds needed)
  dev    — Snowflake DEV
  prod   — Snowflake PROD
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"   # profiles.yml is copied here in the image
DBT_TARGET = os.getenv("DBT_TARGET", "local")
DBT_IMAGE = os.getenv("DBT_RUNNER_IMAGE", "docker-dbt-runner:latest")

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dbt_env = {
    "DBT_TARGET": DBT_TARGET,
    "DBT_DUCKDB_PATH": os.getenv("DBT_DUCKDB_PATH", "/opt/dbt/warehouse/banking_vault.duckdb"),
    "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "MINIO_ROOT_USER": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    "MINIO_ROOT_PASSWORD": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    # Pass Snowflake creds through only when present
    "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "SNOWFLAKE_USER": os.getenv("SNOWFLAKE_USER", ""),
    "SNOWFLAKE_PASSWORD": os.getenv("SNOWFLAKE_PASSWORD", ""),
}

dbt_bin = "/opt/dbt/.venv/bin/dbt"
dbt_prep = "mkdir -p /opt/dbt/warehouse && "

with DAG(
    dag_id="dbt_datavault_dag",
    default_args=default_args,
    description="Load Data Vault 2.0 models (staging → vault → marts)",
    schedule_interval="0 4 * * *",  # 4 AM daily, after ingestion at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["banking", "dbt", "datavault"],
    doc_md=__doc__,
) as dag:

    # Install/refresh dbt packages before each run
    dbt_deps = DockerOperator(
        task_id="dbt_deps",
        image=DBT_IMAGE,
        entrypoint=["/bin/sh", "-lc"],
        command=[f"{dbt_prep}{dbt_bin} deps --project-dir /opt/dbt/project --profiles-dir /opt/dbt/profiles --target {DBT_TARGET}"],
        docker_url="unix://var/run/docker.sock",
        network_mode="banking_platform_network",
        mount_tmp_dir=False,
        auto_remove=True,
        environment=dbt_env,
    )

    # Compile models (fast syntax check before materialising)
    dbt_compile = DockerOperator(
        task_id="dbt_compile",
        image=DBT_IMAGE,
        entrypoint=["/bin/sh", "-lc"],
        command=[f"{dbt_prep}{dbt_bin} compile --project-dir /opt/dbt/project --profiles-dir /opt/dbt/profiles --target {DBT_TARGET} --no-write-json"],
        docker_url="unix://var/run/docker.sock",
        network_mode="banking_platform_network",
        mount_tmp_dir=False,
        auto_remove=True,
        environment=dbt_env,
    )

    # Run all models: staging → hubs/links/satellites → marts
    dbt_run = DockerOperator(
        task_id="dbt_run",
        image=DBT_IMAGE,
        entrypoint=["/bin/sh", "-lc"],
        command=[f"{dbt_prep}{dbt_bin} run --project-dir /opt/dbt/project --profiles-dir /opt/dbt/profiles --target {DBT_TARGET} --no-write-json"],
        docker_url="unix://var/run/docker.sock",
        network_mode="banking_platform_network",
        mount_tmp_dir=False,
        auto_remove=True,
        environment=dbt_env,
    )

    # Run schema + data tests
    dbt_test = DockerOperator(
        task_id="dbt_test",
        image=DBT_IMAGE,
        entrypoint=["/bin/sh", "-lc"],
        command=[f"{dbt_prep}{dbt_bin} test --project-dir /opt/dbt/project --profiles-dir /opt/dbt/profiles --target {DBT_TARGET} --exclude source:* --no-write-json"],
        docker_url="unix://var/run/docker.sock",
        network_mode="banking_platform_network",
        mount_tmp_dir=False,
        auto_remove=True,
        environment=dbt_env,
    )

    dbt_deps >> dbt_compile >> dbt_run >> dbt_test
