# Requirements Mapping Matrix

Generated with `python -m agentlib nasa-swe matrix --class D --safety-critical --format md`; the 64 rows
are every requirement Appendix C marks X for Class D [nasa-software-requirements Appendix C, p. 56].
Because the ground software is safety-critical, the conditional rows SWE-023, SWE-134, SWE-219 and
SWE-220 apply [nasa-software-requirements SWE-134, p. 26] [nasa-software-requirements SWE-219, p. 26]
[nasa-software-requirements SWE-220, p. 27]. Requirements blank for Class D (for example SWE-051 and
SWE-141) are not listed. Status, rationale, approval and evidence are left for the project to fill, then
`python -m agentlib nasa-swe check-matrix rmm.md --class D` must report 0 errors before submission to the
Center Technical Authorities.

Software class: D  
Safety-critical software: yes  
Software IV&V: no / not yet determined  
Applicable ('X') requirements: 64 [nasa-software-requirements Appendix C, p. 56]

Legend: X = Indicates an invoked requirement by this NPR consistent with Software Classification (ref. SWE-139). May be tailored with TA approval (ref. Chapter 2.2). Blank = Optional/Not invoked by this NPR.  
Allowed status values: Compliant, Partially Compliant, Non-Compliant, Planned, Tailored, Not Applicable.

| SWE | Section | Requirement | Authority | Condition | Status | Tailoring / waiver rationale | Approval | Evidence |
|---|---|---|---|---|---|---|---|---|
| SWE-033 | 3.1.2 | The project manager shall assess options for software acquisition versus development. | Center |  |  |  |  |  |
| SWE-013 | 3.1.3 | The project manager shall develop, maintain, and execute software plans, including security plans, that cover the entire software life cycle and, as a minimum, address the requirements of this directive with approved tailoring. | Center |  |  |  |  |  |
| SWE-024 | 3.1.4 | The project manager shall track the actual results and performance of software activities against the software plans. (see list items in NPR) | Center |  |  |  |  |  |
| SWE-034 | 3.1.5 | The project manager shall define and document the acceptance criteria for the software. | Center |  |  |  |  |  |
| SWE-036 | 3.1.6 | The project manager shall establish and maintain the software processes, software documentation plans, list of developed electronic products, deliverables, and list of tasks for the software development that are required for the project's software developers, as well as the action required (e.g., approval, review) of the Government upon receipt of each of the deliverables. | Center |  |  |  |  |  |
| SWE-037 | 3.1.7 | The project manager shall define and document the milestones at which the software developer(s) progress will be reviewed and audited. | Center |  |  |  |  |  |
| SWE-039 | 3.1.8 | The project manager shall require the software developer(s) to periodically report status and provide insight into software development and test activities; at a minimum, the software developer(s) will be required to allow the project manager and software assurance personnel to: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-040 | 3.1.9 | The project manager shall require the software developer(s) to provide NASA with software products, traceability, software change tracking information, and nonconformances in electronic format, including software development and management metrics. | Center |  |  |  |  |  |
| SWE-042 | 3.1.10 | The project manager shall require the software developer(s) to provide NASA with electronic access to the source code developed for the project in a modifiable format. | Center |  |  |  |  |  |
| SWE-139 | 3.1.11 | The project manager shall comply with the requirements in this NPR that are marked with an "X" in Appendix C consistent with their software classification. | Center |  |  |  |  |  |
| SWE-121 | 3.1.12 | Where approved, the project manager shall document and reflect the tailored requirement in the plans or procedures controlling the development, acquisition, and deployment of the affected software. | Center |  |  |  |  |  |
| SWE-125 | 3.1.13 | Each project manager with software components shall maintain a requirements mapping matrix or multiple requirements mapping matrices against requirements in this NPR, including those delegated to other parties or accomplished by contract vehicles or Space Act Agreements. | Center |  |  |  |  |  |
| SWE-027 | 3.1.14 | The project manager shall satisfy the following conditions when a COTS, GOTS, MOTS, OSS, or reused software component is acquired or used: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-015 | 3.2.1 | To better estimate the cost of development, the project manager shall establish, document, and maintain: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-151 | 3.2.2 | The project manager's software cost estimate(s) shall satisfy the following conditions: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-174 | 3.2.3 | The project manager shall submit software planning parameters, including size and effort estimates, milestones, and characteristics, to the Center measurement repository at the conclusion of major milestones. | Center |  |  |  |  |  |
| SWE-016 | 3.3.1 | The project manager shall document and maintain a software schedule that satisfies the following conditions: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-046 | 3.3.3 | The project manager shall require the software developer(s) to provide a software schedule for the project's review, and schedule updates as requested. | Center |  |  |  |  |  |
| SWE-020 | 3.5.1 | The project manager shall classify each system and subsystem containing software in accordance with the highest applicable software classification definitions for Classes A, B, C, D, E, and F software in Appendix D. | Center |  |  |  |  |  |
| SWE-176 | 3.5.2 | The project manager shall maintain records of each software classification determination, each software Requirements Mapping Matrix, and the results of each software independent classification assessments for the life of the project. | Center |  |  |  |  |  |
| SWE-022 | 3.6.1 | The project manager shall plan and implement software assurance, software safety, and IV&V (if required) per NASA-STD-8739.8, Software Assurance and Software Safety Standard. | Center |  |  |  |  |  |
| SWE-205 | 3.7.1 | The project manager, in conjunction with the SMA organization, shall determine if each software component is considered to be safety-critical per the criteria defined in NASA-STD-8739.8. | Center |  |  |  |  |  |
| SWE-023 | 3.7.2 | If a project has safety-critical software, the project manager shall implement the safety-critical software requirements contained in NASA-STD-8739.8. | Center | applies: safety-critical software declared |  |  |  |  |
| SWE-134 | 3.7.3 | If a project has safety-critical software or mission-critical software, the project manager shall implement the following items in the software: (see list items in NPR) | Center | applies: safety-critical software declared |  |  |  |  |
| SWE-219 | 3.7.4 | If a project has safety-critical software, the project manager shall ensure that there is 100 percent code test coverage using the Modified Condition/Decision Coverage (MC/DC) criterion for all identified safety-critical software components. | Center | applies: safety-critical software declared |  |  |  |  |
| SWE-220 | 3.7.5 | If a project has safety-critical software, the project manager shall ensure all identified safety-critical software components have a cyclomatic complexity value of 15 or lower. Any exceedance shall be reviewed and waived with rationale by the project manager or technical approval authority. | Center | applies: safety-critical software declared |  |  |  |  |
| SWE-206 | 3.8.2 | The project manager shall require the software developers and custom software suppliers to provide NASA with electronic access to the models, simulations, and associated data used as inputs for auto-generation of software. | Center |  |  |  |  |  |
| SWE-147 | 3.10.1 | The project manager shall specify reusability requirements that apply to its software development activities to enable future reuse of the software, including the models, simulations, and associated data used as inputs for auto-generation of software, for U.S. Government purposes. | Center |  |  |  |  |  |
| SWE-148 | 3.10.2 | The project manager shall evaluate software for potential reuse by other projects across NASA and contribute reuse candidates to the appropriate NASA internal sharing and reuse software system. However, if the project manager is not a civil servant, then a civil servant will pre-approve all such software contributions; all software contributions should include, at a minimum, the following information: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-156 | 3.11.2 | The project manager shall perform a software cybersecurity assessment on the software components per the Agency security policies and the project requirements, including risks posed by the use of COTS, GOTS, MOTS, OSS, or reused software components. | Center and Center CIO |  |  |  |  |  |
| SWE-154 | 3.11.3 | The project manager shall identify cybersecurity risks, along with their mitigations, in flight and ground software systems and plan the mitigations for these systems. | Center and Center CIO |  |  |  |  |  |
| SWE-157 | 3.11.4 | The project manager shall implement protections for software systems with communications capabilities against unauthorized access per the requirements contained in the NASA-STD-1006, Space System Protection Standard. | Center and Center CIO |  |  |  |  |  |
| SWE-159 | 3.11.5 | The project manager shall test the software and record test results for the required software cybersecurity mitigation implementations identified from the security vulnerabilities and security weaknesses analysis. | Center and Center CIO |  |  |  |  |  |
| SWE-207 | 3.11.6 | The project manager shall identify, record, and implement secure coding practices. | Center and Center CIO |  |  |  |  |  |
| SWE-185 | 3.11.7 | The project manager shall verify that the software code meets the project's secure coding standard by using the results from static analysis tool(s). | Center and Center CIO |  |  |  |  |  |
| SWE-052 | 3.12.1 | The project manager shall perform, record, and maintain bi-directional traceability between the following software elements: | Center |  |  |  |  |  |
| SWE-050 | 4.1.2 | The project manager shall establish, capture, record, approve, and maintain software requirements, including requirements for COTS, GOTS, MOTS, OSS, or reused software components, as part of the technical specification. | Center |  |  |  |  |  |
| SWE-053 | 4.1.5 | The project manager shall track and manage changes to the software requirements. | Center |  |  |  |  |  |
| SWE-054 | 4.1.6 | The project manager shall identify, initiate corrective actions, and track until closure inconsistencies among requirements, project plans, and software products. | Center |  |  |  |  |  |
| SWE-055 | 4.1.7 | The project manager shall perform requirements validation to ensure that the software will perform as intended in the customer environment. | Center |  |  |  |  |  |
| SWE-061 | 4.4.3 | The project manager shall select, define, and adhere to software coding methods, standards, and criteria. | Center |  |  |  |  |  |
| SWE-135 | 4.4.4 | The project manager shall use static analysis tools to analyze the code during the development and testing phases to, at a minimum, detect defects, software security, code coverage, and software complexity. | Center |  |  |  |  |  |
| SWE-062 | 4.4.5 | The project manager shall unit test the software code. | Center |  |  |  |  |  |
| SWE-186 | 4.4.6 | The project manager shall assure that the unit test results are repeatable. | Center |  |  |  |  |  |
| SWE-063 | 4.4.7 | The project manager shall provide a software version description for each software release. | Center |  |  |  |  |  |
| SWE-065 | 4.5.2 | The project manager shall establish and maintain: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-066 | 4.5.3 | The project manager shall test the software against its requirements. | Center |  |  |  |  |  |
| SWE-068 | 4.5.5 | The project manager shall evaluate test results and record the evaluation. | Center |  |  |  |  |  |
| SWE-071 | 4.5.7 | The project manager shall update the software test and verification plan(s) and procedure(s) to be consistent with software requirements. | Center |  |  |  |  |  |
| SWE-189 | 4.5.9 | The project manager shall ensure that the code coverage measurements for the software are selected, implemented, tracked, recorded, and reported. | Center |  |  |  |  |  |
| SWE-192 | 4.5.12 | The project manager shall verify through test the software requirements that trace to a hazardous event, cause, or mitigation technique. | Center |  |  |  |  |  |
| SWE-075 | 4.6.2 | The project manager shall plan and implement software operations, maintenance, and retirement activities. | Center |  |  |  |  |  |
| SWE-077 | 4.6.3 | The project manager shall complete and deliver the software product to the customer with appropriate records, including as-built records, to support the operations and maintenance phase of the software's life cycle. | Center |  |  |  |  |  |
| SWE-194 | 4.6.4 | The project manager shall complete, prior to delivery, verification that all software requirements identified for this delivery have been met or dispositioned, that all approved changes have been implemented, and that all defects designated for resolution prior to delivery have been resolved. | Center |  |  |  |  |  |
| SWE-195 | 4.6.5 | The project manager shall maintain the software using standards and processes per the applicable software classification throughout the maintenance phase. | Center |  |  |  |  |  |
| SWE-196 | 4.6.6 | The project manager shall identify the records and software tools to be archived, the location of the archive, and procedures for access to the products for software retirement or disposal. | Center |  |  |  |  |  |
| SWE-079 | 5.1.2 | The project manager shall develop a software configuration management plan that describes the functions, responsibilities, and authority for the implementation of software configuration management for the project. | Center |  |  |  |  |  |
| SWE-080 | 5.1.3 | The project manager shall track and evaluate changes to software products. | Center |  |  |  |  |  |
| SWE-081 | 5.1.4 | The project manager shall identify the software configuration items (e.g., software records, code, data, tools, models, scripts) and their versions to be controlled for the project. | Center |  |  |  |  |  |
| SWE-082 | 5.1.5 | The project manager shall establish and implement procedures to: (see list items in NPR) | Center |  |  |  |  |  |
| SWE-083 | 5.1.6 | The project manager shall prepare and maintain records of the configuration status of software configuration items. | Center |  |  |  |  |  |
| SWE-084 | 5.1.7 | The project manager shall perform software configuration audits to determine the correct version of the software configuration items and verify that they conform to the records that define them. | Center |  |  |  |  |  |
| SWE-085 | 5.1.8 | The project manager shall establish and implement procedures for the storage, handling, delivery, release, and maintenance of deliverable software products. | Center |  |  |  |  |  |
| SWE-201 | 5.5.1 | The project manager shall track and maintain software non-conformances (including defects in tools and appropriate ground software). | Center |  |  |  |  |  |

_Decision support only. The project manager classifies software (SWE-020) and maintains the Requirements Mapping Matrix (SWE-125); software engineering and software assurance Technical Authorities must agree on the classification, and tailoring of 'X' requirements needs approval of the Authority named in Appendix C (NPR 7150.2D 2.2.5). This tool does not grant compliance, approval or relief._
