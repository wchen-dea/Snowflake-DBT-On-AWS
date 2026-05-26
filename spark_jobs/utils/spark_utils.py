import os
import logging
from pyspark.sql import SparkSession, DataFrame

logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "NILOOMID Banking ETL") -> SparkSession:
    """
    Build a SparkSession wired to MinIO (local) or real S3 (cloud).
    S3A credentials and endpoint are read from the environment so the
    same code works in both local Docker Compose and Kubernetes.
    """
    s3_endpoint = os.getenv("AWS_ENDPOINT_URL_S3", os.getenv("S3_ENDPOINT", ""))
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    master_url = os.getenv("SPARK_MASTER_URL", "local[*]")

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master_url)
        .config("spark.sql.shuffle.partitions", "50")   # sensible default for small local data
        .config("spark.driver.memory", "1g")
        .config("spark.executor.memory", "2g")
        .config("spark.sql.adaptive.enabled", "true")
        # ── S3A / MinIO ────────────────────────────────────
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.access.key", access_key)
        .config("spark.hadoop.fs.s3a.secret.key", secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    )

    if s3_endpoint:
        builder = builder.config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        logger.info("S3A endpoint: %s", s3_endpoint)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    logger.info("Spark session created: %s (master=%s)", app_name, master_url)
    return spark


def read_from_s3(spark: SparkSession, path: str, fmt: str = "parquet") -> DataFrame:
    logger.info("Reading %s from %s", fmt, path)
    return spark.read.format(fmt).load(path)


def write_to_s3(df: DataFrame, path: str, fmt: str = "parquet", mode: str = "overwrite") -> None:
    logger.info("Writing %s to %s (mode=%s)", fmt, path, mode)
    df.write.format(fmt).mode(mode).save(path)
