# SSDF v1.1 pipeline mapping: acme-checkout (GitHub Actions)

> Support != compliance: a mapped control can contribute evidence for a task, but whether the task is implemented depends on scope, configuration, enforcement and the organisation's own criteria.

- Tasks with an example-based supporting control: 8 of 42
- Tasks with interpretive support only: 0
- Tasks with no supporting control in this pipeline: 34

Unmapped steps (no rule; not credited): Checkov IaC scan (control type 'iac-scanning' has no SSDF mapping rule)

Disabled steps (ignored): Cosign image signing

## Tasks with supporting controls

| Task | Support | Controls (basis) | Source |
|---|---|---|---|
| PO.3.2 | supported | Workflows in .github/workflows [pipeline-as-code] (example: PO.3.2 Ex.3: code-based configuration for toolchains (pipelines-as-code)); Actions pinned by commit SHA [ci-hardening] (example: PO.3.2 Ex.6/Ex.7: monitor tools; verify integrity and provenance of each tool) | p.16 |
| PO.4.2 | supported | CodeQL [sast] (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria); Gitleaks [secret-scanning] (example: PO.4.2 Ex.3: automate decision-making utilizing the criteria) | p.17 |
| PS.1.1 | supported | Branch protection on main (2 reviewers, CODEOWNERS) [code-review] (example: PS.1.1 Ex.4: code owner reviews and approves all changes by others); Repository access control [branch-protection] (example: PS.1.1 Ex.1/Ex.2: code in a repository with restricted access; version control with accountability) | p.18 |
| PW.4.1 | supported | Dependabot + Snyk [sca] (example: PW.4.1 Ex.3: source composition analysis as provenance information for components); Lockfiles committed [dependency-pinning] (interpretive: pinning supports maintaining approved component versions (cf. PW.4.1 Ex.5); not named in SSDF) | p.21 |
| PW.4.4 | supported | Dependabot + Snyk [sca] (example: PW.4.4 Ex.1/Ex.2: automatic detection of known vulnerabilities in software components) | p.22 |
| PW.5.1 | supported | ESLint security rules [linting] (example: PW.5.1 Ex.7: linters and formatters to standardise code style (supports, not secure coding itself)) | p.22 |
| PW.7.2 | supported | Branch protection on main (2 reviewers, CODEOWNERS) [code-review] (example: PW.7.2 Ex.1/Ex.3: peer review of code using peer reviewing tools); CodeQL [sast] (example: PW.7.2 Ex.4/Ex.6: static analysis tool / automated tools as code is checked in); Gitleaks [secret-scanning] (interpretive: hard-coded secrets treated as an unsafe practice found by automated tools (cf. PW.7.2 Ex.6); not named in SSDF) | p.23 |
| RV.1.2 | supported | CodeQL [sast] (example: RV.1.2 Ex.1: automated code analysis on a regular or continuous basis for all supported releases) | p.25 |

## Tasks with no supporting control

Organisational tasks are normally evidenced by policy/process records rather than pipeline steps.

| Task | Practice | Organisational | Task text | Source |
|---|---|---|---|---|
| PO.1.1 | PO.1 Define Security Requirements for Software Development | yes | Identify and document all security requirements for the organization’s software development infrastructures a… | p.14 |
| PO.1.2 | PO.1 Define Security Requirements for Software Development | yes | Identify and document all security requirements for organization-developed software to meet, and maintain the… | p.14 |
| PO.1.3 | PO.1 Define Security Requirements for Software Development | yes | Communicate requirements to all third parties who will provide commercial software components to the organiza… | p.14 |
| PO.2.1 | PO.2 Implement Roles and Responsibilities | yes | Create new roles and alter responsibilities for existing roles as needed to encompass all parts of the SDLC.… | p.15 |
| PO.2.2 | PO.2 Implement Roles and Responsibilities | yes | Provide role-based training for all personnel with responsibilities that contribute to secure development. Pe… | p.15 |
| PO.2.3 | PO.2 Implement Roles and Responsibilities | yes | Obtain upper management or authorizing official commitment to secure development, and convey that commitment… | p.16 |
| PO.3.1 | PO.3 Implement Supporting Toolchains | yes | Specify which tools or tool types must or should be included in each toolchain to mitigate identified risks,… | p.16 |
| PO.3.3 | PO.3 Implement Supporting Toolchains | no | Configure tools to generate artifacts of their support of secure software development practices as defined by… | p.16 |
| PO.4.1 | PO.4 Define and Use Criteria for Software Security Checks | yes | Define criteria for software security checks and track throughout the SDLC. | p.17 |
| PO.5.1 | PO.5 Implement and Maintain Secure Environments for Software Development | no | Separate and protect each environment involved in software development. | p.17 |
| PO.5.2 | PO.5 Implement and Maintain Secure Environments for Software Development | yes | Secure and harden development endpoints (i.e., endpoints for software designers, developers, testers, builder… | p.18 |
| PS.2.1 | PS.2 Provide a Mechanism for Verifying Software Release Integrity | no | Make software integrity verification information available to software acquirers. | p.19 |
| PS.3.1 | PS.3 Archive and Protect Each Software Release | no | Securely archive the necessary files and supporting data (e.g., integrity verification information, provenanc… | p.19 |
| PS.3.2 | PS.3 Archive and Protect Each Software Release | no | Collect, safeguard, maintain, and share provenance data for all components of each software release (e.g., in… | p.19 |
| PW.1.1 | PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | no | Use forms of risk modeling – such as threat modeling, attack modeling, or attack surface mapping – to help as… | p.20 |
| PW.1.2 | PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | yes | Track and maintain the software’s security requirements, risks, and design decisions. | p.20 |
| PW.1.3 | PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | yes | Where appropriate, build in support for using standardized security features and services (e.g., enabling sof… | p.20 |
| PW.2.1 | PW.2 Review the Software Design to Verify Compliance with Security Requirements and Risk Information | no | Have 1) a qualified person (or people) who were not involved with the design and/or 2) automated processes in… | p.21 |
| PW.4.2 | PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | yes | Create and maintain well-secured software components in-house following SDLC processes to meet common interna… | p.21 |
| PW.6.1 | PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | no | Use compiler, interpreter, and build tools that offer features to improve executable security. | p.23 |
| PW.6.2 | PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | no | Determine which compiler, interpreter, and build tool features should be used and how each should be configur… | p.23 |
| PW.7.1 | PW.7 Review and/or Analyze Human-Readable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | yes | Determine whether code review (a person looks directly at the code to find issues) and/or code analysis (tool… | p.23 |
| PW.8.1 | PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | yes | Determine whether executable code testing should be performed to find vulnerabilities not identified by previ… | p.24 |
| PW.8.2 | PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | no | Scope the testing, design the tests, perform the testing, and document the results, including recording and t… | p.24 |
| PW.9.1 | PW.9 Configure Software to Have Secure Settings by Default | no | Define a secure baseline by determining how to configure each setting that has an effect on security or a sec… | p.25 |
| PW.9.2 | PW.9 Configure Software to Have Secure Settings by Default | no | Implement the default settings (or groups of default settings, if applicable), and document each setting for… | p.25 |
| RV.1.1 | RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | no | Gather information from software acquirers, users, and public sources on potential vulnerabilities in the sof… | p.25 |
| RV.1.3 | RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | yes | Have a policy that addresses vulnerability disclosure and remediation, and implement the roles, responsibilit… | p.26 |
| RV.2.1 | RV.2 Assess, Prioritize, and Remediate Vulnerabilities | no | Analyze each vulnerability to gather sufficient information about risk to plan its remediation or other risk… | p.26 |
| RV.2.2 | RV.2 Assess, Prioritize, and Remediate Vulnerabilities | yes | Plan and implement risk responses for vulnerabilities. | p.27 |
| RV.3.1 | RV.3 Analyze Vulnerabilities to Identify Their Root Causes | yes | Analyze identified vulnerabilities to determine their root causes. | p.27 |
| RV.3.2 | RV.3 Analyze Vulnerabilities to Identify Their Root Causes | yes | Analyze the root causes over time to identify patterns, such as a particular secure coding practice not being… | p.27 |
| RV.3.3 | RV.3 Analyze Vulnerabilities to Identify Their Root Causes | no | Review the software for similar vulnerabilities to eradicate a class of vulnerabilities, and proactively fix… | p.27 |
| RV.3.4 | RV.3 Analyze Vulnerabilities to Identify Their Root Causes | yes | Review the SDLC process, and update it if appropriate to prevent (or reduce the likelihood of) the root cause… | p.27 |

Self-assessment aid generated from NIST SP 800-218 (SSDF v1.1). It supports, but does not replace, qualified professional judgement, independent assessment or a formal attestation.
