# LAOS v8.0 Reconstruction, Completion, Verification, and Release Plan

**Status:** Authoritative implementation plan; no v8 implementation is claimed by this document.  
**Source baseline:** `/mnt/data/LAOS_v7.0_Complete_System(1).zip`  
**Primary operator:** Highly capable Software Architect AI  
**Execution agents:** Weaker investigation, implementation, testing, verification, and review agents  
**Owner:** Nilhan  
**Target release:** `LAOS v8.0.0`

---

## 1. Executive decision

LAOS v8 must be rebuilt as a trusted, Architect-controlled agent operating system—not as a larger prompt pack.

The Strong Software Architect AI keeps the complete project truth, architecture, future work, risk decisions, hidden checks, acceptance rules, signing authority, and release authority. A weaker agent receives only the minimum stable context plus one bounded, signed Action Capsule for the single action it may perform now.

The runtime must make skipped steps, scope drift, stale evidence, self-review, fake completion, unsafe commands, and unapproved external actions fail closed. Prompts explain the process; code enforces it.

The defining operating rule is:

```text
Nilhan
  → highly capable Software Architect AI + private master LAOS
  → private Architect Control Plane
  → one signed Action Capsule
  → weaker agent inside a scoped execution environment
  → machine-captured checks, evidence, and independent review
  → next action only after acceptance
```

---

## 2. Verified starting point

The current durable workspace contains:

1. The complete original v7 ZIP.
2. The comprehensive v8 design plan.
3. Four surviving v8 documentation files.

The current durable workspace does **not** contain the previously described v8 implementation source tree, test suite, SQLite schema, release artifacts, or test reports. Therefore:

- The historical statement that a prior build passed 35 of 37 tests is useful context, but it is not reproducible evidence.
- No previously claimed v8 control is accepted as implemented until source and tests are present and pass again.
- The program begins from v7 plus the surviving v8 specification documents.
- Any later-recovered v8 source is treated as an untrusted candidate import and merged only module by module after review and regression testing.
- The original v7 ZIP remains immutable.

This protects the rebuild from another false-completion or lost-artifact event.

---

## 3. Exact v8 mission

LAOS v8 exists so the Strong Software Architect AI can:

1. Understand Nilhan’s goal and the real repository.
2. Make and preserve the important product, architecture, security, data, operational, and quality decisions.
3. Convert those decisions into small actions appropriate for a particular weaker agent.
4. Expose only the current action and minimum necessary context.
5. Technically prevent or reject skipped gates, broad edits, stale work, unsupported claims, and unsafe side effects.
6. Measure completion against observable repository and environment outcomes—not agent confidence.
7. Preserve trustworthy state so another Architect or execution session can continue without reconstructing the project from chat.
8. Evaluate whether the framework materially improves weaker-agent performance.

LAOS does not magically increase a weaker model’s intelligence. It transfers the Strong Architect’s decisions into enforceable structure, reduces the weaker agent’s degrees of freedom, improves the agent-computer interface, and catches failure before it becomes accepted truth.

---

## 4. Non-negotiable design principles

### 4.1 Architect-only master authority

Master LAOS, the complete task/action graph, hidden checks, evaluator rubrics, risk decisions, unresolved conflicts, signing keys, and release authority remain private to the Architect/control plane.

### 4.2 One legal action at a time

A weaker agent receives one Action Capsule. Later actions remain unavailable until the runtime accepts the current action.

### 4.3 Default deny

Any permission, path, command, tool, network destination, external effect, or state transition not explicitly allowed is denied.

### 4.4 Machine truth outranks prose

Repository state, test outcomes, external receipts, signed records, and current evidence outrank README claims, prior-agent summaries, and “done” statements.

### 4.5 Fail closed

Missing credentials, unavailable isolation, unknown repository state, invalid signatures, stale evidence, or incomplete capture produces a blocked state—not a guessed pass or fake implementation.

### 4.6 No fake production functionality

No mock, simulated, placeholder, dry-run, or demo behavior may be presented as a working production feature. Test fixtures are permitted only inside tests and must never masquerade as production behavior. Real-agent evaluation must use real model executions.

### 4.7 Separate workflow control from OS isolation

LAOS controls workflow, authority, evidence, and acceptance. A sandbox, container, VM, microVM, or managed isolated environment controls what an execution process can reach.

### 4.8 Risk-adaptive rigor

Trivial low-risk actions should not suffer the same ceremony as production migrations. However, reduced ceremony must never remove the core guarantees: exact authority, fresh state, bounded scope, current evidence, and honest status.

### 4.9 Reproducibility and durable truth

Every claimed release file must exist in durable storage, be reopened, hashed, extracted where relevant, retested, and independently verified before completion is reported.

---

## 5. Release deliverables

The final release must contain, at minimum:

```text
LAOS_v8.0_Complete_System.zip
LAOS_v8.0_Complete_System.zip.sha256
LAOS_v8.0_RELEASE_SUMMARY.json
LAOS_v8.0_BUILD_VERIFICATION.json
LAOS_v8.0_TEST_REPORT.md
LAOS_v8.0_SECURITY_AND_RED_TEAM_REPORT.md
LAOS_v8.0_REAL_AGENT_EVALUATION_REPORT.md
LAOS_v8.0_SBOM.json
LAOS_v8.0_PROVENANCE.json
LAOS_v8.0_SIGNATURES/
LAOS_v8.0_KNOWN_LIMITATIONS.md
LAOS_v8.0_MIGRATION_FROM_V7.md
```

Inside the ZIP:

```text
LAOS_v8.0/
  README.md
  START_HERE_FOR_NILHAN.md
  START_HERE_FOR_ARCHITECT_AI.md
  START_HERE_FOR_CAPTURE_AGENT.md
  START_HERE_FOR_IMPLEMENTATION_AGENT.md
  START_HERE_FOR_REVIEWER.md
  pyproject.toml
  src/laos/
  schemas/
  migrations/
  templates/
  adapters/
  skills/
  examples/
  docs/
  tests/
  tools/
  release_evidence/
```

The signing key must never be included.

---

## 6. Target source architecture

```text
src/laos/
  __init__.py
  __main__.py
  cli/
  domain/
    ids.py
    enums.py
    models.py
    errors.py
    transitions.py
  schemas/
    registry.py
    validation.py
    generation.py
  repository/
    paths.py
    manifest.py
    fingerprint.py
    seals.py
    git_state.py
    archive.py
  state/
    db.py
    migrations.py
    transactions.py
    claims.py
    leases.py
    events.py
    snapshots.py
  identity/
    actors.py
    sessions.py
    capabilities.py
    signatures.py
  policy/
    engine.py
    risk.py
    decisions.py
    approvals.py
  packs/
    architect.py
    execution.py
    capture.py
    review.py
    action_capsule.py
    leak_scan.py
    verify.py
  actions/
    compiler.py
    engine.py
    understand.py
    plan.py
    implement.py
    verify.py
    evidence.py
    handoff.py
    review.py
  capture/
    request.py
    runtime.py
    return_pack.py
    acceptance.py
    continuation.py
  commands/
    broker.py
    registry.py
    results.py
    dangerous.py
  sandbox/
    provider.py
    local_docker.py
    manifest.py
    assurance.py
  evidence/
    cas.py
    manifest.py
    freshness.py
    collectors.py
    secrets.py
    maturity.py
  review/
    capsules.py
    adjudication.py
    repair.py
  side_effects/
    lifecycle.py
    idempotency.py
    receipts.py
    compensation.py
  recovery/
    checkpoints.py
    restore.py
    amendments.py
    anti_thrashing.py
  artifacts/
    staging.py
    deterministic_zip.py
    manifests.py
    verify.py
    sbom.py
  provenance/
    attestations.py
    signing.py
    slsa.py
  prompts/
    profiles.py
    compiler.py
    linter.py
    context.py
  skills/
    registry.py
    signing.py
    verification.py
  telemetry/
    trace.py
    export.py
    redaction.py
  evals/
    runner.py
    graders.py
    comparison.py
    reporting.py
```

Tests are separated into:

```text
tests/unit/
tests/integration/
tests/property/
tests/concurrency/
tests/adversarial/
tests/e2e/
tests/release/
tests/migration/
tests/real_agent/
```

Create an `Evidence/` folder at the root of the v8 working repository. Build, test, review, security, and release evidence should be stored there while engineering proceeds.

---

# 7. Upgrade program

## Phase 0 — Preserve, recover, and establish truth

### Objective

Create a clean, auditable baseline and eliminate ambiguity about what exists.

### Work

1. Preserve the original v7 ZIP read-only and record its size and SHA-256.
2. Extract v7 into a clean source repository without modifying the ZIP.
3. Import the surviving v8 design documents into `docs/design_history/`.
4. Search all available durable storage for any prior v8 source, tests, or archives.
5. If recovered, quarantine them under `recovered_candidates/`; do not merge directly.
6. Create a complete v7 file inventory and map every feature to a proposed v8 module.
7. Run all v7 tests and preserve raw output.
8. Reproduce all known v7 defects as failing tests:
   - capture/continuation fingerprint mismatch;
   - malformed capture accepted;
   - pre-claim modification bypass;
   - symlink escape;
   - unsafe or overly broad command execution;
   - procedural actor identity;
   - concurrent state races.
9. Create architecture decision records for all foundational choices.
10. Establish a source-control baseline tag and branch protection rules.

### Deliverables

- `Evidence/phase_0_v7_hashes.json`
- `Evidence/phase_0_v7_test_output.txt`
- `Evidence/phase_0_known_defect_reproduction.md`
- `docs/adr/`
- `docs/V7_TO_V8_FEATURE_MAP.md`
- clean v8 source skeleton

### Exit gate

- v7 is reproducibly extracted and tested.
- Every known defect has a regression test or a documented reason it cannot yet be reproduced.
- No v8 feature is marked implemented merely because a document describes it.

---

## Phase 1 — Freeze the formal v8 contract

### Objective

Define one coherent domain model, state model, authority model, and error model before implementation spreads.

### Work

1. Define typed entities for projects, packs, repositories, seals, actors, sessions, capabilities, tasks, actions, criteria, checks, evidence, reviews, side effects, artifacts, captures, amendments, and attestations.
2. Define ID formats and global uniqueness rules.
3. Define all state machines and legal transitions.
4. Define formal safety invariants, including:
   - only one current action per dependency chain;
   - no implementation before approved understanding and plan;
   - no criterion closure without current evidence and required review;
   - no actor may review its own build work;
   - no side effect may execute without a valid approval and idempotency record;
   - no next action may be revealed before current action acceptance.
5. Define a stable exception taxonomy and machine-readable error codes.
6. Define risk levels and minimum controls per risk level.
7. Define source-of-truth ordering.
8. Define compatibility versions for pack schemas, runtime protocol, database schema, adapters, skills, and sandbox providers.

### Required exception taxonomy

At minimum:

```text
LAOS-1000 VALIDATION_FAILED
LAOS-1100 SCHEMA_MISMATCH
LAOS-1200 INTEGRITY_FAILED
LAOS-2000 AUTHORIZATION_DENIED
LAOS-2100 POLICY_DENIED
LAOS-2200 CAPABILITY_EXPIRED
LAOS-2300 REPLAY_DETECTED
LAOS-3000 INVALID_STATE_TRANSITION
LAOS-3100 CONFLICT
LAOS-3200 STALE_REPOSITORY
LAOS-3300 STALE_EVIDENCE
LAOS-4000 PATH_VIOLATION
LAOS-4100 SANDBOX_REQUIRED
LAOS-4200 COMMAND_DENIED
LAOS-5000 SIDE_EFFECT_FAILED
LAOS-5100 SIDE_EFFECT_RECONCILIATION_REQUIRED
LAOS-6000 RELEASE_VERIFICATION_FAILED
```

Every CLI failure returns a stable code, human explanation, remediation guidance, and a non-zero exit status.

### Deliverables

- `docs/DOMAIN_MODEL.md`
- `docs/STATE_MACHINES.md`
- `docs/TRUST_AND_AUTHORITY_MODEL.md`
- `docs/ERROR_CONTRACT.md`
- typed model package
- schema registry design

### Exit gate

- Architecture review passes.
- State and authority invariants have executable tests before runtime implementation begins.

---

## Phase 2 — Build correctness and filesystem foundations

### Objective

Fix v7’s most fundamental correctness and containment defects with shared primitives used everywhere.

### 2.1 Strict schema validation

- Use JSON Schema Draft 2020-12 consistently.
- Generate schemas from typed models where practical, then review generated output.
- Use closed schemas (`unevaluatedProperties: false` or equivalent) where extensibility is not intended.
- Validate both structure and semantic references.
- Fail on unknown statuses, duplicate IDs, missing references, invalid paths, invalid hashes, and unsupported versions.
- Bundle schemas and resolve references without network access.
- Add malformed and fuzzed inputs for every external record.

### 2.2 Canonical repository fingerprinting

Create one imported implementation used by capture, continuation, workspace sealing, checks, evidence freshness, and release verification.

Each manifest entry should include:

```json
{
  "path": "relative/posix/path",
  "entry_type": "file|symlink|directory-marker",
  "size_bytes": 123,
  "sha256": "...",
  "mode": "0644",
  "symlink_target": null
}
```

Rules:

- paths are normalized to POSIX form;
- ordering is deterministic;
- symlinks are represented but not followed;
- ignore rules are versioned and identical across all callers;
- the algorithm has an explicit identifier such as `laos-repository-manifest-v1`;
- unsupported algorithm versions fail.

Mandatory round trip:

```text
capture unchanged repository
→ compile continuation
→ verify original repository
→ PASS

change one tracked byte
→ verify
→ FAIL
```

### 2.3 Safe paths and archives

- Resolve every path and prove it remains under the allowed root.
- Reject traversal, absolute external paths, symlink/junction escapes, device files, named pipes, and unsafe archive entries.
- Never extract ZIP entries before validating every entry.
- Set explicit file-count and expanded-size limits.
- Prevent destructive output targets such as repository root, filesystem root, parent workspace, and source archive.

### 2.4 Workspace seals

- Seal repository and Git state before weaker-agent access.
- Bind every action to the approved seal.
- Reject unexplained pre-action drift.
- Support explicit Architect-signed recapture or amendment when drift is legitimate.

### Deliverables

- strict schema layer
- canonical manifest/fingerprint library
- safe path/archive library
- workspace seal system
- v7 regression tests now passing in v8

### Exit gate

No code for action execution is accepted until schema, fingerprint, seal, path, symlink, and archive property tests pass.

---

## Phase 3 — Build the transactional control plane

### Objective

Replace mutable JSON coordination with atomic, concurrency-safe state.

### Work

1. Use SQLite for local single-machine execution.
2. Enable WAL only where appropriate and document that it is a local-machine design, not a distributed database.
3. Use explicit transactions, uniqueness constraints, foreign keys, and optimistic version columns.
4. Build migrations with forward and rollback tests.
5. Implement claims, leases, heartbeats, expiry, and idempotent retries.
6. Append events transactionally with a hash chain.
7. Implement external audit anchoring for important checkpoints and release events.
8. Provide a provider interface for an external transactional database in future multi-machine mode.
9. Add crash-recovery and interrupted-transaction tests.

### Critical static-versus-mutable packaging design

This phase must permanently fix the known immutable-manifest failure.

#### Immutable pack contents

The release pack contains:

- source code;
- schemas;
- migrations;
- static policies;
- templates;
- adapters;
- signed skills;
- documentation;
- examples;
- tests;
- public keys.

It does **not** contain an active mutable runtime database.

#### Runtime-generated state

On first use, LAOS creates:

```text
.laos/state/laos.sqlite3
.laos/state/laos.sqlite3-wal
.laos/state/laos.sqlite3-shm
.laos/locks/
.laos/logs/
.laos/tmp/
```

These paths are excluded from the immutable pack manifest and product-source fingerprint.

#### Separate manifests

1. `IMMUTABLE_PACK_MANIFEST.json` covers shipped static files.
2. `HARNESS_STATIC_MANIFEST.json` covers installed static harness files.
3. `RUNTIME_STATE_SNAPSHOT_MANIFEST.json` covers an explicit, point-in-time state snapshot.
4. `EVIDENCE_MANIFEST.json` covers evidence separately.
5. `RELEASE_ARTIFACT_MANIFEST.json` covers final deliverables.

A state snapshot must use SQLite’s online backup API or another safe database snapshot method. It must not copy the main database file alone while uncheckpointed WAL state may exist.

### Tests for the known failure

- Pack verification passes before and after normal runtime use.
- Changing the mutable database does not invalidate the immutable pack.
- Changing a static runtime file invalidates the immutable pack.
- A runtime snapshot detects later state mutation.
- Snapshot restore reproduces the same logical records.
- The release ZIP contains migrations, not an active mutable database.

### Deliverables

- transactional database and migrations
- claims/leases/events implementation
- immutable/static/runtime/evidence manifest separation
- state snapshot and restore tool

### Exit gate

Concurrency, crash, pack-verification, and state-snapshot tests pass with no race-based false success.

---

## Phase 4 — Authenticate actors and enforce policy

### Objective

Replace self-declared names with real authority boundaries.

### Work

1. Define actor roles: Architect, builder, tester, verifier, reviewer, side-effect operator, release acceptor.
2. Issue short-lived session/capability tokens from the trusted control plane.
3. Store token hashes, not raw tokens.
4. Bind capabilities to project, repository seal, pack, task/action, allowed operations, and expiry.
5. Prevent replay with nonces and used-token records.
6. Use signed Action Capsules with Ed25519 or an equivalent modern signature scheme.
7. Keep private signing keys outside all public packs and execution workspaces.
8. Implement explainable policy decisions without exposing hidden future work.
9. Add dual-control approval for critical side effects and release acceptance.

### Explicit fix for the known side-effect exception defect

All unauthorised operations must pass through one authorization boundary and raise the same domain exception:

```text
AuthorizationDenied
machine code: LAOS-2000
```

For an unauthorised builder attempting to externally verify a side effect:

- the operation is rejected before mutation;
- the side-effect state is unchanged;
- an audit event records the denied attempt;
- CLI JSON contains `LAOS-2000`;
- no lower-level `ValueError`, generic runtime error, or state error leaks through;
- tests assert exact code, state immutability, and audit entry.

### Deliverables

- actor/session/capability system
- signature system
- policy engine and risk matrix
- stable authorization failure contract

### Exit gate

Identity spoofing, role confusion, expired token, replay, builder self-review, and unauthorised side-effect tests all pass.

---

## Phase 5 — Separate trust zones and compile safe packs

### Objective

Physically and cryptographically separate what the Architect knows from what weaker agents receive.

### Pack types

#### Architect Control Pack

Contains full blueprint, future graph, hidden checks, risk decisions, accepted capture truth, unresolved conflicts, evaluator rubrics, and release plan. It does not contain private signing keys where external key storage is possible.

#### Agent Execution Pack

Contains stable public rules, minimal runtime client, approved public checks, model profile, adapter, selected signed skills, repository identity, and public verification key. It contains no future action graph.

#### Action Capsule

Contains one action, nonce, expiry, repository seal, allowed paths, tool capabilities, acceptance criteria addressed, outputs, checks, evidence, maximum attempts, stop conditions, and handoff format.

#### Capture Execution Pack

Read-only investigative authority for existing applications.

#### Review Capsule

Original criteria, final repository state/diff, evidence, review instructions, and hidden checks where permitted. It omits persuasive builder commentary.

#### Release Attestation Pack

Final manifests, checksums, SBOM, provenance, signatures, tests, evaluation, limitations, and acceptance decision.

### Leak scanner

Public packs are blocked if they contain:

- master LAOS files;
- Architect Control Pack files;
- future action IDs or descriptions;
- hidden tests or expected answers;
- signing keys;
- secrets or credentials;
- evaluator rubrics;
- stale files from another compile;
- unapproved source snapshots.

### Deliverables

- deterministic pack compiler
- separate pack schemas
- capsule signing and verification
- leak scanner
- pack verification CLI

### Exit gate

A red-team agent cannot obtain future actions, hidden tests, private rubrics, or signing material from any public pack.

---

## Phase 6 — Build the Anti-Skip Action Engine

### Objective

Make step-skipping technically difficult and acceptance impossible without the required proof.

### Standard sequence

```text
UNDERSTAND
  → PLAN
  → IMPLEMENT | REPAIR | CAPTURE | DEPLOY
  → VERIFY
  → EVIDENCE
  → HANDOFF
  → REVIEW
  → ACCEPT
```

Not every low-risk action needs every visible stage, but the policy engine must explicitly approve any compressed sequence.

### UNDERSTAND gate

The weaker agent must return structured answers covering:

- exact objective;
- acceptance criteria;
- invariants and preserved behavior;
- allowed and forbidden scope;
- explicit non-goals;
- important risks;
- unknowns;
- verification strategy.

Vague acknowledgement fails.

### PLAN gate

The plan maps every criterion to intended files, intended behavior, tests, failure paths, preservation checks, evidence, and rollback or recovery where relevant.

### IMPLEMENT gate

- Repository seal is checked immediately before work.
- Only allowed paths and capabilities are available.
- The runtime records before state.
- The agent cannot reveal or claim later actions.
- Attempts are counted and failed approaches fingerprinted.

### VERIFY gate

- Commands run through the broker.
- Hidden checks run outside the builder’s writable workspace.
- Relevant failure paths and invariants run.
- Test weakening is detected.

### EVIDENCE gate

- Evidence is primarily runtime-captured.
- Each item is linked to a criterion and source seal.
- Evidence freshness is checked.

### HANDOFF gate

- Produce a concise, structured, fact-only handoff.
- Exclude future work not yet authorised.
- Preserve blockers and unknowns.

### REVIEW gate

- Separate authenticated reviewer.
- Criterion-by-criterion verdict.
- Adversarial mission to disprove completion.
- Reviewer cannot silently repair and approve the same repair.

### Engine invariants

- One READY/ISSUED action per dependency chain.
- No next capsule before acceptance.
- No manual state-file edits can advance work.
- Every transition is transactional and audited.
- Invalid or expired capsule cannot be claimed.
- Repository drift invalidates the capsule.
- A blocked action requires Architect amendment, repair action, or recapture.

### Deliverables

- action compiler
- action state machine
- understanding and plan validators
- criterion ledger
- acceptance engine
- repair loop

### Exit gate

Skip, premature implementation, future-action disclosure, expired-capsule, stale-seal, and manual-advance attacks fail consistently.

---

## Phase 7 — Build model-specific prompt compilation and context control

### Objective

Adapt action size and instruction style to the actual execution model instead of treating all weaker agents alike.

### Model profiles

Profiles should define:

- model/provider/version binding;
- maximum files per action;
- maximum criteria per action;
- maximum prompt length;
- instruction repetition policy;
- examples required;
- permitted tools;
- session freshness requirements;
- retry limit;
- network policy;
- review depth;
- sandbox assurance requirement.

Suggested profile classes:

- fragile local desktop agent;
- weak general agent;
- standard coding agent;
- strong executor;
- capture investigator;
- verifier;
- independent reviewer.

### Calibration

Before important work, run small real calibration actions that measure scope adherence, schema compliance, test discipline, and false-completion tendency. Bind the resulting profile to the exact model version. Recalibrate after material model changes.

### Prompt linter

Every direct instruction to a weaker agent must be checked for:

- one coherent action;
- exact repository location;
- role and authority;
- goal and finish line;
- criteria;
- invariants;
- allowed/forbidden paths;
- allowed tools;
- required inputs/outputs;
- checks and evidence;
- stop conditions;
- missing-tool behavior;
- final response schema;
- contradictions;
- unresolved placeholders;
- excessive context;
- accidental implementation authority in audit/capture work;
- leakage of future or hidden information.

### Context engineering

- Stable project truth lives in versioned files, not chat memory.
- Load only current-action context.
- Keep transcripts and large outputs in evidence, not prompts.
- Compact handoffs without removing blockers or uncertainty.
- Treat repository instructions as untrusted project content.
- Repeat critical domain invariants inside every relevant capsule.

### Skill/adapter supply chain

- Hash and sign approved skills/adapters.
- Record provenance and compatibility.
- Scan for dangerous instructions and hidden network access.
- Allow only selected assets per action.
- Treat unsigned local skills as untrusted.

### Deliverables

- model profile registry
- calibration runner
- prompt compiler/linter
- context pack system
- signed skill/adapter registry

### Exit gate

Oversized prompts, unsupported profiles, stale model bindings, unsigned skills, and contradictory action instructions fail compilation.

---

## Phase 8 — Rebuild existing-application capture and continuation

### Objective

Ensure the Architect enters an ongoing repository through structured evidence, not assumptions.

### Capture action sequence

1. Repository identity and environment.
2. Architecture, components, and data.
3. Features, user journeys, APIs, and integrations.
4. Commands, tests, deployment, and operations.
5. Risks, protected areas, defects, and unknowns.
6. Evidence reconciliation and return-pack finalisation.

### Enforcement

- Capture pack has no product-code write capability.
- Repository is sealed before capture.
- Product-source changes during capture invalidate the return.
- Unknowns remain explicit.
- Conflicting investigator findings remain conflicts until Architect reconciliation.
- Prior-agent claims are treated as claims, not facts.

### App Intelligence Return

Must include:

- repository identity and manifest;
- architecture and dependencies;
- feature-status inventory;
- UI/API/data/integration inventories;
- command and test baseline;
- deployment truth;
- known issues and debt;
- protected areas and preservation rules;
- assumptions, unknowns, conflicts, confidence, and evidence links.

### Architect acceptance

The Architect signs a Capture Acceptance Record identifying:

- facts accepted;
- facts rejected;
- unresolved facts;
- preservation contract;
- repository seal accepted;
- allowed continuation scope.

Continuation cannot compile against a changed repository without delta capture, recapture, or explicit amendment.

### Deliverables

- capture compiler/runtime
- strict return validator
- capture acceptance system
- continuation compiler
- delta recapture workflow

### Exit gate

Unchanged capture-to-continuation passes end to end; stale, modified, malformed, unsigned, incomplete, or unaccepted capture returns fail.

---

## Phase 9 — Build safe execution, checks, sandboxing, and evidence

### 9.1 Command broker

- Use argv arrays, never unrestricted `shell=True` as the normal path.
- Freeze executable, arguments, working directory, environment, timeout, network policy, and expected output.
- Deny dangerous command families by default.
- Capture stdout, stderr, exit code, start/end time, command hash, tool version, repository seal, and actor.
- Run verification in a clean environment where possible.

### 9.2 Sandbox provider

Implement a provider interface plus one real provider, initially local Docker where available.

Sandbox requirements:

- non-root process;
- only intended repository mounted;
- no unrelated host files;
- no credentials by default;
- network disabled by default;
- destination allowlists when required;
- CPU, memory, process, and time limits;
- fresh environment per high-risk action;
- outputs returned as patches, evidence, and structured reports.

High-risk execution must fail with `LAOS-4100 SANDBOX_REQUIRED` when required isolation is unavailable. It must not silently fall back to unrestricted host execution.

### 9.3 Evidence engine

Create a content-addressed evidence store under repository-root `Evidence/`.

Every evidence item records:

- evidence ID and type;
- criterion ID;
- action/check/run ID;
- actor/session;
- timestamps;
- repository and criterion-scoped fingerprints;
- file hash and size;
- command or collector provenance;
- maturity level;
- secret/PII scan result;
- dependencies and freshness status.

Evidence maturity:

```text
L0 unsupported assertion
L1 agent-produced structured record
L2 runtime-captured deterministic result
L3 independent rerun or reviewer observation
L4 externally attested result
```

High-risk criteria cannot close on L0/L1 alone.

### Evidence-manifest completion gate

The previously unfinished post-merge evidence validation must become a mandatory release gate. The validator must detect:

- missing files;
- wrong hash/size;
- duplicate IDs;
- wrong criterion link;
- stale repository seal;
- changed evidence dependencies;
- fabricated screenshot metadata;
- missing external receipts;
- secret or PII leakage;
- narrative evidence used above its maturity level;
- manifest entries pointing outside `Evidence/`;
- extra unindexed evidence where complete indexing is required.

The full test suite must run after this validator is merged. No partial or pre-merge test result counts.

### Deliverables

- command broker
- sandbox interface and real provider
- evidence CAS and manifest validator
- check runner and collectors
- secret/PII scanner

### Exit gate

Host-shell bypass, missing sandbox, stale evidence, evidence tampering, secret leakage, and manifest mismatch tests all fail closed.

---

## Phase 10 — Independent review, criterion closure, and adjudication

### Objective

Prevent builders from grading themselves and prevent task-level pass labels from hiding unfinished requirements.

### Work

1. Track every mandatory acceptance criterion separately:

```text
NOT_STARTED → IMPLEMENTED → VERIFIED → REVIEWED → ACCEPTED
```

2. Bind code, checks, evidence, and review verdict to each criterion.
3. Issue a separate signed Review Capsule.
4. Authenticate reviewer identity and reject builder/reviewer equivalence.
5. Require review of failure paths, regression risk, test weakening, scope, security, and unsupported claims.
6. Prevent reviewers from editing code during review unless a new repair action is issued.
7. Route disagreements to Architect adjudication.
8. Require fresh-context review for high/critical risk.
9. Run hidden/adversarial checks outside builder control.

### Deliverables

- criterion ledger
- review capsule compiler
- reviewer submission schema
- adjudication and bounded repair workflow

### Exit gate

A task cannot close while any mandatory criterion lacks current evidence or required independent review.

---

## Phase 11 — Side effects, checkpoints, recovery, and anti-thrashing

### Side-effect lifecycle

```text
PROPOSED
  → AUTHORISED
  → PREPARED
  → EXECUTED
  → EXTERNALLY_VERIFIED
  → COMMITTED
```

Terminal alternatives:

```text
ABORTED | COMPENSATED | RECONCILIATION_REQUIRED
```

Every side effect requires:

- exact operation and target;
- actor capability;
- human/Architect approval when required;
- idempotency key;
- payload fingerprint;
- expected external outcome;
- verification method;
- external receipt;
- timeout ambiguity handling;
- rollback or compensation plan.

Consequential operations—including deployments, payments, emails, public publishing, destructive migrations, credential creation, data export, and production changes—require explicit approval.

### Checkpoints and recovery

- Create content-addressed checkpoints before broad or risky actions.
- Record repository, state, evidence, and action position.
- Restore only through an authorised recovery action.
- Do not delete extra files unless explicitly approved.
- Test interrupted recovery and repeated recovery.

### Anti-thrashing

- Fingerprint failed approaches.
- Detect repeated strategy loops.
- After limits, shrink action, restore checkpoint, block, or escalate.
- Preserve failure history rather than hiding it.

### Deliverables

- side-effect broker
- approval/idempotency/receipt system
- checkpoint/restore system
- amendment workflow
- anti-thrashing engine

### Exit gate

Replay, double execution, wrong actor, payload mutation, ambiguous timeout, compensation, and repeated-failure tests pass.

---

## Phase 12 — Deterministic artifacts, provenance, and release truth

### Objective

Make release claims independently verifiable and prevent mutable runtime state from contaminating immutable release verification.

### Build pipeline

1. Start from a clean source checkout.
2. Run lint, type checks, tests, security scans, secret scan, and license/dependency audit.
3. Build in a clean staging directory.
4. Exclude caches, `.git`, real environment files, credentials, mutable runtime DB/state, logs, locks, temp files, and nested archives.
5. Normalize archive entry ordering, paths, permissions, and timestamps where feasible.
6. Generate SBOM.
7. Generate immutable content manifest last.
8. Build the ZIP once from scratch.
9. Hash and sign the ZIP.
10. Extract into a second clean directory.
11. Re-run schema validation, self-tests, integration tests, leak scan, secret scan, and pack verification against the extracted copy.
12. Compare expected and extracted manifests.
13. Generate provenance and release attestation.
14. Reopen every deliverable and verify size/hash immediately before final reporting.
15. Copy final deliverables to durable storage.
16. Simulate temporary-workspace loss and confirm the durable copy remains usable.

### Provenance

Use SLSA-style provenance and in-toto-compatible attestations where practical. Release signatures should use externally managed keys or Sigstore-style signing rather than a private key stored in the repository.

### Deliverables

- deterministic artifact builder
- manifest verifier
- SBOM generator
- provenance/attestation generator
- signature verifier
- extracted-release test runner

### Exit gate

Any post-build mutation, missing file, mismatched SBOM/provenance, signature failure, secret leak, or extracted-test failure blocks release.

---

## Phase 13 — CLI, operator experience, documentation, and v7 migration

### CLI command families

```text
laos architect init|validate|compile|approve-understanding|approve-plan|amend
laos capture compile|next|validate-return|accept|recapture
laos action next|claim|submit|block|heartbeat|explain
laos check run
laos evidence inspect|verify|snapshot
laos review issue|submit|adjudicate
laos workspace seal|verify
laos checkpoint create|list|restore
laos side-effect propose|approve|execute|verify|reconcile|compensate
laos pack build|verify|scan
laos release build|verify|attest
laos eval run|compare|report
laos doctor|status|audit-export
```

All commands support clear human output and machine-readable JSON. Errors explain the failed gate and exact correction without leaking hidden information.

### Required documentation

- `START_HERE_FOR_NILHAN.md`
- `START_HERE_FOR_ARCHITECT_AI.md`
- `START_HERE_FOR_CAPTURE_AGENT.md`
- `START_HERE_FOR_IMPLEMENTATION_AGENT.md`
- `START_HERE_FOR_REVIEWER.md`
- `MASTER_V8_GUIDE.md`
- `NEW_BUILD_WORKFLOW.md`
- `EXISTING_APP_CAPTURE_WORKFLOW.md`
- `ACTION_CAPSULE_PROTOCOL.md`
- `TRUST_AND_SECURITY_MODEL.md`
- `SANDBOX_REQUIREMENTS.md`
- `EVIDENCE_AND_ACCEPTANCE.md`
- `MODEL_PROFILES_AND_CALIBRATION.md`
- `SIDE_EFFECTS_AND_APPROVALS.md`
- `RECOVERY_AND_AMENDMENTS.md`
- `RELEASE_AND_PROVENANCE.md`
- `REAL_AGENT_EVALUATION.md`
- `LIMITATIONS_AND_HUMAN_APPROVALS.md`
- `MIGRATION_FROM_V7.md`
- `TROUBLESHOOTING.md`
- `COMPATIBILITY_MATRIX.md`

### v7 importer

- Never upgrade v7 packs in place.
- Parse v7 blueprints, tasks, capture returns, and evidence as untrusted input.
- Strictly validate and map into v8 models.
- Conservatively map task states into task/action/criterion states.
- Downgrade unsupported evidence maturity honestly.
- Produce a migration report listing transformed, dropped, blocked, and manually reviewed fields.
- Recompile into new v8 packs.

### Exit gate

A new operator can follow the correct workflow without relying on this conversation, and representative v7 projects migrate or fail with precise, honest explanations.

---

## Phase 14 — Comprehensive testing, red team, and real-agent evaluation

### 14.1 Unit and schema tests

Cover every model, schema, transition, error code, canonicalization rule, and policy decision.

### 14.2 Property-based tests

Generate thousands of cases for:

- path normalization and containment;
- archive entries;
- repository manifest ordering;
- fingerprint determinism;
- state transition invariants;
- token replay and expiry;
- idempotency keys;
- manifest round trips;
- evidence dependency graphs.

### 14.3 Concurrency tests

- simultaneous claim;
- lease expiry and renewal;
- competing event append;
- duplicate check recording;
- conflicting criterion closure;
- simultaneous side-effect execution;
- SQLite busy/retry behavior;
- crash during transaction.

### 14.4 Adversarial tests

- prompt injection in repository files;
- malicious skill/adapter;
- dirty repository;
- pre-claim edits;
- path traversal and symlink escape;
- hidden-test leakage;
- future-action leakage;
- identity spoofing;
- builder self-review;
- test deletion/weakening;
- fake live integration;
- secret in logs/evidence/artifact;
- fabricated screenshot metadata;
- stale capture;
- side-effect replay;
- external timeout after possible success;
- event tampering;
- artifact mutation;
- context overload;
- repeated failed strategy;
- reviewer bias from builder narrative;
- network exfiltration attempt.

### 14.5 End-to-end workflows

Run complete real workflows for:

1. New application.
2. Existing-app capture and continuation.
3. Bug repair with regression test.
4. Security-sensitive change.
5. Recovery after interruption.
6. Approved deployment/side effect.
7. Blocked action due to missing sandbox or credentials.
8. v7 migration.

### 14.6 Cross-platform and sandbox tests

- Portable kernel and CLI on Linux, Windows, and macOS.
- Docker provider on a real Docker-enabled CI runner.
- No release claim of Docker validation until the real provider tests pass.
- Optional hosted provider compatibility tested separately.

### 14.7 Real weaker-agent evaluation

Compare:

1. Normal broad prompt.
2. Static structured prompt.
3. LAOS v7.
4. LAOS v8.
5. Strong reference executor where useful.

Use real models and real tool execution, not simulated responses.

Measure:

- end-to-end functional success;
- mandatory criterion closure;
- skipped gates;
- premature implementation;
- harness-accepted false completion;
- unauthorised file/external changes;
- regression rate;
- test weakening;
- evidence validity and maturity;
- failure-path coverage;
- recovery success;
- repeated approach rate;
- reviewer accuracy;
- human intervention;
- runtime, token, and cost overhead;
- variance across repeated trials.

The release must show material improvement over v7 and broad-prompt baselines without reducing functional success. “Orders of magnitude” may be claimed only if the data supports it.

### Proposed quality thresholds

- 100% pass for security-critical regression and adversarial tests.
- Zero harness-accepted skipped mandatory gates in the controlled release corpus.
- Zero harness-accepted false completion for seeded known failures.
- Zero public-pack leakage of hidden/private material.
- Zero unauthorised side effects in tests.
- Overall code coverage at least 90%; security-critical modules require complete branch coverage plus mutation/property tests.
- Security-critical mutation score target at least 85%.
- All end-to-end workflows pass from a clean install.
- Real-agent evaluation shows statistically credible improvement or the release remains pre-release.

### Deliverables

- complete test suite
- red-team report
- real-agent evaluation dataset, traces, and report
- compatibility report
- residual-risk register

### Exit gate

No open P0/P1 defect, no unverified high-risk claim, and no missing required evaluation.

---

## Phase 15 — Release candidate and final acceptance

### Release train

```text
8.0.0-alpha.1  foundations: schemas, paths, fingerprints, seals, DB
8.0.0-alpha.2  identity, policy, pack separation, action engine
8.0.0-beta.1   capture, evidence, review, side effects, recovery
8.0.0-beta.2   sandbox, provenance, migration, CLI, documentation
8.0.0-rc.1     all automated tests and first real-agent evaluation
8.0.0-rc.2     independent red team and extracted-release retest
8.0.0          all release gates satisfied
```

These are gate names, not calendar promises.

### Final acceptance procedure

1. Freeze source commit.
2. Run all local and CI gates from clean checkout.
3. Build source distribution/wheel where applicable.
4. Install into clean environment.
5. Run full tests.
6. Build master ZIP.
7. Generate manifest, SBOM, provenance, checksums, and signatures.
8. Extract ZIP into a clean location.
9. Re-run release tests from extracted ZIP.
10. Independently verify signatures, hashes, manifests, and attestations.
11. Reopen every output file and record exact size/hash.
12. Copy to durable storage.
13. Reopen durable copies and verify again.
14. Produce a final truth report generated from machine state and evidence.
15. Obtain independent release-acceptor verdict.

### Final acceptance levels

- `ACCEPTED`
- `ACCEPTED_WITH_KNOWN_NON_BLOCKERS`
- `CONDITIONAL_ACCEPTANCE`
- `REJECTED`
- `PARTIAL_NOT_FINAL`

Only `ACCEPTED` or carefully justified `ACCEPTED_WITH_KNOWN_NON_BLOCKERS` may be labelled LAOS v8.0 final.

---

# 8. Immediate known blockers and their exact resolution

## Blocker A — Mutable SQLite DB included in immutable manifest

**Resolution:** Ship migrations, never an active DB. Separate immutable pack, static harness, runtime state snapshot, evidence, and release artifact manifests. Exclude `.laos/state/**`, WAL/SHM, logs, locks, temp, and `Evidence/**` from static-pack integrity. Snapshot state safely through SQLite backup/checkpoint logic when an audit requires a state artifact.

**Proof:** tests listed in Phase 3.

## Blocker B — Wrong exception class for unauthorised side-effect verification

**Resolution:** Centralize authorization. Return `AuthorizationDenied` / `LAOS-2000` before mutation, preserve state, and write a denied-attempt event.

**Proof:** exact exception, CLI code, no mutation, and audit-event tests.

## Blocker C — Evidence-manifest hardening not followed by a complete test run

**Resolution:** Make evidence-manifest validation a release gate. After merge, run the entire unit, integration, adversarial, end-to-end, and extracted-release suite. Preserve raw outputs and source commit hash.

**Proof:** final test report references the exact source and artifact hashes.

## Blocker D — Strongest controls from separate prior implementations not consolidated

**Resolution:** Because the prior source is not currently present, reconstruct every claimed control from the specification and accept it only after tests. Recovered code may accelerate work but cannot lower the proof standard.

## Blocker E — Docker/sandbox provider not verified

**Resolution:** Implement fail-closed provider abstraction and run real Docker integration tests on a Docker-enabled environment before final release. Until then, sandbox support remains `UNVERIFIED` and high-risk actions remain blocked.

## Blocker F — Real weaker-model improvement not measured

**Resolution:** Run the evaluation matrix in Phase 14. Publish raw methodology, model versions, tasks, complete traces, failures, and uncertainty. Do not claim orders-of-magnitude gains without evidence.

---

# 9. Dependency order

```text
Baseline
  ↓
Domain + state + error contracts
  ↓
Schemas + paths + fingerprints + seals
  ↓
Transactional state + identity + policy
  ↓
Pack separation + signatures + leak scan
  ↓
Action engine + criterion ledger
  ↓
Prompt compiler + model profiles
  ↓
Capture/continuation
  ↓
Command broker + sandbox + evidence
  ↓
Review + side effects + recovery
  ↓
Artifacts + provenance + CLI + migration
  ↓
Full tests + real-agent evaluation + red team
  ↓
Extracted, signed, durable release
```

Later layers may not compensate for a failed foundational gate.

---

# 10. Architecture decision records required

1. ADR-001: Architect-only trust model.
2. ADR-002: One-action-at-a-time execution.
3. ADR-003: Typed models and JSON Schema Draft 2020-12.
4. ADR-004: Canonical repository manifest algorithm.
5. ADR-005: Workspace seals and drift policy.
6. ADR-006: SQLite local state and external DB boundary.
7. ADR-007: Static pack versus mutable runtime-state separation.
8. ADR-008: Actor identity and capability tokens.
9. ADR-009: Action Capsule signing and key management.
10. ADR-010: Policy/risk model.
11. ADR-011: Command broker and shell policy.
12. ADR-012: Sandbox provider boundary.
13. ADR-013: Evidence CAS, maturity, and freshness.
14. ADR-014: Independent review and repair separation.
15. ADR-015: Side-effect lifecycle and approval.
16. ADR-016: Deterministic artifact and provenance model.
17. ADR-017: Model profiles and recalibration.
18. ADR-018: v7 migration policy.
19. ADR-019: Real-agent evaluation methodology.
20. ADR-020: Durable release storage and recovery.

---

# 11. Release-blocking test matrix

## Schema and model

- malformed JSON;
- wrong types;
- extra fields;
- missing required fields;
- duplicate IDs;
- broken references;
- unsupported schema version;
- invalid state;
- invalid hash/path/signature.

## Repository and filesystem

- one-byte drift;
- file add/delete/rename;
- mode change;
- symlink and junction escape;
- traversal;
- unsafe ZIP entries;
- ZIP bomb limits;
- pre-claim edit;
- hidden harness change;
- ignored mutable-state change.

## State and concurrency

- double claim;
- stale lease;
- replay;
- conflicting transition;
- concurrent event append;
- crash before/after commit;
- migration failure;
- backup/restore;
- WAL snapshot correctness.

## Action engine

- skip UNDERSTAND;
- skip PLAN;
- implement future work;
- expired capsule;
- wrong repository seal;
- wrong actor;
- out-of-scope change;
- attempt limit;
- repeated failed approach;
- manual state tampering;
- next-action leakage.

## Evidence and review

- missing/tiny/vague evidence;
- stale evidence;
- wrong criterion;
- changed source;
- secret/PII;
- fabricated metadata;
- missing receipt;
- builder self-review;
- reviewer edits code;
- hidden-test tampering;
- test weakening.

## Capture and continuation

- capture writes product code;
- repository changes mid-capture;
- incomplete categories;
- explicit unknowns;
- conflicting investigators;
- invalid signature;
- stale return;
- unaccepted return;
- delta recapture;
- continuation preservation rules.

## Commands and sandbox

- dangerous command;
- shell metacharacter injection;
- wrong cwd;
- environment leak;
- missing timeout;
- network denied;
- host escape;
- missing sandbox;
- secret available inside sandbox;
- provider failure.

## Side effects

- no approval;
- wrong actor;
- duplicate/replay;
- changed payload under same key;
- timeout after possible success;
- verification mismatch;
- compensation;
- manual reconciliation;
- credential expiry;
- correct `LAOS-2000` exception.

## Artifacts and release

- mutable DB accidentally packaged;
- secret in staging;
- cache or nested archive;
- nondeterministic ordering/timestamp;
- post-verification mutation;
- signature failure;
- SBOM mismatch;
- provenance mismatch;
- extracted self-test failure;
- missing deliverable;
- durable-storage loss simulation.

---

# 12. Risk register

| Risk | Consequence | Control |
|---|---|---|
| Over-engineering | LAOS becomes unusable | Risk-adaptive profiles, minimal portable mode, usability evaluation |
| Actions too small | Excessive overhead | Profile-based action sizing and safe gate compression |
| Actions too broad | Weaker agents skip | Compiler limits, calibration, measured skip rate |
| Lost implementation artifacts | Rework and false status | Durable storage, hashes, reopen verification, external source control |
| Hidden tests leak | Agents game checks | Physical separation, leak scan, private verifier storage |
| Sandbox unavailable | Unsafe host execution | Fail closed for high-risk actions |
| SQLite misuse | Corruption or false integrity | Transactions, WAL-aware backups, migration and crash tests |
| Signing key leak | False authority | External key storage, rotation, revocation, no keys in packs |
| Model changes | Profile becomes unsafe | Version binding and mandatory recalibration |
| Evidence growth | Storage burden | Content addressing, deduplication, retention policy |
| Policy false positive | Unnecessary blocks | Explainable decisions and signed amendments |
| Policy false negative | Unsafe authority | Default deny, property tests, independent red team |
| Existing-repo drift | Wrong continuation | Seals, delta capture, Architect reconciliation |
| Reviewer bias | False acceptance | Fresh Review Capsule, hidden checks, adversarial rubric |
| Evaluation gaming | Misleading results | Hidden/rotating tasks, blinded grading, complete traces |
| Documentation drift | Misuse | Docs tested against CLI and schemas; release docs generated from truth |

---

# 13. Definition of done

LAOS v8.0 is complete only when all of the following are true.

## Mission and authority

- Master LAOS is explicitly Architect-only everywhere.
- Weaker agents receive one project-specific action at a time.
- Future work and hidden checks are not exposed.

## Correctness

- One canonical fingerprint implementation is used everywhere.
- All external records receive strict structural and semantic validation.
- Static and mutable runtime manifests are correctly separated.
- Transaction and concurrency invariants pass.

## Anti-skip performance

- Required action order is enforced by runtime.
- Manual or prompt-level skipping cannot advance state.
- Every mandatory criterion is separately closed.
- Real-agent trials show material improvement.

## Security

- Path, symlink, archive, identity, replay, prompt-injection, skill, command, and sandbox tests pass.
- High-risk work cannot run without required isolation.
- Consequential side effects require brokered authority.
- No secrets appear in public packs, logs, evidence, or artifacts.

## Evidence and review

- Acceptance uses fresh runtime-captured evidence.
- Evidence manifest validation passes after final merge.
- Builder and reviewer identities are independent.
- Hidden/adversarial verification passes.

## Recovery

- Crash, checkpoint, restore, amendment, and repeated-failure flows pass.
- Lost sandbox does not lose authoritative control-plane state.

## Release integrity

- Source and extracted ZIP tests pass.
- Manifest, SBOM, provenance, checksums, and signatures verify.
- No active mutable database is included in immutable release content.
- Every final file exists in durable storage and is reopened before reporting.

## Documentation and migration

- All role guides are complete and consistent.
- v7 migration is tested and conservative.
- Limitations and residual risks are explicit.

---

# 14. Implementation method for the upgrade itself

The v8 rebuild should follow its own intended discipline:

1. The Strong Architect retains this complete plan.
2. Each engineering unit is converted into one bounded Action Capsule.
3. The weaker builder receives only that action, relevant files, checks, and stop conditions.
4. Every action creates evidence under repository-root `Evidence/`.
5. A separate verifier reruns checks.
6. A separate reviewer assesses the criterion.
7. The Architect issues the next action only after acceptance.
8. Repeated failures shrink the action or escalate; they do not produce a broader prompt.
9. Release work uses an artifact-only repair action when code is already correct and only packaging is defective.
10. No completion claim is made from memory or chat; it is generated from repository state and evidence.

---

# 15. Authoritative first build sequence

1. Preserve and hash v7.
2. Create clean v8 source repository and root `Evidence/`.
3. Import surviving design documents.
4. Write ADRs and formal domain/state/error contracts.
5. Add failing regressions for every known v7 defect.
6. Implement typed models and strict schemas.
7. Implement safe paths and archives.
8. Implement canonical manifests/fingerprints.
9. Implement workspace seals.
10. Implement SQLite state, migrations, transactions, claims, leases, and events.
11. Implement static/mutable manifest separation.
12. Implement state snapshot/restore.
13. Implement identity, sessions, capabilities, and signatures.
14. Implement policy and risk engine.
15. Implement stable error codes, including `LAOS-2000`.
16. Implement Architect, execution, capture, review, and release packs.
17. Implement leak scanning.
18. Implement Action Capsule issuance and verification.
19. Implement UNDERSTAND and PLAN gates.
20. Implement action sequencing and criterion ledger.
21. Implement model profiles, calibration, prompt compiler, and linter.
22. Rebuild capture, return validation, acceptance, and continuation.
23. Implement command broker.
24. Implement sandbox provider and fail-closed assurance policy.
25. Implement checks and automatic evidence collectors.
26. Implement evidence CAS, freshness, maturity, and final manifest validator.
27. Run full test suite after evidence merge.
28. Implement independent review, adjudication, and repair.
29. Implement side-effect broker and exact authorization behavior.
30. Implement checkpoints, recovery, amendments, and anti-thrashing.
31. Implement deterministic artifacts, SBOM, provenance, and signing.
32. Implement CLI and operator diagnostics.
33. Implement v7 importer and migration reports.
34. Complete role documentation and compatibility matrix.
35. Run cross-platform, sandbox, adversarial, and end-to-end tests.
36. Run real weaker-agent evaluations.
37. Build release candidate from clean checkout.
38. Extract and retest the ZIP.
39. Independently verify and sign all artifacts.
40. Copy to durable storage and reopen every file.
41. Produce machine-generated final truth report.
42. Obtain independent final acceptance.

---

# 16. Primary references informing the architecture

- OpenAI, “The next evolution of the Agents SDK,” 15 April 2026: https://openai.com/index/the-next-evolution-of-the-agents-sdk/
- OpenAI, “Migrate a Legacy Codebase with Sandbox Agents”: https://developers.openai.com/cookbook/examples/agents_sdk/sandboxed-code-migration/sandboxed_code_migration_agent
- Anthropic, “Harness design for long-running application development,” 24 March 2026: https://www.anthropic.com/engineering/harness-design-long-running-apps
- Anthropic, “Demystifying evals for AI agents,” 9 January 2026: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12
- SQLite Write-Ahead Logging: https://sqlite.org/wal.html
- SLSA Provenance v1.2: https://slsa.dev/spec/v1.2/provenance
- Sigstore in-toto attestations: https://docs.sigstore.dev/cosign/verifying/attestation/

---

## Final planning verdict

The correct path is not to patch two failing tests and call the old build v8. The correct path is to reconstruct a durable, testable codebase from v7 and the v8 specification, solve the two known defects as part of a coherent architecture, complete the unverified evidence work, validate a real sandbox provider, run real weaker-agent comparisons, and only then publish a signed, extracted, retested, durably stored `LAOS_v8.0_Complete_System.zip`.
