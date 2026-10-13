# ASVS verification report (fictional example)

Two failures, each with a finding: F-01 (6.3.1) and F-02 (6.4.1). Results below are tool output.

```text
# ASVS 5.0.0 assessment check - Level 1

- Scope: V6
- Verdict: **NOT COMPLIANT (failures)** (valid=True, complete=True)
- In scope: 13 | pass 11 | fail 2 | N/A 0 | not-verified 0 | missing 0 | invalid 0
- Compliance: 84.6% (pass / (in-scope - not-applicable) x 100; missing, invalid and not-verified count as not passed)

## Per-chapter results

| Chapter | In scope | Pass | Fail | N/A | Not verified | Missing | Compliance |
|---|---|---|---|---|---|---|---|
| V6 Authentication | 13 | 11 | 2 | 0 | 0 | 0 | 84.6% |

## Failures

- 6.3.1 (L1) - finding F-01: Verify that controls to prevent attacks such as credential stuffing and password brute force are implemented according to the application’s security documentation.
- 6.4.1 (L1) - finding F-02: Verify that system generated initial passwords or activation codes are securely randomly generated, follow the existing password policy, and expire after a short period of time or after they are initially used. These initial secrets must not be permitted to become the long term password.

## Errors

- none
```
