# Licensing and provenance policy

- **Repository licence:** not yet chosen by the owner. Until a licence is applied, the original
  material (skills, agents, scripts, templates, docs) is all rights reserved by the repository owner.
  Choose a licence before publishing or commercial distribution.
- **Bundled third-party data:**
  - `sources/extracts/owasp-asvs-5.0.0-index.json` and its copies in
    `.claude/skills/security-*/assets/data/` contain requirement IDs, levels and section titles derived
    from OWASP ASVS 5.0.0 — **CC BY-SA 4.0** (verified). Attribution and ShareAlike apply to those files
    and any adaptation of them; requirement text is not reproduced.
  - `sources/extracts/nist-ssdf-practices.json` and its skill copy: practice IDs/titles from NIST SP
    800-218 v1.1 OSCAL catalog (US Government work; verify reuse terms for your jurisdiction).
  - `sources/extracts/gov-design-rules.json`: rules paraphrased in original words from the GOV.UK Design
    System repository (code MIT, Crown Copyright; content believed OGL v3.0 — indirect verification).
  - `google-review` adaptations: Google Engineering Practices are CC BY 3.0 (verified) — attribution
    retained in the `software-code-review` skill.
- **Not reproduced:** Google SRE book (CC BY-NC-ND — no adaptation of book text), Shape Up, NASA and
  ECSS handbooks, HM Treasury Green Book, Basel principles, FCA Handbook, Damodaran materials. Skills
  link to them and paraphrase methods; see each `sources/audits/<id>.md`.
- A public URL does not make content freely redistributable or suitable for model training. Re-check
  licences before redistribution (`scripts/source_freshness.py` lists review dates).
