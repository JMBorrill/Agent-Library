# Agent-Library

Personal professional AI agent and skills library.

## Framework reading material for Claude

Eight official framework PDFs are available in [`sources/pdfs/`](sources/pdfs/).
Start with the [source index and reading instructions](sources/README.md).

- NASA Systems Engineering Handbook, Rev 2
- NASA Software Engineering Requirements, NPR 7150.2D
- NASA Software Assurance and Software Safety Standard, NASA-STD-8739.8B
- NIST AI Risk Management Framework 1.0
- NIST AI RMF Playbook
- NIST Secure Software Development Framework 1.1
- HM Treasury Green Book 2026
- OWASP Application Security Verification Standard 5.0.0

[Provenance manifest](sources/pdf-manifest.json) includes official URLs, editions,
checksums and the remaining frameworks' web links/access restrictions.
[Third-party notices](sources/THIRD_PARTY_NOTICES.md) retain source attribution.

```sh
python3 scripts/verify_source_pdfs.py
```

This checks source integrity; it does not validate agent capabilities or certify
engineering, security or regulatory compliance.

## Build status

This repository currently contains a source pack. At source-pack preparation,
only the initial README was present; the starter implementation kit and master
Claude specification still need importing before the full build mission can run.
See [source-pack progress and limitations](docs/SOURCE_PACK_STATUS.md).
