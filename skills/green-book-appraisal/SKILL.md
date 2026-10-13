---
name: green-book-appraisal
description: >-
  Structures, calculates and quality-checks UK public-sector economic appraisals and business cases under
  the HM Treasury Green Book 2026 edition and the Five Case Model. Covers rationale, SMART objectives, BAU,
  longlist appraisal with critical success factors and the options framework filter, and shortlist social CBA.
  It runs deterministic tools for NPSV, BCR, RPSC, real-terms conversion, the 2026 STPR bands and the 1.5%
  health rate, optimism bias, switching values and sensitivity, and checks business case structure. Use when
  drafting or reviewing a Strategic Outline Case, Outline Business Case or Full Business Case, building an
  options appraisal or appraisal summary table, discounting cash flows to Green Book rules, or checking that
  an appraisal follows Green Book 2026.
metadata:
  version: 1.0.0
  category: economic-appraisal
  maturity: beta
  sources: [treasury-green]
  catalogs: [green-book]
  tools:
    - "python -m agentlib greenbook npv"
    - "python -m agentlib greenbook real"
    - "python -m agentlib greenbook switching"
    - "python -m agentlib greenbook optimism-bias"
    - "python -m agentlib greenbook check-case"
    - "python -m agentlib greenbook params"
    - "python -m agentlib greenbook factors"
    - "python -m agentlib greenbook welfare-weight"
---

# Green Book appraisal and business case development (2026 edition)

This skill applies **HM Treasury's Green Book, 2026 edition** to appraisal and business case work. That covers
the four-stage appraisal process, the Five Case Model, and the business case stages: Strategic Outline Case
(SOC), Outline Business Case (OBC) and Full Business Case (FBC). All numbers come from deterministic tools that
read `catalog/green-book.json`. That catalog was extracted from the pinned 2026 PDF, and every entry cites a PDF
page.

> **Edition discipline.** Use only what the 2026 text states. Do not import parameters remembered from the
> 2018/2020/2022 editions, such as extra discount step-downs after year 75 or optimism bias percentages.
> Run `python -m agentlib greenbook params` to see what the 2026 edition states and what it defers to
> supplementary guidance. Anything deferred must be supplied by the user, and its source must be recorded.

## When to use

- Drafting a SOC, OBC or FBC, or any of its parts: strategic case, options appraisal, economic case, appraisal
  summary table (AST), or monitoring and evaluation (M&E) plan.
- Discounting real-terms cash flows to Green Book rules, comparing options on NPSV/BCR/RPSC, or converting
  nominal values to real terms.
- Applying optimism bias, calculating switching values, or running sensitivity tests.
- Reviewing someone else's business case or appraisal for compliance with Green Book 2026.
- Not for: setting policy objectives (the Green Book does not do this, para 1.1), regulatory impact assessment
  templates (Better Regulation Framework), or full evaluation design (Magenta Book).

## Workflow

Scale the effort to the proposal's cost, complexity and risk (para 1.8). For a review, go straight to step 7.

1. **Frame the proposal.** Place it in the policy hierarchy (programme, project and so on) and pick the business
   case stage: SOC, OBC or FBC (Table 3). Open the matching template:
   [SOC](templates/strategic-outline-case.md), [OBC](templates/outline-business-case.md) or
   [FBC](templates/full-business-case.md).
2. **Rationale and objectives (strategic case).** Write the case for change (the market failure or equity
   rationale) and the theory of change, describing the assumptions behind each link. Describe a fair BAU, which
   is not the same as "do nothing". Set SMART objectives and show strategic fit. Detail:
   [appraisal-process.md](references/appraisal-process.md).
3. **Longlist (economic case, part 1).** Define the five CSFs plus any constraints. Generate options with the
   options framework filter, covering scope, solution, delivery, implementation and funding, and rate each
   option choice green, amber or red with a reason. Record the result in the
   [options long-list matrix](templates/options-longlist-matrix.md). Then shortlist around five options: BAU,
   do minimum, the preferred way forward, a more ambitious version and a less ambitious version. BAU always
   goes to the shortlist.
4. **Prepare the cash flows.** For each option, list monetisable costs and benefits by year. Year 0 is the
   first year with any cost or benefit. Exclude sunk costs and transfers, or treat transfers consistently
   (para 6.38). Include maintenance, residual values and M&E costs. Tag health or life effects with
   `stream=health`, and tag each cost with `bearer=public|non-public`. Record every assumption and its source
   in the [assumptions log](templates/assumptions-log.md).
   - If any values are nominal, convert them first:
     `python -m agentlib greenbook real nominal.csv --deflators deflators.csv [--price-year 2026]`.
     The user must supply the deflator series, for example from the OBR (para 6.49). Never invent one.
5. **Optimism bias.** Run
   `python -m agentlib greenbook optimism-bias --capex X --upper-pct U --mitigation M --source "..."`.
   Add `--opex`, `--benefits` or `--duration` as needed. **U and M are user inputs.** They come from the
   organisation's own forecast-error evidence or from the Green Book supplementary guidance on optimism bias
   (paras 6.80-6.81). The 2026 Green Book contains no percentages. Use the adjusted figures in the cash flows.
   See [risk-and-optimism-bias.md](references/risk-and-optimism-bias.md).
6. **Shortlist appraisal (economic case, part 2).**
   - `python -m agentlib greenbook npv flows.csv --bau "Business as usual" [--format json]` calculates PVB,
     PVC, NPSV, BCR and RPSC and ranks the options. It applies the 2026 STPR (3.5% for years 1-30, 3.0% for
     31-75, 2.5% from year 76, compounded across bands) and 1.5% for health effects. Add `--gilt-rate R` for
     the Annex A private finance sensitivity, using a rate the user supplies.
   - `python -m agentlib greenbook switching flows.csv` gives switching values (NPSV to zero, and the preferred
     option being overtaken) and ±% sensitivity tables. Report these at least for the preferred option
     (para 6.104).
   - Describe unmonetisable impacts, risks, public sector financial impact (nominal and undiscounted) and
     distributional effects. Use `greenbook welfare-weight` where weighting is appropriate, and always show
     the unweighted figures alongside.
   - Complete the [economic appraisal summary / AST](templates/economic-appraisal-summary.md).
   - Detail: [discounting-and-metrics.md](references/discounting-and-metrics.md) and
     [distribution-and-valuation.md](references/distribution-and-valuation.md).
7. **Preferred option and the remaining cases.** Make a balanced value-for-money judgement (Box 1) rather than
   reading off the top BCR. Never apply a BCR threshold (para 6.98). Then draft:
   - the commercial case (procurement and risk allocation),
   - the financial case (affordability in nominal terms, RDEL/CDEL/AME, and contingency from the remaining
     optimism bias),
   - the management case (governance, the [benefits register](templates/benefits-register.md), the risk
     register, and the [M&E plan](templates/me-plan.md)).
   Detail: [five-case-model.md](references/five-case-model.md).
8. **Check.** Run `python -m agentlib greenbook check-case business_case.md`. Add `--strict` in CI. Fix every
   FAIL and explain every WARN. The checker only screens for keywords and structure, so finish with the
   quality checklist below.

### Decision rules

- An option that does not meet the objectives and CSFs does not go to the shortlist. **BAU is the exception
  and is always shortlisted** (para 2.16).
- Use social CBA by default. Use CEA (and NPUC) when the main benefits cannot be monetised (para 6.4).
- Convert to real terms first, then discount. Never add the inflation rate and the discount rate together
  (para 6.56).
- Present options in absolute terms and do not normalise BAU to zero (para 4.19).
- Keynesian multipliers and GDP/GVA changes are not social benefits (paras 6.41-6.43). Assume full
  displacement of jobs unless the chief economist signs off an exception (paras 8.41-8.43).
- If a parameter is not in the 2026 text (see [parameters-and-gaps.md](references/parameters-and-gaps.md)),
  ask the user for it and record its source. Do not supply a remembered value.

## Outputs

- Business case documents built from the templates, with the five cases as `##` headings.
- An economic appraisal summary that includes: the parameters used, with citations; PVB, PVC, NPSV, BCR and
  RPSC per option, ranked; switching values and sensitivity tables; and the AST.
- An assumptions log, an options long-list matrix, a benefits register and an M&E plan.
- Review findings, as a table of severity, issue, the Green Book 2026 paragraph and PDF page, and the fix.
- Cite the source as "HM Treasury Green Book 2026 (treasury-green), para X, PDF p.Y".

### Quality checklist

- [ ] All five cases present. SMART objectives, case for change, theory of change and a fair BAU in place.
- [ ] Longlist documented with CSFs and reasons. Shortlist of about five, including BAU and do minimum.
- [ ] Cash flows in real terms, discounted with the 2026 STPR and the health rate where relevant.
      Figures come from `greenbook npv`, not mental arithmetic.
- [ ] Optimism bias applied explicitly, with the source of its percentages recorded.
- [ ] Sensitivity analysis and switching values for the preferred option.
- [ ] Unmonetisable impacts, distributional effects (PSED), statutory duties (EPPS, biodiversity) and the
      public sector financial impact all covered.
- [ ] Preferred option justified on balanced value for money, with no BCR threshold.
- [ ] M&E plan in place and M&E costs included. Every assumption has a source.

## Sources

- HM Treasury, *The Green Book: UK government guidance on appraisal*, **2026 edition** (source id
  `treasury-green`; `sources/pdfs/hm-treasury-green-book-2026.pdf`). For body pages, the printed page is the
  PDF page minus 6. Pages relied on:
  - Ch.1-2 appraisal overview and Box 1 value for money: PDF pp.7-15
  - Ch.3 policy hierarchy, Five Case Model (Table 2) and business case stages (Table 3): PDF pp.16-22
  - Ch.4 rationale and objectives: PDF pp.23-28
  - Ch.5 longlist, CSFs (Table 4) and the options framework filter: PDF pp.29-36
  - Ch.6 shortlist appraisal, covering time horizons (p.39), inflation (p.45), STPR and health rate (p.46),
    risk (pp.47-49), optimism bias and contingency (p.50), and summary metrics (p.52, Table 10), no BCR
    thresholds (p.53), sensitivity and switching values (p.54): PDF pp.37-54
  - Ch.7 distributional analysis and welfare weights: PDF pp.55-58
  - Ch.8 valuation: PDF pp.59-74
  - Ch.9 the AST: PDF pp.75-77
  - Ch.10 monitoring and evaluation: PDF pp.78-80
  - Annex A private finance: PDF pp.81-85
- Machine-readable extract: `catalog/green-book.json`, generated by `scripts/extract/greenbook.py`.

## Limitations

- This output supports, but does not replace, qualified professional judgement (economists, finance,
  commercial and project delivery professionals). It is not a substitute for departmental or HM Treasury
  assurance, Better Business Cases accreditation, or formal approval.
- The 2026 Green Book defers many values to supplementary guidance and other publications, so the tools
  require them as inputs. These include optimism bias percentages, the gilt rate, GDP deflators, carbon
  values, QALY, VPF and WELLBY values, and pre-calculated discount tables. Users must verify the current
  versions.
- The business case guidance (Five Case Model detail), the Magenta, Teal and Orange Books, and departmental
  guidance such as DfT TAG are not bundled. Template content beyond what the Green Book states follows common
  practice and should be checked against the current business case guidance.
- `check-case` is a keyword and structure screen. It can miss substantive errors and can flag false positives.
- Values derived from the source are only as current as the pinned 2026 PDF. Check GOV.UK for later updates.
