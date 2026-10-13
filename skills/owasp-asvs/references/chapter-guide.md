# ASVS 5.0.0 chapter and section guide

Generated from `catalog/owasp-asvs-5.json` (regenerate with `python -m agentlib asvs chapters --sections`). 
Counts are requirements per level; *Cum. L2* = requirements in scope for a Level 2 verification (L1 + L2). 
PDF page = page of the pinned file `sources/pdfs/owasp-asvs-5-0-0-en.pdf`; printed page = PDF page - 1.

Content: OWASP ASVS 5.0.0, (c) The OWASP Foundation, CC BY-SA 4.0.

## Chapters

| Chapter | Title | Total | L1 | L2 | L3 | Cum. L2 | PDF p. | Typical applicability trigger |
|---|---|---|---|---|---|---|---|---|
| V1 | Encoding and Sanitization | 30 | 8 | 19 | 3 | 27 | 24 | Any app that processes untrusted data (practically always) |
| V2 | Validation and Business Logic | 13 | 4 | 7 | 2 | 11 | 29 | Any app with input or business workflows |
| V3 | Web Frontend Security | 31 | 8 | 11 | 12 | 19 | 33 | Browser-rendered web frontend; omit for pure machine-to-machine APIs (PDF p. 15) |
| V4 | API and Web Service | 16 | 2 | 8 | 6 | 10 | 39 | HTTP APIs, web services, GraphQL, WebSocket |
| V5 | File Handling | 13 | 4 | 5 | 4 | 9 | 42 | File upload, storage or download |
| V6 | Authentication | 47 | 13 | 22 | 12 | 35 | 45 | The app authenticates users or services itself, or relies on an IdP |
| V7 | Session Management | 19 | 6 | 12 | 1 | 18 | 53 | Stateful sessions (N/A only for genuinely stateless designs, cf. PDF p. 19) |
| V8 | Authorization | 13 | 4 | 3 | 6 | 7 | 57 | Any access control (practically always) |
| V9 | Self-contained Tokens | 7 | 4 | 3 | 0 | 7 | 60 | JWT or other self-contained tokens |
| V10 | OAuth and OIDC | 36 | 5 | 24 | 7 | 29 | 62 | OAuth / OIDC client, resource server, AS or OP roles (omit if unused, PDF p. 15) |
| V11 | Cryptography | 24 | 3 | 11 | 10 | 14 | 71 | Any use of cryptography |
| V12 | Secure Communication | 12 | 3 | 6 | 3 | 9 | 76 | Any network communication (practically always) |
| V13 | Configuration | 21 | 1 | 12 | 8 | 13 | 78 | Deployment configuration, secrets, backend connections |
| V14 | Data Protection | 13 | 2 | 7 | 4 | 9 | 82 | Sensitive data defined for the app |
| V15 | Secure Coding and Architecture | 21 | 3 | 10 | 8 | 13 | 85 | Architecture, dependencies, defensive coding (always) |
| V16 | Security Logging and Error Handling | 17 | 0 | 16 | 1 | 16 | 89 | Logging and error handling (always) |
| V17 | WebRTC | 12 | 0 | 7 | 5 | 7 | 93 | WebRTC (omit if unused, PDF p. 15) |
| **All** | | **345** | **70** | **183** | **92** | **253** | | |

## Sections

Sections whose title ends in *Documentation* hold the documented-security-decision requirements; the standard places them first in a chapter and pairs each with an implementation requirement (PDF p. 12).

| Section | Title | Reqs | L1 | L2 | L3 | PDF p. |
|---|---|---|---|---|---|---|
| V1.1 | Encoding and Sanitization Architecture | 2 | 0 | 2 | 0 | 24 |
| V1.2 | Injection Prevention | 10 | 5 | 4 | 1 | 25 |
| V1.3 | Sanitization | 12 | 2 | 9 | 1 | 26 |
| V1.4 | Memory, String, and Unmanaged Code | 3 | 0 | 3 | 0 | 28 |
| V1.5 | Safe Deserialization | 3 | 1 | 1 | 1 | 28 |
| V2.1 | Validation and Business Logic Documentation | 3 | 1 | 2 | 0 | 30 |
| V2.2 | Input Validation | 3 | 2 | 1 | 0 | 30 |
| V2.3 | Business Logic Security | 5 | 1 | 3 | 1 | 31 |
| V2.4 | Anti-automation | 2 | 0 | 1 | 1 | 32 |
| V3.1 | Web Frontend Security Documentation | 1 | 0 | 0 | 1 | 33 |
| V3.2 | Unintended Content Interpretation | 3 | 2 | 0 | 1 | 33 |
| V3.3 | Cookie Setup | 5 | 1 | 3 | 1 | 34 |
| V3.4 | Browser Security Mechanism Headers | 8 | 2 | 4 | 2 | 34 |
| V3.5 | Browser Origin Separation | 8 | 3 | 2 | 3 | 36 |
| V3.6 | External Resource Integrity | 1 | 0 | 0 | 1 | 37 |
| V3.7 | Other Browser Security Considerations | 5 | 0 | 2 | 3 | 38 |
| V4.1 | Generic Web Service Security | 5 | 1 | 2 | 2 | 39 |
| V4.2 | HTTP Message Structure Validation | 5 | 0 | 1 | 4 | 40 |
| V4.3 | GraphQL | 2 | 0 | 2 | 0 | 41 |
| V4.4 | WebSocket | 4 | 1 | 3 | 0 | 41 |
| V5.1 | File Handling Documentation | 1 | 0 | 1 | 0 | 42 |
| V5.2 | File Upload and Content | 6 | 2 | 1 | 3 | 43 |
| V5.3 | File Storage | 3 | 2 | 0 | 1 | 43 |
| V5.4 | File Download | 3 | 0 | 3 | 0 | 44 |
| V6.1 | Authentication Documentation | 3 | 1 | 2 | 0 | 45 |
| V6.2 | Password Security | 12 | 8 | 4 | 0 | 46 |
| V6.3 | General Authentication Security | 8 | 2 | 2 | 4 | 47 |
| V6.4 | Authentication Factor Lifecycle and Recovery | 6 | 2 | 2 | 2 | 48 |
| V6.5 | General Multi-factor authentication requirements | 8 | 0 | 5 | 3 | 49 |
| V6.6 | Out-of-Band authentication mechanisms | 4 | 0 | 3 | 1 | 50 |
| V6.7 | Cryptographic authentication mechanism | 2 | 0 | 0 | 2 | 51 |
| V6.8 | Authentication with an Identity Provider | 4 | 0 | 4 | 0 | 52 |
| V7.1 | Session Management Documentation | 3 | 0 | 3 | 0 | 54 |
| V7.2 | Fundamental Session Management Security | 4 | 4 | 0 | 0 | 54 |
| V7.3 | Session Timeout | 2 | 0 | 2 | 0 | 55 |
| V7.4 | Session Termination | 5 | 2 | 3 | 0 | 55 |
| V7.5 | Defenses Against Session Abuse | 3 | 0 | 2 | 1 | 56 |
| V7.6 | Federated Re-authentication | 2 | 0 | 2 | 0 | 57 |
| V8.1 | Authorization Documentation | 4 | 1 | 1 | 2 | 58 |
| V8.2 | General Authorization Design | 4 | 2 | 1 | 1 | 58 |
| V8.3 | Operation Level Authorization | 3 | 1 | 0 | 2 | 59 |
| V8.4 | Other Authorization Considerations | 2 | 0 | 1 | 1 | 59 |
| V9.1 | Token source and integrity | 3 | 3 | 0 | 0 | 60 |
| V9.2 | Token content | 4 | 1 | 3 | 0 | 61 |
| V10.1 | Generic OAuth and OIDC Security | 2 | 0 | 2 | 0 | 64 |
| V10.2 | OAuth Client | 3 | 0 | 2 | 1 | 64 |
| V10.3 | OAuth Resource Server | 5 | 0 | 4 | 1 | 65 |
| V10.4 | OAuth Authorization Server | 16 | 5 | 6 | 5 | 66 |
| V10.5 | OIDC Client | 5 | 0 | 5 | 0 | 68 |
| V10.6 | OpenID Provider | 2 | 0 | 2 | 0 | 69 |
| V10.7 | Consent Management | 3 | 0 | 3 | 0 | 69 |
| V11.1 | Cryptographic Inventory and Documentation | 4 | 0 | 2 | 2 | 71 |
| V11.2 | Secure Cryptography Implementation | 5 | 0 | 3 | 2 | 72 |
| V11.3 | Encryption Algorithms | 5 | 2 | 1 | 2 | 73 |
| V11.4 | Hashing and Hash-based Functions | 4 | 1 | 3 | 0 | 74 |
| V11.5 | Random Values | 2 | 0 | 1 | 1 | 74 |
| V11.6 | Public Key Cryptography | 2 | 0 | 1 | 1 | 75 |
| V11.7 | In-Use Data Cryptography | 2 | 0 | 0 | 2 | 75 |
| V12.1 | General TLS Security Guidance | 5 | 1 | 2 | 2 | 76 |
| V12.2 | HTTPS Communication with External Facing Services | 2 | 2 | 0 | 0 | 77 |
| V12.3 | General Service to Service Communication Security | 5 | 0 | 4 | 1 | 77 |
| V13.1 | Configuration Documentation | 4 | 0 | 1 | 3 | 79 |
| V13.2 | Backend Communication Configuration | 6 | 0 | 5 | 1 | 79 |
| V13.3 | Secret Management | 4 | 0 | 2 | 2 | 80 |
| V13.4 | Unintended Information Leakage | 7 | 1 | 4 | 2 | 81 |
| V14.1 | Data Protection Documentation | 2 | 0 | 2 | 0 | 82 |
| V14.2 | General Data Protection | 8 | 1 | 3 | 4 | 83 |
| V14.3 | Client-side Data Protection | 3 | 1 | 2 | 0 | 84 |
| V15.1 | Secure Coding and Architecture Documentation | 5 | 1 | 2 | 2 | 85 |
| V15.2 | Security Architecture and Dependencies | 5 | 1 | 2 | 2 | 86 |
| V15.3 | Defensive Coding | 7 | 1 | 6 | 0 | 87 |
| V15.4 | Safe Concurrency | 4 | 0 | 0 | 4 | 88 |
| V16.1 | Security Logging Documentation | 1 | 0 | 1 | 0 | 90 |
| V16.2 | General Logging | 5 | 0 | 5 | 0 | 90 |
| V16.3 | Security Events | 4 | 0 | 4 | 0 | 91 |
| V16.4 | Log Protection | 3 | 0 | 3 | 0 | 92 |
| V16.5 | Error Handling | 4 | 0 | 3 | 1 | 92 |
| V17.1 | TURN Server | 2 | 0 | 1 | 1 | 94 |
| V17.2 | Media | 8 | 0 | 4 | 4 | 94 |
| V17.3 | Signaling | 2 | 0 | 2 | 0 | 96 |
