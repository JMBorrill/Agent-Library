# Matrix check

Ran `python -m agentlib nasa-swe check-matrix fixtures/rmm-class-c.csv` (class C read from the file).

Class: C | rows: 92 | applicable: 92 | missing applicable: 2 | errors: 6 | warnings: 1 | info: 1.
Status counts: Compliant 87, Tailored 1, Not Applicable 2. Evidence coverage 95.6 %.

## Findings to fix before submission (errors)

| SWE | Problem | Fix |
|---|---|---|
| SWE-999 | Unknown id - not a requirement in NPR 7150.2D | Remove or correct the row |
| SWE-191 | Marked X for Class C in Appendix C but missing from the matrix (regression testing) | Add the row with status and evidence |
| SWE-202 | Marked X for Class C but missing (software severity levels) | Add the row |
| SWE-219 | Status Compliant but no evidence (100 % MC/DC coverage) | Attach the MC/DC coverage report |
| SWE-087 | Invalid status "Done" | Use an allowed value (e.g. Compliant + peer review records) |
| SWE-071 | Not Applicable without rationale | Give the justification and risk evaluation, or change status |

## Warnings and notes

- SWE-156 is Tailored with approval only from the Center ETA; relief from Section 3.11 cybersecurity
  requirements needs SAISO or Center CISO agreement [nasa-software-requirements SWE-150, p. 19].
- SWE-141 is blank (not invoked) for Class C in Appendix C, so its Not Applicable row is informational.

Every requirement marked X for the class must be addressed in the matrix, and tailoring of an X
requirement needs the Appendix C Authority's approval [nasa-software-requirements SWE-125, p. 22].
The check is a tool aid; acceptance of the matrix rests with the Technical Authorities.
