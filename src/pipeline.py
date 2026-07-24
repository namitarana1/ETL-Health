from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .quality import deduplicate, validate_claim

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def run(run_date: str, root: Path = ROOT) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    source = root / "data" / "sample" / "claims.jsonl"
    lake = root / "data" / "lake"
    watermark_path = lake / "_control" / "claims_watermark.txt"
    watermark = watermark_path.read_text(encoding="utf-8").strip() if watermark_path.exists() else ""
    all_rows = read_jsonl(source)
    incremental = [row for row in all_rows if row.get("updated_at", "") > watermark]

    write_jsonl(lake / "bronze" / f"claims_{run_date}.jsonl", incremental)
    unique, duplicates = deduplicate(incremental)
    accepted, rejected = [], []
    for row in unique:
        errors = validate_claim(row)
        if errors:
            rejected.append({**row, "error_codes": errors, "rejected_at": started})
        else:
            accepted.append({**row, "allowed_amount": str(Decimal(str(row["allowed_amount"]))), "paid_amount": str(Decimal(str(row["paid_amount"])))})
    for row in duplicates:
        rejected.append({**row, "error_codes": ["DUPLICATE_CLAIM"], "rejected_at": started})

    silver_path = lake / "silver" / "claims.jsonl"
    existing_silver = read_jsonl(silver_path)
    merged_silver, _ = deduplicate(existing_silver + accepted)
    write_jsonl(silver_path, merged_silver)
    write_jsonl(lake / "rejected" / f"claims_{run_date}.jsonl", rejected)

    metrics: dict[str, dict] = defaultdict(lambda: {"claim_count": 0, "allowed_amount": Decimal("0"), "paid_amount": Decimal("0"), "denied_count": 0})
    for row in merged_silver:
        item = metrics[row["provider_id"]]
        item["claim_count"] += 1
        item["allowed_amount"] += Decimal(row["allowed_amount"])
        item["paid_amount"] += Decimal(row["paid_amount"])
        item["denied_count"] += int(row["status"] == "DENIED")
    gold = [{"provider_id": key, **{name: str(value) if isinstance(value, Decimal) else value for name, value in value.items()}} for key, value in sorted(metrics.items())]
    write_jsonl(lake / "gold" / "provider_claim_metrics.jsonl", gold)

    maximum = max((row.get("updated_at", "") for row in incremental), default=watermark)
    watermark_path.parent.mkdir(parents=True, exist_ok=True)
    watermark_path.write_text(maximum, encoding="utf-8")
    audit = {"run_date": run_date, "started_at": started, "source_count": len(incremental), "accepted_count": len(accepted), "rejected_count": len(rejected), "source_allowed_total": str(sum((Decimal(str(r.get("allowed_amount", 0))) for r in incremental if str(r.get("allowed_amount", "")).replace(".", "", 1).isdigit()), Decimal("0"))), "accepted_allowed_total": str(sum((Decimal(r["allowed_amount"]) for r in accepted), Decimal("0"))), "watermark": maximum}
    write_jsonl(lake / "_audit" / f"claims_{run_date}.jsonl", [audit])
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local healthcare medallion pipeline")
    parser.add_argument("--run-date", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.run_date), indent=2))


if __name__ == "__main__":
    main()
