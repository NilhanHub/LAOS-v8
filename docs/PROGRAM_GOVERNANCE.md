# Program governance

## Milestone rule

Only one milestone is considered active for acceptance at a time. Later design exploration is allowed, but no later capability is claimed complete before its dependencies and exit gates pass.

## Change control

Changes to mission, trust zones, state machines, security policy, identity, sandboxing, evidence custody, side effects, or release gates require an ADR or formal amendment.

## Defect handling

Every defect is classified, assigned a target milestone, given a reproducible test specification, and closed only with an executable regression that fails before and passes after the repair.

## Completion language

Use `planned`, `specified`, `implemented`, `tested`, `independently verified`, and `released` precisely. Do not collapse these states into “done.”
