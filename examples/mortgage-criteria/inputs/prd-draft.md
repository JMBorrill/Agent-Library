# Product brief: second-charge criteria search with cited explanations (synthetic)

Owner: product lead (synthetic) · Status: first draft (superseded by prd.md after prd_check findings), not signed by the product owner · Release: pilot slice for 3 fictitious lenders

All lenders, brokers and cases in this brief are fictitious. The platform gives indicative eligibility
or "refer" only; the broker advises and the lender decides. Nothing in this brief is a credit decision.

## Outcomes and metrics
- Median broker time from completed fact-find to a lender shortlist for a second-charge case falls
  from 38 minutes (synthetic observation baseline, MCP-EV-002) to 15 minutes or less within 8 weeks of
  pilot start, measured in a follow-up observation of at least 6 brokers.
- Share of pilot shortlists where the broker opened at least one cited criteria source rises from
  0% (no citations exist today) to at least 80%, measured from the audit log.
- Guardrail: wrong-lender submissions (case declined by the lender on a criterion the platform showed
  as met) do not exceed 2% of pilot submissions; any breach pauses the pilot for review.
- Guardrail: 0 outputs that state or imply a lending decision, measured on the criteria Q&A eval set
  and a weekly 50-answer sample.

## Users
- UK mortgage brokers (advisers and case administrators) handling first and second charge cases for
  consumer clients; many work on laptops between client calls; some use screen readers or magnifiers.
- Consumer borrowers (secondary): they never use the platform directly but are the subjects of the
  case data and of the broker's recommendation; some are in vulnerable circumstances.
- Lender criteria staff (secondary): they supply dated criteria documents and correct rules.

## Job stories
- MCP-STY-001: When I have a second-charge fact-find, I want to see which lenders' criteria the case meets, fails or cannot be judged on, so I can shortlist lenders in minutes rather than opening each lender's documents.
- MCP-STY-002: When I review a lender result, I want to see each rule with its source document and verification date, so I can check the criteria myself before I advise.
- MCP-STY-003: When I ask a criteria question in plain English, I want an answer that cites the lender documents it used, so I can verify the answer before relying on it.
- MCP-STY-004: When I prepare affordability figures, I want CLTV and stressed repayments shown with the lender policy behind the stress rate, so I can explain the numbers to my client.
- MCP-STY-005: When a result looks wrong to me, I want to record my disagreement and reason, so I can keep my own judgement on record and get the criteria corrected.

## Non-goals
- No credit decisions, offers, decision-in-principle or "approval" wording of any kind.
- No consumer-facing journey; the platform is used by brokers only in this release.
- No automated submission of applications to lenders.
- No ranking of lenders by commission or price.

## Assumptions
- Brokers check cited sources rather than trusting summaries (MCP-AS-003, supported by MCP-EV-004).
- Brokers want the lender choice to stay with them (MCP-AS-004, supported by MCP-EV-005).
- AI explanations cut shortlist time without raising wrong-lender submissions (MCP-AS-006) is
  untested; the alpha experiment is planned and the pilot guardrail above measures it.
- Lender criteria can be re-verified within 90 days (MCP-AS-007) is untested; the stale-criteria
  rule makes any older rule return "refer".

## Risks
- Stale or overlapping lender rules give a wrong indicative result -> versioned rules with
  effective dates, a 90-day re-verification limit and validation before load.
- AI answer invents criteria -> answers only from retrieved criteria documents with required
  citations; grounding gate in the eval harness.
- Brokers over-rely on indicative results -> every result labelled indicative, reasons shown, the
  broker records the final choice; override logging.
- Malicious uploaded documents try to steer the assistant -> injection screening plus a tool policy
  in which retrieved content can never trigger side-effecting tools.
- Perimeter risk (information service versus arranging or advising) -> legal counsel review before
  pilot; see the regulatory triage output.

## Accessibility
Target WCAG 2.2 AA. Search, results and rule detail must work with keyboard only and with a screen
reader; result status (eligible indicative, ineligible indicative, refer) is conveyed in text and
not by colour alone; the results table supports 200% zoom without horizontal scrolling on a laptop;
error messages name the missing case fact. Run `ux-accessibility-review` on the prototype before pilot.

## Privacy and security
Case facts are personal data about consumer borrowers. Collect only the criteria facts needed for
matching (no names, addresses or identifiers in the criteria search); redact identifiers before any
text is sent to the AI provider; keep case data per broker firm (tenant) with tenant derived from the
session, never from the request; retain case searches for 90 days unless the firm's own record-keeping
policy requires longer, as decided by the Data Protection Officer; log overrides and access for audit.
A DPIA is required before the pilot. Abuse cases: cross-tenant data access, prompt injection via
uploaded documents, export of case data to non-allowlisted domains.

## Release slices
- Slice 1: rules engine with cited per-rule reasons for 3 fictitious lenders (no AI text).
- Slice 2: affordability arithmetic with lender-policy stress labels.
- Slice 3: cited AI criteria Q&A behind a feature flag, with override logging.
