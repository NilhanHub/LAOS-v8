# LAOS v8.0 — Comprehensive Execution, Recovery, and Release Plan

**Plan date:** 2026-07-12  
**Plan status:** Approved planning baseline; this document does not claim that LAOS v8 has been implemented or released.  
**Primary owner:** Nilhan  
**Primary operator:** Highly capable Software Architect AI  
**Execution users:** Weaker investigation, implementation, testing, verification, and review agents  
**Authoritative v7 source:** `/mnt/data/LAOS_v7.0_Complete_System(1).zip`  
**Existing design input:** `/mnt/data/LAOS_v8_COLOSSAL_UPGRADE_MASTER_PLAN.md`

---

## 1. Current-state truth

The plan starts from what is physically present now, not from prior completion claims.

### 1.1 Confirmed surviving inputs

1. The original LAOS v7 ZIP remains available and must remain byte-for-byte untouched.
2. The 2,005-line LAOS v8 Colossal Upgrade Master Plan survives.
3. Four v8 documentation files survive:
   - `README.md`
   - `START_HERE_FOR_NILHAN.md`
   - `START_HERE_FOR_ARCHITECT_AI.md`
   - `docs/MASTER_V8_GUIDE.md`
4. The surviving v8 directory does not contain an implementation package, source modules, schemas, tests, examples, build scripts, or a release ZIP.
5. The four v8 documents refer to several files that do not yet exist, including capture-agent, implementation-agent, reviewer, security-model, sandbox, and limitations documents.

### 1.2 How previous v8 claims will be handled

- The prior statement that a fuller implementation passed 35 of 37 tests is treated as unverified historical information because the corresponding source and test artifacts do not survive.
- The two reported failures remain mandatory regression requirements:
  1. Static release verification must never include a live mutable SQLite database.
  2. Unauthorized side-effect verification must produce the correct, consistent authorization exception and denial record.
- No prior missing code will be assumed, reconstructed from memory as fact, or described as completed.

### 1.3 Verified v7 baseline facts

The v7 archive contains the compiler, capture tools, continuation compiler, runtime, 17 schemas, templates, role and skill assets, tests, and release evidence. Its release evidence records 14 passing tests. A clean v8 rebuild will preserve useful v7 behavior while replacing its weak trust and enforcement mechanisms.

---

## 2. Exact mission of LAOS v8

LAOS v8 is a private operating and prompt-compilation framework for a highly capable Software Architect AI.

The Architect AI uses LAOS to:

1. Understand a new product objective or an existing repository.
2. Make and preserve the important architecture, product, data, security, operational, and quality decisions.
3. Convert those decisions into extremely bounded, model-appropriate work.
4. Give a weaker agent only the context and authority required for one current action.
5. Prevent skipped gates, premature implementation, broad edits, fake completion, weak evidence, self-review, repeated failure loops, and unsafe external actions.
6. Accept progress only when current repository truth, automatic checks, evidence, and independent review agree.
7. Preserve durable project state so future stateless agents can continue safely.
8. Measure whether the harness actually improves weaker-agent performance.

The master LAOS framework, complete blueprint, future action graph, hidden checks, private evaluator rubrics, signing authority, and release authority must never be handed to the weaker execution agent.

---

## 3. Release objective

LAOS v8.0 is complete only when it is a real, installable, tested system that can safely support:

- New application compilation and execution.
- Existing-application capture, Architect validation, and continuation.
- One-action-at-a-time execution by weaker agents.
- Criterion-level verification and evidence.
- Independent review.
- Controlled recovery and amendments.
- Isolated command execution.
- Controlled external side effects.
- Deterministic release creation and independent verification.
- Real comparative weaker-agent evaluation.

A large prompt pack, documentation-only design, or partially implemented runtime is not LAOS v8.

---

## 4. Non-negotiable engineering principles

### 4.1 Architect-only master authority

The Architect sees the entire project. The weaker agent sees only the current signed Action Capsule and stable public rules.

### 4.2 One legal action at a time

Future actions must not merely be marked “do not start.” They must be absent or cryptographically unusable until issued.

### 4.3 Default deny

File writes, commands, network access, credentials, browser actions, side effects, and destructive operations are denied unless explicitly granted.

### 4.4 Machine truth outranks prose

Current repository state, runtime-captured observations, deterministic checks, and signed records outrank agent confidence, summaries, comments, and old chat.

### 4.5 Fail closed

Invalid schema, missing evidence, stale source, ambiguous identity, unavailable required sandbox, or policy uncertainty must block progress.

### 4.6 No fake production functionality

No mock, demo, placeholder, simulated, dry-run, or planned-but-unbuilt capability may be presented as real product functionality. Test doubles may exist only in clearly isolated test paths.

### 4.7 Workflow control is not OS isolation

LAOS controls authority and workflow. A container, VM, microVM, or managed sandbox controls what the agent process can actually access. High-risk work requires both.

### 4.8 Evidence before confidence

An assertion such as “it works” has no acceptance value unless it is tied to a criterion, a fresh source seal, a reproducible observation, and the required level of proof.

### 4.9 Adapt to the executor

Action size, prompt wording, repetition, examples, tool access, retry budget, and review depth must come from a versioned model profile.

### 4.10 No release by narrative

Completion is established by machine-readable release gates and independently verified artifacts, not by a final message.

---

## 5. Target trust architecture

```text
Nilhan
  │
  ▼
Highly capable Software Architect AI
  │ uses master LAOS privately
  ▼
Trusted Architect Control Plane
  ├── Complete blueprint and App Intelligence
  ├── Full task/action graph
  ├── Hidden checks and evaluator rubrics
  ├── Policy, risk, and approval rules
  ├── Transactional state and audit records
  ├── Pack/capsule signing authority
  └── Release authority
          │
          ▼
One signed, bounded Action Capsule
          │
          ▼
Weaker agent in an isolated workspace
          │
          ▼
Diffs, checks, evidence, receipts, and review
          │
          ▼
Trusted control plane accepts, rejects, repairs, or escalates
          │
          ▼
Next action is issued only after acceptance
```

### 5.1 Required physical separation

LAOS v8 must compile separate deliverables:

1. **Architect Control Pack** — private full truth.
2. **Agent Execution Pack** — stable minimal public runtime and rules.
3. **Current Action Capsule** — one expiring signed authority envelope.
4. **Capture Execution Pack** — read-only investigation workflow.
5. **Review Capsule** — independent verification context.
6. **Release Attestation Pack** — manifests, checksums, SBOM, provenance, signatures, tests, evaluations, and limitations.

The weaker-agent pack must be scanned for private-plan, hidden-check, future-action, credential, personal-data, and master-framework leakage before delivery.

---

## 6. Target repository architecture

```text
LAOS_v8.0/
├── pyproject.toml
├── README.md
├── START_HERE_FOR_NILHAN.md
├── START_HERE_FOR_ARCHITECT_AI.md
├── START_HERE_FOR_CAPTURE_AGENT.md
├── START_HERE_FOR_IMPLEMENTATION_AGENT.md
├── START_HERE_FOR_REVIEWER.md
├── LICENSE
├── src/laos/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli/
│   ├── config/
│   ├── domain/
│   ├── schemas/
│   ├── storage/
│   ├── events/
│   ├── identity/
│   ├── policy/
│   ├── repository/
│   ├── compiler/
│   ├── packs/
│   ├── actions/
│   ├── prompts/
│   ├── capture/
│   ├── continuation/
│   ├── commands/
│   ├── sandbox/
│   ├── evidence/
│   ├── review/
│   ├── side_effects/
│   ├── recovery/
│   ├── artifacts/
│   ├── attestations/
│   ├── observability/
│   ├── evals/
│   └── reporting/
├── resources/
│   ├── schemas/
│   ├── roles/
│   ├── model_profiles/
│   ├── adapters/
│   ├── skills/
│   ├── prompts/
│   ├── policies/
│   └── templates/
├── examples/
├── migrations/
├── tests/
│   ├── unit/
│   ├── property/
│   ├── integration/
│   ├── end_to_end/
│   ├── concurrency/
│   ├── security/
│   ├── packaging/
│   └── real_agent_evals/
├── docs/
├── scripts/
├── Evidence/
└── release/
```

### 6.1 Runtime state separation

The immutable LAOS release contains code, resources, schemas, migrations, templates, and documentation only.

It must not contain:

- `.laos/state.sqlite`
- `.laos/state.sqlite-wal`
- `.laos/state.sqlite-shm`
- Active locks or leases
- Runtime logs
- Current claims
- Live evidence indexes
- Generated project state
- Private signing keys

A project initializes its own mutable `.laos/` directory after installation. Runtime data is governed by a separate runtime-state policy and is never included in the static release manifest.

This is the definitive fix for the previously reported immutable-manifest-versus-SQLite conflict.

---

## 7. Canonical domain model

All trusted records must have strict, versioned models and Draft 2020-12 JSON Schemas generated or checked from one canonical model source.

Minimum entities:

- `Engagement`
- `ProjectBlueprint`
- `Requirement`
- `AcceptanceCriterion`
- `Task`
- `ActionDefinition`
- `ActionCapsule`
- `ActionAttempt`
- `WorkspaceSeal`
- `RepositoryManifest`
- `ActorIdentity`
- `CapabilityGrant`
- `ModelProfile`
- `PromptContract`
- `CheckDefinition`
- `CheckRun`
- `EvidenceObject`
- `EvidenceBinding`
- `ReviewRecord`
- `SideEffectRecord`
- `ApprovalRecord`
- `CheckpointRecord`
- `IncidentRecord`
- `AmendmentRecord`
- `CaptureRequest`
- `AppIntelligenceReturn`
- `CaptureAcceptanceRecord`
- `ContinuationPlan`
- `ArtifactRecord`
- `ReleaseRecord`
- `AttestationRecord`
- `EvaluationRun`

### 7.1 Schema rules

Every trusted schema must:

- Declare its schema dialect and version.
- Reject unknown fields where forward compatibility is not explicitly intended.
- Enforce ID patterns, enums, required fields, path formats, and cross-reference structure.
- Use explicit nullable fields instead of ambiguous omission.
- Carry a record version and migration policy.
- Reject duplicate logical IDs.
- Validate semantic relationships after structural validation.
- Produce precise machine-readable error locations.

---

## 8. Formal state machines

### 8.1 Engagement

```text
DRAFT → ARCHITECT_VALIDATED → COMPILED → SEALED → EXECUTING
→ VERIFYING → RELEASE_CANDIDATE → RELEASED
```

Terminal or corrective alternatives:

```text
BLOCKED | CANCELLED | SUPERSEDED | FAILED | RECAPTURE_REQUIRED
```

### 8.2 Task

```text
DEFINED → READY → ACTIVE → VERIFYING → REVIEWING → ACCEPTED → CLOSED
```

Alternatives:

```text
BLOCKED | REPAIR_REQUIRED | SUPERSEDED | CANCELLED
```

### 8.3 Action

```text
DRAFT → VALIDATED → ISSUED → CLAIMED → IN_PROGRESS → SUBMITTED
→ VERIFIED → ACCEPTED
```

Alternatives:

```text
REJECTED | EXPIRED | REVOKED | BLOCKED | REPAIR_REQUIRED | SUPERSEDED
```

### 8.4 Standard substantive action sequence

```text
UNDERSTAND → PLAN → IMPLEMENT/REPAIR → VERIFY → EVIDENCE → HANDOFF → REVIEW
```

No later action may be claimed until the predecessor is accepted or a signed amendment changes the sequence.

### 8.5 Acceptance criterion

```text
NOT_STARTED → IMPLEMENTED → VERIFIED → INDEPENDENTLY_REVIEWED → ACCEPTED
```

### 8.6 Side effect

```text
PROPOSED → APPROVAL_REQUIRED → APPROVED → PREPARED → EXECUTING
→ EXECUTED → EXTERNALLY_VERIFIED → COMMITTED
```

Terminal alternatives:

```text
DENIED | ABORTED | FAILED | COMPENSATED | MANUAL_RECONCILIATION
```

### 8.7 Release artifact

```text
PLANNED → BUILT → HASHED → EXTRACTED → RETESTED → ATTESTED → FROZEN → PUBLISHED
```

---

## 9. Program milestones

The work is ordered so that later features cannot hide an unsafe foundation.

# Milestone 0 — Recovery, baseline, and governance

### Objective

Create an immutable, reproducible starting point and stop relying on missing prior work.

### Work

1. Preserve the original v7 ZIP and record SHA-256, byte size, entry count, and safe-extraction manifest.
2. Create a fresh version-controlled v8 working repository; do not develop inside the extracted v7 directory.
3. Import the surviving master plan and four v8 documents as design inputs, not as implementation proof.
4. Record every known v7 defect and every prior claimed v8 failure as a regression issue.
5. Create an `Evidence/` directory at the v8 repository root.
6. Create architecture decision records for:
   - Trust-zone separation
   - Runtime-state separation
   - SQLite and migration strategy
   - Schema/model source of truth
   - Signing and identity
   - Sandbox provider interface
   - Release and provenance
7. Establish coding, typing, dependency, test, security, and release policies.
8. Create a requirements-to-workstream traceability ledger.
9. Create an explicit limitations register.
10. Verify that no current v8 implementation is claimed.

### Deliverables

- `BASELINE_MANIFEST.json`
- `RECOVERY_STATE.md`
- `REQUIREMENTS_LEDGER.json`
- `KNOWN_DEFECTS.md`
- `THREAT_MODEL_DRAFT.md`
- Architecture decision records
- Clean v8 source repository

### Exit gate

- Original v7 archive remains unchanged.
- Every known defect has a reproducible test description.
- No missing implementation is treated as present.
- The v8 build repository can be recreated from the recorded baseline.

---

# Milestone 1 — v7.0.1 emergency correctness branch

### Objective

Protect any continued v7 use while v8 is rebuilt and create shared regression fixtures.

### Work

1. Replace all repository fingerprints with one canonical implementation.
2. Use identical field order and ignore rules across capture, continuation, runtime, evidence, and release.
3. Add a fingerprint algorithm ID.
4. Enforce every existing JSON Schema with a real Draft 2020-12 validator.
5. Add semantic validation for references and workflow relationships.
6. Seal repository state before claims to block pre-claim edits.
7. Resolve and contain every filesystem path.
8. Reject symlink escapes and unsafe ZIP entries.
9. Remove or strictly gate `shell=True`.
10. Correct documentation overclaims and explain that LAOS is not an OS sandbox.
11. Add end-to-end unchanged-repository and one-byte-drift tests.
12. Add malformed-capture, path-traversal, pre-claim-edit, and symlink tests.

### Exit gate

- An unchanged captured repository passes continuation freshness verification.
- A one-byte tracked change fails.
- Malformed App Intelligence cannot pass.
- Pre-claim and symlink escape regressions are closed.
- v7.0.1 remains clearly distinct from v8.

---

# Milestone 2 — Typed v8 kernel and strict validation

### Objective

Build a small, composable, strongly validated core before recreating high-level workflows.

### Work

1. Create `pyproject.toml`, package layout, pinned dependency policy, and supported Python version range.
2. Implement typed domain models.
3. Generate or verify versioned JSON Schemas from the canonical models.
4. Implement a schema registry and semantic validators.
5. Implement a stable error hierarchy:
   - `LaosError`
   - `ValidationError`
   - `SecurityError`
   - `AuthorizationDenied`
   - `PolicyDenied`
   - `StateConflict`
   - `RepositoryDrift`
   - `EvidenceError`
   - `ReviewError`
   - `SideEffectError`
   - `ReleaseError`
6. Require all authorization failures to raise or return `AuthorizationDenied` with a stable error code.
7. Add structured logs and machine-readable result envelopes.
8. Add state and schema migration versioning.
9. Add property-based validation tests and malformed-input fuzzing.

### Mandatory regression

An unauthorized builder attempting external side-effect verification must:

- Be denied before any external operation.
- Produce `AuthorizationDenied` or its stable serialized equivalent.
- Record a security event.
- Leave the side-effect record unchanged except for the denied attempt audit entry.

### Exit gate

- All models, schemas, migrations, and error contracts pass unit and property tests.
- Unknown or malformed trusted records fail closed.
- Authorization errors are consistent across every subsystem.

---

# Milestone 3 — Repository truth, safe paths, identity, and transactional state

### Objective

Create trustworthy execution foundations that cannot be bypassed through timing, path tricks, concurrency, or self-declared identities.

### Work

#### Repository truth

1. Implement one canonical manifest algorithm covering regular files, symlink objects, byte size, SHA-256, mode, and Git truth where available.
2. Define one versioned ignore policy.
3. Detect additions, deletions, modifications, mode changes, link-target changes, and case collisions.
4. Sign workspace seals before weaker-agent work.
5. Bind every capsule, check run, evidence object, and review to a seal.
6. Make stale source automatically invalidate dependent proof.

#### Safe paths

7. Resolve paths and prove they remain inside the authorized root.
8. Reject absolute external paths, `..`, symlink/junction escapes, and unsafe archives.
9. Enforce read, write, test, evidence, artifact, and runtime areas separately.
10. Add safe extraction limits for entry count, total size, ratio, nesting, duplicate names, and case collisions.

#### Transactional state

11. Use SQLite as the default single-host canonical state store.
12. Enable foreign keys and transactional state transitions.
13. Use WAL where appropriate, while testing crash and checkpoint behavior.
14. Add schema migrations and backup/recovery tests.
15. Store tasks, actions, attempts, claims, leases, criteria, checks, evidence, reviews, approvals, side effects, artifacts, incidents, policies, and events in normalized tables.
16. Use unique constraints to prevent double claims and duplicate idempotency keys.
17. Use compare-and-swap version fields where needed.
18. Use database time or carefully bounded monotonic lease logic; do not rely only on untrusted agent wall-clock values.
19. Generate human-readable JSON/Markdown views from the database; never use them as canonical mutable state.

#### Identity and capabilities

20. Implement authenticated actor identities and short-lived capability grants.
21. Separate Architect, builder, investigator, tester, verifier, reviewer, approver, and release-verifier roles.
22. Store only token hashes or external identity references.
23. Support revocation and expiry.
24. Bind actions to actor, role, project, repository seal, policy version, nonce, and expiry.

### Exit gate

- Two workers cannot claim the same action.
- A changed repository cannot be hidden by claiming after the edit.
- Path and symlink escapes are denied.
- Actor-name spoofing cannot satisfy role separation.
- Crash/restart tests preserve valid state or fail safely.

---

# Milestone 4 — Policy engine and risk classification

### Objective

Turn permissions and safety rules into executable policy.

### Work

1. Define risk tiers such as low, moderate, high, and critical.
2. Define default-deny permissions for:
   - Filesystem reads/writes
   - Commands
   - Environment variables
   - Secrets
   - Network destinations
   - Browser actions
   - External systems
   - Side effects
3. Bind policy decisions to versioned policy digests.
4. Make issued capsules invalid when their policy or model profile changes.
5. Add human-approval requirements for irreversible or consequential operations.
6. Add critical-task quorum rules: at least two independent verifications or Architect adjudication where appropriate.
7. Add resource budgets for time, CPU, memory, processes, network, token use, and retry count.
8. Add circuit breakers for repeated failures and cascading errors.
9. Add taint labels for untrusted repository text, external content, user-provided data, and generated instructions.
10. Ensure repository content can never override signed control-plane instructions.

### Exit gate

- Every denied action is blocked by code, not merely documented.
- Policy changes revoke incompatible outstanding authority.
- Critical operations cannot proceed without the required approvals and isolation.

---

# Milestone 5 — Pack separation, signing, and leak prevention

### Objective

Compile physically separate trust-zone packages and prove private information cannot leak to weaker agents.

### Work

1. Implement Architect Control Pack compilation.
2. Implement Agent Execution Pack compilation.
3. Implement Capture Execution Pack compilation.
4. Implement Review Capsule compilation.
5. Implement single Action Capsule issuance.
6. Sign pack manifests and capsules using Ed25519 or an equivalent current mechanism.
7. Keep private signing keys outside generated packs.
8. Include public verification material only where needed.
9. Add capsule nonce, issue time, expiry, repository seal, actor binding, role, permissions, policy digest, profile digest, skill digest, and criteria.
10. Build a leak scanner for:
    - Future actions
    - Hidden checks
    - Architect-only notes
    - Master framework documents
    - Secrets and credentials
    - Personal or sensitive data
    - Private evaluator answers
11. Safely extract and independently verify every generated pack.
12. Add pack capability manifests that clearly state what the contained agent may and may not do.

### Exit gate

- The weaker-agent pack contains no future action graph or hidden checks.
- Modifying any signed pack or capsule causes verification failure.
- A capsule cannot be replayed against another project, actor, repository seal, policy version, or time window.

---

# Milestone 6 — Anti-Skip Action Engine

### Objective

Make skipping mandatory steps technically impossible or immediately detectable.

### Work

1. Implement the action graph and one-action issuance rule.
2. Allow only one current READY/ISSUED action in a dependent chain.
3. Implement structured `UNDERSTAND` submissions covering:
   - Objective
   - Criteria
   - Invariants
   - Non-goals
   - Preservation rules
   - Allowed and forbidden scope
   - Unknowns
   - Source references
   - Verification strategy
4. Reject vague understanding responses.
5. Implement structured `PLAN` submissions mapping every criterion to:
   - Files
   - Intended changes
   - Checks
   - Failure paths
   - Preservation checks
   - Evidence
   - Recovery or rollback
6. Reject incomplete plans or plans outside Architect-approved scope.
7. Implement action attempt budgets, stop conditions, and escalation.
8. Detect repeated failed approaches and prevent identical retry loops.
9. Require fresh sessions for profiles or risk tiers that need them.
10. Lock future actions until acceptance.
11. Support signed amendments that supersede outstanding authority while retaining history.
12. Add a non-interference analyzer before allowing parallel actions; parallelism requires disjoint writes, compatible reads, independent criteria, and no conflicting side effects.

### Exit gate

- A weaker agent cannot claim IMPLEMENT before UNDERSTAND and PLAN are accepted.
- A later action cannot be revealed or used early.
- A task cannot close with an incomplete mandatory criterion.
- Repeated identical failure triggers repair, reduction, recovery, or Architect escalation.

---

# Milestone 7 — Model profiles, prompt compiler, and context control

### Objective

Make Architect instructions appropriate for the actual weaker executor rather than sending one universal prompt style.

### Work

1. Define versioned profiles such as:
   - Fragile local desktop agent
   - Weak general desktop agent
   - Standard coding agent
   - Strong coding executor
   - Investigation specialist
   - Test verifier
   - Independent reviewer
2. Profiles control:
   - Files per action
   - Criteria per action
   - Prompt size
   - Instruction count
   - Repetition
   - Examples
   - Tools
   - Retry budget
   - Session freshness
   - Network policy
   - Review depth
3. Implement small real calibration actions.
4. Record observed compliance, skip rate, scope adherence, tool use, and evidence quality.
5. Reduce action size automatically when performance degrades.
6. Escalate tasks that exceed a profile’s demonstrated safety ceiling.
7. Implement a prompt linter that rejects missing role, goal, finish line, scope, checks, evidence, stop conditions, unavailable-tool handling, or final response format.
8. Detect contradictions, unresolved placeholders, excessive context, and accidental audit-to-write permission.
9. Create context manifests distinguishing:
   - Signed instruction
   - Trusted project truth
   - Evidence
   - Untrusted repository content
   - Untrusted external content
10. Compact handoffs without deleting blockers, conflicts, or uncertainty.
11. Add an explicit uncertainty ledger; unresolved facts stay unknown until resolved.

### Exit gate

- Every prompt snapshot passes linting.
- Each released profile has calibration evidence.
- Oversized work is decomposed automatically.
- A model profile cannot silently grant more authority than policy allows.

---

# Milestone 8 — Existing-application capture and continuation rebuild

### Objective

Let weaker investigators gather evidence without altering the application, then let the Architect form its own validated understanding before implementation.

### Work

1. Create strict `CaptureRequest` and `AppIntelligenceReturn` models.
2. Seal the repository before capture.
3. Issue read-only capture actions for:
   - Repository identity and environment
   - Architecture, components, and data
   - Features, UI, APIs, authentication, and authorization
   - Integrations and external systems
   - Commands, tests, build, deployment, and operations
   - Known defects, debt, protected areas, conflicts, and unknowns
4. Technically deny product-code edits, repairs, deployments, cloud changes, and external side effects during capture.
5. Require evidence references for every material claim.
6. Record confidence, contradictions, and unknowns explicitly.
7. Validate the return structurally, semantically, cryptographically, and against the original repository seal.
8. Require Architect acceptance or rejection of individual facts.
9. Create preservation rules and continuation constraints from accepted facts.
10. Compile continuation only against the unchanged accepted repository or after explicit recapture/amendment.
11. Use the exact same canonical fingerprint module in every stage.
12. Add real round-trip tests from capture through continuation to the first implementation capsule.

### Exit gate

- Capture cannot modify product code.
- A malformed or stale return cannot pass.
- The Architect acceptance record distinguishes accepted, rejected, conflicted, and unknown facts.
- An unchanged repository passes continuation verification; drift blocks it.

---

# Milestone 9 — Command broker, sandbox, and clean verifier

### Objective

Prevent weaker agents from obtaining arbitrary host authority and make every command reproducible and attributable.

### Work

1. Replace shell strings with structured executable-and-argument arrays.
2. Require explicit working directory, environment allowlist, timeout, resource limit, and network policy.
3. Deny dangerous operations by default, including destructive root deletion, privilege escalation, hard reset/clean, disk operations, and download-pipe-shell patterns.
4. Allow shell semantics only through a separately signed high-trust exception.
5. Stream output into immutable transcripts with size controls and secret redaction.
6. Implement provider interface for:
   - Local low-risk execution
   - Docker/container execution
   - Managed sandbox execution
   - Future microVM provider
7. High-risk actions must fail closed when no qualifying sandbox is available.
8. Mount only the intended repository and required ephemeral paths.
9. Run as non-root.
10. Keep credentials absent by default and inject short-lived secrets only for specifically approved commands.
11. Disable network by default; use an egress allowlist or broker.
12. Run acceptance checks in a clean verifier workspace separate from the builder’s mutable workspace.
13. Add sandbox conformance tests in CI where the required provider is available.

### Exit gate

- No general `shell=True` path exists for normal checks.
- A high-risk action cannot fall back silently to host execution.
- Commands, environment, outputs, exit status, and source seal are fully recorded.
- Clean verification detects builder-environment-only success.

---

# Milestone 10 — Evidence engine and criterion-level closure

### Objective

Replace agent-written completion claims with fresh, automatic, criterion-linked proof.

### Work

1. Create the repository-root `Evidence/` folder in every managed project.
2. Store canonical evidence in a broker-controlled, content-addressed area not writable by the builder; expose signed indexes or copies under `Evidence/`.
3. Automatically capture:
   - Commands
   - Working directories
   - Timestamps
   - Exit codes
   - Output hashes
   - Source seals
   - Repository diffs
   - Test results
   - Browser journeys
   - API interactions
   - Database before/after observations
   - Build and deployment verification
4. Define evidence levels:
   - L0 unsupported assertion
   - L1 runtime-captured observation
   - L2 deterministic automated proof
   - L3 independent proof
   - L4 externally attested proof
5. Assign a minimum evidence level per criterion and risk tier.
6. Invalidate evidence automatically when relevant source or policy changes.
7. Require every criterion to link to code/configuration, checks, evidence, and review.
8. Add negative evidence requirements for secrets, cross-scope data, unauthorized actions, fake integrations, hidden-test changes, and regressions.
9. Scan evidence for credentials and sensitive data.
10. Generate a claim-to-evidence matrix and outcome-closure ledger.
11. Ensure evidence manifests cannot reference missing, mutable, or out-of-scope objects.

### Exit gate

- A task cannot close on prose alone.
- Stale evidence is rejected.
- Every mandatory criterion has current proof at the required level.
- Evidence tampering or missing objects causes verification failure.

---

# Milestone 11 — Verification depth and independent review

### Objective

Verify real behavior, failure modes, invariants, preservation, and security independently of the builder.

### Work

1. Require relevant happy-path, invalid-input, missing-data, unauthorized, wrong-scope, duplicate, retry, timeout, partial-failure, and recovery checks.
2. Require every bug fix to include a regression check that catches the original defect.
3. Prevent builders from weakening, deleting, or rewriting protected tests.
4. Keep hidden checks outside builder write authority.
5. Create authenticated Review Capsules.
6. Ensure the reviewer is a different identity and usually a fresh context.
7. Give the reviewer the original criterion contract, final source, evidence, and authorized hidden checks—not a persuasive builder narrative.
8. Instruct reviewers to try to disprove completion.
9. Record a verdict for each criterion.
10. Prevent review actions from silently repairing product code.
11. Return defects to bounded repair actions.
12. Require Architect adjudication for disagreements.
13. Require dual review or quorum for critical tasks.

### Exit gate

- A builder cannot review or accept its own work.
- Review covers every mandatory criterion.
- Test weakening, hidden-check alteration, and unsupported evidence are detected.
- Critical-risk work satisfies quorum policy.

---

# Milestone 12 — Side effects, approvals, recovery, and anti-thrashing

### Objective

Control consequential external actions and make interruption or failure recoverable.

### Work

#### Side effects

1. Implement the full side-effect lifecycle.
2. Require proposer, approver, executor, independent verifier, idempotency key, payload digest, expected result, verification method, receipt, and compensation plan where applicable.
3. Prevent duplicate execution and replay.
4. Require human or governed approval for production deployment, spending, email/public publishing, data export, destructive migration, credential creation, and irreversible cloud operations.
5. Keep unauthorized attempts as auditable denial events.
6. Use the stable `AuthorizationDenied` contract for all role failures.

#### Recovery

7. Create immutable/content-addressed checkpoints before risky actions.
8. Scope checkpoints to authorized paths and record the repository seal.
9. Implement safe recovery that does not delete unrelated files.
10. Add claim leases and heartbeats.
11. Reclaim expired work safely.
12. Track failed-approach signatures.
13. Escalate repeated identical failures.
14. Support signed amendments, task reopening, recapture, and manual reconciliation.

### Exit gate

- Side effects cannot bypass approval, identity, idempotency, or external verification.
- Unauthorized verification produces the correct security exception and no state advance.
- Interrupted actions recover without losing accepted history.
- Repeated failure cannot loop indefinitely.

---

# Milestone 13 — Tamper-resistant events, artifacts, provenance, and release truth

### Objective

Make the release independently verifiable and prevent mutable runtime data from contaminating static integrity claims.

### Work

#### Event and provenance records

1. Append events transactionally.
2. Hash-chain event exports.
3. Sign critical decisions, packs, capsules, artifacts, and release records.
4. Anchor important event digests outside the working repository where possible.
5. Produce in-toto-compatible attestations and SLSA-style provenance.
6. Support Sigstore/Cosign or offline keys according to the release environment.

#### Static versus mutable separation

7. Define an immutable release inclusion policy.
8. Exclude all live runtime files, including SQLite databases, WAL/SHM files, locks, leases, logs, current evidence indexes, caches, and temporary output.
9. Ship only database migrations and initialization code.
10. Add tests proving that release manifests never include mutable runtime state.
11. Add tests proving that an extracted release initializes a new runtime database after installation.

#### Deterministic release build

12. Build source ZIP and wheel from a clean staging directory.
13. Exclude `.git`, caches, real environment files, secrets, nested releases, unrelated outputs, and live runtime data.
14. Generate a complete content manifest.
15. Generate an SBOM.
16. Build the release twice and compare where reproducibility is feasible.
17. Safely extract the ZIP into a second clean directory.
18. Run the full validation and test suite from the extracted ZIP.
19. Install the wheel in a fresh virtual environment and run smoke and resource tests.
20. Hash, sign, and attest the artifacts.
21. Freeze artifacts after verification.
22. Reopen and stat every claimed file before completion is reported.
23. Generate a machine-readable release summary from verified truth only.

### Mandatory regression tests

- `test_static_manifest_excludes_state_sqlite`
- `test_static_manifest_excludes_sqlite_wal_and_shm`
- `test_extracted_release_contains_no_live_runtime_database`
- `test_runtime_initializes_database_after_install`
- `test_post_build_artifact_mutation_fails_verification`
- `test_extracted_zip_full_suite_passes`

### Exit gate

- Source tree, release ZIP, extracted ZIP, installed wheel, manifests, SBOM, provenance, signatures, checksums, and reports agree.
- No mutable runtime state is inside the immutable package.
- Altering any protected artifact or attestation is detected.

---

# Milestone 14 — Real weaker-agent evaluation laboratory

### Objective

Prove what LAOS improves, identify where it fails, and adapt profiles from real traces rather than assumption.

### Comparison groups

1. Normal broad prompt.
2. Static structured prompt.
3. LAOS v7.
4. LAOS v8 action-controlled execution.
5. Stronger reference executor where useful.

### Benchmark families

- New application feature.
- Existing-application capture.
- Continuation change.
- Bug repair.
- Security-sensitive authorization feature.
- Data migration.
- UI journey.
- API integration.
- Deployment preflight.
- Recovery after interruption.
- Prompt-injection repository.
- Deliberately incomplete task.

### Metrics

- Full task success.
- Criterion closure.
- Skipped mandatory gates.
- Premature implementation.
- Out-of-scope changes.
- False completion accepted by harness.
- Test weakening.
- Evidence truthfulness.
- Failure-path coverage.
- Regression rate.
- Recovery success.
- Repeated failed approaches.
- Human interventions.
- Time, token, and cost consumption.
- Variance across repeated runs.

### Method

1. Use real agents and real tool execution.
2. Use repeated runs and fixed benchmark versions.
3. Keep hidden checks and grader rubrics outside the executor context.
4. Grade intermediate traces and tool calls, not only final responses.
5. Capture every failure as a regression candidate.
6. Version model profiles and detect model-behavior drift over time.
7. Separate technical release readiness from unproven marketing claims.

### Exit gate

- LAOS v8 demonstrates measurable improvement over broad-prompt and v7 baselines on the selected weaker-agent set.
- Any “orders-of-magnitude” claim is made only if the data supports it.
- Evaluation traces, graders, datasets, and summaries are included in the Release Attestation Pack without leaking sensitive project data.

---

# Milestone 15 — Documentation, migration, and operator experience

### Objective

Make correct use obvious to Nilhan, the Architect AI, weaker agents, reviewers, and release verifiers.

### Required documents

- `START_HERE_FOR_NILHAN.md`
- `START_HERE_FOR_ARCHITECT_AI.md`
- `START_HERE_FOR_CAPTURE_AGENT.md`
- `START_HERE_FOR_IMPLEMENTATION_AGENT.md`
- `START_HERE_FOR_REVIEWER.md`
- `MASTER_V8_GUIDE.md`
- `TRUST_AND_SECURITY_MODEL.md`
- `SANDBOX_REQUIREMENTS.md`
- `LIMITATIONS_AND_HUMAN_APPROVALS.md`
- `NEW_BUILD_WORKFLOW.md`
- `EXISTING_APP_CAPTURE_AND_CONTINUATION.md`
- `ACTION_CAPSULE_PROTOCOL.md`
- `EVIDENCE_AND_REVIEW.md`
- `SIDE_EFFECTS_AND_APPROVALS.md`
- `RECOVERY_AND_AMENDMENTS.md`
- `RELEASE_AND_PROVENANCE.md`
- `REAL_AGENT_EVALUATION.md`
- `MIGRATION_FROM_V7.md`
- `CLI_REFERENCE.md`
- `TROUBLESHOOTING.md`

### Usability work

1. Keep master and execution instructions visibly separate.
2. Use progressive disclosure for weaker agents.
3. Put the exact current action and stop conditions at the top of every execution prompt.
4. Provide one copy-pasteable prompt per agent action.
5. Explain what Nilhan gives to whom and what must never be shared.
6. Document source-of-truth order.
7. Keep limitations and unverified claims visible.
8. Provide migration tooling and reports for v7 blueprints, captures, and evidence where safe.
9. Ensure docs refer only to files that exist in the release.

### Exit gate

- Every role can follow its path without reading private material.
- Documentation has no broken internal references.
- The mission and trust separation are unmistakable in every entry point.

---

# Milestone 16 — Release candidate, red team, and durable publication

### Objective

Close all blockers through an independent final verification path.

### Work

1. Run all unit, property, integration, end-to-end, concurrency, security, sandbox, packaging, and evaluation suites.
2. Run static typing, linting, dependency audit, secret scan, and malicious-archive tests.
3. Perform an independent red-team review of:
   - Goal hijacking
   - Prompt injection
   - Tool misuse
   - Identity and privilege abuse
   - Memory/state poisoning
   - Insecure inter-agent communication
   - Cascading failure
   - Trust exploitation
   - Rogue or compromised executor behavior
4. Build final artifacts in a clean environment.
5. Extract and retest the ZIP.
6. Install and retest the wheel.
7. Verify sandbox conformance in an environment where the provider is actually available.
8. Verify signatures and attestations outside the build tree.
9. Confirm no private Architect material or secrets exist in execution packs.
10. Reopen the final ZIP, checksum, manifest, SBOM, provenance, release report, and summary.
11. Copy final deliverables to durable storage.
12. Produce a final release decision with limitations and evaluation results.

### Exit gate

Every release blocker in Section 13 is closed and every final artifact is physically present, reopened, hashed, and independently verified.

---

## 10. Cross-cutting security improvements

The following controls apply to every milestone:

1. **Prompt-injection boundary:** repository files, issue text, web pages, and tool output are untrusted data, never authority.
2. **Capability revocation:** outstanding capsules and tokens can be revoked immediately.
3. **Policy-drift guard:** capsule validity includes policy, model-profile, skill-registry, and repository-seal digests.
4. **Skill supply-chain security:** every skill and adapter has a version, hash, provenance, permissions, compatibility declaration, and tests.
5. **Secret lifecycle:** secrets are short-lived, scoped, redacted from transcripts, and never stored in packs or evidence.
6. **Data minimization:** execution packs contain only the data needed for the current role and action.
7. **Resource abuse prevention:** quotas and circuit breakers prevent denial-of-wallet and runaway work.
8. **Cascading-failure containment:** one failed agent or external system cannot automatically authorize broader work.
9. **Independent acceptance:** critical changes require role separation and, where appropriate, quorum review.
10. **No hidden downgrade:** unavailable verification or sandbox features produce BLOCKED, not a weaker silent fallback.
11. **Audit export:** a complete, signed, privacy-conscious trace can be exported for future Architect sessions and independent review.
12. **Schema evolution:** trusted records can be migrated explicitly; unknown future versions are never guessed.

---

## 11. Comprehensive test matrix

### 11.1 Schema and semantic validation

- Valid record accepted.
- Missing required field rejected.
- Wrong type rejected.
- Unknown field rejected where closed.
- Invalid enum or ID rejected.
- Duplicate ID rejected.
- Broken reference rejected.
- Invalid state transition rejected.
- Future unknown schema version rejected or routed to explicit migration.
- Malformed App Intelligence rejected.

### 11.2 Repository truth

- Same repository produces same manifest.
- One-byte change detected.
- Add, delete, rename, mode change, and symlink-target change detected.
- Case collision rejected.
- Ignore-policy change invalidates seal.
- Capture and continuation use the same algorithm.
- Pre-claim edit detected.
- Evidence/runtime directories do not invalidate product-source truth under the defined policy.

### 11.3 Paths and archives

- `..` traversal rejected.
- Absolute external path rejected.
- Symlink escape rejected.
- ZIP traversal rejected.
- Duplicate/case-colliding entries rejected.
- Symlink archive entry handled safely.
- Zip bomb and excessive-file-count protections enforced.
- Artifact collection cannot follow external links.

### 11.4 State and concurrency

- Double claim prevented.
- Lost update prevented.
- Duplicate idempotency key prevented.
- Lease expiry handled safely.
- Crash during transition rolls back or reconciles.
- Event append is serialized.
- Migration rollback and backup restore tested.
- Generated views cannot overwrite canonical state.

### 11.5 Identity and policy

- Self-declared actor name is insufficient.
- Expired/revoked token denied.
- Wrong role denied.
- Wrong project/seal denied.
- Policy change invalidates capsule.
- Builder cannot review itself.
- Unauthorized side-effect verification returns `AuthorizationDenied`.
- Denial produces an audit event and no state advance.

### 11.6 Action engine

- IMPLEMENT cannot precede accepted UNDERSTAND and PLAN.
- Future action unavailable.
- Capsule replay denied.
- Expired capsule denied.
- Missing criterion mapping denied.
- Attempt budget enforced.
- Repeated approach triggers escalation.
- Signed amendment supersedes old capsule.
- Parallel actions denied when interference is possible.

### 11.7 Pack separation

- Architect-only data absent from execution pack.
- Future tasks absent.
- Hidden checks absent.
- Private keys absent.
- Pack tampering detected.
- Leak scanner catches seeded secrets and hidden-answer text.
- Extracted pack verifies independently.

### 11.8 Capture and continuation

- Capture is read-only.
- Investigator cannot deploy or repair.
- Evidence-free claims rejected.
- Unknowns preserved.
- Stale capture rejected.
- Architect acceptance required.
- Unchanged continuation succeeds.
- Changed repository requires recapture or signed amendment.

### 11.9 Commands and sandbox

- Normal commands run without shell semantics.
- Dangerous command denied.
- Working-directory escape denied.
- Environment allowlist enforced.
- Timeout and resource limits enforced.
- Network denied by default.
- Missing required sandbox blocks high-risk action.
- Clean verifier catches local-state dependence.
- Secrets are redacted.

### 11.10 Evidence and review

- Evidence object hash verified.
- Missing object rejected.
- Stale evidence rejected.
- Wrong criterion binding rejected.
- Insufficient evidence level rejected.
- Test weakening detected.
- Reviewer product-code write denied.
- Critical review quorum enforced.
- Claim-to-evidence matrix matches final criterion ledger.

### 11.11 Side effects and recovery

- Approval required where policy says so.
- Replay and duplicate execution prevented.
- External verification requires independent role.
- Failed operation remains uncommitted.
- Compensation record required where applicable.
- Checkpoint restore preserves unrelated files.
- Expired claim safely reclaimed.
- Recovery retains accepted audit history.

### 11.12 Release and provenance

- Static manifest excludes SQLite, WAL, SHM, locks, logs, and active state.
- Runtime database initializes after install.
- Deterministic build comparison performed.
- Secret scan passes.
- SBOM generated and validates.
- ZIP extraction is safe.
- Extracted ZIP runs full suite.
- Wheel installs in clean environment.
- Signature and attestation verify externally.
- Post-build mutation is detected.
- Every claimed final file is reopened and hashed.

### 11.13 Real-agent evaluation

- Multiple agents and repeated runs.
- Fixed datasets and hidden graders.
- Trace-level grading.
- Skip, scope, false-completion, evidence, regression, recovery, and cost metrics.
- Model-profile drift detection.
- No simulated execution presented as real evaluation.

---

## 12. Absolute release blockers

LAOS v8.0 must not be released while any of the following is true:

1. Master LAOS, future actions, hidden tests, private evaluator answers, or Architect notes can leak to a weaker agent.
2. A weaker agent can obtain or use the next action early.
3. A malformed trusted record can enter canonical state.
4. Capture and continuation fingerprints disagree.
5. Pre-claim repository drift can be hidden.
6. Path, archive, or symlink escape remains possible.
7. Two workers can claim or advance the same action.
8. Typed actor names can impersonate independent roles.
9. A builder can review or accept its own work.
10. A mandatory criterion can close without fresh evidence.
11. Hidden or protected tests can be altered by the builder.
12. A dangerous command can run through an unrestricted host shell.
13. High-risk execution silently proceeds without a real sandbox.
14. External side effects can bypass approval, idempotency, or independent verification.
15. Unauthorized side-effect verification raises the wrong error class or changes state.
16. Live SQLite runtime files appear in the immutable release or its content manifest.
17. Evidence or artifact mutation can pass undetected.
18. The release ZIP cannot be safely extracted and fully retested.
19. The installed wheel cannot initialize and verify its bundled resources.
20. Secrets or private Architect material exist in execution deliverables.
21. Required documentation points to nonexistent files.
22. Critical security findings remain open.
23. Real-agent evaluation has not been run, if performance claims are included.
24. Final deliverables are not physically present in durable storage and reopened before the release declaration.

---

## 13. Definition of done

LAOS v8.0 is done only when all of the following are true:

### Mission

- The Architect-only mission is clear in every entry point.
- Weaker agents receive only minimal public context and one current capsule.

### Correctness

- Strict schemas and semantic validation are universal.
- Canonical fingerprinting passes complete round trips.
- Transactional state and concurrency tests pass.

### Anti-skip behavior

- Mandatory action order is enforced.
- Every criterion is independently tracked and proven.
- Attempts, stop conditions, and escalation work.

### Security

- Paths, archives, identities, policies, commands, sandboxes, secrets, skills, and side effects are enforced by code.
- Threat-model and red-team findings are closed or explicitly accepted with documented residual risk.

### Evidence and review

- Evidence is automatic, current, criterion-linked, and tamper-evident.
- Review is authenticated and independent.

### Recovery

- Crashes, expired claims, failed approaches, checkpoints, amendments, and recapture are tested.

### Release integrity

- No live runtime state exists in static artifacts.
- ZIP and wheel are independently verified.
- Manifests, SBOM, provenance, signatures, checksums, reports, and summaries agree.
- Final artifacts are reopened from durable storage.

### Performance

- Real-agent evaluations quantify improvement and limitations.
- No unsupported “orders-of-magnitude” claim is made.

### Documentation

- All required documents exist, are internally consistent, and contain no broken references.
- Migration from v7 is tested and explained.

---

## 14. Recommended implementation order

The first build sequence should be executed in this exact dependency order:

1. Freeze and hash v7.
2. Create clean v8 repository and Evidence folder.
3. Record requirements, defects, threat model, and ADRs.
4. Turn every known defect into a failing regression test.
5. Implement package skeleton and stable error hierarchy.
6. Implement canonical models and strict schemas.
7. Implement schema migrations and semantic validators.
8. Implement safe paths and safe archive handling.
9. Implement canonical repository manifests and workspace seals.
10. Implement SQLite state, migrations, transactions, events, claims, and leases.
11. Implement authenticated identities and capabilities.
12. Implement policy and risk engine.
13. Implement signing and authority envelopes.
14. Implement Architect, execution, capture, and review pack separation.
15. Implement leak scanning.
16. Implement Action Capsules and one-action issuance.
17. Implement UNDERSTAND and PLAN gates.
18. Implement criterion ledger and acceptance rules.
19. Implement model profiles, calibration, and prompt linter.
20. Rebuild existing-app capture and continuation.
21. Implement command broker.
22. Implement sandbox provider interface and at least one real tested provider.
23. Implement automatic evidence and clean verification.
24. Implement independent review and critical quorum.
25. Implement side-effect broker and approvals.
26. Implement checkpoints, recovery, amendments, and anti-thrashing.
27. Implement event signatures, provenance, and attestations.
28. Implement deterministic ZIP/wheel release pipeline with static/runtime separation.
29. Implement real-agent evaluation laboratory.
30. Complete documentation, migration, and CLI.
31. Run full red team and release candidate verification.
32. Reopen all final deliverables from durable storage before declaring completion.

---

## 15. New improvements added beyond the earlier master plan

The following refinements should be explicitly added to v8:

1. **No runtime database in any release artifact:** only migrations and initialization code ship.
2. **Stable security exception contract:** every authorization denial uses one typed hierarchy and machine-readable code.
3. **Authority Envelope:** every capsule is bound to actor, role, project, seal, policy, model profile, skills, nonce, and expiry.
4. **Uncertainty Ledger:** unknown facts cannot silently become assumptions or requirements.
5. **Context provenance labels:** agents can distinguish signed instructions, trusted truth, evidence, and untrusted content.
6. **Capability revocation:** a compromised or obsolete capsule can be invalidated immediately.
7. **Policy/model/skill drift guard:** changes invalidate incompatible outstanding capsules.
8. **Non-interference analysis:** parallel work is allowed only when independence is proven.
9. **Critical-task quorum:** high-impact work can require two independent verifiers or Architect adjudication.
10. **Secret lifecycle controls:** ephemeral injection, redaction, and non-persistence.
11. **Resource and cost circuit breakers:** prevent runaway attempts and denial-of-wallet.
12. **Degradation without deception:** unavailable components block affected actions rather than silently weakening assurance.
13. **Replayable trace bundles:** checks and decisions can be independently reconstructed where technically feasible.
14. **Schema/version migration discipline:** no guessing when trusted record formats evolve.
15. **Profile drift monitoring:** model behavior is recalibrated as providers and models change.
16. **Evidence escrow:** canonical proof is held outside the builder’s write authority while a signed project-facing index remains under the root `Evidence/` folder.
17. **External release verification:** signatures and attestations must be verifiable outside the build workspace.
18. **Artifact durability gate:** existence, stat, hash, extraction, and retest are performed after the artifact is moved to its final durable location.

---

## 16. Program risk register

| Risk | Consequence | Required mitigation |
|---|---|---|
| Scope becomes too large | Endless rebuild | Milestone gates; no later work before foundation passes |
| Framework becomes too complex | Weaker agents and operators fail to use it | Progressive disclosure; one action; small composable modules |
| Overcontrol slows simple work | Excessive friction | Risk-tiered profiles and low-risk fast path without weakening core truth |
| False sense of security | Unsafe high-risk use | Clear OS-sandbox boundary and tested provider requirement |
| State corruption or races | Invalid project truth | Transactions, constraints, backups, crash tests, external DB option |
| Prompt injection | Goal hijack or tool misuse | Signed authority, untrusted-content labels, default deny |
| Hidden information leaks | Weaker agent gains plan/evaluator answers | Physical pack separation and leak scanner |
| Agent/model behavior changes | Profiles become unsafe | Versioned calibration and drift monitoring |
| Evidence storage grows without bound | Cost and maintenance burden | Content addressing, deduplication, retention policy, summaries |
| Release artifact disappears | Work is lost or falsely claimed | Durable storage, reopen/hash/extract gates, optional external publication |
| Sandbox unavailable | High-risk tests unverified | CI/managed provider requirement; fail closed |
| Real-agent eval unavailable | Performance claim unproven | Release limitations remain explicit; no unsupported numerical claim |
| Cryptographic keys share compromised host | Provenance weak | External KMS/OIDC or offline key; external anchor/verifier |
| Test suite becomes slow or flaky | False confidence and poor iteration | Test tiers, deterministic fixtures, time budgets, flake quarantine with no silent ignore |

---

## 17. Release outputs

The final durable release set must include:

- `LAOS_v8.0_Complete_System.zip`
- `LAOS_v8.0_Complete_System.zip.sha256`
- Python wheel
- Source archive
- Content-integrity manifest
- SBOM
- Provenance statement
- Signature/attestation envelope
- Full automated test report
- Extracted-release test report
- Sandbox conformance report
- Security and red-team report
- Real-agent evaluation report
- Migration report
- Known limitations
- Machine-readable release summary
- Final human-readable release report

No completion statement may be issued until each listed file that is claimed has been reopened from its final storage path and verified.

---

## 18. Final execution rule

The upgrade must proceed as a sequence of verified milestones, not as one enormous generation.

At the end of every milestone:

1. Run its defined tests.
2. Record evidence under the root `Evidence/` folder and in the protected canonical evidence store.
3. Update the requirements ledger.
4. Perform an independent review.
5. Freeze the milestone result with hashes.
6. Begin the next milestone only after the exit gate passes.

That process is itself the first real proof that LAOS v8 follows the discipline it is designed to impose on weaker agents.
