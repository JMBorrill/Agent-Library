# Trade-space method notes (library guidance)

**Morphological analysis** (general engineering method, Zwicky): list the functions, list options per
function, form concepts as one option per function. The space grows multiplicatively (3 × 2 × 3 = 18),
so screening rules are essential.

**Screening rules**
- *Incompatible*: physically or logically impossible together (rolling wheels + attitude control in
  ballistic flight serves no purpose for a non-hopping concept).
- *Requires*: one option depends on another (a flywheel spin-up needs a high-power source).
- *Maturity*: options below the project TRL threshold need a maturation plan; the script flags them.

**TRL caution**: TRL scales differ between organisations (NASA, ESA, EU H2020 definitions); record which
scale you use and who assessed it. A vendor's TRL claim is `vendor` evidence.

**From screening to selection**: export survivors to `se-decision-analysis`; score with evidence; check
sensitivity; record the decision with the decision owner.

**Design solution record**: once selected, document the concept with predicted performance against each
allocated requirement and the basis of each prediction (estimate → analysis → test as the design matures).
