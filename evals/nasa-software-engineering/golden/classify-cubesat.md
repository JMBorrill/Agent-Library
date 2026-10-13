# Classification

Classified with `python -m agentlib nasa-swe classify --answers fixtures/cubesat-answers.yaml`.

Candidate class: **Class C** - Mission Support Software or Aeronautic Vehicles, or Major Engineering/Research Facility Software

Matched Appendix D criteria:

- C-5: "Software for NASA Class D payloads, as defined in NPR 8705.4." [nasa-software-requirements Appendix D Class C, p. 82]
- Appendix D also lists CubeSat mission software among the Class C space-system examples [nasa-software-requirements Appendix D Class C, p. 83].

Exclusions considered:

- The flight software operates the spacecraft and is needed for the primary mission objectives, which
  would otherwise point to Class B (criteria B-1a, B-1b) [nasa-software-requirements Appendix D Class B, p. 81].
  However, Class B excludes software for NASA Class D payloads as defined in NPR 8705.4 (exclusion B-x3)
  [nasa-software-requirements Appendix D Class B, p. 82], and the mission is designated a Class D payload.
- Not human-rated, so Class A does not apply.

Safety-critical: not declared. If the SWE-205 determination with SMA finds safety-critical components,
SWE-023, SWE-134, SWE-219 and SWE-220 apply (all marked X for Class C).

# Applicable requirements

Appendix C marks 92 requirements X for Class C; generate the matrix with
`python -m agentlib nasa-swe matrix --class C`.

# Authority

This is a candidate classification only. The project manager classifies each system and subsystem
(SWE-020) [nasa-software-requirements SWE-020, p. 24]; the software engineering and software assurance
Technical Authorities must agree on it, and the NASA Chief Engineer is the ultimate TA for classification
disputes [nasa-software-requirements Appendix D D.2, p. 79]. Record the decision (SWE-176)
[nasa-software-requirements SWE-176, p. 25].
