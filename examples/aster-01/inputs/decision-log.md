# Decision log entry ASTER-DEC-001 (synthetic)

| Field | Value |
|---|---|
| Question | Which hopping concept should the ASTER-01 ground demonstrator carry into preliminary design? |
| Decision owner (human) | ASTER Phase 1 project lead (synthetic) |
| Alternatives considered | SPRING-IMU, SPRING-CAM, FLYWHEEL-IMU, WHEEL-REF (reference, screened out by mass must ≤ 12 kg) |
| Criteria and weights | C1 launch-speed error 0.30, C2 stored energy 0.20, C3 mass 0.15, C4 TRL 0.15, C5 relocation time 0.20 — proposed by systems-architect 2026-10-12; not yet confirmed by the decision owner |
| Analysis | outputs/08-decision-matrix.json; margin 0.087; C1 switching weight 0.194 (to SPRING-IMU); 75 % of the leading score rests on estimates (weak-evidence warning) |
| Recommendation (analyst) | SPRING-CAM leads on current estimates; recommend measuring launch-speed repeatability (C1) on a bench before deciding |
| **Decision (owner)** | PENDING — no decision recorded |
| Date / signature | none |
| Rationale for any departure | n/a until a decision is made |
| Assumptions and open uncertainties | All scores are estimates or first-order analysis; flywheel energy depends on assumed inertia 0.002 kg m² and 0.15 m lever arm |
| Revisit triggers | Bench data for C1; weight confirmation by the owner; mass TPM breach |
