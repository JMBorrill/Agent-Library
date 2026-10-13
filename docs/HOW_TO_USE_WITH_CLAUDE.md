# Instructions: handing this to Claude

## Recommended: Claude Code (local/cloud repo workspace)
1. Download `standards-agent-factory-kit.zip` and unzip it. The ZIP contains the existing starter skills, agents, templates, scripts, source registry and new build brief.
2. Open the extracted folder in Claude Code (or push the folder to **your own** GitHub repository before opening Claude Code, if you choose).
3. Paste the full text of `docs/MASTER_CLAUDE_BUILD_PROMPT.md` into Claude Code (or ask Claude Code to read that file and execute it).
4. Make sure Claude can read URLs on the internet and can edit/run files in the repository. If network access to a reference fails, Claude should mark it inaccessible and continue with verified sources.
5. Review the first source audit, then let Claude run through phases and update `docs/progress.md`. Do not give Claude unrelated API keys or real customer data.
6. For subsequent sessions, say: `Read docs/progress.md and docs/MASTER_CLAUDE_BUILD_PROMPT.md; resume from the first incomplete framework, run tests, and update measured coverage.`

## Claude chat / Project (without code workspace)
Attach the ZIP and `MASTER_CLAUDE_BUILD_PROMPT.md`. Ask Claude to implement files in an output ZIP. Note that Claude chat may not have the same shell, web, Git or multi-agent capabilities as Claude Code, so end-to-end execution and tests are easier in Claude Code.

## You do NOT need to attach every handbook
The `docs/VERIFIED_REFERENCE_URLS.md` and `sources/registry.json` provide entry points. If a primary source cannot be retrieved, consider attaching a copy you are lawfully entitled to use, without asking the agent to redistribute it.

## Baseline sanity checks
`python3 scripts/check_repo.py`
`python3 scripts/check_framework_manifest.py`

These commands validate starter formatting/mapping only, NOT professional engineering quality. Claude is tasked with adding deeper evaluations and complete implementation.
