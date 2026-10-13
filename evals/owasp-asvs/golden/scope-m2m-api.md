# ASVS 5.0.0 scoping - Payments settlement API

## Target level

**Level 2 recommended, with selected Level 3 requirements for token and key handling.** ASVS does not
prescribe a level; the organisation chooses one from its risks, data sensitivity and user expectations
[owasp-asvs Which level to achieve, p. 15]. A payment settlement service moves money between partner
banks, so Level 2 is the defensible minimum. The accountable owner should decide whether to go to full
Level 3, the level the standard illustrates for online banking. Levels are cumulative: Level 2 means all
L1 and L2 requirements [owasp-asvs Level 2, p. 14].

## Chapter scope

| Chapter / section | In scope? | Reason |
|---|---|---|
| V1 Encoding and Sanitization | Yes | Processes untrusted partner data (JSON, CSV exports) |
| V2 Validation and Business Logic | Yes | Settlement amounts, sequencing, anti-automation |
| V3 Web Frontend Security | **No** | Machine-to-machine API with no browser frontend; the standard gives this example [owasp-asvs The structure of the ASVS, p. 15] |
| V4 API and Web Service | Yes (V4.1, V4.2; V4.3/V4.4 only if GraphQL/WebSocket are used - not the case) | REST API |
| V5 File Handling | Yes | Partner CSV batch upload |
| V6 Authentication | Partially - client authentication only, through the AS | No end-user login; record the N/A requirements individually with justifications |
| V7 Session Management | Not applicable as a whole: stateless bearer-token API | Each requirement is listed as N/A with a justification, as the report must note [owasp-asvs Verification reporting, p. 19] |
| V8 Authorization | Yes | Partner/tenant data separation |
| V9 Self-contained Tokens | Yes | JWT access tokens |
| V10 OAuth and OIDC | **V10.1 and V10.3 only** | The API is an OAuth resource server; the AS is a separate product (V10.4 out of scope); no OIDC |
| V11 Cryptography | Yes | Signing keys, payload encryption |
| V12 Secure Communication | Yes | mTLS between services |
| V13 Configuration | Yes | Secrets, backend connections |
| V14 Data Protection | Yes | Account numbers |
| V15 Secure Coding and Architecture | Yes | Dependencies, concurrency (double-settlement races) |
| V16 Security Logging and Error Handling | Yes | Audit trail |
| V17 WebRTC | **No** | Not used [owasp-asvs The structure of the ASVS, p. 15] |

## Checklist

```sh
python -m agentlib asvs checklist --level 2 --chapters V1 V2 V4 V5 V6 V7 V8 V9 V10.1 V10.3 V11 V12 V13 V14 V15 V16 --format csv -o asvs-l2.csv
```

Chapter exclusions (V3, V17, V10.4-V10.7) must appear in the report, together with the verifier's
opinion on them. The report should describe what was included rather than what was left out
[owasp-asvs Scope of Verification, p. 19].
