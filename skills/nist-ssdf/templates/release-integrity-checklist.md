# Software Release Integrity Checklist

> Per-release checklist supporting SSDF v1.1 PS.1 (Protect All Forms of Code), PS.2 (Provide a Mechanism for
> Verifying Software Release Integrity), PS.3 (Archive and Protect Each Software Release) and related build
> tasks (PO.3.2, PO.5.1, PW.6.2, PW.4.4). NIST SP 800-218 Table 1, PDF pp.16-23. Items reflect notional
> implementation examples - they are options, not SSDF requirements; tick what your policy requires.

| Field | Value |
|---|---|
| Product / component | |
| Release version | |
| Build id / pipeline run | |
| Release manager | |
| Date | |

## Source and build
- [ ] All changes merged through reviewed pull requests with code-owner approval (PS.1.1 Ex.4)
- [ ] Commits signed / signature policy satisfied (PS.1.1 Ex.3)
- [ ] Build ran from pipeline-as-code in the dedicated build environment (PO.3.2 Ex.3; PW.6.2 Ex.3)
- [ ] Build tools and pipeline dependencies verified (integrity/provenance) (PO.3.2 Ex.7)
- [ ] Approved compiler/build configuration used; no unexplained warnings (PW.6.2)
- [ ] Third-party components checked for known vulnerabilities and integrity (PW.4.4 Ex.1, Ex.2, Ex.6)
- [ ] Security criteria/gates for this release met or exceptions approved (PO.4.1, PO.4.2)

## Integrity information for acquirers (PS.2.1)
- [ ] Release files hashed; hashes published on a well-secured site (PS.2.1 Ex.1)
- [ ] Executables/packages signed with a certificate consumers can validate (PS.2.1 Ex.2; PS.1.1 Ex.5)
- [ ] Signing keys protected; code signing process reviewed recently (PS.2.1 Ex.3)

## Provenance and archive (PS.3.1, PS.3.2)
- [ ] SBOM / provenance data produced for this release (see SBOM/provenance record template)
- [ ] Provenance data integrity protected (signed or stored separately) (PS.3.1 Ex.2; PS.3.2 Ex.3)
- [ ] Provenance made available to acquirers and internal response teams per policy (PS.3.2 Ex.1, Ex.2)
- [ ] Release files and images archived with read-only access (PS.3.1 Ex.1)
- [ ] Retention period recorded (policy per PO.1.2 Ex.4)

## Sign-off
| Role | Name | Decision | Date |
|---|---|---|---|
| Release manager | | | |
| Security reviewer | | | |

---
Checklist supports, but does not replace, qualified professional judgement and release approval.
