# LAOS v8 Master Operating Guide

## 1. Mission

LAOS v8 exists so a highly capable Software Architect AI can convert its deeper reasoning, architecture, risk judgment, and project understanding into small, enforceable instructions that weaker agents can execute reliably.

Master LAOS is private to the Architect. Weaker agents never receive the master framework, full blueprint, future action graph, hidden checks, Architect notes, signing keys, or release authority. They receive only stable public context and one signed Action Capsule at a time.

## 2. Trust zones

### Private Architect Control Plane

Contains the full blueprint, hidden checks, future actions, state database, acceptance policy, risk assessments, App Intelligence, audit anchors, and public verification key. The signing key stays outside even this pack when possible.

### Public Agent Execution Pack

Contains stable public project rules, a model profile, adapter, public checks, selected verified role/profile assets, schemas needed by the weaker agent, and the Architect public key. It intentionally omits the task graph.

### Current Action

Contains the current signed Action Capsule, one copy-pasteable instruction, relevant schemas, and the public key. The capsule expires, is nonce-bound, is tied to a repository seal, and becomes invalid when replaced or amended.

### Application repository

Contains product source and a root-level `Evidence/` folder. LAOS runtime state should live under `.laos/`, which is deliberately outside product-source fingerprints.

### Sandbox

Contains the weaker process. It should have only the intended repository mounted, no unrelated credentials, and externally controlled network and resource limits.

## 3. New-build workflow

1. Architect gathers requirements and resolves ambiguity.
2. Architect creates a strict `ProjectBlueprint`.
3. Compiler validates IDs, references, graph order, model limits, risk controls, checks, evidence, and the Strong Harness Guide hash.
4. Compiler seals the repository before weaker-agent work.
5. Compiler creates separate private/public/current-action packs and scans public material for leaks.
6. Weaker agent uses a fresh authenticated session, claims the current capsule, and performs only that action.
7. Runtime compares repository state with the seal and action scope.
8. Checks run through the command broker and produce automatic transcripts.
9. Evidence is content-addressed and linked to criteria and current source truth.
10. Independent reviewer records criterion-by-criterion verdicts.
11. Criterion ledger and action sequence must both pass before task closure.
12. Architect issues the next action or creates an amendment/recapture.

## 4. Existing-application workflow

Implementation is locked until capture is complete.

1. Architect creates a `CaptureRequest` with required fact categories, questions, and protected paths.
2. LAOS fingerprints and seals the current repository.
3. Weaker investigator receives read-only capture actions.
4. Investigator returns `AppIntelligenceReturn` with source references, confidence, conflicts, known issues, protected areas, commands, and unknowns.
5. LAOS strictly validates structure, signature where required, categories, source references, and repository freshness.
6. Architect independently checks the evidence and signs a `CaptureAcceptanceRecord` identifying accepted/rejected facts and preservation rules.
7. A `ContinuationRequest` is compiled only against the unchanged accepted repository or after explicit recapture/amendment.
8. Continuation actions preserve verified behavior and declared protected areas.

## 5. Anti-skip action protocol

A substantive task normally uses:

```text
UNDERSTAND → PLAN → IMPLEMENT/REPAIR/DEPLOY → VERIFY → EVIDENCE → HANDOFF → REVIEW
```

The action engine allows only one READY/ISSUED action at a time for a dependency chain. Each action has:

- One objective and role
- Prerequisites and sequence
- Criteria addressed
- Read/write/command/network/side-effect permissions
- Planned implementation scope where relevant
- Public checks and private hidden checks
- Required evidence
- Exact outputs
- Stop conditions
- Attempt budget
- Risk tier and fresh-session rule
- Workspace seal, nonce, issue time, expiry, and Ed25519 signature

The runtime—not the weaker agent—controls transitions. Future actions remain absent from the weaker-agent materials.

## 6. Understanding and plan gates

The UNDERSTAND response must map the objective, criteria, invariants, non-goals, preservation rules, allowed/forbidden areas, uncertainties, source references, and verification plan. A generic “understood” response fails.

The PLAN response must map every criterion to files, intended changes, checks, failure paths, preservation checks, and rollback where relevant. Missing criterion coverage or scope outside the Architect-approved planned paths fails.

## 7. Repository truth

LAOS uses one versioned canonical manifest throughout. It covers regular files, symlink objects, byte size, SHA-256, mode, policy digest, and filtered Git truth. It detects add/delete/modify/mode/link-target changes and case collisions. Runtime and evidence directories are excluded by the same policy so proof collection does not invalidate product truth.

A workspace seal is signed before weaker-agent execution. Pre-claim drift, stale captures, post-check source changes, or capsule/seal mismatch fail closed.

## 8. Evidence and acceptance

Evidence levels:

- L0: unsupported assertion
- L1: runtime-captured observation
- L2: deterministic automated proof
- L3: independent proof
- L4: externally attested proof

Each criterion declares a minimum. Evidence is stored under `Evidence/objects/` or specialised subdirectories, hashed, linked to an action and criteria, and bound to a fresh workspace manifest. Secret-like output is rejected.

A task closes only when all required actions are accepted and every mandatory criterion is independently verified or explicitly accepted under the policy.

## 9. Review

Review uses a distinct authenticated actor and fresh context. The reviewer receives the requirement/criterion contract, final repository state, relevant evidence, and authorised hidden checks—not a persuasive builder narrative. The reviewer records a verdict for every required criterion and cannot write product code.

## 10. Side effects

External writes use:

```text
PROPOSED → APPROVAL_REQUIRED → APPROVED → PREPARED → EXECUTING
→ EXECUTED → EXTERNALLY_VERIFIED → COMMITTED
```

Terminal alternatives include denied, aborted, failed, compensated, and manual reconciliation. Every operation has an idempotency key, payload digest, expected result, verification method, compensation plan, proposer, executor, independent verifier, and external receipt where required.

## 11. Recovery and change

Claims have leases and heartbeats. Expired claims return safely. Checkpoints are immutable deterministic archives scoped to authorised paths. Repeated identical failures trigger Architect escalation. A signed amendment supersedes all outstanding authority while preserving accepted history. Material existing-app changes can require recapture.

## 12. Release truth

The release builder validates source, regenerates and compares schemas, verifies bundled resources, runs tests, builds a deterministic ZIP twice, safely extracts it, revalidates and retests it, builds a wheel, installs that wheel into a fresh virtual environment, verifies bundled resources, and produces SBOM, provenance, signature envelope, checksums, and a machine-readable output manifest.

## 13. Source-of-truth order

1. Current signed specification/amendment
2. Current sealed repository and state database
3. Deterministic checks and immutable evidence
4. Independent review and external receipts
5. Current runtime reports
6. Handoff prose and prior-agent summaries
7. Old chats, comments, or unverified claims

## 14. Limits

LAOS cannot turn a local process into a secure sandbox. It cannot prove independent provenance when all keys and artifacts remain on one compromised host. It cannot claim weaker-agent improvement without real comparative trials. It cannot safely guess missing credentials, requirements, or deployment truth. These conditions must remain visible and blocked rather than being papered over.
