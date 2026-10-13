Combine `owasp-asvs` (product: the API's security properties and their verification) with `nist-ssdf`
(process: how the pipeline builds and releases the software). Run the `secure-software-delivery` workflow:
`application-security-verifier` selects the ASVS level and verifies; `secure-development-reviewer` assesses the
pipeline; `evidence-auditor` checks the evidence before the release recommendation.
