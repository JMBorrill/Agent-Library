# Security requirements - document upload (ASVS Level 2)

| ID | Level | Requirement (short) | Acceptance test |
|---|---|---|---|
| V5.2.1 | 1 | Limit file size | 21 MB upload rejected |
| V5.2.2 | 1 | Check extension and content | Renamed .exe rejected |
| V5.2.4 | 2 | Per-user file quota | Quota exceeded rejected |
| V5.3.1 | 1 | Do not execute uploaded files | 403 on direct access |
| V5.3.2 | 1 | Generated storage paths | Traversal attempt stored safely |
| V12.3.1 | 2 | Virus-scan uploads | EICAR quarantined |

Documentation of upload policy is optional at Level 2.
