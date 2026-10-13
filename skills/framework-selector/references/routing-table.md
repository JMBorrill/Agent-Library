# Routing table

| Problem signal | Primary skill(s) | Supporting skill(s) | Subagent(s) | Workflow |
|---|---|---|---|---|
| New system / mission / product concept, ConOps, architecture, life-cycle reviews | `nasa-systems-engineering` | `requirements-engineering`, `evidence-and-citation` | `systems-engineer` | `technical-review-gate` |
| Writing, reviewing or tracing requirements; verification matrix | `requirements-engineering` | `nasa-systems-engineering` | `requirements-engineer` | `technical-review-gate` |
| Software for NASA or high-assurance contexts: classification, compliance matrix, plans | `nasa-software-engineering` | `nasa-software-assurance`, `nist-ssdf` | `software-engineering-lead` | `software-assurance-audit` |
| Software assurance, software safety, IV&V, safety-critical software | `nasa-software-assurance` | `nasa-software-engineering` | `software-assurance-engineer` | `software-assurance-audit` |
| Secure development process, supply chain, SBOM, vulnerability response, attestation | `nist-ssdf` | `owasp-asvs` | `secure-development-reviewer` | `secure-software-delivery` |
| Web/API application security requirements or verification, pentest scoping, findings mapping | `owasp-asvs` | `nist-ssdf` | `application-security-verifier` | `secure-software-delivery` |
| AI/ML system risk, governance, impact assessment, model cards, AI incident monitoring | `nist-ai-rmf` | `owasp-asvs`, `nist-ssdf` | `ai-risk-assessor`, `ai-governance-advisor` | `ai-system-assurance` |
| Public spending proposal, options appraisal, cost-benefit analysis, business case | `green-book-appraisal` | `nasa-systems-engineering` (for technical options), `evidence-and-citation` | `economic-appraisal-analyst` | `public-investment-business-case` |
| Any deliverable that will be relied on | `evidence-and-citation` | — | `evidence-auditor` | all |
| Multi-discipline decision needing a panel | `framework-selector` | all relevant | `review-board-chair` | any |

## How frameworks combine

- **SSDF + ASVS:** SSDF says *how the organisation develops software securely* (process); ASVS says *what
  security properties the application must have and how to verify them* (product). SSDF PW tasks on
  security requirements and testing are naturally satisfied with ASVS as the requirement set.
- **NPR 7150.2D + NASA-STD-8739.8B:** the NPR sets engineering requirements by software class; the
  standard sets the assurance and safety tasks that check them. Use both for Class A-C or safety-critical software.
- **AI RMF + SSDF/ASVS:** an AI system is also software; AI RMF covers socio-technical risk, SSDF/ASVS
  cover the conventional security of the software that hosts the model.
- **NASA SE + Green Book:** NASA SE structures technical alternatives and trade studies; the Green Book
  structures the public value-for-money decision between them (economic case) and the delivery plan
  (management case).
