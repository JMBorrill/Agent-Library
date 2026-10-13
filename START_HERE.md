# Your Claude agent/skills factory: start here

This is the existing `standard-driven-agent-lab` starter library, bundled with a new implementation mission, source research links, a framework plan and machine-readable NASA 17-process crosswalk.

## Recommended workflow
1. Open this repository in Claude Code.
2. Read or paste `docs/MASTER_CLAUDE_BUILD_PROMPT.md`.
3. Claude should run `python3 scripts/check_repo.py` and `python3 scripts/check_framework_manifest.py` first.
4. Claude should verify sources, then implement source-grounded agents, skills, validators and real test cases, recording progress in `docs/progress.md`.
5. Review and approve consequential actions. Use the skill pack installer only in dry-run mode before copying files to another project.

## Key included files
- `docs/MASTER_CLAUDE_BUILD_PROMPT.md` — complete autonomous build instructions.
- `docs/VERIFIED_REFERENCE_URLS.md` — plain-text official and technical source URLs (URLs checked at curation time; content sections still need audit).
- `sources/registry.json` — canonical source list.
- `sources/framework-build-plan.json` — source-to-capability build backlog.
- `sources/nasa-17-processes.json` — preliminary NASA technical-process crosswalk.
- `docs/FRAMEWORK_BUILD_PLAN.md` — human-readable proposed skills and agents by framework.
- `docs/QUALITY_AND_ACCEPTANCE.md` — completion gates and caution against false assurances.
- `docs/HOW_TO_USE_WITH_CLAUDE.md` — onboarding and prompt for resuming.

## Important
The skills and agents carried forward from the starter are initial scaffolds, **not** fully researched or professionally reviewed implementations. Do not treat mapping/checker PASS as design qualification, product suitability, FCA compliance or legal advice. Real credit applications and client data are not needed.
