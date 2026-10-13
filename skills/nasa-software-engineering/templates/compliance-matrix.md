# Requirements Mapping Matrix - NPR 7150.2D - <project / component>

> Generate the rows with `python -m agentlib nasa-swe matrix --class <X> [--safety-critical] [--ivv]`
> (md, csv or json) - do not type the list by hand. Validate with
> `python -m agentlib nasa-swe check-matrix <file> --class <X>` until it reports 0 errors.

Software class: <A-F>
Safety-critical software: <yes / no / pending SWE-205>
Software IV&V: <yes / no>
Classification record: <ref>  |  Matrix version: <v>  |  Date: <yyyy-mm-dd>

Allowed status values: Compliant, Partially Compliant, Non-Compliant, Planned, Tailored, Not Applicable.

| SWE | Section | Requirement | Authority | Condition | Status | Tailoring / waiver rationale | Approval | Evidence |
|---|---|---|---|---|---|---|---|---|
| SWE-033 | 3.1.2 | The project manager shall assess options for software acquisition versus development. | Center |  | <status> | <rationale if not Compliant> | <approver> | <document id / link> |
| ... | | | | | | | | |

## Tailoring requests (one per tailored 'X' requirement)

| SWE | Relief requested (partial / complete) | Rationale | Risk evaluation and mitigations | Supporting material | Authority | Signature / date |
|---|---|---|---|---|---|---|

Rules: approval of the Authority named in Appendix C is required for tailoring of 'X' requirements
(NPR 7150.2D 2.2.5, p. 18); HQ-authority requirements need NASA HQ approval (p. 17); Section 3.11
cybersecurity relief needs SAISO / Center CISO agreement (pp. 12, 19).

## Signatures (NPR 7150.2D 2.2.6, SWE-126 b)

| Role | Name | Signature | Date |
|---|---|---|---|
| Project manager | | | |
| Engineering Technical Authority | | | |
| SMA Technical Authority | | | |
| CIO / SAISO (Class F or 3.11 relief) | | | |
| Health and Medical TA (if applicable) | | | |
