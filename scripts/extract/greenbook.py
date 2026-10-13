#!/usr/bin/env python3
"""Extract the HM Treasury Green Book (2026 edition) catalog from the pinned PDF.

Source : sources/pdfs/hm-treasury-green-book-2026.pdf (source id ``treasury-green``)
Licence: Crown copyright 2026, Open Government Licence v3.0. Item texts are
         paraphrases (short verbatim fragments only where exact wording
         matters) and carry attribution to HM Treasury.
Output : catalog/green-book.json

Method
------
``pdftotext -layout`` renders each PDF page (form-feed separated, so the Nth
chunk is PDF page N). Every catalog item below is defined by hand from a full
read of the 2026 text and carries an *anchor*: a regular expression matched
against the whitespace-normalised text of the body pages (PDF pp. 7-85). The
anchor must match on exactly one page; that page becomes ``citation.pdf_page``
and the printed folio ("The Green Book  N") found on the same page becomes
``citation.printed_page``. Numeric ``parameters`` are parsed from the text with
regular expressions and asserted against the values read by a human, so the
catalog cannot silently drift from the PDF.

IMPORTANT: this is the 2026 edition. Values from earlier editions (2018, 2020,
2022) are NOT used. Where the 2026 text defers a value to supplementary guidance
(e.g. optimism bias percentages, the gilt rate, the social value of carbon,
QALY/VPF/WELLBY values, pre-calculated discount factor tables, GDP deflator
forecasts) the catalog records that under ``parameters.not_in_edition`` and the
tools require the value as an explicit user input.

Run:  python scripts/extract/greenbook.py [--check]
``--check`` regenerates in memory and fails if catalog/green-book.json differs.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "sources" / "pdfs" / "hm-treasury-green-book-2026.pdf"
OUT = ROOT / "catalog" / "green-book.json"
EXTRACTION_DATE = "2026-10-13"
EXPECTED_PDF_PAGES = 88
BODY_FIRST_PAGE = 7      # PDF p.7 = printed page 1 (Chapter 1)
BODY_LAST_PAGE = 85      # PDF p.85 = printed page 79 (end of Annex A)
PRINTED_PAGE_OFFSET = 6  # printed folio = PDF page - 6 (verified per page below)

# Sanity expectations (all verified by reading the 2026 text)
EXPECTED_STAGES = 4          # Table 1 (PDF p.11): four stages of appraisal
EXPECTED_CASES = 5           # Para 3.12 / Table 2 (PDF pp.19-20)
EXPECTED_BC_STAGES = 3       # Table 3 (PDF p.21): SOC, OBC, FBC
EXPECTED_CSFS = 5            # Table 4 (PDF p.30)
EXPECTED_DUTIES = 3          # Para 3.18 (PDF p.21)
EXPECTED_OFF_CATEGORIES = 5  # Para 5.25 (PDF pp.33-34)
EXPECTED_SHORTLIST = 5       # Para 5.18 (PDF p.32)

GROUPS = [
    ("general", "Purpose, scope and principles of the Green Book (Chapters 1-2)"),
    ("process", "The appraisal process (Table 1)"),
    ("five-case", "The Five Case Model (Table 2)"),
    ("bc-stages", "Project business case stages (Table 3)"),
    ("duties", "Statutory duties reflected in appraisal (para 3.18)"),
    ("rationale", "Rationale and objectives (Chapter 4)"),
    ("csf", "Critical success factors (Table 4)"),
    ("longlist", "Generating options and longlist appraisal (Chapter 5)"),
    ("shortlist", "Shortlist appraisal: scope, time horizon, costs and benefits (Chapter 6)"),
    ("prices-discounting", "Inflation and discounting (Chapter 6)"),
    ("risk", "Risk, uncertainty, optimism bias and contingency (Chapter 6)"),
    ("metrics", "Summary metrics, preferred option, sensitivity and switching values (Chapter 6)"),
    ("distributional", "Distributional and place-based analysis (Chapter 7)"),
    ("valuation", "Valuation of social costs and social benefits (Chapter 8)"),
    ("presentation", "Presentation of results (Chapter 9)"),
    ("me", "Monitoring and evaluation (Chapter 10)"),
    ("private-finance", "Private finance models (Annex A)"),
]

# (id, group, title, anchor-regex, text, extra) -- text is a paraphrase of the cited passage.
ITEMS: list[tuple[str, str, str, str, str, dict]] = [
    # ---------------------------------------------------------------- general
    ("general.mandatory", "general", "Who must follow the Green Book",
     r"1\.3 The Green Book is intended for anyone",
     "Mandatory for UK government departments and arm's length bodies, with the accompanying business case "
     "guidance, when developing proposals involving significant public spending; also used for regulatory "
     "impact assessments.", {"para": "1.3-1.4", "level": "must"}),
    ("general.proportionality", "general", "Proportionality",
     r"1\.8 Green Book guidance should be used proportionately",
     "Guidance should be used proportionately: effort should correlate with the proposal's scale, cost, "
     "complexity and risk.", {"para": "1.8", "level": "should"}),
    ("general.supplementary-guidance", "general", "Supplementary guidance",
     r"1\.9 Many of the appraisal topics",
     "Many topics are covered in more detail in supplementary guidance listed on GOV.UK; departmental "
     "supplementary guidance is peer-reviewed by the Chief Economist Appraisal Group.",
     {"para": "1.9", "level": "guidance"}),
    ("general.appraisal-vs-evaluation", "general", "Appraisal versus evaluation",
     r"1\.10 Appraisal is distinct from evaluation",
     "Appraisal assesses a proposal before approval; evaluation assesses it after implementation (Magenta "
     "Book). Consider from the outset how the proposal will be evaluated.", {"para": "1.10", "level": "should"}),
    ("general.roamef", "general", "ROAMEF cycle",
     r"2\.2 Appraisal is just one stage",
     "A proposal typically progresses through Rationale, Objectives, Appraisal, Monitoring, Evaluation and "
     "Feedback (ROAMEF). The Green Book focuses on the first three.", {"para": "2.2-2.3", "level": "guidance"}),
    ("general.social-value", "general", "Social value",
     r"2\.5 The social value of a proposal",
     "Social value is the value a proposal brings to UK residents: all benefits, costs and risks affecting "
     "wellbeing (prosperity, justice, security, climate, environment, health, distributional effects), not "
     "just financial returns.", {"para": "2.4-2.5", "level": "guidance"}),
    ("general.value-for-money", "general", "Definition of value for money (Box 1)",
     r"Box 1\. Definition of value for money Value for money is",
     "Value for money is a balanced judgement on the optimal use of public resources, based on: performance "
     "against objectives and CSFs (options failing objectives cannot be VfM); monetisable costs and benefits; "
     "unmonetisable costs and benefits; public sector financial impact; distribution across groups and places; "
     "and risk and uncertainty.", {"para": "2.6 / Box 1", "level": "must"}),
    ("general.fraud-risk", "general", "Fraud risk",
     r"2\.24 Practitioners should pay particular attention to fraud risk",
     "Pay particular attention to fraud risk where public money is distributed through grants, loans or other "
     "payments (Government Fraud Risk Assessment Standard).", {"para": "2.24", "level": "should"}),

    # ---------------------------------------------------------------- process (Table 1)
    ("stage.1-rationale-objectives", "process", "Stage 1: Rationale and objectives",
     r"Table 1\. The appraisal process",
     "Set out why government needs to act, what is needed to bring about the desired outcomes, and what "
     "would happen if government does not act; establish specific objectives.",
     {"para": "2.8 / Table 1", "stage_number": 1, "level": "must"}),
    ("stage.2-options-longlist", "process", "Stage 2: Generating options and longlist appraisal",
     r"Table 1\. The appraisal process",
     "Generate and assess a wide range of possible options for achieving the objectives; take the most "
     "compelling forward as a shortlist.", {"para": "2.8 / Table 1", "stage_number": 2, "level": "must"}),
    ("stage.3-shortlist", "process", "Stage 3: Shortlist appraisal",
     r"Table 1\. The appraisal process",
     "Detailed analysis of the shortlisted options using social cost-benefit analysis or social "
     "cost-effectiveness analysis.", {"para": "2.8 / Table 1", "stage_number": 3, "level": "must"}),
    ("stage.4-preferred-option", "process", "Stage 4: Identifying the preferred option",
     r"Table 1\. The appraisal process",
     "Identify a single preferred option that optimises value for money and present it, with details of the "
     "appraisal process, in advice to decision makers.",
     {"para": "2.8 / Table 1", "stage_number": 4, "level": "must"}),
    ("process.evidence", "process", "All stages informed by evidence",
     r"2\.9 All four stages of appraisal must be informed by evidence",
     "All four stages must be informed by evidence, including previous evaluations of similar interventions; "
     "sources of uncertainty should be clearly communicated.", {"para": "2.9-2.10", "level": "must"}),

    # ---------------------------------------------------------------- five case model (Table 2)
    ("case.strategic", "five-case", "Strategic case",
     r"Table 2\. The Five Case Model",
     "Sets out the rationale and objectives for the intervention.",
     {"para": "3.12 / Table 2", "level": "must",
      "demonstrates": "The case for change and the SMART objectives the intervention will achieve.",
      "contents": ["Case for change", "Theory of change", "SMART objectives", "Business as usual",
                   "Strategic fit"],
      "guidance_sources": ["Business case guidance", "Green Book Chapter 4"]}),
    ("case.economic", "five-case", "Economic case",
     r"Table 2\. The Five Case Model",
     "Sets out the longlist and shortlist of options for achieving the objectives in the strategic case and "
     "identifies the preferred option that delivers the best value for money.",
     {"para": "3.12 / Table 2", "level": "must",
      "demonstrates": "The preferred option optimises value for money among a genuine range of options.",
      "contents": ["Critical success factors", "Longlist appraisal", "Shortlist appraisal"],
      "guidance_sources": ["Business case guidance", "Green Book Chapters 5-8"]}),
    ("case.commercial", "five-case", "Commercial case",
     r"Table 2\. The Five Case Model",
     "Describes how government will source the inputs required for delivering the preferred option and who "
     "will manage the risks associated with delivery and operation.",
     {"para": "3.12 / Table 2", "level": "must",
      "demonstrates": "The preferred option can be sourced on commercially viable terms with appropriate risk allocation.",
      "contents": ["Procurement strategy", "Service requirements and outputs", "Risk allocation",
                   "Charging mechanism", "Key contractual arrangements", "Personnel implications"],
      "guidance_sources": ["Business case guidance", "Commercial Standard and Sourcing Playbook",
                           "Cabinet Office Central Commercial Teams"]}),
    ("case.financial", "five-case", "Financial case",
     r"Table 2\. The Five Case Model",
     "Concerned with the affordability of the proposal for the public bodies involved.",
     {"para": "3.12 / Table 2", "level": "must",
      "demonstrates": "The proposal is affordable and funded for every public body involved.",
      "contents": ["Public sector costs in RDEL, CDEL or AME",
                   "Impact on income, expenditure and balance sheet of public bodies",
                   "Overall affordability and funding"],
      "guidance_sources": ["Business case guidance", "Consolidated budgeting guidance",
                           "Departmental finance teams"]}),
    ("case.management", "five-case", "Management case",
     r"Table 2\. The Five Case Model",
     "Sets out the practical arrangements for implementation and demonstrates that the preferred option can "
     "be delivered successfully.",
     {"para": "3.12 / Table 2", "level": "must",
      "demonstrates": "The preferred option can be delivered successfully.",
      "contents": ["Governance arrangements (roles, responsibilities, plans)",
                   "Change management, benefits realisation and risk management arrangements",
                   "Monitoring and evaluation plan", "Contingency arrangements and plans"],
      "guidance_sources": ["Business case guidance", "Teal Book (project delivery)",
                           "Orange Book (risk management)", "Magenta Book (monitoring and evaluation)"]}),
    ("five-case.interdependence", "five-case", "Five cases developed together",
     r"3\.15 The five dimensions cannot be developed or viewed in isolation",
     "The five dimensions are not five separate business cases but interconnected perspectives developed "
     "together iteratively and proportionately; no additional 'case' should be invented for special features "
     "(express them as objectives, CSFs or social costs/benefits).", {"para": "3.15-3.16", "level": "should"}),

    # ---------------------------------------------------------------- business case stages (Table 3)
    ("bc.soc", "bc-stages", "Strategic Outline Case (SOC)",
     r"Table 3\. Appraisal across the project business case process",
     "First stage: makes the case for change, identifies SMART objectives and sets out an initial longlist "
     "and shortlist of options to identify a preferred way forward.",
     {"para": "3.17 / Table 3", "level": "must",
      "appraisal_stages": ["Rationale and objectives", "Options generation and longlist appraisal",
                           "Identification of preferred way forward"]}),
    ("bc.obc", "bc-stages", "Outline Business Case (OBC)",
     r"Table 3\. Appraisal across the project business case process",
     "Second stage: revisits the SOC options to identify the preferred option after more detailed analysis, "
     "and outlines commercial, financial and management arrangements.",
     {"para": "3.17 / Table 3", "level": "must",
      "appraisal_stages": ["Shortlist appraisal", "Identification of preferred option"]}),
    ("bc.fbc", "bc-stages", "Full Business Case (FBC)",
     r"Table 3\. Appraisal across the project business case process",
     "Third stage: sets out the full commercial, financial and management arrangements required to deliver "
     "the project successfully, following procurement.",
     {"para": "3.17 / Table 3", "level": "must",
      "appraisal_stages": ["Review and iterate the appraisal following the procurement process"]}),

    # ---------------------------------------------------------------- statutory duties
    ("duty.epps", "duties", "Environmental principles policy statement (EPPS) duty",
     r"3\.18 There are three statutory duties",
     "Environment Act 2021 duty on Ministers to have due regard to the EPPS; identify environmental effects of "
     "options and apply the five principles; reflect explicitly at longlist and shortlist stages.",
     {"para": "3.18", "level": "must"}),
    ("duty.biodiversity", "duties", "Biodiversity duty",
     r"3\.18 There are three statutory duties",
     "Public authorities in England must consider what they can do to conserve and enhance biodiversity; "
     "reflect explicitly at longlist and shortlist stages.", {"para": "3.18", "level": "must"}),
    ("duty.psed", "duties", "Public sector equality duty (PSED)",
     r"3\.18 There are three statutory duties",
     "Have due regard to eliminating conduct prohibited by the Equality Act 2010, advancing equality of "
     "opportunity and fostering good relations; assess differential impacts on people with protected "
     "characteristics and consider mitigation.", {"para": "3.18", "level": "must"}),

    # ---------------------------------------------------------------- rationale
    ("rationale.case-for-change", "rationale", "Case for change",
     r"4\.2 A case for change explains why the government needs to act",
     "Explains why the government needs to act, why the outcomes are worth pursuing, why government is best "
     "placed, and why businesses, households and charities cannot achieve them themselves.",
     {"para": "4.2-4.5", "level": "should"}),
    ("rationale.market-failure", "rationale", "Market failure and equity rationales",
     r"4\.6 Economists often consider market failures",
     "Rationales include market failures (public goods, externalities, market power, imperfect information, "
     "co-ordination failure) and equity; PESTLE analysis can frame context.",
     {"para": "4.6-4.8", "level": "guidance"}),
    ("rationale.theory-of-change", "rationale", "Theory of change",
     r"4\.9 A theory of change explains how the inputs and outputs",
     "The logical chain from inputs to outputs to outcomes, with stated, evidenced assumptions agreed by "
     "decision makers.", {"para": "4.9-4.13", "level": "should"}),
    ("rationale.bau", "rationale", "Business as usual (BAU)",
     r"4\.14 The business as usual \(BAU\) is the outcome",
     "The outcome expected if current arrangements continue and the proposal is not implemented; a "
     "benchmark. BAU does not mean doing nothing and must be fair and reasonable.",
     {"para": "4.14-4.18", "level": "must"}),
    ("rationale.bau-absolute", "rationale", "Present options in absolute terms",
     r"4\.19 The social costs and social benefits associated with different options",
     "Costs and benefits should usually be presented in absolute terms rather than as increments from BAU; "
     "avoid normalising BAU to zero.", {"para": "4.19", "level": "should"}),
    ("rationale.deadweight-additionality", "rationale", "Deadweight and additionality",
     r"4\.17 Fully understanding the BAU",
     "Deadweight: outcomes that would have happened anyway. Additionality: outcomes caused by the "
     "intervention.", {"para": "4.17", "level": "guidance"}),
    ("rationale.smart-objectives", "rationale", "SMART objectives",
     r"4\.21 The objectives of a proposal must be SMART",
     "Objectives must be specific, measurable, achievable, realistic and time-limited; few in number; "
     "ideally outcome-based rather than output-based.", {"para": "4.20-4.26", "level": "must"}),
    ("rationale.strategic-fit", "rationale", "Strategic fit",
     r"4\.27 The strategic fit of a proposal",
     "Alignment with the higher-level programme/portfolio/policy, other proposals of the originating "
     "organisation and those of other public bodies.", {"para": "4.27", "level": "should"}),
    ("rationale.transformational-change", "rationale", "Transformational change",
     r"4\.28 Some proposals have the objective of bringing about transformational",
     "Claims of transformational change (radical, permanent, qualitative change, often with tipping points "
     "and feedback) must be transparently explained and supported by evidence.",
     {"para": "4.28-4.30", "level": "must"}),
    ("rationale.policy-hierarchy", "rationale", "Policy hierarchy and golden thread",
     r"3\.5 The alignment between the objectives set at the policy level",
     "Objectives cascade from policy to portfolio, programme and project (the 'golden thread'); a project "
     "appraisal need not justify its parent programme.", {"para": "3.2-3.10", "level": "guidance"}),

    # ---------------------------------------------------------------- CSFs (Table 4)
    ("csf.1-objectives-strategic-fit", "csf", "CSF 1: Objectives and strategic fit",
     r"Table 4\. Examples of critical success factors",
     "The proposal meets its SMART objectives and has strategic fit with other public sector activity.",
     {"para": "5.5 / Table 4", "level": "guidance"}),
    ("csf.2-value-for-money", "csf", "CSF 2: Value for money",
     r"Table 4\. Examples of critical success factors",
     "The proposal represents the optimal use of public resources to achieve its objectives.",
     {"para": "5.5 / Table 4", "level": "guidance"}),
    ("csf.3-supplier-capacity", "csf", "CSF 3: Supplier capacity and capability",
     r"Table 4\. Examples of critical success factors",
     "Suppliers can feasibly provide the inputs; government and suppliers can agree payments and risk transfer.",
     {"para": "5.5 / Table 4", "level": "guidance"}),
    ("csf.4-affordability", "csf", "CSF 4: Affordability",
     r"Table 4\. Examples of critical success factors",
     "The proposal is affordable for all of the public bodies involved.", {"para": "5.5 / Table 4", "level": "guidance"}),
    ("csf.5-achievability", "csf", "CSF 5: Achievability",
     r"Table 4\. Examples of critical success factors",
     "Robust arrangements are in place to deliver, monitor and evaluate the proposal.",
     {"para": "5.5 / Table 4", "level": "guidance"}),
    ("csf.constraints", "csf", "Constraints as CSFs",
     r"5\.6 A proposal.s critical success factors might also include constraints",
     "CSFs may include constraints such as legal requirements, ethical standards, social acceptability, "
     "timing and environmental policy.", {"para": "5.6", "level": "guidance"}),

    # ---------------------------------------------------------------- longlist
    ("longlist.purpose", "longlist", "Longlist: options generation and longlist appraisal",
     r"5\.1 A longlist is a wide range of potential options",
     "Generate a wide range of options and assess them against objectives and CSFs to narrow to a shortlist; "
     "options failing objectives or CSFs must not proceed.", {"para": "5.1-5.2, 5.9", "level": "should"}),
    ("longlist.documented", "longlist", "Document longlist reasoning",
     r"5\.4 The process of options generation and longlist appraisal should be clearly documented",
     "Document which options were considered and why each was or was not progressed to the shortlist.",
     {"para": "5.3-5.4", "level": "should"}),
    ("longlist.indicative-estimates", "longlist", "Indicative estimates at longlist",
     r"5\.10 Practitioners should use longlist appraisal to start identifying",
     "Longlist appraisal typically uses indicative estimates and ranges rather than detailed CBA.",
     {"para": "5.10", "level": "guidance"}),
    ("longlist.dependencies", "longlist", "Dependencies and unintended consequences",
     r"5\.11 Practitioners should consider dependencies",
     "Consider external dependencies and potential unintended consequences (e.g. gaming of incentive schemes).",
     {"para": "5.11-5.12", "level": "should"}),
    ("longlist.off", "longlist", "Options framework filter (OFF)",
     r"5\.13 The Green Book recommends conducting options generation and longlist",
     "Recommended (not mandatory) method: break options into components, rate option choices and recombine "
     "them; delivered through structured facilitated workshops with explicit deliberation.",
     {"para": "2.12, 5.13, 5.21-5.23", "level": "recommended"}),
    ("longlist.off-categories", "longlist", "OFF categories",
     r"5\.25 Practitioners start by identifying a set of categories",
     "Five recommended categories: scope, solution, delivery, implementation and funding, considered in "
     "that order.", {"para": "5.25-5.32", "level": "recommended",
                    "categories": ["Scope", "Solution", "Delivery", "Implementation", "Funding"]}),
    ("longlist.off-ratings", "longlist", "OFF ratings (green/amber/red)",
     r"5\.26 The options framework filter is an iterative process",
     "Green: best meets CSFs; amber: meets CSFs less well (both carried forward); red: fails CSFs (dropped). "
     "Record the reason for each rating with evidence, assumptions and sources.",
     {"para": "5.26-5.27", "level": "must"}),
    ("longlist.mcda-mca", "longlist", "MCDA acceptable; simple MCA not recommended",
     r"5\.14 Another potential approach to longlist appraisal is multi-criteria decision",
     "MCDA with swing weighting and an expert facilitator may be used; simple weighting-and-scoring MCA is "
     "recommended against. SWOT may also be used.", {"para": "5.14-5.16", "level": "recommended"}),
    ("longlist.summary-matrix", "longlist", "Options summary matrix",
     r"5\.33 Practitioners can present the results of the options framework filter",
     "Present OFF results in an options summary matrix (categories, BAU, option choices, ratings) "
     "accompanied by a record of workshop decisions and rationale.", {"para": "5.33-5.34", "level": "must"}),
    ("shortlist.composition", "longlist", "Shortlist composition (around five options)",
     r"5\.17 A shortlist should generally include around five options",
     "Around five options: BAU, do minimum, preferred way forward, more ambitious and less ambitious "
     "preferred way forward (the latter may be excluded if the preferred way forward is the do minimum).",
     {"para": "5.17-5.19, 5.35", "level": "should",
      "options": ["Business as usual", "Do minimum", "Preferred way forward",
                  "More ambitious preferred way forward", "Less ambitious preferred way forward"]}),
    ("shortlist.bau-always", "longlist", "BAU always shortlisted",
     r"2\.16 Practitioners conclude longlist appraisal",
     "Options not achieving objectives must not be shortlisted, except BAU, which must always be taken "
     "forward as the benchmark.", {"para": "2.16, 5.18", "level": "must"}),
    ("shortlist.do-minimum", "longlist", "Do minimum",
     r"5\.18 The five options on the shortlist should typically include",
     "The option that just achieves the objectives; shows whether other options add genuinely worthwhile "
     "improvements or 'gold plating'.", {"para": "5.18", "level": "should"}),
    ("shortlist.pwf-vs-preferred", "longlist", "Preferred way forward vs preferred option",
     r"5\.20 Longlist appraisal identifies a preferred way forward",
     "Longlist appraisal identifies a preferred way forward; shortlist appraisal identifies the preferred "
     "option, which may differ.", {"para": "5.20", "level": "guidance"}),

    # ---------------------------------------------------------------- shortlist
    ("shortlist.methods", "shortlist", "CBA or CEA",
     r"6\.4 There are two main methods of analysis for shortlist appraisal",
     "Social cost-benefit analysis (recommended for detailed comparison) or social cost-effectiveness "
     "analysis (when main benefits are unmonetisable or options deliver the same output differently).",
     {"para": "2.19, 6.4", "level": "should"}),
    ("shortlist.scope-uk", "shortlist", "Scope is UK society",
     r"6\.5 The scope of all appraisals is UK society",
     "Scope is all UK residents; consider impacts on other public bodies, households, businesses and "
     "charities, not just the originating organisation.", {"para": "6.5-6.7", "level": "must"}),
    ("shortlist.time-horizon", "shortlist", "Time horizon",
     r"6\.9 The time horizon of an appraisal",
     "Cover the whole lifetime of the proposal. Standard horizons additional to year 0: 60 years "
     "infrastructure, 30 years refurbishment, 10 years regulations, 10 years other; agree longer periods "
     "with HM Treasury where effects extend beyond 60 years.", {"para": "6.9-6.13", "level": "should"}),
    ("shortlist.year-0", "shortlist", "Year 0",
     r"6\.10 The first year of an appraisal is known as year 0",
     "Year 0 is generally the first year with social costs or benefits; may be standardised to a calendar or "
     "financial year across options.", {"para": "6.10", "level": "guidance"}),
    ("shortlist.climate-scenarios", "shortlist", "Climate scenarios",
     r"6\.14 Practitioners should take climate change impacts into account",
     "Horizons ending before 2040: appraise against a 2C warming scenario; ending 2040 or later: at least "
     "2C and 4C scenarios (AECC supplementary guidance).", {"para": "6.14, 8.86", "level": "should"}),
    ("shortlist.classification", "shortlist", "Classifying costs and benefits",
     r"6\.26 Social costs and social benefits are either monetisable or unmonetisable",
     "Monetisable (cash / non-cash) vs unmonetisable (quantifiable / qualitative); monetise where possible "
     "and proportionate, focusing on decisive impacts.", {"para": "6.23-6.30", "level": "should"}),
    ("shortlist.cost-types", "shortlist", "Capital, operating and maintenance costs",
     r"6\.31 Practitioners should distinguish between capital costs",
     "Distinguish capital, operating and maintenance costs; appraisals must reflect maintenance needed to "
     "sustain benefits.", {"para": "6.31, 8.34", "level": "must"}),
    ("shortlist.sunk-costs", "shortlist", "Exclude sunk costs",
     r"6\.32 Sunk costs are costs that have already been incurred",
     "Sunk costs must not be included; consider the opportunity cost of continuing to use already-paid "
     "resources.", {"para": "6.32", "level": "must"}),
    ("shortlist.transfers", "shortlist", "Economic transfers",
     r"6\.33 An economic transfer is a transfer of money",
     "Transfers (taxes, grants, subsidies, benefits, fines) net to zero for society; either include as "
     "offsetting items (pushes BCR towards one) or exclude, and explain; must be shown in distributional "
     "analysis and public sector financial impact.", {"para": "6.33-6.40", "level": "must"}),
    ("shortlist.no-macro", "shortlist", "No GDP/GVA or Keynesian multipliers",
     r"6\.41 Appraisal is concerned with the welfare and wellbeing impacts",
     "Do not compare options on GDP/GVA changes and do not count Keynesian multiplier effects as social "
     "benefits.", {"para": "6.41-6.43", "level": "should"}),
    ("shortlist.cost-of-funds", "shortlist", "Costs of raising public funds",
     r"6\.44 There are costs associated with raising public funds",
     "Generally not included in appraisal, except when assessing private finance model options (Annex A).",
     {"para": "6.44", "level": "should"}),

    # ---------------------------------------------------------------- prices & discounting
    ("prices.real-terms", "prices-discounting", "Real prices",
     r"6\.47 Social costs and social benefits should be estimated in real prices",
     "Estimate in real prices (nominal equals real in year 0): forecast nominal prices then remove general "
     "inflation using the GDP deflator.", {"para": "6.45-6.48", "level": "should"}),
    ("prices.gdp-deflator-source", "prices-discounting", "GDP deflator forecasts",
     r"6\.49 Practitioners can find forecasts of the GDP deflator",
     "Five-year GDP deflator forecasts: latest OBR Economic and Fiscal Outlook; fifty-year: OBR Long-term "
     "economic determinants. (No deflator values are given in the Green Book.)",
     {"para": "6.49", "level": "guidance"}),
    ("prices.relative-price-effects", "prices-discounting", "Relative price effects",
     r"6\.50 Practitioners should use historical evidence and appropriate forecasts",
     "Include significant relative price effects (e.g. construction) in CBA; quality changes may be "
     "reflected in real prices.", {"para": "6.50-6.51", "level": "should"}),
    ("discount.stpr", "prices-discounting", "Social Time Preference Rate (STPR)",
     r"6\.54 The discount rate used in the Green Book",
     "STPR is 3.50% real for years 1 to 30, 3.00% for years 31 to 75, and 2.50% for year 76 onwards. "
     "Derivation is in the supplementary guidance on discounting.", {"para": "6.52-6.54", "level": "should"}),
    ("discount.factors", "prices-discounting", "Applying discount factors",
     r"6\.55 To adjust for discounting",
     "Multiply future-year values by that year's discount factor; pre-calculated factors are in the "
     "supplementary guidance on discounting (Table 8 gives a worked example).",
     {"para": "6.55, 6.57 / Table 8", "level": "should"}),
    ("discount.real-only", "prices-discounting", "Discount real values only",
     r"6\.56 Discounting is distinct from adjusting for inflation",
     "The STPR is a real rate and must be applied only to real values; never add inflation and discount "
     "rates together.", {"para": "6.56", "level": "must"}),
    ("discount.health", "prices-discounting", "Health discount rate",
     r"6\.58 The social benefits and social costs of a proposal may include effects on the",
     "Health and life effects are discounted at 1.5% (wealth effect excluded); the health rate applies in "
     "every year of the appraisal; other effects use the standard STPR.", {"para": "6.58", "level": "should"}),
    ("discount.no-retrospective", "prices-discounting", "No retrospective discounting",
     r"6\.59 Discounting should not be applied retrospectively",
     "Do not discount (or compound) costs and benefits that have already occurred.",
     {"para": "6.59", "level": "should"}),

    # ---------------------------------------------------------------- risk
    ("risk.risk-uncertainty", "risk", "Risk and uncertainty",
     r"6\.61 Practitioners must consider risk and uncertainty",
     "Must be considered as part of the VfM judgement. Uncertainty: assumptions not fully known; risk: the "
     "effect of uncertainty on objectives (consistent with the Orange Book).",
     {"para": "6.60-6.64", "level": "must"}),
    ("risk.risk-costs", "risk", "Risk costs",
     r"6\.65 The existence of risk in an appraisal brings about different types of costs",
     "Impact costs, correction costs and prevention costs; include risk costs in appraisal.",
     {"para": "2.23, 6.65", "level": "should"}),
    ("risk.mitigation-transfer", "risk", "Risk mitigation and transfer",
     r"6\.66 Practitioners should consider how to reduce the risk",
     "Weigh the costs and benefits of mitigation and of transferring risk to the party best able to manage it.",
     {"para": "6.66", "level": "should"}),
    ("risk.contingent-liabilities", "risk", "Contingent liabilities",
     r"6\.67 Contingent liabilities are potential future costs",
     "Appraise contingent liabilities as part of the expected social cost of risk (HM Treasury contingent "
     "liability approval framework).", {"para": "6.67", "level": "should"}),
    ("risk.quantifying-uncertainty", "risk", "Expressing uncertainty",
     r"6\.68 Practitioners should try to give an indication of the uncertainty",
     "Central estimate and range; expected values (probability-weighted); confidence intervals; P90 values; "
     "consider tail risks proportionately.", {"para": "6.68-6.73", "level": "should"}),
    ("risk.advanced-methods", "risk", "Advanced risk methods",
     r"6\.74 Scenario analysis is a method of analysing uncertainty",
     "Scenario analysis, decision trees, real options analysis and Monte Carlo analysis for higher-cost, "
     "higher-risk proposals.", {"para": "6.74-6.77", "level": "guidance"}),
    ("risk.optimism-bias", "risk", "Optimism bias",
     r"6\.78 Optimism bias is the demonstrated systematic tendency",
     "Must explicitly adjust at the outset: increase costs and durations and decrease benefits. Size the "
     "adjustment from the organisation's historical forecast errors; if none, use generic values in the "
     "Green Book supplementary guidance on optimism bias (no percentages are given in the 2026 Green Book "
     "itself). Reduce the adjustment in proportion to risks prevented.",
     {"para": "2.25, 6.78-6.82", "level": "must"}),
    ("risk.contingency", "risk", "Contingency",
     r"6\.83 Contingency is an allowance in the financial dimension",
     "Contingency (financial case) = remaining optimism bias adjustment + value of unprevented risk, "
     "converted to nominal; typically not allocated to the project because government self-insures. "
     "Prevention costs belong in core costs.", {"para": "6.83-6.84", "level": "should"}),

    # ---------------------------------------------------------------- metrics
    ("metrics.public-sector-financial-impact", "metrics", "Public sector financial impact",
     r"6\.86 Public sector financial impact refers to the estimated costs and receipts",
     "Lifetime costs and receipts for all public bodies, excluding wider social costs; shown in nominal, "
     "undiscounted terms; cost-shifting within the public sector is not VfM.",
     {"para": "6.85-6.91", "level": "should"}),
    ("metrics.econ-vs-financial", "metrics", "Economic vs financial case treatment (Table 9)",
     r"Table 9\. Main differences between treatment of costs and benefits",
     "Economic case: real, discounted at STPR, transfers optional, wider social impacts included. Financial "
     "case: nominal, undiscounted, transfers always included, wider social impacts excluded; depreciation "
     "only in the financial dimension.", {"para": "6.88, 6.92 / Table 9", "level": "should"}),
    ("metrics.pv-variables", "metrics", "PVB, PVC, PVC public, PVC non-public",
     r"6\.93 Practitioners can use the steps so far to calculate four different variables",
     "Present values (real, discounted) of monetisable benefits (PVB), costs (PVC), public sector financial "
     "costs (PVC public) and costs outside the public sector (PVC non-public).", {"para": "6.93", "level": "guidance"}),
    ("metrics.npsv", "metrics", "Net present social value (NPSV)",
     r"Table 10\. Summary metrics of social value",
     "NPSV = PVB - PVC.", {"para": "6.93 / Table 10", "level": "should", "formula": "PVB - PVC"}),
    ("metrics.bcr", "metrics", "Benefit-cost ratio (BCR)",
     r"Table 10\. Summary metrics of social value",
     "BCR = PVB / PVC: monetisable social benefits per pound of monetisable social cost.",
     {"para": "6.93 / Table 10", "level": "should", "formula": "PVB / PVC"}),
    ("metrics.rpsc", "metrics", "Return on public sector cost (RPSC)",
     r"Table 10\. Summary metrics of social value",
     "RPSC = (PVB - PVC non-public) / PVC public: social value relative to cost to the public sector.",
     {"para": "6.93 / Table 10", "level": "should", "formula": "(PVB - PVC_non_public) / PVC_public"}),
    ("metrics.npuc", "metrics", "Net present unit cost (NPUC)",
     r"Table 10\. Summary metrics of social value",
     "For CEA: PVC relative to quantifiable (non-monetisable) social benefits.",
     {"para": "6.93 / Table 10", "level": "should", "formula": "PVC / quantifiable benefits"}),
    ("metrics.sign-convention", "metrics", "Sign convention affects BCR",
     r"6\.95 Practitioners should take care when looking at impacts",
     "Treating an impact as a negative benefit or a cost changes the BCR (not NPSV or RPSC); explain the "
     "choice. Use a consistent approach across similar decisions.", {"para": "6.94-6.95", "level": "should"}),
    ("metrics.ranking-not-sufficient", "metrics", "Initial ranking is not sufficient",
     r"6\.96 Practitioners should use summary metrics of social value to produce an",
     "Rank options by summary metrics as a first step only; a single metric is not enough for the balanced "
     "VfM judgement (Box 1).", {"para": "2.30, 6.96-6.97", "level": "should"}),
    ("metrics.no-bcr-thresholds", "metrics", "No BCR thresholds",
     r"6\.98 Practitioners should not make judgements on value for money using BCR",
     "Do not judge VfM using BCR thresholds (e.g. rejecting a proposal with BCR below two). A BCR below one "
     "may still be VfM if there are significant unmonetisable benefits, subject to rigorous scrutiny.",
     {"para": "6.98-6.99", "level": "must"}),
    ("metrics.same-objectives", "metrics", "Compare options with the same objectives only",
     r"6\.100 Summary metrics of social value should only be used for comparing",
     "Summary metrics compare options meeting the same objectives, not proposals with different objectives.",
     {"para": "6.100", "level": "should"}),
    ("metrics.sensitivity", "metrics", "Sensitivity analysis",
     r"6\.102 Sensitivity analysis tests how changes in key assumptions",
     "Stress-test uncertain assumptions (e.g. input costs, demand) and show effects on social value.",
     {"para": "2.27, 6.102", "level": "should"}),
    ("metrics.switching-values", "metrics", "Switching values",
     r"6\.103 A switching value is the value that a key variable would need to change",
     "The value a key variable must reach for an option to stop being VfM (e.g. NPSV negative, or preferred "
     "option overtaken). At minimum, sensitivity analysis and switching values for the preferred option must "
     "be included in results; can also test unmonetisable benefits.", {"para": "6.103-6.105", "level": "should"}),

    # ---------------------------------------------------------------- distributional
    ("distributional.proportionate", "distributional", "Proportionate distributional analysis",
     r"7\.3 It may not be proportionate to calculate all distributional effects",
     "Effort proportionate to scale: describe small effects; analyse significant effects; present welfare "
     "effects where redistribution is an objective or effects are highly significant.",
     {"para": "7.1-7.4", "level": "should"}),
    ("distributional.equivalisation", "distributional", "Income equivalisation",
     r"7\.7 Equivalisation adjusts household incomes",
     "Adjust household incomes for composition (Figure 7 scores: first adult 0.67, additional adult 0.33, "
     "child 14+ 0.33, child under 14 0.20).", {"para": "7.5-7.7 / Figure 7", "level": "should"}),
    ("distributional.welfare-weights", "distributional", "Distributional (welfare) weights",
     r"7\.10 Calculating a welfare weight for a particular group",
     "Welfare weight = (national median equivalised income / group median equivalised income)^1.3; weighted "
     "impact = income change x weight; weighted estimates must be shown alongside unweighted.",
     {"para": "7.8-7.15", "level": "must"}),
    ("distributional.place-based", "distributional", "Place-based analysis",
     r"7\.16 Place-based analysis assesses how the benefits, costs and risks",
     "Assess distribution across places; consider additionality, deadweight, displacement, substitution and "
     "leakage; sub-national metrics always alongside UK-wide values.", {"para": "7.16-7.20", "level": "should"}),
    ("distributional.local-authority-funding", "distributional", "Distributing money to local authorities",
     r"7\.21 A proposal that gives money to local authorities",
     "Follow the funding simplification doctrine; choose allocation or competition; competitive processes "
     "run bids to OBC with final allocation conditional on a satisfactory FBC.",
     {"para": "7.21-7.24", "level": "should"}),

    # ---------------------------------------------------------------- valuation
    ("valuation.opportunity-cost", "valuation", "Opportunity cost and market prices",
     r"8\.1 Practitioners should assess the value of goods and services",
     "Value at opportunity cost, starting from market prices excluding taxes and subsidies; use non-market "
     "valuation where markets fail.", {"para": "8.1-8.5", "level": "should"}),
    ("valuation.hierarchy", "valuation", "Valuation hierarchy",
     r"8\.6 There are various different valuation techniques",
     "From most to least reliable: market prices, generic prices, revealed preference, then stated "
     "preference / wellbeing valuation; use ranges and sensitivity for non-market prices.",
     {"para": "8.6-8.22 / Figure 8", "level": "should"}),
    ("valuation.residual-value", "valuation", "Residual value",
     r"8\.32 An asset.s residual value or liability",
     "Include an asset's residual value or liability at the end of the appraisal period.",
     {"para": "8.31-8.33", "level": "should"}),
    ("valuation.labour-displacement", "valuation", "Full displacement of jobs",
     r"8\.41 Practitioners should generally assume that proposals do not bring about",
     "Assume no increase in national labour supply; any exception needs compelling evidence signed off by "
     "the chief economist.", {"para": "8.41-8.43", "level": "should"}),
    ("valuation.life-health", "valuation", "Life and health values",
     r"8\.55 A proposal might involve a risk to human life",
     "Use VPF (TAG data book), SLY/VOLY and QALY (supplementary guidance on health); values are not given in "
     "the Green Book.", {"para": "8.55-8.58", "level": "should"}),
    ("valuation.ghg", "valuation", "Energy use and GHG emissions",
     r"8\.63 The Climate Change Act 2008",
     "Value changes in energy use (quantity x LRVC) and emissions (quantity x emissions factor x social "
     "value of carbon) per DESNZ supplementary guidance; report levels and monetised values.",
     {"para": "8.63-8.74", "level": "should"}),
    ("valuation.ghg-negligible", "valuation", "Negligible emissions threshold",
     r"8\.75 The level of detail and complexity devoted to emissions analysis",
     "Generally negligible if below 0.1 MtCO2e in every year of the appraisal horizon; basic analysis still "
     "required.", {"para": "8.75", "level": "guidance"}),
    ("valuation.natural-capital", "valuation", "Natural capital screening",
     r"8\.80 Practitioners should consider the natural capital screening questions",
     "Screen options against natural capital assets; if any apply, follow the ENCA four-step approach.",
     {"para": "8.76-8.84", "level": "should"}),
    ("valuation.efficiency-fraud-error", "valuation", "Efficiency savings, fraud and error",
     r"8\.88 A proposal might generate social benefits by reducing the resources",
     "Efficiency savings must not come from reduced outputs; treat fraud proceeds as a one-sided transfer "
     "or a social cost; assume fraud where error status is doubtful.", {"para": "8.88-8.99", "level": "should"}),

    # ---------------------------------------------------------------- presentation
    ("presentation.exec-summary", "presentation", "Business case executive summary",
     r"9\.2 The presentation of appraisal results will depend",
     "Spending appraisals are presented in a business case beginning with an executive summary covering the "
     "five dimensions; regulation follows the Better Regulation Framework.", {"para": "9.1-9.2", "level": "should"}),
    ("presentation.ast", "presentation", "Appraisal summary table (AST)",
     r"9\.3 The Green Book recommends presenting the results of shortlist appraisal",
     "Recommended AST per shortlisted option: description (why preferred or inferior); summary metrics "
     "(NPSV, BCR, RPSC or NPUC); unmonetisable costs and benefits; public sector financial impact (nominal, "
     "undiscounted); distribution across groups and places; with risks and uncertainties for each element.",
     {"para": "2.32, 9.3-9.6 / Table 12", "level": "recommended"}),

    # ---------------------------------------------------------------- M&E
    ("me.definitions", "me", "Monitoring and evaluation",
     r"10\.1 Appraisal takes place as a proposal is being developed",
     "Monitoring tracks delivery progress; evaluation assesses design, implementation and outcomes "
     "(Magenta Book). Goals: learning and accountability.", {"para": "10.1-10.3", "level": "guidance"}),
    ("me.evaluation-types", "me", "Types of evaluation",
     r"10\.4 The Magenta Book sets out three types of evaluation",
     "Process, impact and value for money evaluation.", {"para": "10.4", "level": "guidance"}),
    ("me.evidence-input", "me", "Evaluation evidence as input",
     r"10\.5 Appraisals should be informed by evaluation evidence",
     "Use evaluation evidence for rationale, objectives and option appraisal, including historical forecast "
     "errors to derive optimism bias adjustments.", {"para": "10.5-10.6", "level": "should"}),
    ("me.plan", "me", "Evaluation plan",
     r"10\.7 Practitioners should develop an evaluation plan",
     "Develop an evaluation plan once a preferred option is identified and have a robust plan before final "
     "approval, based on the theory of change; the management case sets out monitoring and evaluation.",
     {"para": "10.7", "level": "should"}),
    ("me.costs", "me", "M&E costs included",
     r"10\.8 Appraisals should include the costs of monitoring and evaluation",
     "Include M&E costs in the economic and financial dimensions; no fixed proportion, assess case by case.",
     {"para": "10.8-10.9", "level": "should"}),
    ("me.registry-publication", "me", "Evaluation registry and business case publication",
     r"10\.11 UK government departments are required to register",
     "Register evaluations on the Government Evaluation Registry; GMPP business cases must be published "
     "within four months of HM Treasury approval.", {"para": "10.11-10.12", "level": "must"}),

    # ---------------------------------------------------------------- private finance
    ("pf.longlist", "private-finance", "Private finance at longlist",
     r"A\.9 At longlist appraisal stage, practitioners should use qualitative questions",
     "Use the Table A.1 qualitative questions alongside the CSFs to decide whether a private finance model "
     "should be the preferred way forward or shortlisted.", {"para": "A.8-A.9 / Table A.1", "level": "must"}),
    ("pf.shortlist-requirements", "private-finance", "Private finance shortlist requirements",
     r"A\.10 If an option involving a private finance model is brought forward",
     "Include a public sector option (unless agreed with HM Treasury) and an additional sensitivity "
     "discounting the costs of all shortlisted options at the risk-free real gilt rate.",
     {"para": "A.10", "level": "must"}),
    ("pf.payments-as-costs", "private-finance", "Model payments as they occur",
     r"A\.11 In the economic case, practitioners should model the social costs",
     "Model private finance social costs as public-to-private payments over the contract as they occur, "
     "regardless of balance sheet classification.", {"para": "A.11-A.12", "level": "should"}),
    ("pf.public-sector-option", "private-finance", "Public sector option (comparator)",
     r"A\.13 At least one shortlisted option must be equivalent in quality",
     "An equivalent-quality, publicly financed and procured option, adjusted for effective tax differences; "
     "optimism bias applied to all options.", {"para": "A.13-A.16", "level": "must"}),
    ("pf.gilt-sensitivity", "private-finance", "Gilt-rate sensitivity",
     r"A\.17 In addition to standard shortlist appraisal",
     "Discount only the costs of each shortlisted option at the risk-free real gilt rate matching the "
     "weighted average contract duration (consult HM Treasury for the rate; none is given in the Green Book).",
     {"para": "A.17-A.18", "level": "must"}),
]


# ---------------------------------------------------------------- PDF helpers
def read_pages(pdf: Path) -> list[str]:
    if shutil.which("pdftotext"):
        raw = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                             capture_output=True, text=True).stdout
        pages = raw.split("\f")
        if pages and not pages[-1].strip():
            pages = pages[:-1]
        return pages
    from pypdf import PdfReader  # fallback

    return [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]


def norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


FOLIO_RE = re.compile(r"(?:The Green Book\s+(\d{1,2})\s*$)|(?:^\s*(\d{1,2})\s+The Green Book)", re.M)


def printed_folio(page_text: str) -> int | None:
    found = FOLIO_RE.findall(page_text)
    for a, b in reversed(found):
        return int(a or b)
    return None


def locate(pages_norm: list[str], pattern: str) -> int:
    rx = re.compile(pattern)
    hits = [i + 1 for i, t in enumerate(pages_norm)
            if BODY_FIRST_PAGE <= i + 1 <= BODY_LAST_PAGE and rx.search(t)]
    if len(hits) != 1:
        raise AssertionError(f"anchor /{pattern}/ matched pages {hits}; expected exactly one")
    return hits[0]


def _num(rx: str, text: str) -> str:
    m = re.search(rx, text)
    if not m:
        raise AssertionError(f"parameter pattern not found: /{rx}/")
    return m.group(1)


# ---------------------------------------------------------------- parameters
def build_parameters(pages_norm: list[str], cite) -> dict:
    p_stpr = locate(pages_norm, r"6\.54 The discount rate used in the Green Book")
    t = pages_norm[p_stpr - 1]
    r1 = float(_num(r"set at (\d\.\d+)% in real terms for years 1 to 30", t))
    r2 = float(_num(r"It is (\d\.\d+)% for years 31 to 75", t))
    r3 = float(_num(r"then (\d\.\d+)% for year 76 onwards", t))
    assert (r1, r2, r3) == (3.5, 3.0, 2.5), (r1, r2, r3)

    p_health = locate(pages_norm, r"6\.58 The social benefits and social costs")
    h = float(_num(r"discounted at a lower rate of (\d\.\d+)%", pages_norm[p_health - 1]))
    assert h == 1.5
    assert re.search(r"The health discount.{0,120}?rate applies in every year", pages_norm[p_health - 1] + " " +
                     pages_norm[p_health]), "health rate 'every year' statement not found"

    p_t8 = locate(pages_norm, r"Table 8\. Discounting and present values")
    t8 = re.search(r"Discount factor ((?:\d\.\d{3,4}\s*){6})", pages_norm[p_t8 - 1])
    assert t8, "Table 8 discount factors not found"
    t8_factors = [float(x) for x in t8.group(1).split()]
    assert t8_factors == [1.0, 0.9662, 0.9335, 0.9019, 0.8714, 0.8420], t8_factors

    p_t7 = locate(pages_norm, r"Table 7\. Removing the effects of general price inflation")
    t7 = re.search(r"GDP deflator factor \(C\) ((?:\d\.\d{3,4}\s*){6})", pages_norm[p_t7 - 1])
    assert t7, "Table 7 deflator factors not found"
    t7_factors = [float(x) for x in t7.group(1).split()]
    assert t7_factors == [1.0, 0.9804, 0.9612, 0.9423, 0.9238, 0.9057], t7_factors

    p_th = locate(pages_norm, r"6\.11 Practitioners should use the following time horizons")
    th = pages_norm[p_th - 1]
    horizons = {
        "infrastructure": int(_num(r"(\d+) years for infrastructure", th)),
        "refurbishment": int(_num(r"(\d+) years for refurbishment", th)),
        "regulations": int(_num(r"(\d+) years for regulations", th)),
        "other": int(_num(r"(\d+) years as a standard measure", th)),
    }
    assert horizons == {"infrastructure": 60, "refurbishment": 30, "regulations": 10, "other": 10}, horizons

    p_ww = locate(pages_norm, r"7\.15 The .1\.3. in the welfare weights formula")
    eta = float(_num(r"The .(\d\.\d). in the welfare weights formula", pages_norm[p_ww - 1]))
    assert eta == 1.3

    p_eq = locate(pages_norm, r"Figure 7\. Methodology for income equivalisation")
    eq = pages_norm[p_eq - 1]
    equiv = {
        "first_adult": float(_num(r"First adult (\d\.\d\d)", eq)),
        "additional_adult": float(_num(r"Each additional adult (\d\.\d\d)", eq)),
        "child_14_and_over": float(_num(r"Child of 14 years or over (\d\.\d\d)", eq)),
        "child_under_14": float(_num(r"Child under 14 years (\d\.\d\d)", eq)),
    }
    assert equiv == {"first_adult": 0.67, "additional_adult": 0.33, "child_14_and_over": 0.33,
                     "child_under_14": 0.2}, equiv

    p_sl = locate(pages_norm, r"5\.17 A shortlist should generally include around five options")
    p_ghg = locate(pages_norm, r"8\.75 The level of detail and complexity")
    ghg = float(_num(r"emissions of below (\d\.\d) megatonnes", pages_norm[p_ghg - 1]))
    assert ghg == 0.1
    p_clim = locate(pages_norm, r"6\.14 Practitioners should take climate change impacts")
    assert re.search(r"ends before 2040 should be appraised against a climate scenario in which global "
                     r"temperatures rise by 2.C", pages_norm[p_clim - 1])
    p_gmpp = locate(pages_norm, r"10\.12 UK government departments are required to publish business cases")
    months = int({"four": 4}[_num(r"published within (\w+) months", pages_norm[p_gmpp - 1])])
    p_ob = locate(pages_norm, r"6\.81 If a public body does not have evidence on their historical optimism")
    p_gilt = locate(pages_norm, r"A\.17 In addition to standard shortlist appraisal")
    p_def = locate(pages_norm, r"6\.49 Practitioners can find forecasts of the GDP deflator")
    p_scc = locate(pages_norm, r"8\.10 The Green Book and its supplementary guidance provide numerous generic")
    p_qaly = locate(pages_norm, r"8\.57 A proposal might affect not just life expectancy")
    p_vpf = locate(pages_norm, r"8\.55 A proposal might involve a risk to human life")
    p_wellby = locate(pages_norm, r"8\.22 Wellbeing analysis can be extended")
    p_df = locate(pages_norm, r"6\.55 To adjust for discounting")
    p_y0 = locate(pages_norm, r"6\.10 The first year of an appraisal is known as year 0")
    p_bcr = locate(pages_norm, r"6\.98 Practitioners should not make judgements on value for money using BCR")

    return {
        "stpr": {
            "description": "Social Time Preference Rate (real). Year 0 is undiscounted (factor 1). The rate for "
                           "year t applies to the step from year t-1 to t, so factors compound across bands.",
            "bands": [
                {"from_year": 1, "to_year": 30, "rate": r1 / 100},
                {"from_year": 31, "to_year": 75, "rate": r2 / 100},
                {"from_year": 76, "to_year": None, "rate": r3 / 100},
            ],
            "year_zero_factor": 1.0,
            "citation": cite(p_stpr, "Chapter 6, para 6.54"),
            "year_zero_citation": cite(p_y0, "Chapter 6, para 6.10"),
            "note": "The 2026 text states 2.50% 'for year 76 onwards' with no further step-down; earlier-edition "
                    "schedules are not used.",
        },
        "health_discount_rate": {
            "rate": h / 100,
            "applies": "every year of the appraisal, to health and life effects only",
            "citation": cite(p_health, "Chapter 6, para 6.58"),
        },
        "table8_worked_example": {
            "description": "Table 8 discount factors for years 0-5 (STPR 3.5%), used as a regression check.",
            "discount_factors": t8_factors,
            "citation": cite(p_t8, "Chapter 6, Table 8"),
        },
        "table7_worked_example": {
            "description": "Table 7 GDP deflator factors for years 0-5 at 2% general inflation (illustrative only).",
            "deflator_factors": t7_factors,
            "inflation_rate": 0.02,
            "citation": cite(p_t7, "Chapter 6, Table 7"),
        },
        "time_horizons_years_after_year0": {**horizons, "citation": cite(p_th, "Chapter 6, para 6.11"),
                                            "note": "Agree a suitable period with HM Treasury if significant effects "
                                                    "extend beyond 60 years (para 6.12)."},
        "welfare_weight_elasticity": {"value": eta,
                                      "formula": "(median equivalised income of national population / median "
                                                 "equivalised income of group) ^ 1.3",
                                      "citation": cite(p_ww, "Chapter 7, paras 7.11-7.15")},
        "equivalisation_scores": {**equiv, "reference": "couple with no children = 1.00",
                                  "citation": cite(p_eq, "Chapter 7, Figure 7")},
        "shortlist_size": {"value": 5, "qualifier": "around", "citation": cite(p_sl, "Chapter 5, para 5.17")},
        "climate_scenarios": {"horizon_ends_before_2040": ["2C"], "horizon_ends_2040_or_later": ["2C", "4C"],
                              "citation": cite(p_clim, "Chapter 6, para 6.14 (also para 8.86)")},
        "ghg_negligible_threshold_mtco2e_per_year": {"value": ghg,
                                                     "citation": cite(p_ghg, "Chapter 8, para 8.75")},
        "gmpp_business_case_publication_months": {"value": months,
                                                  "citation": cite(p_gmpp, "Chapter 10, para 10.12")},
        "bcr_threshold": {"value": None,
                          "statement": "No BCR threshold may be used to judge value for money.",
                          "citation": cite(p_bcr, "Chapter 6, paras 6.98-6.99")},
        "not_in_edition": [
            {"parameter": "optimism_bias_percentages",
             "statement": "Not given in the 2026 Green Book. Use the organisation's historical forecast errors, "
                          "else generic values from the Green Book supplementary guidance on optimism bias "
                          "(or departmental guidance, e.g. DfT). Must be supplied by the user.",
             "citation": cite(p_ob, "Chapter 6, paras 6.80-6.81")},
            {"parameter": "risk_free_real_gilt_rate",
             "statement": "Not given. Rate matching the weighted average duration of the private finance "
                          "contract; consult HM Treasury. Must be supplied by the user.",
             "citation": cite(p_gilt, "Annex A, para A.17")},
            {"parameter": "gdp_deflator_series",
             "statement": "Not given. Use the latest OBR Economic and Fiscal Outlook (5 years) and Long-term "
                          "economic determinants (50 years). Must be supplied by the user.",
             "citation": cite(p_def, "Chapter 6, para 6.49")},
            {"parameter": "discount_factor_table",
             "statement": "Pre-calculated factors are in the supplementary guidance on discounting; the tools "
                          "compute factors from the stated STPR bands instead.",
             "citation": cite(p_df, "Chapter 6, para 6.55")},
            {"parameter": "social_value_of_carbon",
             "statement": "Not given. DESNZ supplementary guidance.",
             "citation": cite(p_scc, "Chapter 8, para 8.10")},
            {"parameter": "qaly_value",
             "statement": "Not given. Green Book supplementary guidance on health.",
             "citation": cite(p_qaly, "Chapter 8, para 8.57")},
            {"parameter": "value_of_prevented_fatality",
             "statement": "Not given. DfT TAG data book.",
             "citation": cite(p_vpf, "Chapter 8, para 8.55")},
            {"parameter": "wellby_value",
             "statement": "Not given. Supplementary guidance on wellbeing.",
             "citation": cite(p_wellby, "Chapter 8, para 8.22")},
        ],
    }


def build(pdf: Path = PDF) -> dict:
    pages = read_pages(pdf)
    assert len(pages) == EXPECTED_PDF_PAGES, f"expected {EXPECTED_PDF_PAGES} pages, got {len(pages)}"
    pages_norm = [norm(p) for p in pages]

    folios = {}
    for i in range(BODY_FIRST_PAGE, BODY_LAST_PAGE + 1):
        f = printed_folio(pages[i - 1])
        assert f == i - PRINTED_PAGE_OFFSET, f"PDF p.{i}: printed folio {f} != {i - PRINTED_PAGE_OFFSET}"
        folios[i] = f

    def cite(pdf_page: int, section: str) -> dict:
        return {"pdf_page": pdf_page, "printed_page": folios[pdf_page], "section": section}

    groups = []
    group_pages: dict[str, int] = {}
    items = []
    seen = set()
    for iid, group, title, anchor, text, extra in ITEMS:
        assert iid not in seen, f"duplicate id {iid}"
        seen.add(iid)
        page = locate(pages_norm, anchor)
        para = extra.get("para", "")
        section = f"para {para}" if para and not para[0].isalpha() else para
        item = {"id": iid, "title": title, "text": text, "group": group,
                "citation": cite(page, section or title)}
        item.update({k: v for k, v in extra.items()})
        items.append(item)
        group_pages.setdefault(group, page)
    for gid, gtitle in GROUPS:
        assert gid in group_pages, f"group {gid} has no items"
        groups.append({"id": gid, "title": gtitle, "citation": cite(group_pages[gid], gtitle)})

    # sanity counts
    def count(prefix: str) -> int:
        return sum(1 for i in items if i["id"].startswith(prefix))

    assert count("stage.") == EXPECTED_STAGES
    assert count("case.") == EXPECTED_CASES
    assert count("bc.") == EXPECTED_BC_STAGES
    assert sum(1 for i in items if re.match(r"csf\.\d", i["id"])) == EXPECTED_CSFS
    assert count("duty.") == EXPECTED_DUTIES
    off = next(i for i in items if i["id"] == "longlist.off-categories")
    assert len(off["categories"]) == EXPECTED_OFF_CATEGORIES
    sl = next(i for i in items if i["id"] == "shortlist.composition")
    assert len(sl["options"]) == EXPECTED_SHORTLIST
    # the five case names must all appear in para 3.12
    p312 = pages_norm[locate(pages_norm, r"3\.12 The Five Case Model is a framework") - 1]
    for name in ("strategic case", "economic case", "commercial case", "financial case", "management case"):
        assert f"The {name}" in p312, name
    # Table 4 must list all five CSF headings
    t4 = pages_norm[locate(pages_norm, r"Table 4\. Examples of critical success factors") - 1]
    for name in ("Objectives and", "Value for money", "Supplier capacity and", "Affordability", "Achievability"):
        assert name in t4, name

    return {
        "catalog_id": "green-book",
        "source_id": "treasury-green",
        "title": "The Green Book: UK government guidance on appraisal - appraisal process, Five Case Model, "
                 "key concepts and parameters",
        "edition": "2026 edition (HM Treasury, ISBN 978-1-918417-12-8, PU3608)",
        "description": "Machine-readable extract of the 2026 Green Book: the four-stage appraisal process, the "
                       "Five Case Model (what each case contains and must demonstrate), business case stages "
                       "(SOC/OBC/FBC), key appraisal concepts with paragraph references, and numeric appraisal "
                       "parameters actually stated in the 2026 text. Values deferred to supplementary guidance "
                       "are listed under parameters.not_in_edition and must be supplied by users. Crown "
                       "copyright 2026, Open Government Licence v3.0.",
        "extraction": {
            "method": "Manual reading of the full 2026 text; each item anchored by regex to a unique body page "
                      "of `pdftotext -layout` output; parameters parsed by regex and asserted "
                      "(scripts/extract/greenbook.py).",
            "date": EXTRACTION_DATE,
            "fidelity": "paraphrased",
            "notes": "Item texts paraphrase the cited paragraphs; para numbers are those printed in the 2026 "
                     "edition. Printed page = PDF page - 6 for body pages (verified from folios).",
            "pages_reviewed": "1-88 (body text PDF pp. 7-85)",
        },
        "groups": groups,
        "items": items,
        "parameters": build_parameters(pages_norm, cite),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if the committed catalog differs")
    ap.add_argument("--pdf", default=str(PDF))
    args = ap.parse_args(argv)
    data = build(Path(args.pdf))
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != text:
            print(f"{OUT.relative_to(ROOT)} is stale; run python scripts/extract/greenbook.py", file=sys.stderr)
            return 1
        print(f"{OUT.relative_to(ROOT)} is up to date ({len(data['items'])} items)")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['groups'])} groups, {len(data['items'])} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
