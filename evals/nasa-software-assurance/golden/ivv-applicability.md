# IV&V applicability

The mission is a Category 1 project (NPR 7120.5) with Class A software reaching KDP A, so software IV&V is
required: SWE-141 requires IV&V for Category 1 projects, for Category 2 projects with Class A or B payload
risk classification, and for projects selected by the MDAA [nasa-software-requirements SWE-141, p. 25].
SWE-141 is marked X for Classes A and B with Authority HQ OSMA; the NASA Chief, SMA makes the final
decision on any tailoring of it (SWE-223) [nasa-software-requirements SWE-223, p. 12].

## What follows

- IPEP: the project manager, with NASA IV&V, ensures an IV&V Project Execution Plan is developed,
  approved, maintained and executed (SWE-131) [nasa-software-requirements SWE-131, p. 25]. The IV&V
  Provider develops and negotiates the IPEP with the project (4.4.2.2) and the NASA SMA TA (SMA Technical Authority)
  reviews and concurs with it (4.4.2.3) [nasa-software-assurance 4.4.2.3, p. 50].
- Access: IV&V gets the artefacts, source code and data it needs (SWE-178); the project responds to IV&V
  issues and risks and tracks them to closure (SWE-179) [nasa-software-requirements SWE-179, p. 26].
- Scope: the IV&V Provider conducts planning and risk assessment to decide which behaviours to analyse
  (4.4.2.1) and applies the 4.4.2.x requirements as tailored in the IPEP - e.g. hazard causes and controls
  traced to requirements (4.4.2.20) and independent testing of hazard-related requirements (4.4.2.46)
  [nasa-software-assurance 4.4.2.46, p. 56].
- SA tasks: confirm the IV&V requirements are complete (SWE-141 task 1) and that the IPEP exists (SWE-131
  task 1) [nasa-software-assurance Table 1 SWE-131, p. 26].
- Independence: technical, managerial and financial (4.4.1.2).
