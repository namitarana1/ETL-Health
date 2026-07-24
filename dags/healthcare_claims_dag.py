"""Illustrative Airflow DAG; deploy this file only in an Airflow environment."""
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.empty import EmptyOperator
except ImportError:  # Keeps repository tooling usable without Airflow installed.
    DAG = None

if DAG:
    with DAG(
        dag_id="healthcare_claims_medallion",
        start_date=datetime(2026, 1, 1),
        schedule="0 2 * * *",
        catchup=False,
        default_args={"retries": 3, "retry_delay": timedelta(minutes=10)},
        tags=["healthcare", "claims", "databricks", "snowflake"],
    ) as dag:
        ingest = EmptyOperator(task_id="adf_or_glue_ingest")
        bronze_to_silver = EmptyOperator(task_id="databricks_bronze_to_silver")
        quality_gate = EmptyOperator(task_id="quality_and_reconciliation")
        silver_to_gold = EmptyOperator(task_id="databricks_silver_to_gold")
        snowflake_load = EmptyOperator(task_id="snowflake_load")
        ingest >> bronze_to_silver >> quality_gate >> silver_to_gold >> snowflake_load
