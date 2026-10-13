# ASVS verification plan - <Application name>

| Field | Value |
|---|---|
| Standard | OWASP ASVS 5.0.0 (identifiers `v5.0.0-<chapter>.<section>.<requirement>`) |
| Application / version | <name>, <version or commit>, <environment(s)> |
| Target level | L<1/2/3> - levels are cumulative (all requirements at or below L<n>) |
| Level decided by / date | <accountable owner>, <date> |
| Verifier(s) | <names, independence from development team> |
| Plan version / date | <v0.1>, <date> |

## 1. Level rationale

<Risk, data sensitivity, user expectations, contractual or regulatory drivers. Cite
[owasp-asvs Which level to achieve, p. 15].>

## 2. Scope

### Application boundary
<Components, interfaces (web UI, REST/GraphQL APIs, WebSocket, WebRTC), identity model (local auth / IdP /
OAuth roles), data classes, supporting HTTP components (WAF, proxy, load balancer) treated as in scope.>

### Chapters and sections included

| Chapter / section | Included? | Reason |
|---|---|---|
| V1 Encoding and Sanitization | Yes | |
| V3 Web Frontend Security | <Yes/No> | <e.g. No: machine-to-machine API only> |
| V10 OAuth and OIDC | <sections, e.g. V10.1, V10.2, V10.5> | <roles the application plays> |
| V17 WebRTC | <Yes/No> | |
| ... | | |

Checklist generated with:

```sh
python -m agentlib asvs checklist --level <n> --chapters <...> --format csv -o asvs-checklist.csv
```

In-scope requirement count: <from tool output>.

## 3. Verification approach

| Chapter | Methods (doc review / source review / config review / manual test / automated test) | Evidence expected | Access needed |
|---|---|---|---|
| V6 Authentication | | | |
| ... | | | |

Documentation requirements (`Vn.1`) are verified against the documents first; paired implementation
requirements are verified separately.

## 4. Access, accounts and environments

- Documentation: <list>
- Source repositories / commit: <list>
- Configuration (IdP, cloud, TLS, secrets manager): <list>
- Test accounts per role / tenant: <list>
- People available for interviews: <list>

## 5. Status vocabulary and recording

Statuses: `pass`, `fail` (requires finding reference), `not-applicable` (requires justification),
`not-verified` (work outstanding). Assessment file format: YAML/JSON/CSV with `id`, `status`,
`evidence`, `finding_ref`, `justification`; checked with
`python -m agentlib asvs check-assessment <file> --level <n> --chapters <...>`.

## 6. Schedule and deliverables

| Milestone | Date | Deliverable |
|---|---|---|
| Kick-off / access confirmed | | |
| Verification complete | | Assessment file passing `check-assessment` |
| Draft report | | Verification report |
| Retest | | Updated assessment |

## 7. Constraints, assumptions and risks

<Time box, environments unavailable, third-party components excluded, etc.>

---
Requirement text and structure: OWASP ASVS 5.0.0, (c) The OWASP Foundation, CC BY-SA 4.0.
