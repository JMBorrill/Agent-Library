# Prompt-injection review method notes (original wording)

## Threat model in one paragraph
An LLM cannot reliably tell instructions from data: any text in its context window can steer it.
*Direct* injection comes from the user; *indirect* injection arrives inside content the system
fetches or receives — an inbound CRM email, an uploaded payslip, a web page, a tool's output. The
damage happens when the model has tools: it can send data out (email, URL fetch, markdown image
rendering) or change records. The durable mitigation is architectural — constrain what
untrusted-provenance instructions can cause — with detection as an early-warning layer.

## Scanner rules and why
| Rule | Signal | Typical false positive |
|---|---|---|
| instruction-override | "ignore/disregard ... previous ... instructions", "New instructions:" | security training, articles about attacks |
| role-reassignment | "you are now", "act as a ...", DAN/developer mode, fake `SYSTEM:` turns | scripts, role-play fiction |
| prompt-exfiltration | requests to reveal the system prompt, keys, credentials | IT help-desk text about API keys |
| hidden-text | zero-width/bidi characters, Unicode tag characters (decoded in evidence), HTML comments or CSS-hidden spans with instruction words | right-to-left language text, email templates |
| exfiltration-url | markdown image/link with query parameters, template placeholders in URLs, "append ... to the URL" | tracking pixels in marketing email |
| tool-coercion | "use/call/run ... tool/command", "mark ... as approved without ...", tool-call JSON | developer documentation |
| data-egress-request (medium) | "send/forward ... to <email>" | ordinary business email (expected `review`) |
| concealment (medium) | "do not tell the user/underwriter/anyone" | rare |
| encoded-payload | base64 run ≥ 40 chars decoding to printable text; high if decoded text itself matches | signed tokens, data URIs (binary data is skipped) |
| addressed-to-ai (low) | "Note to AI assistant:", "AI model:" | AI product documentation |
| authority-bypass (medium) | a third party's approval claimed ("the owner has already okayed this") **and** a verification bypass ("no need to check", "can skip") in the same document | genuine delegated instructions from a colleague |
| bulk-personal-data-request (medium) | send/text/email/export ... every/each/all clients' names, addresses, phone numbers | an owner legitimately asking for their own route sheet (expected `review`) |

Text is normalised (invisible characters removed, NFKC) before matching, so zero-width splitting
does not evade the override rule. Scores: high = 4, medium = 2, low = 1; any high or score ≥ 4 →
`flag`; score ≥ 2 → `review`.

## Known false negatives (by design, documented in the corpus)
Paraphrased social engineering without trigger phrases (the two social-engineering rules catch
only claimed-authority-plus-bypass and bulk personal-data requests, and were written with corpus
samples m13/m15 in view); non-English instructions; instructions
inside images or PDFs that were not text-extracted; multi-turn attacks split across documents;
novel encodings (hex, rot13, homoglyph-heavy text beyond NFKC). Treat the detection rate as
specific to this corpus.

## Tool policy design principles
1. Allowlist tools; anything else is denied.
2. Classify each tool as side-effecting or not. URL fetches count as side-effecting.
3. Provenance is attached by the orchestrator, not by the model. Retrieved content and tool
   output may *inform* answers but may not *cause* side effects.
4. Egress: forbidden domains always deny; personal data only to named domains; other
   destinations need approval.
5. Human approval shows the complete arguments and the provenance chain, not a model summary.
6. Log every decision with its reasons for audit.
7. Taint, do not trust labels: a call proposed in a turn whose context held untrusted content
   inherits that provenance (`turn_context_provenance`), whatever the session label says. A user
   clicking "draft reply" on a malicious thread must not turn the thread's text into user intent.
8. Bind recipients to the thread's recipients of record (from the customer record, never the
   inbound sender, which an attacker controls); default-deny unlisted destinations for
   side-effecting tools; derive data classification from the tool rather than the caller.

## Corpus design
Label every sample; include benign samples from the same channels as the attacks (otherwise the
false-positive rate is meaningless); keep known misses in the corpus with a flag so improvements
and regressions are visible. All samples here are synthetic; domains use `.example` or are
generic public services named only on a deny list.

## Relation to the AI RMF (unverified)
Secondary sources list *secure and resilient* among the seven trustworthiness characteristics;
injection resistance and tool-use control are treated here as evidence for that characteristic
and for MANAGE-function risk treatment *(function/category mapping not verified against the
primary)*.
