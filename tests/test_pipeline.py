import csv
import tempfile
import unittest
from pathlib import Path

from scripts.generate_payer_dataset import generate
from src.pipeline import read_jsonl, run
from src.quality import validate_claim


class PipelineTests(unittest.TestCase):
    def make_project(self, folder: str) -> Path:
        root = Path(folder)
        generate(root / "data" / "synthetic_payer", member_count=20, claim_count=50, seed=7)
        return root

    def test_full_run_builds_silver_and_gold(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_project(folder)
            result = run("2026-07-24", root, full_refresh=True)
            self.assertEqual(result["status"], "SUCCEEDED")
            self.assertEqual(len(result["datasets"]), 9)
            self.assertEqual(len(read_jsonl(root / "data" / "lake" / "silver" / "medical_claims.jsonl")), 50)
            self.assertTrue(read_jsonl(root / "data" / "lake" / "gold" / "provider_claim_kpis.jsonl"))
            self.assertTrue(read_jsonl(root / "data" / "lake" / "gold" / "financial_reconciliation.jsonl"))

    def test_unchanged_incremental_run_processes_zero_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_project(folder)
            run("2026-07-24", root, full_refresh=True)
            result = run("2026-07-25", root)
            self.assertEqual(result["changed_count"], 0)
            self.assertEqual(len(read_jsonl(root / "data" / "lake" / "silver" / "medical_claims.jsonl")), 50)

    def test_invalid_foreign_key_is_quarantined(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_project(folder)
            run("2026-07-24", root, full_refresh=True)
            payment_path = root / "data" / "synthetic_payer" / "payments.csv"
            with payment_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["claim_id"] = "CLM-NOT-FOUND"
            with payment_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            result = run("2026-07-25", root, dataset="payments")
            self.assertEqual(result["changed_count"], 1)
            rejected = read_jsonl(next((root / "data" / "lake" / "rejected" / "payments").glob("*2026-07-25*.jsonl")))
            self.assertIn("UNMATCHED_CLAIM_ID", rejected[0]["error_codes"])

    def test_claim_financial_validation(self):
        row = {"claim_id": "1", "member_id": "M", "provider_id": "P", "service_date": "2026-01-01", "allowed_amount": "10", "paid_amount": "12", "status": "APPROVED", "updated_at": "2026-01-02T00:00:00Z"}
        self.assertIn("PAID_EXCEEDS_ALLOWED", validate_claim(row))


if __name__ == "__main__":
    unittest.main()
