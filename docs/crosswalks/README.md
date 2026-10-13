# Crosswalks: source element → skill → agent → artifact → test

One JSON file per registered source (`<source-id>.json`), validated by `scripts/validate_library.py`.

```json
{
  "source_id": "owasp-asvs",
  "status": "ACTIVE",                     // or BLOCKED_SOURCE (rows may then be empty)
  "notes": "free text",
  "rows": [
    {
      "source_element": "V8 Authorization",           // topic/control/process as named by the source
      "source_pointer": "5.0/en/0x17-V8-Authorization.md",  // exact pointer actually checked, or "unverified"
      "source_verification": "verified",              // verified | partially_verified | unverified
      "skills": ["security-asvs-controls"],
      "agents": ["security-reviewer"],
      "artifacts": ["asvs-control-map.csv"],
      "tests": ["tests/test_security_asvs_controls.py"],
      "status": "tested"                               // mapped | implemented | tested | blocked
    }
  ]
}
```

`status` here is the author's claim; `scripts/coverage_report.py` recomputes measured coverage from the
files actually present and the tests actually passing.
