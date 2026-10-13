# Testing and evaluation

| Layer | Command | What it proves | Runs in CI |
|---|---|---|---|
| Source integrity | `python scripts/verify_source_pdfs.py` | Pinned PDFs match manifest SHA-256, size, page count | yes |
| Structure | `python -m agentlib validate` | Front matter schemas, required sections, links, source ids, catalog page ranges, workflow wiring, eval specs, plugin manifest, registry freshness | yes |
| Tools | `python -m pytest` | Framework calculators/validators/CLIs behave correctly incl. hand-calculated numeric cases and catalog counts | yes |
| Skills (offline) | `python -m agentlib eval` | Each eval case's golden output passes its checks and its negative output fails — the checks are satisfiable *and* discriminating | yes |
| Skills (live) | `python -m agentlib eval --mode live [--skill X] [--model M]` | Claude, with the skill loaded as system context, produces outputs that pass the same checks | manual workflow (`live-evals.yml`), needs `ANTHROPIC_API_KEY` |
| Ad-hoc output | `python -m agentlib eval --mode grade --skill X --case Y --output file.md` | Grade any output (another model, a human draft) against a case | — |
| Output evidence | `python -m agentlib evidence check doc.md --require-citations` | Citations valid, identifiers real, no over-claims | used by workflows |

## Writing a good eval case

1. Prompt: a realistic request, with fixtures for any input data.
2. Checks: prefer *semantic* deterministic checks — framework identifiers that must appear, numbers that a
   `python` grader recomputes, required table columns, forbidden over-claims — over generic word counts.
3. Golden: a high-quality answer written to the skill's output format. It must pass.
4. Negative: a plausible but wrong answer (wrong level, hallucinated id, missing BAU option, over-claim).
   It must fail. If you cannot write a negative that fails, the checks are too weak.
5. Threshold: default 1.0 (all checks). Lower it only with a written reason in the suite.

## Live evaluation results

Live runs write each response to `evals/results/<skill>__<case>.md` and, with `--json`, a machine-readable
report. Treat live failures as signals to improve the skill text (or the checks, if the response was
genuinely good). Record notable results in `docs/STATUS.md`.
