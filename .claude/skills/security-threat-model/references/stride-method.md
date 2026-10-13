# STRIDE data-flow threat modelling notes

Original guidance for this library. STRIDE (Spoofing, Tampering, Repudiation, Information
disclosure, Denial of service, Elevation of privilege) is a mnemonic that originated at Microsoft;
it is not part of OWASP ASVS or any other registered source. Statements about STRIDE conventions are
general knowledge *(unverified here)*.

## Element types and the categories that usually apply
| Element | Typical categories | Notes |
|---|---|---|
| External entity | S, R | Who is it really? Can they deny actions? |
| Process | S, T, R, I, D, E | All six; elevation lives here. |
| Data store | T, I, D (R if it holds logs) | Integrity, confidentiality, availability of data at rest. |
| Data flow | T, I, D | The script's default per boundary-crossing flow. |

## Multi-tenant SaaS: tenant-isolation threat prompts
- Tenant identifier accepted from the request body, path or header instead of the authenticated session.
- Query or ORM call missing the tenant filter; reporting/export jobs that bypass the repository layer.
- Shared caches keyed without tenant; search indexes shared across tenants.
- Background jobs and queues that lose the tenant context, or retry under a default tenant.
- AI features: retrieval or conversation memory mixing tenants; prompts that include another
  tenant's records; model output used to call tools without an authorization re-check.
- Admin/support impersonation features without audit and scoping.

## Rating
Likelihood × impact on 1–3 (low, medium, high): 9 or 6 → high, 4 or 3 → medium, 2 or 1 → low.
This is a coarse, explainable rating for prioritisation, not a quantitative risk analysis. Use
`se-risk-analysis` when you need consequence/likelihood tables tied to a project risk register.

## Mapping mitigations to ASVS 5.0.0
- Cite as `v5.0.0-<chapter>.<section>.<requirement>` (the lowercase `v` and version are part of the
  ASVS-recommended citation). `ASVS-v5.0.0-x.y.z` (library convention) is also accepted.
- Pick IDs by reading the requirement text; the index only carries chapter/section titles and the
  minimum level. Section titles that commonly fit: V8.2 General Authorization Design and V8.3
  Operation Level Authorization (tenant isolation); V1.2 Injection Prevention; V3.3 Cookie Setup;
  V12.2 HTTPS Communication with External Facing Services; V2.4 Anti-automation; V14.2 General
  Data Protection; V13.3 Secret Management.
- ASVS v4 and v5 IDs differ throughout; never carry a v4 ID forward without re-mapping.

## Common review challenges
- "Which flow carries the session token, and where is it validated?"
- "What happens to tenant context when this job is retried?"
- "What does the AI provider keep, for how long, and who agreed to it?"
- "Who owns this accepted risk, and when is it revisited?"
