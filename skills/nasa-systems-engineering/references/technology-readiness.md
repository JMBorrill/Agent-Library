# Technology readiness (Appendix G)

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`), Appendix G "Technology Assessment /
Insertion" (PDF pp. 259-268). PDF pages. Catalog: `nasa-se lifecycle --kind trl`.

## TRL scale (Figure G.4-1, PDF p. 264; transcribed from the figure)

| TRL | Description |
|---|---|
| 1 | Basic principles observed and reported |
| 2 | Technology concept and/or application formulated |
| 3 | Analytical and experimental critical function and/or characteristic proof-of-concept |
| 4 | Component and/or breadboard validation in laboratory environment |
| 5 | Component and/or breadboard validation in relevant environment |
| 6 | System/subsystem model or prototype demonstration in a relevant environment (ground or space) |
| 7 | System prototype demonstration in a target/space environment |
| 8 | Actual system completed and "flight qualified" through test and demonstration (ground or flight) |
| 9 | Actual system "flight proven" through successful mission operations |

Software TRL definitions are in NPR 7123.1, not in the handbook (PDF p. 265).

## Assessment rules

- Technology assessment = (1) determine current maturity as TRLs, then (2) determine the difficulty of
  advancing, the Advancement Degree of Difficulty (AD2) (glossary PDF p. 246; G.4 PDF p. 263).
- Establishing TRLs means determining **what was demonstrated and under what conditions** (PDF p. 264).
- Define terms first ("breadboard", "relevant environment" vary between disciplines); quantify judgement
  calls using form, fit and function; use a balanced, experienced assessment team (PDF p. 265).
- **Heritage**: if the architecture and the environment have changed, the TRL drops to TRL 5, at least
  initially; further analysis may support TRL 6 or 7 - but it is no longer TRL 9 (PDF pp. 265-266).
- **System TRL is the lowest TRL present** in the system; elements at higher TRLs that have never been
  integrated as a unit lower the unit's TRL, by an amount depending on integration complexity (PDF p. 268).
- Use a PBS to make sure no technology slips through the cracks, even at concept level (PDF p. 263).
- Glossary: typically TRL 6 (technology demonstrated in a relevant environment) is required for a technology
  to be integrated into an SE process (PDF p. 246). Treat project- or program-specific thresholds (e.g. at
  PDR) as coming from the governing directives, not from this handbook.
- The Technology Development Plan is required for transition from Phase A to Phase B (glossary, PDF p. 246)
  and is baselined in Pre-Phase A per the phase blue box (PDF p. 39).

## Recording an assessment

| Element (PBS) | What was built (form/fit/function, scale) | Environment demonstrated | Integrated as unit? | Heritage changes | TRL | Evidence | Assessor |
|---|---|---|---|---|---|---|---|

State the system TRL as the minimum of its elements and list the elements that drive it.
