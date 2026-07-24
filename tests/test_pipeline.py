import tempfile
import unittest
from pathlib import Path

from src.pipeline import run
from src.quality import deduplicate, validate_claim


class QualityTests(unittest.TestCase):
    def test_invalid_claim_has_financial_and_member_errors(self):
        row = {"claim_id": "1", "member_id": "", "provider_id": "P", "service_date": "2026-01-01", "allowed_amount": "10", "paid_amount": "12", "status": "APPROVED", "updated_at": "2026-01-02T00:00:00Z"}
        self.assertEqual(validate_claim(row), ["MISSING_MEMBER_ID", "PAID_EXCEEDS_ALLOWED"])

    def test_deduplicate_keeps_latest(self):
        rows = [{"claim_id": "1", "updated_at": "2026-01-01"}, {"claim_id": "1", "updated_at": "2026-01-02"}]
        unique, duplicates = deduplicate(rows)
        self.assertEqual(unique[0]["updated_at"], "2026-01-02")
        self.assertEqual(len(duplicates), 1)

    def test_watermark_makes_second_run_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sample = root / "data" / "sample"
            sample.mkdir(parents=True)
            sample.joinpath("claims.jsonl").write_text('{"claim_id":"1","member_id":"M","provider_id":"P","service_date":"2026-01-01","allowed_amount":"10","paid_amount":"8","status":"APPROVED","updated_at":"2026-01-02T00:00:00Z"}\n', encoding="utf-8")
            self.assertEqual(run("2026-01-03", root)["accepted_count"], 1)
            self.assertEqual(run("2026-01-04", root)["source_count"], 0)
            silver = root / "data" / "lake" / "silver" / "claims.jsonl"
            gold = root / "data" / "lake" / "gold" / "provider_claim_metrics.jsonl"
            self.assertEqual(len(silver.read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(len(gold.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
