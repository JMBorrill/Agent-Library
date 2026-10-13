# Assurance case AC-ACME-1: Acme Checkout API is acceptable for release (fictional)

- **Scope:** Acme Checkout API (fictional), commit a1b2c3d
- **Decision authority:** Head of Security Assurance (fictional)

## Argument

- **C1** (high): The checkout API is acceptably secure for release.
  - *Argument:* Product security (ASVS V6 at L1) and secure development process (SSDF) both hold, with open findings treated as release conditions.
  - **C1.1** (high): Authentication requirements at ASVS L1 (V6) are met except F-01, F-02.
    - Evidence EV-1 [E3]: ASVS V6 L1 verification results (data/asvs-v6-l1.yaml)
  - **C1.2** (medium): Code is reviewed before merge.
    - Evidence EV-2 [E2]: SSDF assessment row PW.7.1 and branch protection settings (data/ssdf-assessment.yaml)
  - **C1.3** (medium): Release integrity can be verified by consumers. **[UNDEVELOPED]**
    - *Justification:* PS.2.1 is planned (target 2026-12-15); release signing not yet in place.

## Evidence register

| ID | Description | Artefact | Method | Strength |
|---|---|---|---|---|
| EV-1 | ASVS V6 L1 verification results | data/asvs-v6-l1.yaml | Test | E3 |
| EV-2 | SSDF assessment row PW.7.1 and branch protection settings | data/ssdf-assessment.yaml | Inspection | E2 |

_This case structures an argument for the decision authority; it does not by itself establish that the top claim is true._
