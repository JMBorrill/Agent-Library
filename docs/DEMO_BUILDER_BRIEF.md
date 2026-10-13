# Brief for building a worked demonstration

A demonstration shows the library being *used* on a realistic project, end to end, with every
deterministic step reproducible by `python3 examples/run_demos.py` and drift-checked in CI.

## Layout (`examples/<demo>/`)
```
README.md                 narrative (sections below)
demo.json                 ordered steps executed by examples/run_demos.py
inputs/                   synthetic artifacts you author (profile, ConOps, requirements, matrices, ...)
outputs/                  generated ONLY by run_demos.py (never hand-edit) + RUN-SUMMARY.md
review/                   left for the independent reviewer — create only review/README.md saying
                          "Independent review pending; performed by a separate reviewer agent."
```

## demo.json step format
```json
{"demo": "aster-01", "title": "Project ASTER — ...", "steps": [
  {"id": "01-framework-selection", "skill": "select-frameworks", "script": "select_frameworks.py",
   "args": ["inputs/profile.json", "--markdown"], "expect_exit": 0,
   "output": "outputs/01-framework-selection.md", "purpose": "choose packs/skills/agents"}
]}
```
Paths in `args` are relative to the demo directory. Read each skill's SKILL.md for its exact CLI.
Prefer `--json` outputs for checkers and `--markdown` where a script offers it. Every script must be
deterministic — pass `--as-of 2026-10-13` (or `--milestone`) wherever a script supports dates.

## Required content
1. **Framework selection** — first step runs `select-frameworks`; README explains selected and
   rejected packs and why, and states the oversight level.
2. **Agent selection** — which agents act as authors and which as reviewers, per phase.
3. **Skill execution** — at least 8 steps across ≥ 3 packs. Include at least one *draft → fix* pair:
   run a checker on a realistic first draft that genuinely has defects (`expect_exit: 1`), then on the
   corrected version (`expect_exit: 0`). Do not fabricate defects that no real draft would have.
4. **Specification** — the main technical/product specification artifact(s) in `inputs/` (e.g.
   requirements, PRD, ICD, rules, threat model, oversight matrix).
5. **Verification procedures** — V&V matrix / acceptance tests / eval sets with *planned* activities;
   no result may be `pass` unless the demo itself executed it (e.g. an eval run on recorded fixture
   responses counts and must say so; a physical test never counts).
6. **Limitations and unknowns**, **evidence actually checked**, and **human sign-offs required** (list
   who; never record them as given).
7. Last step: `independent-review` `claim_check.py` over `README.md` and `inputs` (expect 0) — rewrite
   any overclaiming text until it passes.

## Honesty rules
- All data synthetic and labelled so (names end "(synthetic)"; lenders/customers fictitious).
- All numerical design values are *proposed*; physics constants cited (e.g. CODATA G).
- Sources: cite registry IDs and mark unverified section numbers *(unverified)*.
- No real credit decisions, no real personal data, no real secrets.

## Self-check
```
python3 examples/run_demos.py --demo <demo>          # generates outputs
python3 examples/run_demos.py --demo <demo> --check   # must print PASS
python3 .claude/skills/independent-review/scripts/claim_check.py examples/<demo>/README.md examples/<demo>/inputs
```
Do not edit anything outside `examples/<demo>/`. Report: steps (id, skill, expected/actual exit),
the draft→fix pairs, limitations, and anything in the library that blocked you (bugs, missing CLI options)
— report library bugs rather than working around them silently.
