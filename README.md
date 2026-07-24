# Multi-Cloud Healthcare Lakehouse

A portfolio-ready reference implementation of a healthcare data platform spanning Azure Databricks, Azure Data Factory, ADLS, Event Hubs, AWS Glue, S3, Kafka, Snowflake, and Apache Airflow.

The repository uses synthetic, de-identified data and a dependency-free local runner so the core design can be demonstrated without cloud accounts. Production adapters are represented by configuration and orchestration examples.

## Platform scope

- Claims, pharmacy, eligibility, provider, payment, authorization, EHR, and encounter domains
- Batch ingestion from databases, REST, SFTP, Blob Storage, and S3
- Near-real-time ingestion from Kafka and Event Hubs
- Bronze, silver, and gold lakehouse layers with incremental watermarks
- Reusable schema validation, quality rules, rejection handling, audit logging, and reconciliation
- Snowflake KPI models for approvals, denials, payments, utilization, and authorization turnaround
- Airflow orchestration with retries, alerts, SLAs, checkpoints, and restart-safe tasks
- RBAC, encryption, masking, secrets-management, and audit-control guidance for PHI

## Architecture

```text
15+ sources                 Multi-cloud lakehouse                  Consumers
DB / REST / SFTP ─┐        ┌──────────────────────────┐         ┌──────────────┐
Blob / S3 ────────┼──────> │ Bronze: immutable raw    │         │ Snowflake    │
Kafka / Event Hubs┘        │ Silver: valid, deduped   │───────> │ BI / reports │
                           │ Gold: curated healthcare │         │ Analytics    │
ADF / Glue ingestion       └──────────────────────────┘         └──────────────┘
                                  Databricks / PySpark
                         Airflow orchestration + quality gates
```

Production scale represented by this design: 1–2 TB/day, 20+ batch pipelines, 1M+ events/day, 100+ TB lake storage, 5–10M records/run, 30+ DAGs, and 800+ monthly executions.

## Run locally

Requires Python 3.10+ and no third-party packages.

```powershell
python -m src.pipeline --run-date 2026-07-24
python -m unittest discover -s tests -v
```

Outputs are written to `data/lake/{bronze,silver,gold,rejected}`. Re-running the same input is idempotent; the watermark prevents older records from being processed again.

### Open the interactive demo

```powershell
cd demo-ui
npm run dev
```

Open the local address shown in the terminal. Select **Run pipeline demo** to watch records move through ingestion, bronze, validation, curation, and Snowflake serving. The dashboard also includes dataset search, relationship mapping, masked claim previews, quality checks, reconciliation status, and gold-layer KPIs.

## Synthetic payer dataset

Generate a linked, UnitedHealthcare-style (but wholly synthetic and unaffiliated) dataset for payer analytics:

```powershell
python scripts\generate_payer_dataset.py --members 1000 --claims 5000 --seed 42
```

The output covers members, eligibility, providers, medical claim headers and lines, pharmacy claims, authorizations, payments, and encounters. See `data/synthetic_payer/README.md` for its data dictionary and disclaimer.

## Repository map

```text
src/                 Local pipeline, quality, reconciliation, audit utilities
config/              Dataset contracts and platform configuration
dags/                Airflow orchestration example
sql/                  Snowflake tables and healthcare KPI transformations
data/sample/          Synthetic input data only
docs/                 Architecture, security, operations, and résumé mapping
tests/                Unit tests for critical quality and incremental logic
```

## Cloud implementation notes

The local JSONL files map to Delta tables in ADLS/S3. In production, replace `JsonLake` with Spark DataFrame reads/writes, use Delta `MERGE` for upserts, store watermarks in a control table, load gold tables through Snowflake stages/Snowpipe, and retrieve all credentials from Key Vault or Secrets Manager. See [docs/production-design.md](docs/production-design.md).

## Safety

All included names and identifiers are fictitious. Never commit PHI, secrets, access keys, connection strings, or production extracts to this repository.
