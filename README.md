# LAOS v8 rebuild repository

**Current state: Stage 2 complete; Stage 3 authorized; LAOS v8 privileged runtime not implemented.**

This repository now contains the Stage 1 recovery/governance baseline and the Stage 2 strict typed kernel: canonical
models, Draft 2020-12 schemas, fail-closed parsing, stable errors, transition tables, canonical hashing, platform
diagnostics, dependency locks, migration discovery, tests, and bootstrap evidence. It does not contain the Security
Spine, a privileged working LAOS v8 runtime, or a v8 release.

The active plan is root `LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md` Revision 1.1. `LAOS_v8_TEN_STAGE_IMPLEMENTATION_PLAN.md` is a subordinate execution index. Earlier documents under `design_inputs/` are historical Stage 0 inputs.

This repository is the clean, version-controlled rebuild workspace for LAOS v8. It preserves the verified LAOS v7 baseline, imports surviving v8 plans only as design inputs, records every known defect as a regression obligation, and establishes the mission, trust architecture, threat model, ADRs, policies, and requirements ledger.

The master framework is for the highly capable Software Architect AI. Weaker agents must never receive this repository or master planning material directly; later milestones will compile separate, minimal execution packs and one Action Capsule at a time.

Start with:

1. `LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md`
2. `RECOVERY_STATE.md`
3. `docs/PLAN_AUTHORITY.md`
4. `PROGRAM_STAGE_LEDGER.json`
5. `REQUIREMENTS_LEDGER.json`
6. `RELEASE_BLOCKERS.json`
7. `THREAT_REGISTER.json`

The `laos` Stage 2 CLI exposes diagnostics, status, schema export, and read-only migration discovery only. Do not
describe it as an execution runtime or release. The exact status is machine-readable in `IMPLEMENTATION_STATUS.json`.
