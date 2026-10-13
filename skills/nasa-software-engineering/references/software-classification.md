# Software classification (NPR 7150.2D Appendix D)

All page numbers are PDF pages of the pinned NPR 7150.2D (printed page numbers are identical).
Criterion ids (`A-1a`, `C-x1` ...) are the question ids used by
`python -m agentlib nasa-swe classify`; they are assigned by this library to the lettered items of
Appendix D and are not identifiers defined by the NPR.

## Why classification matters

- The project manager classifies each system and subsystem containing software using the highest
  applicable class definition in Appendix D (SWE-020, p. 24) and keeps records of each classification
  determination, each Requirements Mapping Matrix and each independent classification assessment for
  the life of the project (SWE-176, p. 25).
- Software assurance may perform an independent classification or concur with engineering's; the
  engineering and SA Technical Authorities need to agree, and a disagreement follows the Center's
  dissenting-opinion process (Note to 3.5.1, pp. 24-25).
- The class selects the default requirement set in Appendix C (2.2.2, p. 18). Counts of requirements
  marked `X` in Appendix C: Class A 100, B 100, C 92, D 64, E 12, F 65 (computed from the catalog).
- If a system evolves to a higher or lower class, plans and supplier contracts must be updated (SWE-021,
  p. 19).

## The five underlying factors (D.1, p. 79)

(1) usage of the software with or within a NASA system, (2) criticality of the system to NASA's major
programs and projects, (3) extent to which humans depend upon the system, (4) developmental and
operational complexity, and (5) extent of the Agency's investment. Classes A-E cover
engineering-related software; Class F covers business and IT infrastructure software.

## Resolution rules (D.2, p. 79)

- Software in a given system/subsystem belongs to a single class; if more than one class appears to
  apply, assign the higher class.
- Discrepancies within Classes A-E are resolved with the definitions and the five factors; Engineering
  and SMA provide dual TA chains; the NASA Chief Engineer is the ultimate TA for classification disputes.

## Classes (summary - quote the PDF for exact wording)

| Class | Title | Definition pages | Key discriminators |
|---|---|---|---|
| A | Human Rated Space Software Systems | 79-80 | Ground/flight software needed for a primary mission objective of human space flight and directly interacting with human space flight systems, limited to software required to operate the vehicle/asset, sustain a safe habitable environment, achieve primary mission objectives, or directly prepare consumed resources. Excludes superfluous software that happens to fly, aeronautics/R&T/science without space flight applications, and test systems in a development environment. |
| B | Non-Human Space Rated Software Systems or Large Scale Aeronautics Vehicles | 80-82 | Space flight/ground software for non-human-rated systems required to operate the vehicle/asset, achieve primary mission objectives or prepare consumed resources; large-scale (life-cycle cost > $250M) NASA-unique aeronautics software integral to vehicle control, cabin environment or emergency systems. Excludes non-primary instruments, test systems in a development environment, and NASA Class D payloads (NPR 8705.4). |
| C | Mission Support Software or Aeronautic Vehicles, or Major Engineering/Research Facility Software | 82-83 | Single non-primary instrument science return; mission data analysis/processing; defects affecting secondary objectives or causing operational problems; testing of space assets; verification of system requirements by analysis; other space flight operations; non-large-scale aeronautics control/cabin/emergency; official record copy of flight/test data; operation of a major facility; sounding rockets and payloads; NASA Class D payload software. Examples include CubeSat and SmallSat mission software (p. 83). |
| D | Basic Science/Engineering Design and Research and Technology Software | 83-84 | Ground software for secondary science analysis, engineering development tools, informal testing, mission planning/formulation tools, non-major RDT&E labs, decision support in non-mission-critical situations; airborne software with minor or no effect; research software in a major facility but independent of its operation. Excludes software that can impact primary/secondary objectives or lose space-system data, operates a major facility or an airborne vehicle, or is flight software. |
| E | Design Concept, Research, Technology, and General Purpose Software | 84-85 | Design-concept/hypothesis exploration not used for decisions on operational or to-be-built Class A-C systems; minor analyses of science/experimental data; general-purpose computing (e.g. word processing). Cannot be safety-critical - safety-critical software must be Class D or higher (p. 85). Excludes flight systems, operational support, mission-affecting and safety-critical software. |
| F | General Purpose Computing, Business, and IT Software | 85-86 | Business and IT software supporting the Agency, Centers or projects (e.g. enterprise applications, web, networks). The NASA CIO (or designee) has institutional authority on all Class F projects (Note to SWE-140, p. 12). |

## Using the classifier

```sh
python -m agentlib nasa-swe classify --list-questions          # ids, page, text
cat > answers.yaml <<'EOF'
B-scope: yes      # non-human-rated space system
B-1a: yes         # operates the spacecraft
B-x3: no          # not a NASA Class D payload
safety_critical: no
EOF
python -m agentlib nasa-swe classify --answers answers.yaml
```

Scope questions (`A-scope`, `B-scope`, `B-scope-2`) gate the Class A/B criteria so that, for example,
"integral to the control of an airborne vehicle" counts for Class B only for large-scale NASA-unique
aeronautics vehicles; otherwise the self-contained Class C aeronautics criterion `C-2` applies.

Report the result as `Candidate class: Class X`, list the matched criteria and every exclusion
considered, and state that the formal classification is the project's, agreed by the Engineering and
SMA Technical Authorities.

## Common pitfalls

- Classifying a whole project instead of each system/subsystem (separate subsystems can have different
  classes, D.1, p. 79).
- Treating prototypes as Class E after a program decides to use them operationally - Appendix D says
  the software should then be upgraded to its appropriate class (Class E examples, p. 85).
- Calling safety-critical software Class E.
- Forgetting that NASA Class D payload software is excluded from Class B and listed under Class C.
