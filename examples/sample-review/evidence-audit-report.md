# Evidence audit (fictional example)

- `python -m agentlib evidence check *.md --require-citations`: no errors (see `tests/test_sample_review.py`).
- Spot-checks: ASVS level-selection guidance [owasp-asvs, p. 15] and the statement that higher levels are
  recommendations [owasp-asvs, p. 13] confirmed against the pinned PDF.
- Evidence strengths: assessment rows cite illustrative records only; in a real review each would be an
  evidence record per the evidence-and-citation skill.
- **Verdict:** Pass with corrections (illustrative evidence must be replaced by real records).
