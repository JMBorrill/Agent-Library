# Native Claude Code plugin evals

These cases run with `claude plugin eval .` (the directory is set by `experimental.evals` in
`.claude-plugin/plugin.json`). Each case checks that Claude Code **fires the right skill** for a natural request
(`skill-fired`, reported as a plugin-fired indicator against the no-plugin baseline), that the answer contains
**framework-grounded content** (`framework-content` regex) and that it **does not over-claim**.

They make real model calls and cost money; run them on demand:

```sh
claude plugin eval . --allow-tools Bash --runs 1 --threshold 0.66 --max-cost-usd 5
claude plugin eval . --case 'asvs-*'
```

They complement, not replace, the deterministic suites in `evals/` (`python -m agentlib eval`), which grade
output quality offline and in live API mode.
