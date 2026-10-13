# Rule catalogue for static_checks.py

Original to this library. ASVS references are to OWASP ASVS 5.0.0 chapter/section titles
(CC BY-SA 4.0, © The OWASP Foundation); read the requirements in that section for the actual
verification criteria.

| ID | Rule | Detects (heuristic) | Typical fix | ASVS 5.0.0 area (mapping) |
|---|---|---|---|---|
| SC001 | hardcoded-secret | AWS key IDs (`AKIA` + 16), private key blocks, `sk-...`, GitHub tokens, credential-named variables assigned a literal | Secret manager / environment; rotate; purge history | V13.3 Secret Management (section) |
| SC002 | sql-string-building | SQL keywords on a line with f-string, `%`, `.format(`, `+` or JS `${}` interpolation | Parameterised queries / bound parameters | V1.2 Injection Prevention (section) |
| SC003 | missing-tenant-filter | SQL string (or `.sql` statement) touching a configured tenant table without the tenant column; INSERT without the tenant column | Repository-layer tenant scoping, row-level security, tests per tenant | V8 Authorization (chapter) |
| SC004 | debug-mode-enabled | `DEBUG = True`, `app.run(debug=True)`, `app.debug = True`, `FLASK_DEBUG=1`, `NODE_ENV='development'` | Environment-specific config; debug off by default | V13.4 Unintended Information Leakage (section) |
| SC005 | weak-password-hash | MD5/SHA-1 call within 3 lines of a password word | Argon2id, scrypt, bcrypt or PBKDF2 with per-password salt | V11.4 Hashing and Hash-based Functions (section) |
| SC006 | insecure-deserialization | `pickle/cPickle/dill/marshal/shelve.load(s)`, `yaml.load` without SafeLoader, `yaml.unsafe_load`, `unserialize(` | JSON; `yaml.safe_load`; signed, schema-validated formats | V1.5 Safe Deserialization (section) |
| SC007 | tls-verification-disabled | `verify=False`, `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `CERT_NONE`, `check_hostname=False`, unverified SSL context | Keep verification on; pin a private CA bundle if needed | V12 Secure Communication (chapter) |
| SC008 | cors-wildcard-credentials | Any-origin CORS (`*` or reflect-all `origin: true`) within 8 lines of credentials enabled | Explicit origin allow-list | V3.5 Browser Origin Separation (section) |
| SC009 | jwt-verification-disabled | `none` in allowed algorithms, `"alg": "none"`, `verify_signature: False`, `jwt.decode(..., verify=False)` | Fixed algorithm allow-list, verify signature, audience and expiry | V9.1 Token source and integrity (section) |

## Why title-level mapping only
The bundled ASVS index carries requirement IDs, levels and section titles but not requirement text.
Assigning a specific requirement ID would be a guess, so rules cite the section whose title clearly
matches, or only the chapter when two or more sections could apply (e.g. V12.1/V12.2/V12.3 for TLS;
V8.2/V8.3 for tenant scoping). A human should pick the exact requirement when recording evidence.

## Known blind spots
- ORM/query-builder injection, stored procedures, dynamic table names.
- Secrets split across lines, base64-encoded or in non-scanned file types (YAML, .env, JSON).
- Tenant scoping implemented in middleware/RLS (the rule may flag queries that are actually safe —
  suppress with the reason "RLS policy X enforces tenant_id").
- Framework defaults (e.g. Django `DEBUG` from environment) and runtime configuration.

## Suppression format
`static-checks: ignore[SC003] RLS policy tenant_isolation on appointments enforces tenant_id`
on the reported line. Missing reason → suppression ignored and the finding stays an error.
