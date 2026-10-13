# SSDF PS.3.2 - provenance data and SBOMs

**Task (NIST SP 800-218, SSDF v1.1, Table 1, PS.3.2, PDF p.19 / printed p.10):** "Collect, safeguard,
maintain, and share provenance data for all components of each software release (e.g., in a software bill of
materials [SBOM])." It sits under practice PS.3 "Archive and Protect Each Software Release" in the Protect the
Software (PS) group.

## What it means

For every release you should know which components it contains and where they came from, keep that
provenance data protected and current, and share it with the people who need it. The SBOM is the example the
task gives; SSDF does not mandate an SBOM format. Provenance is defined in a footnote by quoting SP 800-53 as
the chronology of the origin, development, ownership, location and changes to a component (PDF p.15).

The four notional implementation examples (options, not requirements - PDF p.13) are:

1. Share provenance data with acquirers per policy, preferably in standards-based formats.
2. Share it with internal operations and response teams to help mitigate vulnerabilities.
3. Protect its integrity and let recipients verify it.
4. Update it every time any component changes.

Related tasks: PS.3.1 (p.19) - archive release files and provenance data; PW.4.1 (p.21) Example 3 - obtain
provenance for acquired components; RV.1.1 (p.25) Example 3 - use composition data to spot new vulnerabilities.
Appendix A Table 2 maps PS.3.2 to EO 14028 Section 4e(vi), 4e(vii) and 4e(x) (PDF p.33).

## Evidence an assessor should ask for

| Element | Evidence |
|---|---|
| Collected | SBOM files for the last few releases, generated in the build; tool and format |
| Complete | Comparison of SBOM against lockfiles/images for one release; documented known gaps |
| Safeguarded | Signature or attestation over the SBOM; storage with restricted write access |
| Maintained | Evidence SBOMs regenerate when components change (pipeline config, release history) |
| Shared | Customer-facing distribution channel or policy; internal PSIRT access |

Status guidance: an SBOM that is generated but not protected, kept current or shared is `partial`, not
`implemented`.

This explanation supports, but does not replace, qualified professional judgement.
