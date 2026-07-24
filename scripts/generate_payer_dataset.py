"""Generate deterministic synthetic payer data. No real people or proprietary data."""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST = ["Alex", "Avery", "Casey", "Jordan", "Morgan", "Riley", "Taylor", "Cameron"]
LAST = ["Brooks", "Diaz", "Gupta", "Johnson", "Kim", "Martinez", "Patel", "Williams"]
STATES = ["AZ", "CA", "CO", "FL", "IL", "MN", "NC", "NY", "TX", "WA"]
PLANS = ["COMMERCIAL_HMO", "COMMERCIAL_PPO", "MEDICARE_ADVANTAGE", "MEDICAID_MANAGED_CARE"]
DIAGNOSES = ["E11.9", "I10", "J45.909", "M54.50", "Z00.00", "N39.0"]
PROCEDURES = ["99213", "99214", "80053", "83036", "71046", "97110"]
SPECIALTIES = ["Primary Care", "Cardiology", "Endocrinology", "Orthopedics", "Radiology", "Behavioral Health"]
DRUGS = [("00093-1045-98", "METFORMIN", "500 MG"), ("00378-1805-10", "LISINOPRIL", "10 MG"), ("00078-0615-15", "ATORVASTATIN", "20 MG"), ("00173-0682-20", "ALBUTEROL", "90 MCG")]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(output: Path, member_count: int, claim_count: int, seed: int) -> dict[str, int]:
    rng = random.Random(seed)
    today = date(2026, 7, 1)
    members, eligibility, providers = [], [], []
    for i in range(1, member_count + 1):
        member_id = f"MBR{i:07d}"
        members.append({"member_id": member_id, "first_name": FIRST[i % len(FIRST)], "last_name": LAST[(i * 3) % len(LAST)], "date_of_birth": (today - timedelta(days=rng.randint(18 * 365, 85 * 365))).isoformat(), "gender_code": rng.choice(["F", "M", "X"]), "state": rng.choice(STATES), "synthetic_record": "Y"})
        start = date(2025, 1, 1) + timedelta(days=rng.randint(0, 180))
        eligibility.append({"eligibility_id": f"ELG{i:07d}", "member_id": member_id, "plan_type": rng.choice(PLANS), "coverage_start_date": start.isoformat(), "coverage_end_date": "2026-12-31", "coverage_status": "ACTIVE", "group_id": f"GRP{rng.randint(1, 50):04d}"})
    for i in range(1, max(25, member_count // 10) + 1):
        providers.append({"provider_id": f"PRV{i:06d}", "npi": f"9{i:09d}", "provider_name": f"Synthetic Care Center {i}", "specialty": SPECIALTIES[i % len(SPECIALTIES)], "network_status": rng.choice(["IN_NETWORK", "IN_NETWORK", "OUT_OF_NETWORK"]), "state": rng.choice(STATES)})

    claims, lines, payments, authorizations, pharmacy, encounters = [], [], [], [], [], []
    for i in range(1, claim_count + 1):
        member = rng.choice(members)
        provider = rng.choice(providers)
        service = today - timedelta(days=rng.randint(1, 540))
        allowed = round(rng.uniform(45, 4000), 2)
        status = rng.choices(["APPROVED", "DENIED", "PENDING"], [0.82, 0.13, 0.05])[0]
        paid = round(allowed * rng.uniform(0.65, 1.0), 2) if status == "APPROVED" else 0.0
        claim_id = f"CLM{i:09d}"
        claims.append({"claim_id": claim_id, "member_id": member["member_id"], "provider_id": provider["provider_id"], "claim_type": rng.choice(["PROFESSIONAL", "INSTITUTIONAL"]), "service_from_date": service.isoformat(), "service_to_date": (service + timedelta(days=rng.randint(0, 3))).isoformat(), "primary_diagnosis_code": rng.choice(DIAGNOSES), "claim_status": status, "billed_amount": f"{allowed * rng.uniform(1.05, 1.8):.2f}", "allowed_amount": f"{allowed:.2f}", "paid_amount": f"{paid:.2f}", "denial_reason_code": rng.choice(["CO16", "CO50", "CO97"]) if status == "DENIED" else "", "received_date": (service + timedelta(days=rng.randint(1, 20))).isoformat(), "updated_at": f"2026-07-{rng.randint(1, 20):02d}T{rng.randint(0, 23):02d}:00:00Z"})
        line_count = rng.randint(1, 3)
        for line_no in range(1, line_count + 1):
            lines.append({"claim_line_id": f"{claim_id}-{line_no}", "claim_id": claim_id, "line_number": line_no, "procedure_code": rng.choice(PROCEDURES), "place_of_service": rng.choice(["11", "21", "22", "23"]), "units": rng.randint(1, 4), "line_allowed_amount": f"{allowed / line_count:.2f}"})
        if status == "APPROVED":
            payments.append({"payment_id": f"PAY{i:09d}", "claim_id": claim_id, "payment_date": (service + timedelta(days=rng.randint(14, 45))).isoformat(), "payment_amount": f"{paid:.2f}", "payment_method": rng.choice(["EFT", "CHECK"]), "reconciliation_status": "MATCHED"})
        if rng.random() < 0.22:
            requested = service - timedelta(days=rng.randint(1, 14))
            decision = rng.choice(["APPROVED", "DENIED"])
            authorizations.append({"authorization_id": f"AUT{i:09d}", "member_id": member["member_id"], "provider_id": provider["provider_id"], "procedure_code": rng.choice(PROCEDURES), "requested_date": requested.isoformat(), "decision_date": (requested + timedelta(days=rng.randint(0, 5))).isoformat(), "decision": decision})
        encounters.append({"encounter_id": f"ENC{i:09d}", "member_id": member["member_id"], "provider_id": provider["provider_id"], "encounter_date": service.isoformat(), "encounter_type": rng.choice(["OFFICE", "INPATIENT", "OUTPATIENT", "EMERGENCY"]), "diagnosis_code": rng.choice(DIAGNOSES)})
    for i in range(1, max(1, claim_count // 3) + 1):
        member = rng.choice(members)
        ndc, drug, strength = rng.choice(DRUGS)
        fill = today - timedelta(days=rng.randint(1, 365))
        pharmacy.append({"rx_claim_id": f"RX{i:09d}", "member_id": member["member_id"], "ndc": ndc, "drug_name": drug, "strength": strength, "fill_date": fill.isoformat(), "days_supply": rng.choice([30, 60, 90]), "quantity": rng.choice([30, 60, 90]), "claim_status": rng.choice(["PAID", "PAID", "REJECTED"]), "member_pay_amount": f"{rng.uniform(0, 75):.2f}", "plan_pay_amount": f"{rng.uniform(5, 500):.2f}"})

    datasets = {"members": members, "eligibility": eligibility, "providers": providers, "medical_claims": claims, "medical_claim_lines": lines, "payments": payments, "authorizations": authorizations, "pharmacy_claims": pharmacy, "encounters": encounters}
    for name, rows in datasets.items():
        write_csv(output / f"{name}.csv", rows)
    return {name: len(rows) for name, rows in datasets.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "synthetic_payer")
    parser.add_argument("--members", type=int, default=1000)
    parser.add_argument("--claims", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(generate(args.output, args.members, args.claims, args.seed))
