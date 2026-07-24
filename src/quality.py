from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation


def validate_required(row: dict, fields: tuple[str, ...]) -> list[str]:
    return [f"MISSING_{field.upper()}" for field in fields if row.get(field) in (None, "")]


def validate_date(row: dict, field: str, *, allow_future: bool = True) -> list[str]:
    value = row.get(field, "")
    try:
        parsed = date.fromisoformat(str(value))
    except ValueError:
        return [f"INVALID_{field.upper()}"]
    if not allow_future and parsed > date.today():
        return [f"FUTURE_{field.upper()}"]
    return []


def validate_decimal(row: dict, field: str, *, nonnegative: bool = True) -> list[str]:
    try:
        value = Decimal(str(row.get(field, "")))
    except InvalidOperation:
        return [f"INVALID_{field.upper()}"]
    return [f"NEGATIVE_{field.upper()}"] if nonnegative and value < 0 else []


def validate_domain(row: dict, field: str, values: set[str]) -> list[str]:
    return [] if row.get(field) in values else [f"INVALID_{field.upper()}"]


def validate_foreign_key(row: dict, field: str, known_values: set[str]) -> list[str]:
    value = row.get(field, "")
    return [] if not value or value in known_values else [f"UNMATCHED_{field.upper()}"]


def validate_claim(row: dict) -> list[str]:
    """Compatibility validator for claim-like records."""
    normalized = {
        **row,
        "service_from_date": row.get("service_from_date", row.get("service_date", "")),
        "claim_status": row.get("claim_status", row.get("status", "")),
    }
    errors = validate_required(normalized, ("claim_id", "member_id", "provider_id", "service_from_date", "allowed_amount", "paid_amount", "claim_status", "updated_at"))
    errors += validate_date(normalized, "service_from_date", allow_future=False)
    errors += validate_decimal(normalized, "allowed_amount")
    errors += validate_decimal(normalized, "paid_amount")
    errors += validate_domain(normalized, "claim_status", {"APPROVED", "DENIED", "PENDING"})
    try:
        if Decimal(str(normalized.get("paid_amount", ""))) > Decimal(str(normalized.get("allowed_amount", ""))):
            errors.append("PAID_EXCEEDS_ALLOWED")
    except InvalidOperation:
        pass
    return sorted(set(errors))


def deduplicate(rows: list[dict], primary_key: str = "claim_id", order_field: str = "updated_at") -> tuple[list[dict], list[dict]]:
    latest: dict[str, dict] = {}
    duplicates: list[dict] = []
    for row in sorted(rows, key=lambda item: item.get(order_field, "")):
        key = row.get(primary_key, "")
        if key in latest:
            duplicates.append(latest[key])
        latest[key] = row
    return list(latest.values()), duplicates
