# Outline Business Case (OBC): <proposal name>

<!-- Green Book 2026 Table 3 (PDF p.21): the OBC revisits the SOC options, carries out detailed shortlist appraisal to
identify the preferred option, and outlines the commercial, financial and management arrangements.
Run `python -m agentlib greenbook check-case <this file> --strict` before submission. -->

## Executive summary
<!-- All five dimensions; the preferred option and why; key risks; funding ask (para 9.2). -->

## 1. Strategic case
<!-- Update the SOC: case for change, theory of change, BAU, SMART objectives, strategic fit, statutory duties. Note any changes since the SOC. -->

## 2. Economic case
### 2.1 Longlist recap and changes since the SOC
### 2.2 Shortlisted options
<!-- BAU, do minimum, preferred way forward, more/less ambitious; equivalent public sector option if private finance is considered (para A.13). -->
### 2.3 Method and parameters
<!-- CBA or CEA (para 6.4); appraisal period (para 6.11); price base year; real terms via GDP deflator; STPR 3.5%/3.0%/2.5%
bands and 1.5% health rate (paras 6.54, 6.58); treatment of transfers (para 6.38); climate scenarios (para 6.14).
Paste the 'Parameters used' block from `greenbook npv`. -->
### 2.4 Costs and benefits
<!-- By option: capital, operating, maintenance, residual value, M&E costs; monetised benefits; unmonetisable impacts. Every input in the assumptions log. -->
### 2.5 Optimism bias and risk
<!-- `greenbook optimism-bias` output with the source of the percentages; risk costs (impact, correction, prevention); contingent liabilities. -->
### 2.6 Results
<!-- Paste the `greenbook npv` table (PVB, PVC, NPSV, BCR, RPSC; absolute values, BAU not normalised to zero). -->
### 2.7 Sensitivity analysis and switching values
<!-- Paste the `greenbook switching` tables; comment on how plausible the switching values are. -->
### 2.8 Distributional and place-based analysis
<!-- Proportionate (para 7.3); PSED; weighted alongside unweighted (para 7.13). -->
### 2.9 Appraisal summary table and preferred option
<!-- templates/economic-appraisal-summary.md; balanced value-for-money judgement (Box 1). -->

## 3. Commercial case
<!-- Procurement strategy; service requirements and outputs; risk allocation; charging mechanism; key contractual arrangements; personnel implications (Table 2). -->

## 4. Financial case
<!-- Public sector costs in RDEL/CDEL/AME (nominal, undiscounted); impact on income, expenditure and balance sheet; affordability and funding; contingency (para 6.84). -->

## 5. Management case
<!-- Governance; plan to FBC; change management; benefits register (templates/benefits-register.md); risk management;
M&E plan (templates/me-plan.md, para 10.7); contingency arrangements. -->

## Annexes
- Assumptions log
- Cash flow model and `greenbook` outputs (JSON)
- Risk register
- Options long-list matrix (from the SOC, updated)
