# NimbusPay Fraud Detection

NimbusPay is a digital payments company. This tool scores transactions for fraud risk and summarizes chargeback exposure by risk tier.

## Quick start

```bash
pip install -r requirements.txt
python analyze_fraud.py
pytest
```

## Files

| File | Purpose |
|---|---|
| `analyze_fraud.py` | Main pipeline: loads data, scores transactions, prints report |
| `features.py` | Feature engineering: merges accounts, flags large amounts and login pressure |
| `risk_rules.py` | Scoring logic: `score_transaction` (0–100) and `label_risk` (low/medium/high) |
| `test_risk_rules.py` | Pytest tests for scoring and labeling functions |
| `transactions.csv` | Raw payment transactions |
| `accounts.csv` | Account-level data including prior chargeback history |
| `chargebacks.csv` | Confirmed fraud chargebacks used to validate rule performance |

## Risk signals

| Signal | Low risk | Elevated | High |
|---|---|---|---|
| Device risk score | < 40 | 40–69 | ≥ 70 |
| Transaction amount | < $500 | $500–999 | ≥ $1,000 |
| Transactions in 24h | < 3 | 3–5 | ≥ 6 |
| Failed logins in 24h | 0 | 2–4 | ≥ 5 |
| Prior chargebacks | 0 | 1 | ≥ 2 |
| International | No | — | Yes |
