"""
Banking Processing DAG
Orchestrates the full medallion pipeline: Bronze (Spark) → Silver (Spark) → Gold (dbt marts).

Targets (set DBT_TARGET env var):
  local  — Spark standalone (spark://spark-master:7077) + DuckDB/MinIO  (default)
  dev    — Spark on K8s + Snowflake DEV
  prod   — Spark on K8s + Snowflake PROD
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dbt"
DBT_TARGET = os.getenv("DBT_TARGET", "local")
DBT_IMAGE = os.getenv("DBT_RUNNER_IMAGE", "docker-dbt-runner:latest")
SPARK_MASTER = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
SPARK_S3A_PACKAGES = os.getenv(
    "SPARK_S3A_PACKAGES",
    "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
)

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

# Common Spark env — S3 reads/writes go to MinIO in local mode
spark_conf = {
    "spark.master": SPARK_MASTER,
    "spark.jars.packages": SPARK_S3A_PACKAGES,
    "spark.hadoop.fs.s3a.endpoint": os.getenv("AWS_ENDPOINT_URL_S3", "http://minio:9000"),
    "spark.hadoop.fs.s3a.access.key": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    "spark.hadoop.fs.s3a.secret.key": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    "spark.hadoop.fs.s3a.path.style.access": "true",
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
    "spark.sql.adaptive.enabled": "true",
}

dbt_env = {
    "DBT_TARGET": DBT_TARGET,
    "DBT_DUCKDB_PATH": os.getenv("DBT_DUCKDB_PATH", "/opt/dbt/warehouse/banking_vault.duckdb"),
    "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "MINIO_ROOT_USER": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
    "MINIO_ROOT_PASSWORD": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
    "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "SNOWFLAKE_USER": os.getenv("SNOWFLAKE_USER", ""),
    "SNOWFLAKE_PASSWORD": os.getenv("SNOWFLAKE_PASSWORD", ""),
}

dbt_bin = "/opt/dbt/.venv/bin/dbt"
dbt_prep = "mkdir -p /opt/dbt/warehouse && "

with DAG(
    dag_id="banking_processing_dag",
    default_args=default_args,
    description="Full medallion pipeline: Bronze → Silver (Spark) + Gold (dbt)",
    schedule_interval="0 3 * * *",  # 3 AM daily, after ingestion at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=2,  # Increased from 1
    tags=["banking", "spark", "dbt", "processing"],
    doc_md=__doc__,
) as dag:

    # ── Bronze layer: raw CSV → Parquet in MinIO/S3 ────────
    bronze_ingest = SparkSubmitOperator(
        task_id="bronze_ingestion",
        application="/opt/airflow/spark_jobs/bronze_ingestion.py",
        conn_id="spark_default",
        name="banking_bronze_{{ ds }}",
        conf=spark_conf,
        verbose=False,
    )

    # ── Silver layer: clean + dedupe Bronze data ───────────
    silver_transform = SparkSubmitOperator(
        task_id="silver_transform",
        application="/opt/airflow/spark_jobs/silver_transform.py",
        conn_id="spark_default",
        name="banking_silver_{{ ds }}",
        conf=spark_conf,
        verbose=False,
    )

    # ── Gold layer: dbt Data Vault + marts ─────────────────
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

    bronze_ingest >> silver_transform >> dbt_run >> dbt_test
