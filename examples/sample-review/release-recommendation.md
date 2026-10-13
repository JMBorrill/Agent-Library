# Review board decision record (fictional example)

| Field | Value |
|---|---|
| Review | secure-software-delivery v1.0.0 |
| Subject | Acme Checkout API (fictional), commit a1b2c3d |
| Accountable decision-maker | Head of Security Assurance (fictional) |

## Recommendation

**Proceed with conditions.** ASVS V6 (L1) verification found two failures (F-01, F-02); the SSDF assessment
shows release integrity verification (PS.2.1) is planned, not implemented. The assurance case
(`assurance-case.md`) is *incomplete* by design: claim C1.3 is undeveloped.

## Conditions and actions

| ID | Action | Owner | Due | Closes |
|---|---|---|---|---|
| A-1 | Fix F-01 and F-02 and re-verify 6.3.1 and 6.4.1 | Auth team | before release | F-01, F-02 |
| A-2 | Implement release signing and publish verification instructions | Platform security lead | 2026-12-15 | PS.2.1, C1.3 |

## Residual risks

| Risk | Proposed treatment | Acceptance authority |
|---|---|---|
| Consumers cannot verify release integrity until A-2 | Accept temporarily with A-2 tracked | Head of Security Assurance |

## Limitations

Fictional, illustrative example produced with AI assistance. It does not constitute approval; the decision
rests with the accountable decision-maker named above.
