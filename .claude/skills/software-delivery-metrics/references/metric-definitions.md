# Metric definitions and data rules

Paraphrased from DORA's metrics guide (dora.dev, CC BY 4.0, Google LLC); operational rules below are
this library's own choices, because DORA does not prescribe exact formulas
(`sources/audits/dora.md`, "Limitations").

| Metric (DORA name) | Category (guide) | Library operational definition |
|---|---|---|
| Change lead time | throughput | For each commit in each **successful** deployment in the window: `deployed_at − commit_time`, hours. |
| Deployment frequency | throughput | Count of production deployments (any status) with `start ≤ deployed_at < end`; also per day, per week, and median hours between consecutive deployments. |
| Failed deployment recovery time | throughput (as written in the 2026-01 guide) | For each failed deployment with `restored_at`: `restored_at − deployed_at`, hours. Unrecovered failures are counted, not imputed. |
| Change fail rate | instability | `failed / all deployments` in the window. |
| Deployment rework rate | instability | `is_rework = yes / deployments with a known rework flag`. |

## Statistics
- Median and p75/p90 by linear interpolation: sort values, rank = (n − 1) × p / 100, interpolate.
  Example: lead times 1, 2, 6, 24 h → median 4 h, p75 10.5 h, p90 18.6 h.
- Means are not reported: delivery durations are heavily right-skewed.

## Data hygiene rules enforced by `dora_metrics.py`
| Rule | Severity | Reason |
|---|---|---|
| `naive-timestamp` | error | Without an offset, durations across DST/time zones are wrong. |
| `negative-duration` | error | Commit after deploy or restore before deploy means bad joins. |
| `malformed-row`, `duplicate-deploy-id` | error | Row cannot be trusted. |
| `mixed-services` | warning | Metrics are best per application/service. |
| `small-sample` | warning | Default threshold 10 (library default, configurable). |
| `unrecovered-failure`, `missing-commit-times`, `missing-rework-flag` | warning | Metric computed on a subset. |

## History of names (for reading older dashboards)
2014 work used deployment frequency, lead time for changes, MTTR and change fail rate. In 2023
MTTR / time to restore was redefined as failed deployment recovery time so that only failures caused
by changes count. Deployment rework rate was added in 2024, giving five metrics in two factors.

## The seven common pitfalls (headings from the guide; paraphrased)
1. Setting metrics as a goal. 2. Having one metric to rule them all. 3. Using industry as a shield
against improving. 4. Making disparate comparisons. 5. Having siloed ownership. 6. Competing.
7. Focusing on measurement at the expense of improvement.
