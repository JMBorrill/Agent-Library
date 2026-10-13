# SBOM / Provenance Record

> Record supporting SSDF v1.1 PS.3.2 ("Collect, safeguard, maintain, and share provenance data for all
> components of each software release (e.g., in a software bill of materials [SBOM])", NIST SP 800-218 Table 1,
> PDF p.19) and PW.4.1 Example 3 (obtain provenance information for acquired components, PDF p.21).
> SP 800-218 defines provenance (footnote, PDF p.15) by quoting SP 800-53. SSDF does not mandate an SBOM format
> or field list; its References column for PS.3.2 points to NTIASBOM (NTIA minimum elements) among others - use
> your chosen standard's required fields.

| Field | Value |
|---|---|
| Product / release | |
| Release date | |
| Build id / commit | |
| Record owner | |

## 1. SBOM
| Item | Value |
|---|---|
| Format and version | [e.g. SPDX x.y / CycloneDX x.y] |
| Generation tool and version | |
| Generated at (build stage) | [source / build / binary analysis] |
| Location (immutable) | |
| Hash of SBOM file | |
| Signature / attestation reference | (PS.3.2 Ex.3: protect integrity and let recipients verify) |
| Completeness notes (known unknowns, excluded components) | |

## 2. Build provenance
| Item | Value |
|---|---|
| Source repository and revision | |
| Build platform / runner identity | |
| Build definition (pipeline file + revision) | |
| Inputs fetched (dependency sources, registries) | |
| Provenance statement location and signature | |

## 3. Third-party component provenance (PW.4.1 Ex.3, Ex.5)
| Component | Version | Supplier / origin | Provenance evidence (SBOM, SCA, binary SCA) | Approved? |
|---|---|---|---|---|

## 4. Sharing and maintenance
| Recipient | What is shared | Format | Channel | Policy reference |
|---|---|---|---|---|
| Acquirers / customers | | | | (PS.3.2 Ex.1) |
| Internal operations / PSIRT | | | | (PS.3.2 Ex.2) |

Update trigger: regenerate whenever any component changes (PS.3.2 Ex.4). Monitoring: SBOM fed into
vulnerability monitoring (RV.1.1 Ex.3).

---
Record supports, but does not replace, qualified professional judgement.
