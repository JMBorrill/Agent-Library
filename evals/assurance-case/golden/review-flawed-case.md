Problems:

1. **Cycle:** C1 → C1.2 → C1, so C1 is used as evidence for itself (circular argument), and there is no root claim.
2. **C1.1** is a leaf with no evidence and no status: either attach evidence of adequate strength or mark it
   `undeveloped` with a justification.
3. **EV-3** is not used by any claim: link it to the claim it supports or remove it.

Run `python -m agentlib assurance-case check case.yaml` to confirm the fixes; it reports all three.
