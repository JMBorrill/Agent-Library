# Framework implementation plan

**This is a proposed build queue, not a claim that capabilities have been implemented or that all source sections have been reviewed.** Canonical source URLs and versions live in `sources/registry.json`. Each row must end with a source audit, source-to-skill crosswalk, working artifacts and tests or an explicit access block.

| Phase | Framework / source ID | Proposed reusable capabilities | Evidence target |
|---|---|---|---|
| A | `nasa-se` | se-stakeholder-conops, se-requirements, se-logical-decomposition, se-architecture-trades, se-interface-control, se-risk-analysis, se-implementation-integration, se-verification-validation, se-technical-planning, se-change-control, se-review-gates, se-transition, se-configuration-management, se-technical-data-management, se-technical-assessment, se-decision-analysis | NASA 17 process crosswalk + deliberate missing-test fixtures |
| A | `nasa-se-design` | se-stakeholder-conops, se-requirements, se-logical-decomposition, se-architecture-trades | atomic requirements and source traceability check |
| A | `nasa-se-realize` | se-implementation-integration, se-verification-validation, se-transition | test references and verification versus validation distinction |
| A | `nasa-se-manage` | se-technical-planning, se-risk-analysis, se-interface-control, se-change-control, se-configuration-management, se-technical-data-management, se-technical-assessment, se-decision-analysis | risk/change ownership and evidence gaps |
| B | `ecss-se` | space-mission-assurance, space-technical-budgets, space-qualification-planning | ECSS edition and source access gate |
| C | `nasa-software` | software-requirements-traceability, software-assurance-plan, software-vv | requirements-to-test-to-result references |
| C | `google-review` | software-code-review, software-maintainability | intentionally flawed PR fixture |
| C | `google-sre` | sre-service-level-objectives, sre-incident-response, sre-production-readiness | error budget computations and incident fixture |
| C | `dora` | software-delivery-metrics, software-improvement-experiment | metric definitions and data granularity checks |
| C | `owasp-asvs` | security-threat-model, security-asvs-controls, security-release-gate | deliberately vulnerable test scenarios |
| C | `nist-ssdf` | security-supply-chain, security-secure-development | SSDF control evidence checks |
| D | `gov-service` | product-discovery, product-experiment-design, product-service-journey, product-delivery-gates | hypothesis versus observation audit |
| D | `gov-design` | ux-accessibility-review, ux-form-patterns | keyboard/input/error messages fixture |
| D | `shape-up` | product-shaping, product-scope-risk | unsupported assumptions and rabbit holes |
| E | `treasury-green` | finance-options, finance-appraisal, finance-five-cases | sensitivity and non-financial effects caveat |
| E | `damodaran` | finance-unit-economics, finance-valuation, finance-npv-irr | NPV/IRR and sensitivity known-answer tests |
| E | `basel-credit` | credit-governance, credit-risk-controls | no false loan approval claims |
| E | `fca` | finance-fca-scope-check, finance-consumer-duty-review | jurisdiction/product-scope and human-signoff fixture |
| F | `nist-ai` | ai-risk-assessment, ai-eval-harness, ai-prompt-injection-review, ai-human-oversight | benign/malicious prompts and expected outcomes |

## Rules for converting the table to working library

1. A chapter-level source can reuse a parent framework skill: it does not require a separate identical skill. Document all links in a crosswalk.
2. Count only sources actually researched and skills actually tested. The queue does not determine completion.
3. No self-approval by author agents; humans own safety, regulatory and investment sign-off.
4. All sample cases must use synthetic data.
5. If a source is behind access restrictions, do not invent coverage; mark it blocked and continue.
