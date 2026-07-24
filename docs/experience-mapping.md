# Experience-to-project mapping

| Capability | Evidence in this repository |
|---|---|
| Azure/AWS batch and streaming ingestion | `config/platform.yml`, architecture and production design |
| Bronze, silver, gold lakehouse | `src/pipeline.py` and generated `data/lake` outputs |
| Cleansing, validation, deduplication | `src/quality.py` |
| Incremental watermark processing | `_control/claims_watermark.txt` logic |
| Rejections and reprocessing | rejected output with stable error codes |
| Reconciliation and audit logging | per-run source/accepted/rejected counts and totals |
| Snowflake reporting and 20+ KPI patterns | `sql/snowflake_kpis.sql` |
| 30+ Airflow DAG operating model | `dags/healthcare_claims_dag.py` template |
| Spark performance improvements | partitioning, AQE, broadcast, compaction guidance |
| 50+ TB migration controls | migration validation section in production design |
| CI/CD, monitoring, recovery | operations section in production design |
| PHI security and compliance | security section in production design |

Quantitative production achievements in the original experience statement are design targets and prior outcomes, not claims about the small synthetic local run.
