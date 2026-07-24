# Synthetic payer dataset

This folder contains generated, de-identified test data modeled after common US health-insurance operations. It is not supplied, endorsed, or used by UnitedHealthcare, and it contains no real members, providers, claims, or proprietary information.

## Tables and relationships

- `members.csv`: synthetic member demographics
- `eligibility.csv`: plan enrollment; joins to members on `member_id`
- `providers.csv`: synthetic network directory
- `medical_claims.csv`: claim headers joining members and providers
- `medical_claim_lines.csv`: one-to-many service lines by `claim_id`
- `pharmacy_claims.csv`: synthetic prescription transactions
- `authorizations.csv`: prior-authorization decisions
- `payments.csv`: approved-claim disbursements and reconciliation status
- `encounters.csv`: utilization events

All identifiers are fabricated. Code-like values are included only to support realistic engineering exercises.

Regenerate deterministically from the project root:

```powershell
python scripts\generate_payer_dataset.py --members 1000 --claims 5000 --seed 42
```
