# Evidence record

| Field | Value |
|---|---|
| Record ID | EV-0001 |
| Requirement / control assessed | `PW.7.1` code review [nist-ssdf PW.7.1, p. 23] |
| Artefact examined | Branch protection settings of `app/payments`; 20 merged pull requests (September) |
| Artefact version | commit a1b2c3d; settings as viewed 2026-10-01 |
| Method | Inspection |
| Examined by / date | Assessor, 2026-10-01 |
| Observation (facts only) | Branch protection requires one approving review; all 20 sampled pull requests had one approval before merge. |
| Result | Met (for the sampled period) |
| Claim strength | E3 — corroborated by configuration and pull-request history |
| Assessor judgement | Evidence indicates peer review is enforced and practised; review depth and use of security criteria were not assessed. |
| Linked findings / actions | Consider a security-focused review checklist. |
| Limitations | Sample limited to September; administrators' ability to bypass protection not tested. |
