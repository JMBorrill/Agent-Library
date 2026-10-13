# Software cause areas for the lander hazard analysis

From NASA-STD-8739.8B Appendix A, Table 2 (`python -m agentlib nasa-swe hazard-causes`)
[nasa-software-assurance Table 2, p. 59]. Walk each area for every hazard with software involvement:

1. Data errors (e.g. out-of-range inputs, missing integrity checks, stuck sensors)
2. Commanding errors (e.g. out-of-sequence commands, missing prerequisite checks)
3. Flight computer errors (e.g. CPU overload, watchdog failures, reset behaviour)
4. Operating systems errors
5. Programmable logic device errors
6. Flight system time management errors (e.g. race conditions, late response to off-nominal conditions)
7. Coding, logic, and algorithm failures, algorithm specification errors
8. Fault tolerance and fault management errors
9. Software processes errors
10. Human-machine interface errors
11. Security and virus errors
12. Unknown/Unknowns errors (e.g. COTS limitations, compiler behaviour)

Follow the phased approach of A.1: must-work / must-not-work functions in Phase 1, design analysis and
requirements gap analysis (SWE-184) in Phase 2, test results closing hazard verifications (SWE-068) in
Phase 3 [nasa-software-assurance A.1.3, p. 58]. Confirm the hazard reports contain all software
contributions (SWE-205 task 1) [nasa-software-assurance Table 1 SWE-205, p. 26].
