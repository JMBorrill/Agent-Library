# Risk method notes (library guidance)

Original text; aligned with common risk-management practice. NASA SE Handbook §6.4 and related NASA
risk-management guidance (e.g. risk-informed decision making and continuous risk management) are the
registered source family but were not readable in-session — terms below are generic.

## Risk vs issue
A **risk** is a possible future event; an **issue** has happened (a failed test, a late part). Issues
go to the action/NCR log; they may create new risks.

## Writing statements
Good: "Given the latch pawl wears with each cycle, there is a possibility the latch releases under load
during setup, resulting in uncontrolled leg motion within reach of the operator."
Poor: "Latch might fail." — no condition, no consequence, cannot be mitigated purposefully.

## Ordinal scoring
Likelihood and consequence scales are labels with defined descriptors (e.g. consequence 5 = injury or
loss of the test article). Multiplying them only ranks risks; it does not create a probability. Keep
the descriptors in the policy file next to the thresholds.

## Handling approaches
- **Mitigate** — act to reduce likelihood and/or consequence; becomes verifiable when linked to a
  requirement or verification activity.
- **Research** — reduce uncertainty (tests, analysis) before deciding.
- **Watch** — define a measurable trigger; re-evaluate when it fires.
- **Accept** — an accountable person accepts with rationale; recorded with name and date.
- **Transfer** — contractual/insurance; residual technical risk usually remains.

## FMEA limitations
- RPN = S×O×D overweights detection and occurrence for severe effects; equal RPNs can hide different
  risks → treat high severity separately (implemented: S ≥ 9 always flagged).
- FMEA covers single failures; combine with fault-tree analysis for combinations and common causes.
- Scales (1–10) must be defined per project; numbers from different teams are not comparable.
