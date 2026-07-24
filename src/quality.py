from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation


REQUIRED = ("claim_id", "member_id", "provider_id", "service_date", "allowed_amount", "paid_amount", "status", "updated_at")


def validate_claim(row: dict) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED:
        if row.get(field) in (None, ""):
            errors.append(f"MISSING_{field.upper()}")
    try:
        service_date = date.fromisoformat(str(row.get("service_date", "")))
        if service_date > date.today():
            errors.append("FUTURE_SERVICE_DATE")
    except ValueError:
        errors.append("INVALID_SERVICE_DATE")
    try:
        allowed = Decimal(str(row.get("allowed_amount", "")))
        paid = Decimal(str(row.get("paid_amount", "")))
        if allowed < 0 or paid < 0:
            errors.append("NEGATIVE_AMOUNT")
        if paid > allowed:
            errors.append("PAID_EXCEEDS_ALLOWED")
    except InvalidOperation:
        errors.append("INVALID_AMOUNT")
    if row.get("status") not in {"APPROVED", "DENIED", "PENDING"}:
        errors.append("INVALID_STATUS")
    return sorted(set(errors))


def deduplicate(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    latest: dict[str, dict] = {}
    duplicates: list[dict] = []
    for row in sorted(rows, key=lambda item: item.get("updated_at", "")):
        claim_id = row.get("claim_id", "")
        if claim_id in latest:
            duplicates.append(latest[claim_id])
        latest[claim_id] = row
    return list(latest.values()), duplicates
