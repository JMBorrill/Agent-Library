Assessment for Customer portal 3.2 (commit 9f2c1ab) against ASVS 5.0.0 Level 1, chapter V2. Levels are cumulative,
so the Level 1 requirements in V2 are 2.1.1, 2.2.1, 2.2.2 and 2.3.1. Checked with
`python -m agentlib asvs check-assessment assessment.json`: the file is valid and complete, with 1 fail.

```json
{
  "application": "Customer portal 3.2 (commit 9f2c1ab)",
  "standard": "OWASP ASVS 5.0.0",
  "level": 1,
  "chapters": ["V2"],
  "results": [
    {"id": "2.1.1", "status": "pass", "evidence": "docs/security/input-validation.md v1.4 reviewed 2026-09-30"},
    {"id": "2.2.1", "status": "pass", "evidence": "api/validators.py schema validation; tests/test_validation.py negative tests"},
    {"id": "2.2.2", "status": "fail", "finding_ref": "F-12", "evidence": "Discount percentage validated only client-side; 150 accepted by direct POST"},
    {"id": "2.3.1", "status": "not-applicable", "justification": "No multi-step business logic flows; single-form submissions only (verified against routes and UI)"}
  ]
}
```

Result: 2 pass, 1 fail, 1 not applicable, so 66.7% of applicable requirements pass. Level 1 is not achieved for V2 until F-12 is
remediated and retested.
