# SSDF v1.1 practices and tasks at a glance

Generated from `catalog/nist-ssdf.json` (NIST SP 800-218, Table 1, PDF pp.14-28; printed page = PDF page - 9).
Task wording below is abbreviated; run `python -m agentlib ssdf show <id>` for the verbatim task, its notional
implementation examples and informative references. 4 groups, 19 practices, 42 tasks.

Group definitions are in Section 2 (PDF p.13, printed p.4). The table lists practices and tasks in no order of
importance or sequence (PDF p.13).

## PO - Prepare the Organization

Organizations should ensure that their people, processes, and technology are prepared to perform secure software development at the organization level. Many organizations will find some PO practices to also be applicable to subsets of their software development, like individual development groups or projects. (PDF p.13)

| Practice | Task | Task (abbreviated) | PDF page | EO 14028 4e (App. A) |
|---|---|---|---|---|
| PO.1 Define Security Requirements for Software Development | PO.1.1 | Identify and document all security requirements for the organization’s software development infrastructures and process… | 14 | - |
| PO.1 Define Security Requirements for Software Development | PO.1.2 | Identify and document all security requirements for organization-developed software to meet, and maintain the requireme… | 14 | - |
| PO.1 Define Security Requirements for Software Development | PO.1.3 | Communicate requirements to all third parties who will provide commercial software components to the organization for r… | 14 | 4e(vi) |
| PO.2 Implement Roles and Responsibilities | PO.2.1 | Create new roles and alter responsibilities for existing roles as needed to encompass all parts of the SDLC. Periodical… | 15 | - |
| PO.2 Implement Roles and Responsibilities | PO.2.2 | Provide role-based training for all personnel with responsibilities that contribute to secure development. Periodically… | 15 | - |
| PO.2 Implement Roles and Responsibilities | PO.2.3 | Obtain upper management or authorizing official commitment to secure development, and convey that commitment to all wit… | 16 | - |
| PO.3 Implement Supporting Toolchains | PO.3.1 | Specify which tools or tool types must or should be included in each toolchain to mitigate identified risks, as well as… | 16 | 4e(iii) |
| PO.3 Implement Supporting Toolchains | PO.3.2 | Follow recommended security practices to deploy, operate, and maintain tools and toolchains. | 16 | 4e(i)(F), 4e(ii), 4e(iii), 4e(v), 4e(vi) |
| PO.3 Implement Supporting Toolchains | PO.3.3 | Configure tools to generate artifacts of their support of secure software development practices as defined by the organ… | 16 | 4e(i)(F), 4e(ii), 4e(v) |
| PO.4 Define and Use Criteria for Software Security Checks | PO.4.1 | Define criteria for software security checks and track throughout the SDLC. | 17 | 4e(iv), 4e(v) |
| PO.4 Define and Use Criteria for Software Security Checks | PO.4.2 | Implement processes, mechanisms, etc. to gather and safeguard the necessary information in support of the criteria. | 17 | 4e(iv), 4e(v) |
| PO.5 Implement and Maintain Secure Environments for Software Development | PO.5.1 | Separate and protect each environment involved in software development. | 17 | 4e(i)(A), 4e(i)(B), 4e(i)(C), 4e(i)(D), 4e(i)(F), 4e(ii), 4e(iii), 4e(v), 4e(vi) |
| PO.5 Implement and Maintain Secure Environments for Software Development | PO.5.2 | Secure and harden development endpoints (i.e., endpoints for software designers, developers, testers, builders, etc.) t… | 18 | 4e(i)(C), 4e(i)(E), 4e(i)(F), 4e(ii), 4e(iii), 4e(v), 4e(vi) |

## PS - Protect the Software

Organizations should protect all components of their software from tampering and unauthorized access. (PDF p.13)

| Practice | Task | Task (abbreviated) | PDF page | EO 14028 4e (App. A) |
|---|---|---|---|---|
| PS.1 Protect All Forms of Code from Unauthorized Access and Tampering | PS.1.1 | Store all forms of code – including source code, executable code, and configuration-as-code – based on the principle of… | 18 | 4e(iii), 4e(iv) |
| PS.2 Provide a Mechanism for Verifying Software Release Integrity | PS.2.1 | Make software integrity verification information available to software acquirers. | 19 | 4e(iii), 4e(x) |
| PS.3 Archive and Protect Each Software Release | PS.3.1 | Securely archive the necessary files and supporting data (e.g., integrity verification information, provenance data) to… | 19 | 4e(iii), 4e(vi), 4e(x) |
| PS.3 Archive and Protect Each Software Release | PS.3.2 | Collect, safeguard, maintain, and share provenance data for all components of each software release (e.g., in a softwar… | 19 | 4e(vi), 4e(vii), 4e(x) |

## PW - Produce Well-Secured Software

Organizations should produce well-secured software with minimal security vulnerabilities in its releases. (PDF p.13)

| Practice | Task | Task (abbreviated) | PDF page | EO 14028 4e (App. A) |
|---|---|---|---|---|
| PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | PW.1.1 | Use forms of risk modeling – such as threat modeling, attack modeling, or attack surface mapping – to help assess the s… | 20 | - |
| PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | PW.1.2 | Track and maintain the software’s security requirements, risks, and design decisions. | 20 | 4e(v) |
| PW.1 Design Software to Meet Security Requirements and Mitigate Security Risks | PW.1.3 | Where appropriate, build in support for using standardized security features and services (e.g., enabling software to i… | 20 | - |
| PW.2 Review the Software Design to Verify Compliance with Security Requirements and Risk Information | PW.2.1 | Have 1) a qualified person (or people) who were not involved with the design and/or 2) automated processes instantiated… | 21 | 4e(iv), 4e(v) |
| PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | PW.4.1 | Acquire and maintain well-secured software components (e.g., software libraries, modules, middleware, frameworks) from… | 21 | 4e(iii), 4e(vi), 4e(x) |
| PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | PW.4.2 | Create and maintain well-secured software components in-house following SDLC processes to meet common internal software… | 21 | - |
| PW.4 Reuse Existing, Well-Secured Software When Feasible Instead of Duplicating Functionality | PW.4.4 | Verify that acquired commercial, open-source, and all other third-party software components comply with the requirement… | 22 | 4e(iii), 4e(iv), 4e(vi), 4e(x) |
| PW.5 Create Source Code by Adhering to Secure Coding Practices | PW.5.1 | Follow all secure coding practices that are appropriate to the development languages and environment to meet the organi… | 22 | 4e(iv) |
| PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | PW.6.1 | Use compiler, interpreter, and build tools that offer features to improve executable security. | 23 | 4e(iv) |
| PW.6 Configure the Compilation, Interpreter, and Build Processes to Improve Executable Security | PW.6.2 | Determine which compiler, interpreter, and build tool features should be used and how each should be configured, then i… | 23 | 4e(iv) |
| PW.7 Review and/or Analyze Human-Readable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | PW.7.1 | Determine whether code review (a person looks directly at the code to find issues) and/or code analysis (tools are used… | 23 | 4e(iv) |
| PW.7 Review and/or Analyze Human-Readable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | PW.7.2 | Perform the code review and/or code analysis based on the organization’s secure coding standards, and record and triage… | 23 | 4e(iv), 4e(v) |
| PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | PW.8.1 | Determine whether executable code testing should be performed to find vulnerabilities not identified by previous review… | 24 | - |
| PW.8 Test Executable Code to Identify Vulnerabilities and Verify Compliance with Security Requirements | PW.8.2 | Scope the testing, design the tests, perform the testing, and document the results, including recording and triaging al… | 24 | 4e(iv), 4e(v) |
| PW.9 Configure Software to Have Secure Settings by Default | PW.9.1 | Define a secure baseline by determining how to configure each setting that has an effect on security or a security-rela… | 25 | 4e(iv) |
| PW.9 Configure Software to Have Secure Settings by Default | PW.9.2 | Implement the default settings (or groups of default settings, if applicable), and document each setting for software a… | 25 | 4e(iv) |

## RV - Respond to Vulnerabilities

Organizations should identify residual vulnerabilities in their software releases and respond appropriately to address those vulnerabilities and prevent similar ones from occurring in the future. (PDF p.13)

| Practice | Task | Task (abbreviated) | PDF page | EO 14028 4e (App. A) |
|---|---|---|---|---|
| RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | RV.1.1 | Gather information from software acquirers, users, and public sources on potential vulnerabilities in the software and… | 25 | 4e(iv), 4e(vi), 4e(viii) |
| RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | RV.1.2 | Review, analyze, and/or test the software’s code to identify or confirm the presence of previously undetected vulnerabi… | 25 | 4e(iv), 4e(vi), 4e(viii) |
| RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis | RV.1.3 | Have a policy that addresses vulnerability disclosure and remediation, and implement the roles, responsibilities, and p… | 26 | 4e(viii) |
| RV.2 Assess, Prioritize, and Remediate Vulnerabilities | RV.2.1 | Analyze each vulnerability to gather sufficient information about risk to plan its remediation or other risk response. | 26 | 4e(iv), 4e(viii) |
| RV.2 Assess, Prioritize, and Remediate Vulnerabilities | RV.2.2 | Plan and implement risk responses for vulnerabilities. | 27 | 4e(iv), 4e(v), 4e(viii) |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | RV.3.1 | Analyze identified vulnerabilities to determine their root causes. | 27 | - |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | RV.3.2 | Analyze the root causes over time to identify patterns, such as a particular secure coding practice not being followed… | 27 | - |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | RV.3.3 | Review the software for similar vulnerabilities to eradicate a class of vulnerabilities, and proactively fix them rathe… | 27 | 4e(iv), 4e(viii) |
| RV.3 Analyze Vulnerabilities to Identify Their Root Causes | RV.3.4 | Review the SDLC process, and update it if appropriate to prevent (or reduce the likelihood of) the root cause recurring… | 27 | - |

## Retired identifiers (do not assess)

SSDF 1.1 keeps these ids in Table 1 only as pointers (Change Log, PDF p.36):

- PW.3: "Moved to PW.4" (PDF p.21)
- PW.3.1: "Moved to PO.1.3" (PDF p.21) <!-- evidence:ignore -->
- PW.3.2: "Moved to PW.4.4" (PDF p.21) <!-- evidence:ignore -->
- PW.4.3: "Moved to PW.1.3" (PDF p.21) <!-- evidence:ignore -->
- PW.4.5: "Moved to PW.4.1 and PW.4.4" (PDF p.22) <!-- evidence:ignore -->
- PW.5.2: "Moved to PW.5.1 as example" (PDF p.22) <!-- evidence:ignore -->

Use the current id in any assessment; `ssdf check-assessment` rejects retired ids.
