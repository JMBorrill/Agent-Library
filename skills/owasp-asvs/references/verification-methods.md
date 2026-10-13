# Verification methods

Source: OWASP ASVS 5.0.0 "How to Verify ASVS Compliance" and "Verification Mechanisms" (PDF pp. 19-20,
printed 18-19), "Use cases" (PDF pp. 17-18). Paraphrased.

## What the standard says

- ASVS is deliberately not a testing guide; how to test a requirement in a given environment belongs to
  the OWASP Web Security Testing Guide, how to implement it to the Cheat Sheet Series (PDF pp. 12, 19).
- Verifying many requirements (especially L2 and L3) needs access to documentation, source code,
  configuration and the people involved, in addition to penetration testing with valid credentials
  (PDF p. 20).
- Provide robust evidence: work papers, screenshots, scripts, testing logs. Running an automated tool
  without thorough testing is insufficient; every requirement must be verifiably tested (PDF p. 20).
- DAST/SAST can cover some straightforward technical requirements (e.g. output encoding) when tuned, but
  cannot fully verify complex requirements, business logic or access control. "Testable using automation"
  is not the same as running an off-the-shelf tool; application-specific automated tests (like unit or
  integration tests) are encouraged (PDF p. 20; see also PDF p. 18 on automated tests).
- Black-box testing without documentation or source is discouraged as inefficient and ineffective;
  prefer documentation- or source-code-led (hybrid) testing with access to developers (PDF p. 20).
- Methods may vary by organisation but must be disclosed in the report and ideally be repeatable
  (PDF p. 19).

## Method selection per requirement type (library guidance)

| Requirement type | Primary method | Supporting evidence |
|---|---|---|
| Documentation (`Vn.1 ... Documentation`, also 10.1, 11.1) | Document review against the requirement | Document id/version, approver; then verify the paired implementation requirement separately (PDF p. 12) |
| Injection, encoding, sanitisation (V1) | Source review of sinks + targeted dynamic tests | Code locations, test payloads and responses |
| Business logic, anti-automation (V2) | Design walkthrough + manual testing of flows | Flow diagrams, test cases, rate-limit config |
| Browser headers, cookies, origin separation (V3) | Response inspection (automatable) + config review | Header captures for representative responses |
| API, GraphQL, WebSocket (V4) | API spec review + dynamic tests | OpenAPI/GraphQL schema, request/response logs |
| Authentication, session, tokens, OAuth/OIDC (V6, V7, V9, V10) | Configuration + source review + manual tests with valid accounts | IdP/AS config exports, token samples (redacted) |
| Authorization (V8) | Matrix-driven manual tests with multiple roles/tenants + code review of enforcement point | Access matrix, test evidence per role |
| Cryptography, TLS, secrets (V11, V12, V13.3) | Inventory review + config scans + code review | Crypto inventory, TLS scan output, vault config |
| Configuration and leakage (V13) | Deployed-environment checks | Screens/requests from production-like env |
| Data protection (V14) | Data classification review + traffic/cache inspection | Classification doc, cache headers, storage review |
| Secure coding, dependencies (V15) | SCA output + code review + architecture review | SBOM, remediation SLA vs component age |
| Logging and errors (V16) | Log inventory review + induced events and errors | Sample log lines, error responses |
| WebRTC (V17) | TURN/media/signalling config review + targeted tests | Server config, DTLS/SRTP settings |

## Evidence record minimum

Requirement id (v5.0.0-x.y.z), method, artefact examined (path/URL, version/commit, environment), date,
verifier, observation, result (pass/fail/not-applicable/not-verified), finding id (if fail),
justification (if N/A). Use the library evidence discipline (`skills/evidence-and-citation/`) for claim
strength and citation format.
