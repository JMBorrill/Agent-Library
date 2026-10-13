# Pipeline control -> SSDF task mapping rules

These are the rules `python -m agentlib ssdf map-pipeline` applies (source of truth:
`PIPELINE_RULES` in `agentlib/frameworks/ssdf.py`; print them with `python -m agentlib ssdf pipeline-controls`).

Principles:

- **Support is not compliance.** A mapped control can contribute evidence towards a task. Whether a task is
  implemented depends on scope (all products? all releases?), configuration, enforcement, the organisation's own
  criteria (PO.4.1) and records. SSDF focuses on outcomes and does not prescribe tools (PDF p.8, printed p.vi;
  PDF pp.10-11).
- **Basis `example`** means an SSDF notional implementation example (or the task text itself) names this kind of
  control, cited as `<task> Ex.<n>` (example numbering as printed in Table 1). Notional examples are optional and
  not exhaustive (PDF p.13).
- **Basis `interpretive`** means a reasonable reading that the SSDF text does not name (e.g. secret scanning).
  Treat it as weaker; the tool reports such tasks as `interpretive-support`, not `supported`.
- `scheduled: true` on a scanning step (runs on a schedule against supported releases) adds RV.1.x support;
  `blocking: true` (the step fails the build) adds PO.4.2 Ex.3 support.
- Steps with `enabled: false` are ignored; unknown control types are listed as unmapped and earn nothing.
- Organisational tasks (policy, roles, training, criteria, disclosure policy, root-cause processes) are flagged
  `organisational`: a pipeline rarely evidences them; expect policy/process records instead.

## Input format

```yaml
pipeline:
  name: payments-api (GitHub Actions)
  steps:                       # or `controls:`; a step may also be a bare string such as "sbom"
    - name: CodeQL             # free text, shown in the report
      type: sast               # control type or alias from the table below (or give `tool: cosign`)
      blocking: true           # fails the build on findings -> adds PO.4.2 support
      scheduled: true          # also runs on a schedule against supported releases -> adds RV.1.x support
    - name: Cosign
      type: signing
      enabled: false           # ignored
```

Run `python -m agentlib ssdf map-pipeline pipeline.yaml [--format json]`. The report lists, for each task,
`supported` (at least one example-based control), `interpretive-support`, or `no-supporting-control`, plus
unmapped and disabled steps.

## Rules

| Control | Aliases | Tasks (basis) | If scheduled | If blocking |
|---|---|---|---|---|
| sast | static-analysis, code-scanning, codeql, semgrep, sonarqube, sonarcloud, bandit, gosec, checkmarx, fortify | PW.7.2 (example: PW.7.2 Ex.4/Ex.6: static analysis tool / automated tools as code is checked in) | RV.1.2 (example: RV.1.2 Ex.1: automated code analysis on a regular or continuous basis for all supported releases) | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) |
| secret-scanning | secrets-scanning, gitleaks, trufflehog, detect-secrets, push-protection | PW.7.2 (interpretive: hard-coded secrets treated as an unsafe practice found by automated tools (cf. PW.7.2 Ex.6); not named in SSDF) | - | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) |
| code-review | peer-review, required-reviews, pull-request-review, codeowners, merge-request-approval | PW.7.2 (example: PW.7.2 Ex.1/Ex.3: peer review of code using peer reviewing tools); PS.1.1 (example: PS.1.1 Ex.4: code owner reviews and approves all changes by others) | - | - |
| branch-protection | protected-branches, repo-access-control, least-privilege-repo, scm-access-control | PS.1.1 (example: PS.1.1 Ex.1/Ex.2: code in a repository with restricted access; version control with accountability) | - | - |
| commit-signing | signed-commits, gpg-commits, gitsign | PS.1.1 (example: PS.1.1 Ex.3: use commit signing for code repositories) | - | - |
| sca | dependency-scanning, software-composition-analysis, dependabot, renovate-vuln, snyk, osv-scanner, npm-audit, pip-audit, owasp-dependency-check, trivy-fs | PW.4.4 (example: PW.4.4 Ex.1/Ex.2: automatic detection of known vulnerabilities in software components); PW.4.1 (example: PW.4.1 Ex.3: source composition analysis as provenance information for components) | RV.1.1 (example: RV.1.1 Ex.3: automatically review software composition data to identify new vulnerabilities) | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) |
| container-scanning | image-scanning, trivy-image, grype, clair | PW.4.4 (example: PW.4.4 Ex.2: automatic detection of known vulnerabilities in software components) | RV.1.1 (example: RV.1.1 Ex.3: automatically review composition data for new vulnerabilities) | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) |
| sbom | sbom-generation, syft, cyclonedx, spdx | PS.3.2 (example: PS.3.2 task text: provenance data for all components, e.g. in an SBOM); PW.4.1 (example: PW.4.1 Ex.3: obtain provenance information (e.g., SBOM) for each component) | - | - |
| provenance | slsa, build-provenance, in-toto, attestations | PS.3.2 (example: PS.3.2 Ex.3: protect integrity of provenance data and let recipients verify it); PS.3.1 (example: PS.3.1 Ex.2: store and protect provenance data, e.g. by signing it) | - | - |
| signing | artifact-signing, code-signing, cosign, sigstore, authenticode, gpg-sign | PS.1.1 (example: PS.1.1 Ex.5: code signing to help protect integrity of executables); PS.2.1 (example: PS.2.1 Ex.2: code signing that consumers can validate (only if signatures/keys are published to acquirers)) | - | - |
| checksums | hashes, release-hashes, sha256sums | PS.2.1 (example: PS.2.1 Ex.1: post cryptographic hashes for release files on a well-secured website); PS.1.1 (example: PS.1.1 Ex.6: cryptographic hashes to protect file integrity) | - | - |
| dependency-pinning | lockfile, pinned-dependencies, version-pinning | PW.4.1 (interpretive: pinning supports maintaining approved component versions (cf. PW.4.1 Ex.5); not named in SSDF) | - | - |
| dependency-integrity | hash-pinning, dependency-signature-verification, verified-dependencies, require-hashes | PW.4.4 (example: PW.4.4 Ex.6: confirm integrity of components through digital signatures or other mechanisms) | - | - |
| private-registry | artifact-proxy, vetted-repository, internal-mirror, curated-registry | PW.4.1 (example: PW.4.1 Ex.4: repositories hosting sanctioned and vetted open-source components) | - | - |
| dast | dynamic-analysis, zap, burp, dynamic-scanning | PW.8.2 (example: PW.8.2 Ex.2: dynamic vulnerability testing in the automated test suite) | RV.1.2 (example: RV.1.2 Ex.1: automated testing on a regular or continuous basis) | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) |
| fuzzing | fuzz-testing, oss-fuzz, libfuzzer, afl | PW.8.2 (example: PW.8.2 Ex.5: fuzz testing tools) | RV.1.2 (example: RV.1.2 Ex.1: automated testing on a regular or continuous basis) | - |
| penetration-test | pentest, pen-test | PW.8.2 (example: PW.8.2 Ex.6: penetration testing for high-risk scenarios) | - | - |
| security-tests | security-unit-tests, security-regression-tests, security-functional-tests | PW.8.2 (example: PW.8.2 Ex.1/Ex.3: functional testing of security features; tests for previously reported vulnerabilities) | - | - |
| compiler-hardening | hardening-flags, warnings-as-errors, clean-build, pie-aslr | PW.6.2 (example: PW.6.2 Ex.1/Ex.2/Ex.4: compiler warnings, clean build, randomisation features) | - | - |
| toolchain-updates | up-to-date-build-tools, toolchain-patching | PW.6.1 (example: PW.6.1 Ex.1: up-to-date versions of compiler, interpreter and build tools) | - | - |
| isolated-build | hermetic-build, ephemeral-runners, dedicated-build-environment | PW.6.2 (example: PW.6.2 Ex.3: all builds in a dedicated, highly controlled build environment) | - | - |
| reproducible-builds | reproducible-build, deterministic-builds | PO.3.2 (example: PO.3.2 Ex.4: technologies and processes for reproducible builds) | - | - |
| pipeline-as-code | pipelines-as-code, ci-as-code | PO.3.2 (example: PO.3.2 Ex.3: code-based configuration for toolchains (pipelines-as-code)) | - | - |
| ci-hardening | pinned-actions, least-privilege-ci-tokens, tool-integrity-verification, runner-hardening | PO.3.2 (example: PO.3.2 Ex.6/Ex.7: monitor tools; verify integrity and provenance of each tool) | - | - |
| security-gate | policy-as-code, quality-gate, release-gate, opa, conftest | PO.4.2 (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria); PO.4.1 (interpretive: a gate implies criteria exist (PO.4.1 Ex.3); the criteria themselves need separate evidence) | - | - |
| artifact-retention | audit-trail, scan-results-retention, evidence-store, ci-logs-retention | PO.3.3 (example: PO.3.3 Ex.1/Ex.3: audit trail from tooling; retention policies for artifact data); PO.4.2 (example: PO.4.2 Ex.1/Ex.4: toolchain gathers information; protected from alteration (if immutable)) | - | - |
| release-archive | immutable-artifact-repository, release-retention | PS.3.1 (example: PS.3.1 Ex.1: store release files in repositories with read-only access) | - | - |
| findings-tracking | issue-tracking, vulnerability-tracking, defectdojo | RV.2.1 (example: RV.2.1 Ex.1: use issue tracking software to record each vulnerability); PW.7.2 (interpretive: PW.7.2 task text requires recording and triaging discovered issues) | - | - |
| vulnerability-monitoring | dependency-track, continuous-monitoring, vuln-feed-monitoring | RV.1.1 (example: RV.1.1 Ex.1/Ex.3: monitor vulnerability sources; review composition data for new vulnerabilities) | - | - |
| vulnerability-disclosure | vdp, security-txt, bug-bounty, psirt | RV.1.3 (example: RV.1.3 Ex.1/Ex.2: vulnerability disclosure program; PSIRT); RV.1.1 (interpretive: a reporting channel helps gather reports from acquirers and users) | - | - |
| security-advisories | advisories, csaf, vex | RV.2.2 (example: RV.2.2 Ex.3: develop and release security advisories) | - | - |
| automated-updates | trusted-update-delivery, signed-updates | RV.2.2 (example: RV.2.2 Ex.4: deliver remediations via an automated and trusted delivery mechanism) | - | - |
| linting | linter, formatter, eslint, pylint, ruff | PW.5.1 (example: PW.5.1 Ex.7: linters and formatters to standardise code style (supports, not secure coding itself)) | - | - |
| secure-coding-ide | ide-security-plugin, pre-commit-security-hooks | PW.5.1 (example: PW.5.1 Ex.5: development environments with automated secure-coding features) | - | - |
| secure-config-tests | default-settings-tests, secure-defaults-check | PW.9.1 (example: PW.9.1 Ex.1: test that settings, including defaults, work as expected); PW.9.2 (example: PW.9.2 Ex.1: verify the approved configuration is in place) | - | - |
| threat-modeling | threat-model, risk-modeling | PW.1.1 (example: PW.1.1 task text: threat modeling, attack modeling, attack surface mapping) | - | - |
| design-review | security-design-review, architecture-review | PW.2.1 (example: PW.2.1 Ex.1-3: review design against requirements and risk models) | - | - |
| mfa | sso-mfa, multi-factor-authentication, conditional-access | PO.5.1 (example: PO.5.1 Ex.1: multi-factor, risk-based authentication for each environment); PO.5.2 (example: PO.5.2 Ex.5: MFA for development endpoints and resources (only if enforced there)) | - | - |
| environment-separation | network-segmentation, separate-environments | PO.5.1 (example: PO.5.1 Ex.2: network segmentation and access controls separating environments) | - | - |
| security-training | secure-coding-training, role-based-training | PO.2.2 (example: PO.2.2 task text: role-based training) | - | - |
