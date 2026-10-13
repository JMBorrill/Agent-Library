# Levels and scoping (ASVS 5.0.0)

Source: OWASP ASVS 5.0.0, "Application Security Verification Levels" to "How to use the ASVS"
(PDF pp. 13-15, printed 12-14) and "Scope of Verification" (PDF p. 19, printed 18). Paraphrased; read the
pages before quoting. Machine-readable level definitions: `catalog/owasp-asvs-5.json` -> `levels`.

## How the levels work

- Three levels, increasing in depth and complexity; organisations are expected to start at Level 1 and
  move up as their needs require (PDF p. 13).
- **Cumulative.** Each level states what must be achieved *at that level*; requirements of higher
  levels remain recommendations (PDF p. 13). For Level 2 an application must implement all L1 and L2
  requirements, around 70% of the standard (PDF p. 14). Tools in this library therefore select
  `level <= target` (`asvs checklist --level N`).
- Some requirements apply from one level but impose stricter conditions at higher levels inside the
  requirement text ("For L2 and up ...", "For L3 ..."), to avoid duplicates (PDF p. 13). Examples in the
  catalog: 3.4.1 (HSTS subdomains for L2+), 5.2.2 (file content checks for all files at L2+), 6.3.3
  (hardware-based factor for L3). When verifying at level N, apply the clause that matches N.
- Levelling is priority-based: risk reduction (C/I/A impact, first layer vs defence in depth) compared
  with implementation effort, while keeping a low barrier to entry (PDF p. 14). Organisations may pull
  specific higher-level requirements forward for their own risk reasons (PDF p. 14).

| Level | Character (paraphrase) | Count in 5.0.0 | Cumulative scope | PDF p. |
|---|---|---|---|---|
| L1 | Minimum, critical starting point; first-layer defences against common attacks needing no other precondition; ~20% of requirements. Not necessarily black-box testable. | 70 | 70 | 14 |
| L2 | What most applications should strive for; less common attacks or more complex protections. | 183 | 253 | 14 |
| L3 | Highest assurance; defence in depth and hard-to-implement controls (~30%). | 92 | 345 | 15 |

Counts are from the catalog; the standard itself states 70 L1 of 345 total (PDF p. 23).

## Choosing a level

ASVS deliberately does not prescribe a level for an application type. The organisation analyses its
risks and decides, considering application sensitivity and user expectations (PDF p. 15). Illustrations
from the standard: an early-stage start-up holding limited sensitive data might start at L1; an online
bank would find it hard to justify less than L3 to its customers (PDF p. 15). Version 5.0 explicitly
moved away from mandating levels by risk alone; maturity and the message to users also matter
(PDF p. 24).

Practical decision aid (library guidance, not ASVS text):

| Signal | Suggests |
|---|---|
| First adoption, low data sensitivity, small team, need a baseline quickly | L1, plan towards L2 |
| Typical business application handling personal or commercial data; most SaaS and internal line-of-business apps | L2 |
| High-value transactions, health/financial data at scale, safety- or life-critical, regulator/customer expects highest assurance | L3 (or L2 + selected L3) |
| Procurement / supplier assurance | State the level in the contract; require evidence of verification (PDF p. 18) |

Record the decision, the decision-maker (an accountable owner, not the verifier) and the rationale in
the verification plan.

## Scoping chapters and sections

- Chapters and sections exist so irrelevant parts can be filtered out (PDF p. 15). The standard's own
  examples: V3 (web frontend) is not relevant to a machine-to-machine API; V10 and V17 can be ignored
  when OAuth/OIDC or WebRTC are not used (PDF p. 15). Organisations are encouraged to tailor (fork)
  ASVS, omitting irrelevant sections such as GraphQL or WebSockets, while keeping requirement
  identifiers traceable (PDF pp. 16-17).
- V10 is organised by role: V10.1 generic, V10.2 OAuth client, V10.3 resource server, V10.4
  authorization server, V10.5 OIDC client (relying party), V10.6 OpenID Provider, V10.7 consent
  management (PDF pp. 62-70). Include only the roles the application plays (e.g.
  `--chapters V10.1 V10.2 V10.5` for an app that signs users in via an external OP).
- Application boundary: the application is the software product being developed; components that
  serve, modify or validate HTTP traffic (WAF, load balancer, proxy) can count for related controls;
  DNS, backups and other external processes are generally out of scope (PDF p. 11).
- **Report exclusions positively.** State what was included; give an opinion on the rationale for
  excluding requirements that were not implemented (PDF p. 19). Distinguish *chapter out of scope*
  (technology absent) from *requirement not applicable* (status `not-applicable` + justification),
  which the report must also list (PDF p. 19).

## Scope record (minimum)

1. Application name, version/commit, environments examined.
2. Target level and rationale; who decided.
3. In-scope chapters/sections; excluded chapters with reason.
4. Verification methods and access granted (docs, source, config, people).
5. Known constraints (time box, test accounts, environments not reachable).
