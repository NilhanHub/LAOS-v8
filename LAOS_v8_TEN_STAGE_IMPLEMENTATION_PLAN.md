# LAOS v8 — Ten-Stage Implementation Plan

Status: active execution index for LAOS v8 Revision 1.1.

## Authority

This document groups implementation work into ten internal stages. It does not replace, weaken, reinterpret, or override `LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md`. If the documents disagree, the reviewed Revision 1.1 plan and machine-observed artifact truth control.

Stages are not releases or public-review checkpoints. Work may be incomplete inside a stage, but every applicable original milestone gate remains binding before the stage closes.

## Stages

1. **Recovery and program truth** — reconstruct Stage 0; import Revision 1.1; reconcile requirements, threats, ADRs, blockers, scope, migration, and fixture-only v7 regressions.
2. **Typed kernel and platform contracts** — package, strict models and schemas, stable errors, transition tables, dependency locks, CI, support matrix, performance budgets, and migration discovery.
3. **Mandatory Security Spine** — transactional state, seals, safe paths, identity, policy, minimum capsule, broker, qualifying sandbox, evidence capture, clean verifier, model-call mediation, and emergency stop.
4. **Alpha Vertical Trust Slice** — one real defect through bounded edit, verification, evidence, independent review, CAS promotion, crash reconciliation, randomized pilot, and scope freeze.
5. **Core product workflows** — mature pack separation, signing, Action Engine, model profiles, prompt/context controls, new-build compilation, and existing-application capture/continuation.
6. **Execution assurance** — mature command/sandbox providers, evidence custody, privacy, criterion closure, protected checks, independent review, and quorum.
7. **Side effects and recovery** — deny-all protocol, optional retained adapters, trusted approval, `OUTCOME_UNKNOWN`, reconciliation, checkpoints, incident response, revocation, and trust recovery.
8. **Release engineering and operator readiness** — external anchoring, deterministic artifacts, SBOM/provenance, consumer verification, migration, documentation, operator journeys, and evaluation charter.
9. **Candidate red team and sealed evaluation** — feature freeze, independent red team, behavior-fix loop, exact candidate freeze, one preregistered holdout run, and efficacy decision.
10. **Evaluated-revision publication** — build only the evaluated revision, independently reproduce/verify, close RB-001 through RB-025, transfer to durable storage, retrieve, reopen, extract/install, retest, and publish honestly.

## Global gates

- No real weaker agent handles untrusted content before Stage 3 passes.
- No platform expansion occurs before the Stage 4 go/no-go decision.
- Offline v8.0 is verification/read-only; privileged offline authority is unsupported.
- No final holdout opens before Stage 9 candidate freeze.
- A behavior-affecting post-evaluation change invalidates the evaluation and requires a new untouched holdout.
- No v8.0 completion claim occurs before Stage 10 closes every applicable release blocker.

## Stage closure discipline

At each stage closure, run applicable tests, capture evidence, update affected ledgers, record the honestly achieved independent-review level, freeze the result with Git and hashes, list open cross-stage dependencies, and rerun every affected earlier gate.

