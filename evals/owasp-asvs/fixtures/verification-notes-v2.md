Verification notes - Customer portal 3.2 (commit 9f2c1ab), ASVS 5.0.0 Level 1, chapter V2 only.

- Input validation rules are documented in docs/security/input-validation.md v1.4 (reviewed 2026-09-30); covers all business data items.
- Server-side schema validation for every API body (api/validators.py); negative tests in tests/test_validation.py pass.
- The discount "percentage" field is validated only in the browser; posting 150 directly is accepted. Logged as finding F-12.
- The portal has no multi-step business flows (single-form submissions only); sequential-step logic does not exist.
