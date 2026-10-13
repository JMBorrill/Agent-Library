# Coverage and complexity rules for safety-critical software

| SWE | Requirement (NPR 7150.2D) | Source |
|---|---|---|
| SWE-219 | If the project has safety-critical software, 100 percent code test coverage using the Modified Condition/Decision Coverage (MC/DC) criterion for all identified safety-critical software components; deviations from 100 percent are reviewed and waived with rationale by the TAs (Note). | [nasa-software-requirements SWE-219, p. 26] |
| SWE-220 | All identified safety-critical components have a cyclomatic complexity value of 15 or lower; any exceedance is reviewed and waived with rationale by the project manager or technical approval authority. | [nasa-software-requirements SWE-220, p. 27] |
| SWE-134 | Safety-critical or mission-critical software implements items a-l (safe states, two independent operator actions for overrides, prerequisite checks, error handling ...). | [nasa-software-requirements SWE-134, p. 26] |
| SWE-135 | Static analysis during development and testing, incl. code coverage and complexity. | [nasa-software-requirements SWE-135, p. 34] |

Software assurance confirms 100 % coverage or a developer risk assessment, and confirms complexity of 15
or lower or a developer risk assessment (NASA-STD-8739.8B Table 1)
[nasa-software-assurance Table 1 SWE-219, p. 28] [nasa-software-assurance Table 1 SWE-220, p. 28].

The safety-critical determination itself is made by the project manager with the SMA organization
(SWE-205) [nasa-software-requirements SWE-205, p. 26].
