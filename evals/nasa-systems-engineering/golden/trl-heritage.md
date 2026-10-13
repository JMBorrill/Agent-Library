# TRL assessment: Selene Pathfinder attitude determination

TRL definitions from Figure G.4-1 [nasa-se G.4, p. 264]; assessment rules from Appendix G.

| Element | What was demonstrated, and where | Assessed TRL | Basis |
|---|---|---|---|
| Star tracker (heritage) | Flight proven in LEO, but new optical bench and interface electronics (architecture changed) and lunar environment (environment changed) | TRL 5 (initially) | When the architecture and environment have changed, a heritage system drops to TRL 5 at least initially; analysis/testing may raise it to TRL 6 or 7, but it is no longer TRL 9 [nasa-se G.4, p. 265] |
| Attitude estimation algorithm | Breadboard processor validated in the laboratory | TRL 4 | Component and/or breadboard validation in laboratory environment [nasa-se G.4, p. 264] |
| Reaction wheels | Same model, same configuration and environment, flown on two lunar missions | TRL 9 | Actual system flight proven through successful mission operations |

**System TRL: TRL 4.** The TRL of a system is the lowest TRL present in it; the attitude determination
subsystem is also limited because these elements have not been integrated as a unit [nasa-se G.4, p. 268].

## Recommendations

- Star tracker: analyse and test the new bench/electronics and the lunar thermal and radiation environment
  to justify TRL 6 (system/subsystem model or prototype demonstration in a relevant environment).
- Algorithm: test in a relevant environment (e.g. hardware-in-the-loop with representative sky and
  thermal conditions).
- Record what was demonstrated, at what fidelity and in which environment for each element; this
  assessment supports, but does not replace, the project's technology assessment team.
