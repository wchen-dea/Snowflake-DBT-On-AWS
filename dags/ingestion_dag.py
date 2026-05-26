"""
S3 to Snowflake Ingestion DAG
Ingests raw banking data from S3 to Snowflake RAW layer
"""
import os
import time
from datetime import datetime, timedelta
from airflow import DAG
from airflow.exceptions import AirflowException, AirflowNotFoundException
from airflow.hooks.base import BaseHook
from airflow.providers.snowflake.transfers.copy_into_snowflake import CopyFromExternalStageToSnowflakeOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

SPARK_MASTER = os.getenv('SPARK_MASTER_URL', 'spark://spark-master:7077')
SNOWFLAKE_CONN_ID = os.getenv('SNOWFLAKE_CONN_ID', 'snowflake_default')
DBT_TARGET = os.getenv('DBT_TARGET', 'local')
IS_LOCAL = DBT_TARGET == 'local'
DUCKDB_PATH = os.getenv('DBT_DUCKDB_PATH', '/opt/dbt/warehouse/banking_vault.duckdb')
S3_ENDPOINT = os.getenv('AWS_ENDPOINT_URL_S3', f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}")
S3_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', os.getenv('MINIO_ROOT_USER', 'minioadmin'))
S3_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'))
SPARK_S3A_PACKAGES = os.getenv(
    'SPARK_S3A_PACKAGES',
    'org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262',
)

with DAG(
    dag_id='s3_to_snowflake_ingest',
    default_args=default_args,
    description='Batch ingestion from S3 to Snowflake',
    schedule_interval='0 2 * * *',  # 2 AM daily
    catchup=False,
    max_active_runs=5,  # Allow new runs while older backfilled runs drain
    tags=['ingestion', 'banking', 's3', 'snowflake'],
    doc_md=__doc__,
) as dag:

    def _duckdb_connection(read_only: bool = False, max_lock_retries: int = 5):
        import duckdb

        endpoint = S3_ENDPOINT.replace('http://', '').replace('https://', '')
        use_ssl = S3_ENDPOINT.startswith('https://')

        for attempt in range(max_lock_retries + 1):
            try:
                con = duckdb.connect(DUCKDB_PATH, read_only=read_only)
                try:
                    con.execute("LOAD httpfs;")
                except Exception:
                    con.execute("INSTALL httpfs;")
                    con.execute("LOAD httpfs;")
                con.execute(f"SET s3_endpoint='{endpoint}';")
                con.execute(f"SET s3_access_key_id='{S3_ACCESS_KEY}';")
                con.execute(f"SET s3_secret_access_key='{S3_SECRET_KEY}';")
                con.execute("SET s3_url_style='path';")
                con.execute(f"SET s3_use_ssl={'true' if use_ssl else 'false'};")
                return con
            except Exception as exc:
                is_lock_error = 'Could not set lock on file' in str(exc) or 'Conflicting lock is held' in str(exc)
                if is_lock_error and attempt < max_lock_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if is_lock_error:
                    mode = 'read-only' if read_only else 'read-write'
                    raise AirflowException(
                        f"DuckDB file lock conflict for {DUCKDB_PATH} using {mode} mode. "
                        "Retry later or stop concurrent DuckDB clients (for example duckdb-ui) during ingestion checks."
                    ) from exc
                raise

        raise AirflowException(f"Failed to connect to DuckDB at {DUCKDB_PATH}")

    def load_raw_to_duckdb(table_name: str, s3_path: str):
        con = _duckdb_connection(read_only=False)
        try:
            con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            con.execute(
                f"CREATE OR REPLACE TABLE raw.{table_name} AS "
                f"SELECT * FROM read_csv_auto('{s3_path}', HEADER=TRUE);"
            )
        finally:
            con.close()

    def check_duckdb_row_count(table_name: str):
        con = _duckdb_connection(read_only=True)
        try:
            row_count = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
            if row_count <= 0:
                raise AirflowException(f"DuckDB raw.{table_name} is empty")
        finally:
            con.close()

    def validate_snowflake_connection():
        """Fail fast with a clear message if Snowflake connection is missing."""
        try:
            BaseHook.get_connection(SNOWFLAKE_CONN_ID)
        except AirflowNotFoundException as exc:
            raise AirflowException(
                f"Snowflake connection '{SNOWFLAKE_CONN_ID}' is not configured. "
                "Create the Airflow connection or set SNOWFLAKE_CONN_ID to a valid conn_id."
            ) from exc

    validate_snowflake_conn = None
    if not IS_LOCAL:
        validate_snowflake_conn = PythonOperator(
            task_id='validate_snowflake_connection',
            python_callable=validate_snowflake_connection,
            retries=0,
        )

    # Task 1: Spark Bronze Layer Processing
    spark_bronze_processing = SparkSubmitOperator(
        task_id='spark_bronze_processing',
        application='/opt/airflow/spark_jobs/bronze_ingestion.py',
        conn_id='spark_default',
        name='banking_bronze_ingest_{{ ds }}',
        conf={
            'spark.master': SPARK_MASTER,
            'spark.jars.packages': SPARK_S3A_PACKAGES,
            # Local-safe sizing for the compose Spark worker (default 2G, 2 cores)
            'spark.executor.memory': os.getenv('INGEST_SPARK_EXECUTOR_MEMORY', '1g'),
            'spark.driver.memory': os.getenv('INGEST_SPARK_DRIVER_MEMORY', '1g'),
            'spark.executor.cores': os.getenv('INGEST_SPARK_EXECUTOR_CORES', '1'),
            'spark.executor.instances': os.getenv('INGEST_SPARK_EXECUTOR_INSTANCES', '1'),
            'spark.hadoop.fs.s3a.endpoint': os.getenv('AWS_ENDPOINT_URL_S3', 'http://minio:9000'),
            'spark.hadoop.fs.s3a.access.key': os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin'),
            'spark.hadoop.fs.s3a.secret.key': os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
            'spark.hadoop.fs.s3a.aws.credentials.provider': 'org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider',
            'spark.hadoop.fs.s3a.path.style.access': 'true',
            'spark.hadoop.fs.s3a.impl': 'org.apache.hadoop.fs.s3a.S3AFileSystem',
            'spark.sql.adaptive.enabled': 'true',
        },
        application_args=[
            '--source-bucket', 's3://banking-raw-data',
            '--source-prefix', 'banking/{{ ds }}/',
            '--target-bucket', 's3://banking-processed',
            '--target-prefix', 'bronze/{{ ds }}/',
            '--execution-date', '{{ ds }}',
        ],
        verbose=True,
    )

    # Task Group: Load RAW layer (DuckDB in local, Snowflake in non-local)
    with TaskGroup('load_to_snowflake', tooltip='Load processed data to warehouse') as load_group:
        if IS_LOCAL:
            load_customers = PythonOperator(
                task_id='load_customers',
                python_callable=load_raw_to_duckdb,
                op_kwargs={
                    'table_name': 'raw_customers',
                    's3_path': 's3://raw-bucket/customers/customers.csv',
                },
            )

            load_accounts = PythonOperator(
                task_id='load_accounts',
                python_callable=load_raw_to_duckdb,
                op_kwargs={
                    'table_name': 'raw_accounts',
                    's3_path': 's3://raw-bucket/accounts/accounts.csv',
                },
            )

            load_transactions = PythonOperator(
                task_id='load_transactions',
                python_callable=load_raw_to_duckdb,
                op_kwargs={
                    'table_name': 'raw_transactions',
                    's3_path': 's3://raw-bucket/transactions/transactions.csv',
                },
            )
        else:
            load_customers = CopyFromExternalStageToSnowflakeOperator(
                task_id='load_customers',
                snowflake_conn_id=SNOWFLAKE_CONN_ID,
                table='RAW_DB.BANKING.RAW_CUSTOMERS',
                stage='BANKING_STAGE',
                prefix='bronze/{{ ds }}/customers/',
                file_format='(TYPE=PARQUET)',
                copy_options='MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE',
            )

            load_accounts = CopyFromExternalStageToSnowflakeOperator(
                task_id='load_accounts',
                snowflake_conn_id=SNOWFLAKE_CONN_ID,
                table='RAW_DB.BANKING.RAW_ACCOUNTS',
                stage='BANKING_STAGE',
                prefix='bronze/{{ ds }}/accounts/',
                file_format='(TYPE=PARQUET)',
                copy_options='MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE',
            )

            load_transactions = CopyFromExternalStageToSnowflakeOperator(
                task_id='load_transactions',
                snowflake_conn_id=SNOWFLAKE_CONN_ID,
                table='RAW_DB.BANKING.RAW_TRANSACTIONS',
                stage='BANKING_STAGE',
                prefix='bronze/{{ ds }}/transactions/',
                file_format='(TYPE=PARQUET)',
                copy_options='MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE',
            )

    # Task 3: Data Quality Checks
    with TaskGroup('data_quality_checks', tooltip='Validate loaded data') as quality_group:
        if IS_LOCAL:
            check_customers = PythonOperator(
                task_id='check_customers_count',
                python_callable=check_duckdb_row_count,
                op_kwargs={'table_name': 'raw_customers'},
            )

            check_accounts = PythonOperator(
                task_id='check_accounts_referential_integrity',
                python_callable=check_duckdb_row_count,
                op_kwargs={'table_name': 'raw_accounts'},
            )
        else:
            check_customers = SnowflakeOperator(
                task_id='check_customers_count',
                snowflake_conn_id=SNOWFLAKE_CONN_ID,
                sql="""
                    SELECT 
                        COUNT(*) as row_count,
                        COUNT(DISTINCT customer_id) as unique_customers,
                        COUNT(*) - COUNT(customer_id) as null_keys
                    FROM RAW_DB.BANKING.RAW_CUSTOMERS
                    WHERE _loaded_at::DATE = '{{ ds }}';
                """,
            )

            check_accounts = SnowflakeOperator(
                task_id='check_accounts_referential_integrity',
                snowflake_conn_id=SNOWFLAKE_CONN_ID,
                sql="""
                    SELECT COUNT(*) as orphaned_accounts
                    FROM RAW_DB.BANKING.RAW_ACCOUNTS a
                    LEFT JOIN RAW_DB.BANKING.RAW_CUSTOMERS c ON a.customer_id = c.customer_id
                    WHERE a._loaded_at::DATE = '{{ ds }}'
                    AND c.customer_id IS NULL;
                """,
            )

    # Task 4: Send completion notification
    def send_completion_notification(**context):
        """Log completion metrics"""
        import logging
        logging.info(f"Ingestion completed for {context['ds']}")
        return f"SUCCESS: Data loaded for {context['ds']}"

    notify_completion = PythonOperator(
        task_id='notify_completion',
        python_callable=send_completion_notification,
        provide_context=True,
    )

    # Define task dependencies
    if IS_LOCAL:
        spark_bronze_processing >> load_group >> quality_group >> notify_completion
    else:
        spark_bronze_processing >> validate_snowflake_conn >> load_group >> quality_group >> notify_completion
