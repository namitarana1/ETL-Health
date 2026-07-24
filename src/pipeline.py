from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .quality import validate_date, validate_decimal, validate_domain, validate_foreign_key, validate_required

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    required: tuple[str, ...]
    date_fields: tuple[str, ...] = ()
    decimal_fields: tuple[str, ...] = ()
    domains: tuple[tuple[str, frozenset[str]], ...] = ()
    foreign_keys: tuple[tuple[str, str], ...] = ()


SPECS: dict[str, DatasetSpec] = {
    "members": DatasetSpec("member_id", ("member_id", "date_of_birth", "state", "synthetic_record"), ("date_of_birth",), domains=(("synthetic_record", frozenset({"Y"})),)),
    "providers": DatasetSpec("provider_id", ("provider_id", "npi", "provider_name", "specialty", "network_status"), domains=(("network_status", frozenset({"IN_NETWORK", "OUT_OF_NETWORK"})),)),
    "eligibility": DatasetSpec("eligibility_id", ("eligibility_id", "member_id", "plan_type", "coverage_start_date", "coverage_end_date", "coverage_status"), ("coverage_start_date", "coverage_end_date"), domains=(("coverage_status", frozenset({"ACTIVE", "INACTIVE"})),), foreign_keys=(("member_id", "members"),)),
    "medical_claims": DatasetSpec("claim_id", ("claim_id", "member_id", "provider_id", "service_from_date", "claim_status", "allowed_amount", "paid_amount", "updated_at"), ("service_from_date", "service_to_date", "received_date"), ("billed_amount", "allowed_amount", "paid_amount"), (("claim_status", frozenset({"APPROVED", "DENIED", "PENDING"})),), (("member_id", "members"), ("provider_id", "providers"))),
    "medical_claim_lines": DatasetSpec("claim_line_id", ("claim_line_id", "claim_id", "line_number", "procedure_code", "line_allowed_amount"), decimal_fields=("line_allowed_amount",), foreign_keys=(("claim_id", "medical_claims"),)),
    "payments": DatasetSpec("payment_id", ("payment_id", "claim_id", "payment_date", "payment_amount", "reconciliation_status"), ("payment_date",), ("payment_amount",), (("reconciliation_status", frozenset({"MATCHED", "UNMATCHED"})),), (("claim_id", "medical_claims"),)),
    "authorizations": DatasetSpec("authorization_id", ("authorization_id", "member_id", "provider_id", "requested_date", "decision_date", "decision"), ("requested_date", "decision_date"), domains=(("decision", frozenset({"APPROVED", "DENIED", "PENDING"})),), foreign_keys=(("member_id", "members"), ("provider_id", "providers"))),
    "pharmacy_claims": DatasetSpec("rx_claim_id", ("rx_claim_id", "member_id", "ndc", "fill_date", "claim_status", "member_pay_amount", "plan_pay_amount"), ("fill_date",), ("member_pay_amount", "plan_pay_amount"), (("claim_status", frozenset({"PAID", "REJECTED"})),), (("member_id", "members"),)),
    "encounters": DatasetSpec("encounter_id", ("encounter_id", "member_id", "provider_id", "encounter_date", "encounter_type"), ("encounter_date",), foreign_keys=(("member_id", "members"), ("provider_id", "providers"))),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload + ("\n" if payload else ""), encoding="utf-8")
    temporary.replace(path)


def row_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_control(path: Path) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def validate_row(name: str, row: dict, reference_keys: dict[str, set[str]]) -> list[str]:
    spec = SPECS[name]
    errors = validate_required(row, spec.required)
    for field in spec.date_fields:
        errors += validate_date(row, field, allow_future=field in {"coverage_end_date"})
    for field in spec.decimal_fields:
        errors += validate_decimal(row, field)
    for field, values in spec.domains:
        errors += validate_domain(row, field, set(values))
    for field, dataset in spec.foreign_keys:
        errors += validate_foreign_key(row, field, reference_keys.get(dataset, set()))
    if name == "medical_claims":
        try:
            if Decimal(row["paid_amount"]) > Decimal(row["allowed_amount"]):
                errors.append("PAID_EXCEEDS_ALLOWED")
        except (InvalidOperation, KeyError):
            pass
    if name == "eligibility" and row.get("coverage_start_date", "") > row.get("coverage_end_date", ""):
        errors.append("COVERAGE_DATE_RANGE_INVALID")
    if name == "authorizations" and row.get("requested_date", "") > row.get("decision_date", ""):
        errors.append("DECISION_PRECEDES_REQUEST")
    return sorted(set(errors))


def process_dataset(name: str, source_dir: Path, lake: Path, run_id: str, control: dict, reference_keys: dict[str, set[str]], full_refresh: bool) -> dict:
    spec = SPECS[name]
    rows = read_csv(source_dir / f"{name}.csv")
    current_hashes = {row[spec.key]: row_hash(row) for row in rows}
    previous_hashes = {} if full_refresh else control.get(name, {})
    changed = [row for row in rows if previous_hashes.get(row[spec.key]) != current_hashes[row[spec.key]]]
    write_jsonl(lake / "bronze" / name / f"run_id={run_id}.jsonl", [{**row, "_ingested_at": run_id, "_source_file": f"{name}.csv"} for row in changed])

    accepted, rejected = [], []
    seen: set[str] = set()
    for row in changed:
        key = row.get(spec.key, "")
        errors = validate_row(name, row, reference_keys)
        if key in seen:
            errors.append(f"DUPLICATE_{spec.key.upper()}")
        seen.add(key)
        if errors:
            rejected.append({**row, "error_codes": sorted(set(errors)), "rejected_at": run_id})
        else:
            accepted.append({**row, "_processed_at": run_id})

    silver_path = lake / "silver" / f"{name}.jsonl"
    existing = [] if full_refresh else read_jsonl(silver_path)
    merged = {row[spec.key]: row for row in existing}
    merged.update({row[spec.key]: row for row in accepted})
    write_jsonl(silver_path, sorted(merged.values(), key=lambda row: row[spec.key]))
    write_jsonl(lake / "rejected" / name / f"run_id={run_id}.jsonl", rejected)
    reference_keys[name] = set(merged)
    control[name] = current_hashes
    return {"dataset": name, "source_count": len(rows), "changed_count": len(changed), "accepted_count": len(accepted), "rejected_count": len(rejected), "silver_count": len(merged)}


def build_gold(lake: Path, run_id: str) -> dict[str, int]:
    tables = {name: read_jsonl(lake / "silver" / f"{name}.jsonl") for name in SPECS}
    claims = tables["medical_claims"]
    providers = {row["provider_id"]: row for row in tables["providers"]}
    eligibility = {row["member_id"]: row for row in tables["eligibility"]}

    provider_metrics: dict[str, dict] = defaultdict(lambda: {"claim_count": 0, "approved_count": 0, "denied_count": 0, "allowed_amount": Decimal("0"), "paid_amount": Decimal("0")})
    member_metrics: dict[str, dict] = defaultdict(lambda: {"claim_count": 0, "encounter_count": 0, "rx_claim_count": 0, "paid_amount": Decimal("0")})
    plan_metrics: dict[str, dict] = defaultdict(lambda: {"member_count": set(), "claim_count": 0, "paid_amount": Decimal("0")})
    for claim in claims:
        provider = provider_metrics[claim["provider_id"]]
        provider["claim_count"] += 1
        provider["approved_count"] += int(claim["claim_status"] == "APPROVED")
        provider["denied_count"] += int(claim["claim_status"] == "DENIED")
        provider["allowed_amount"] += Decimal(claim["allowed_amount"])
        provider["paid_amount"] += Decimal(claim["paid_amount"])
        member = member_metrics[claim["member_id"]]
        member["claim_count"] += 1
        member["paid_amount"] += Decimal(claim["paid_amount"])
        plan = eligibility.get(claim["member_id"], {}).get("plan_type", "UNKNOWN")
        plan_metrics[plan]["member_count"].add(claim["member_id"])
        plan_metrics[plan]["claim_count"] += 1
        plan_metrics[plan]["paid_amount"] += Decimal(claim["paid_amount"])
    for encounter in tables["encounters"]:
        member_metrics[encounter["member_id"]]["encounter_count"] += 1
    for rx in tables["pharmacy_claims"]:
        member_metrics[rx["member_id"]]["rx_claim_count"] += 1

    provider_rows = []
    for provider_id, values in sorted(provider_metrics.items()):
        count = values["claim_count"]
        provider_rows.append({"provider_id": provider_id, "provider_name": providers.get(provider_id, {}).get("provider_name", "UNKNOWN"), "specialty": providers.get(provider_id, {}).get("specialty", "UNKNOWN"), "claim_count": count, "approval_rate": f"{values['approved_count'] / count:.4f}", "denial_rate": f"{values['denied_count'] / count:.4f}", "allowed_amount": str(values["allowed_amount"]), "paid_amount": str(values["paid_amount"]), "payment_variance": str(values["allowed_amount"] - values["paid_amount"]), "_refreshed_at": run_id})
    member_rows = [{"member_id": key, **{field: str(value) if isinstance(value, Decimal) else value for field, value in values.items()}, "_refreshed_at": run_id} for key, values in sorted(member_metrics.items())]
    plan_rows = [{"plan_type": key, "member_count": len(values["member_count"]), "claim_count": values["claim_count"], "paid_amount": str(values["paid_amount"]), "_refreshed_at": run_id} for key, values in sorted(plan_metrics.items())]

    authorization_by_decision: dict[str, list[int]] = defaultdict(list)
    for row in tables["authorizations"]:
        turnaround = (datetime.fromisoformat(row["decision_date"]) - datetime.fromisoformat(row["requested_date"])).days
        authorization_by_decision[row["decision"]].append(turnaround)
    auth_rows = [{"decision": decision, "authorization_count": len(days), "average_turnaround_days": f"{sum(days) / len(days):.2f}", "_refreshed_at": run_id} for decision, days in sorted(authorization_by_decision.items())]

    payment_total = sum((Decimal(row["payment_amount"]) for row in tables["payments"]), Decimal("0"))
    claim_paid_total = sum((Decimal(row["paid_amount"]) for row in claims), Decimal("0"))
    reconciliation = [{"medical_claim_count": len(claims), "payment_count": len(tables["payments"]), "claim_paid_total": str(claim_paid_total), "payment_total": str(payment_total), "difference": str(claim_paid_total - payment_total), "matched_payment_count": sum(row["reconciliation_status"] == "MATCHED" for row in tables["payments"]), "_refreshed_at": run_id}]

    outputs = {"provider_claim_kpis": provider_rows, "member_utilization": member_rows, "plan_performance": plan_rows, "authorization_metrics": auth_rows, "financial_reconciliation": reconciliation}
    for name, rows in outputs.items():
        write_jsonl(lake / "gold" / f"{name}.jsonl", rows)
    return {name: len(rows) for name, rows in outputs.items()}


def run(run_date: str, root: Path = ROOT, full_refresh: bool = False, dataset: str | None = None) -> dict:
    started = datetime.now(timezone.utc)
    run_id = f"{run_date}T{started.strftime('%H%M%S%fZ')}"
    source_dir = root / "data" / "synthetic_payer"
    lake = root / "data" / "lake"
    control_path = lake / "_control" / "row_watermarks.json"
    control = {} if full_refresh else load_control(control_path)
    reference_keys = {name: {row[spec.key] for row in read_jsonl(lake / "silver" / f"{name}.jsonl")} for name, spec in SPECS.items()}
    order = ["members", "providers", "eligibility", "medical_claims", "medical_claim_lines", "payments", "authorizations", "pharmacy_claims", "encounters"]
    selected = order if dataset is None else [dataset]
    audits = [process_dataset(name, source_dir, lake, run_id, control, reference_keys, full_refresh) for name in selected]
    control_path.parent.mkdir(parents=True, exist_ok=True)
    control_path.write_text(json.dumps(control, indent=2, sort_keys=True), encoding="utf-8")
    gold_counts = build_gold(lake, run_id)
    summary = {"run_id": run_id, "mode": "full_refresh" if full_refresh else "incremental", "status": "SUCCEEDED", "datasets": audits, "gold_outputs": gold_counts, "source_count": sum(item["source_count"] for item in audits), "changed_count": sum(item["changed_count"] for item in audits), "accepted_count": sum(item["accepted_count"] for item in audits), "rejected_count": sum(item["rejected_count"] for item in audits), "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3)}
    write_jsonl(lake / "_audit" / f"run_id={run_id}.jsonl", [summary])
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the multi-domain healthcare medallion pipeline")
    parser.add_argument("--run-date", required=True, help="Logical run date in YYYY-MM-DD format")
    parser.add_argument("--full-refresh", action="store_true", help="Rebuild silver state from all source rows")
    parser.add_argument("--dataset", choices=sorted(SPECS), help="Process one dataset and refresh all gold outputs")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    print(json.dumps(run(args.run_date, args.root, args.full_refresh, args.dataset), indent=2))


if __name__ == "__main__":
    main()
