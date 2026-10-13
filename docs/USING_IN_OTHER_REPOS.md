# Using the library in other repositories

There are three supported ways to use these skills, agents and workflows elsewhere. Pick one.

| Option | Best for | Gives you | Updates |
|---|---|---|---|
| A. Claude Code plugin | Individuals and teams using Claude Code | All skills, subagents and slash commands, namespaced | `/plugin update` |
| B. Vendored install (`agentlib install`) | Repos that must pin and review exactly what Claude loads | Chosen skills copied into `.claude/`, lock file with hashes | Re-run install; local edits protected |
| C. Python tools only | CI pipelines and scripts | `agentlib` CLI: calculators, checklists, validators, evidence checker | `pip install -U` |

## A. Install as a Claude Code plugin

In Claude Code:

```text
/plugin marketplace add JMBorrill/Agent-Library
/plugin install professional-agent-library@jmborrill-agent-library
```

Skills then load automatically when relevant (e.g. ask "appraise these options using the Green Book").
Plugin slash commands are namespaced by plugin name, e.g. `/professional-agent-library:secure-delivery-review`.
Subagents appear in `/agents`.

For local development of the plugin itself:

```sh
claude --plugin-dir /path/to/Agent-Library
```

To make the plugin available to everyone working in a repository, commit a `.claude/settings.json` there:

```json
{
  "extraKnownMarketplaces": {
    "jmborrill-agent-library": {"source": {"source": "github", "repo": "JMBorrill/Agent-Library"}}
  },
  "enabledPlugins": {"professional-agent-library@jmborrill-agent-library": true}
}
```

The skills call `python -m agentlib ...` for deterministic tools. Make the tools available in the consuming
environment with option C (`pip install "git+https://github.com/JMBorrill/Agent-Library"`) and set
`AGENTLIB_ROOT` to a checkout of this repository so catalogs resolve (or use option B with `catalog`).

## B. Vendored install with `agentlib install`

From a checkout of this library:

```sh
pip install -r requirements-dev.txt
# everything
python -m agentlib install /path/to/target-repo --components skills agents commands workflows templates catalog
# only what you need (referenced skills follow automatically)
python -m agentlib install /path/to/target-repo --skill owasp-asvs --skill nist-ssdf --components skills agents
# preview
python -m agentlib install /path/to/target-repo --dry-run
```

Layout created in the target:

```
.claude/skills/<skill>/...      # loaded by Claude Code as project skills
.claude/agents/*.md             # project subagents
.claude/commands/*.md           # project slash commands (/secure-delivery-review, ...)
.agent-library/workflows/       # workflow definitions referenced by commands
.agent-library/templates/       # cross-cutting templates
.agent-library/catalog/         # framework catalogs (for the CLI tools)
.agent-library.lock.json        # library version + SHA-256 of every installed file
```

Re-running the install upgrades files you have not modified; files you edited locally are skipped and
reported (use `--force` to overwrite). Commit the result so every collaborator and CI run sees the same
skills. With the `catalog` component installed, the CLI finds `.agent-library/` automatically when run from
the repository root, so the tools work after `pip install "git+https://github.com/JMBorrill/Agent-Library"`
with no further configuration (`AGENTLIB_ROOT` overrides the location).

> Commands and workflows reference paths such as `workflows/<id>.yaml` and `templates/...` relative to the
> library root. In a vendored install those live under `.agent-library/`; Claude resolves them when told
> (the commands say which file to open). If you vendor only skills, use the skills directly.

## C. Use the Python tools in CI

```sh
pip install "git+https://github.com/JMBorrill/Agent-Library"
git clone --depth 1 https://github.com/JMBorrill/Agent-Library /tmp/agent-library
export AGENTLIB_ROOT=/tmp/agent-library
agentlib asvs checklist --level 2 --format csv > asvs-l2.csv
agentlib ssdf check-assessment security/ssdf-assessment.yaml
agentlib nasa-se lint-requirements docs/requirements.csv
agentlib evidence check docs/assessments/*.md --require-citations
```

Example GitHub Actions step in a consuming repository:

```yaml
- name: Check assessment evidence
  run: |
    pip install "git+https://github.com/JMBorrill/Agent-Library"
    git clone --depth 1 https://github.com/JMBorrill/Agent-Library "$RUNNER_TEMP/agent-library"
    AGENTLIB_ROOT="$RUNNER_TEMP/agent-library" agentlib evidence check docs/assessments/*.md --require-citations
```

### Reusable GitHub Action

The repository root is also a composite action, so consumers need no install step:

```yaml
- uses: actions/checkout@v5
- uses: JMBorrill/Agent-Library@main   # pin to a commit SHA or tag in production
  with:
    args: evidence check docs/assessments/*.md --require-citations
- uses: JMBorrill/Agent-Library@main
  with:
    args: asvs check-assessment security/asvs-l2.yaml --level 2
```

The step fails when the command exits non-zero; the exit code is also exposed as the `exit-code` output.
Arguments are split on whitespace (globs expand; quoting is not supported).

## Using skills programmatically (Claude Agent SDK / API)

See [`examples/`](../examples/) for a minimal Claude Agent SDK script that loads this library as a plugin,
and `agentlib/evals/runner.py` (`skill_system_prompt`) for loading a skill as system context via the
Messages API.

## Which skill do I need?

Run `python -m agentlib route "<your problem>"` or use the `framework-selector` skill / `/select-frameworks`
command. The routing table is in `skills/framework-selector/references/routing-table.md`.
