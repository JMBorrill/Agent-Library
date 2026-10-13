# ASVS verification plan (fictional example)

- **Application:** Acme Checkout API (fictional), commit a1b2c3d.
- **Target level:** L1 for this illustrative sample, scoped to V6 Authentication. A real payments API would
  normally justify L2 or above: ASVS leaves level choice to the organisation's risk assessment
  [owasp-asvs, p. 15], and higher levels are recommendations rather than mandatory [owasp-asvs, p. 13].
- **Method:** configuration review, code review and test of each requirement; evidence recorded per row.
- **Checklist:** `python -m agentlib asvs checklist --level 1 --chapters V6` (13 requirements).
