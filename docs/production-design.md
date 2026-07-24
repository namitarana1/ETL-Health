# Production design

## Processing

Use Auto Loader or structured streaming for incremental file discovery and Event Hubs/Kafka ingestion. Persist checkpoints outside the table path. Apply explicit schemas, rescue unexpected columns, quarantine malformed records, and use Delta `MERGE` keyed by the healthcare business identifier and `updated_at`. Partition on low-cardinality access fields such as service month—not patient or claim identifiers. Use adaptive query execution, early filters, broadcast joins for genuinely small dimensions, and scheduled compaction.

## Quality and reconciliation

Quality gates cover required identifiers, duplicate business keys, valid service dates, code-set validity, nonnegative financial amounts, paid-versus-allowed checks, provider matches, schema drift, and referential integrity. Each run records source, accepted, and rejected counts plus financial control totals. Rejected rows retain error codes and can be corrected and replayed without reprocessing unaffected partitions.

## Snowflake

Expose only curated gold data through external/internal stages and idempotent loads. Use streams/tasks or an orchestrated stored procedure with dependency state, audit records, restart markers, and exception handling. Apply clustering only where pruning evidence justifies its cost. Secure views and masking policies protect sensitive columns.

## Operations

Airflow coordinates ADF, Glue, Databricks, quality gates, reconciliation, and Snowflake. DAGs define retries, timeouts, SLAs, ownership, alert routes, and restart-safe task boundaries. Central logs carry `run_id`, `dataset`, `layer`, `record_count`, `duration`, and error category. CI validates Python, SQL, notebooks, contracts, and DAG imports before promotion through development, QA, and production.

## Security

- Least-privilege RBAC and service identities; no shared user credentials
- TLS in transit and provider-managed/customer-managed encryption at rest
- Secrets stored in Azure Key Vault or AWS Secrets Manager
- Column masking, tokenization, and row policies for PHI
- Private endpoints/network controls and immutable audit logging
- Synthetic data in development; production data access is approved and monitored

## Migration validation

For historical migrations, compare source and target counts, financial totals, null rates, duplicate rates, rejects, and domain control totals by partition before release. Maintain signed manifests and rerunnable partition-level checkpoints.
