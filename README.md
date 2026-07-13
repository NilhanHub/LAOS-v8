# LAOS v8 rebuild repository

**Current state: Stage 2 complete; Stage 3 Mandatory Security Spine is a review candidate awaiting Nilhan; the full
LAOS v8 runtime is not implemented.**

The repository contains the Stage 1 recovery/governance baseline, the accepted Stage 2 typed kernel, and a Stage 3
local Security Spine review candidate. Stage 3 implements transactional local SQLite state, repository seals,
safe paths and archives, authenticated capability bindings, default-deny policy, a minimum signed Action Capsule,
workspace and command brokers, a digest-pinned network-denied Docker sandbox, broker-owned evidence, a local-only
model path, emergency stop, and minimal pre-Alpha operator recovery paths. These are local test-profile controls,
not production signing, complete evidence custody, a complete privileged runtime, or a release.

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

The `laos` CLI exposes diagnostics, status, schema export, read-only migration discovery, denial explanation, state
backup/restore, evidence export/purge reconciliation, and epoch-bound trust recovery. See
`docs/STAGE_3_OPERATOR_PATHS.md`. Do not describe these paths as a complete execution runtime or production release.
The exact status is machine-readable in `IMPLEMENTATION_STATUS.json`.
