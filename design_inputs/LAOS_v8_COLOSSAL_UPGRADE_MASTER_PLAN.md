# LAOS v8.0 Colossal Upgrade Master Plan

**Working title:** Architect-Controlled Anti-Skip Agent Operating System  
**Source baseline:** `LAOS_v7.0_Complete_System(1).zip`  
**Plan status:** Proposed; no v8 implementation is claimed by this document  
**Primary owner:** Nilhan  
**Primary system user:** Highly capable Software Architect AI  
**Execution users:** Weaker investigation, implementation, testing, review, and verification agents  

---

## 1. Executive decision

LAOS v8 should not be a larger prompt pack. It should be a **trusted control plane** used by a highly capable Software Architect AI to translate its project understanding into small, signed, enforceable, project-specific actions that weaker agents can execute safely.

The central redesign is:

> **The Architect sees the whole project. A weaker agent sees only the one action it is authorised to perform now. The runtime—not the agent—decides whether that action is complete and whether the next action may be revealed.**

LAOS v7 already contains valuable foundations: project-pack compilation, capture and continuation workflows, task state, checks, evidence, review, side-effect records, checkpoints, artifact verification, and documentation. Those concepts should be retained. The upgrade should replace the fragile parts: document-heavy execution, task-level rather than action-level control, mutable file state, inconsistent fingerprints, weak schema enforcement, procedural identity, host-shell execution, and insufficient real-agent evaluation.

This is a major-version rebuild because it changes the trust model, storage model, pack format, runtime protocol, and execution workflow.

---

## 2. Exact mission of LAOS v8

LAOS v8 exists to let a strong Software Architect AI:

1. Fully understand Nilhan's intended product or an existing repository.
2. Make and preserve the important architectural, product, security, data, operational, and quality decisions.
3. Convert those decisions into bounded work that is appropriate for the specific weaker agent being used.
4. Reveal only the minimum context and authority needed for the current action.
5. Prevent skipped steps, premature implementation, broad unauthorised edits, fake completion, weak evidence, self-review, repeated failure loops, and unsafe external actions.
6. Verify progress through independent, machine-captured evidence rather than persuasive agent prose.
7. Preserve enough durable state for another stateless agent or Architect session to continue reliably.
8. Measure whether the harness actually improves weaker-agent performance and continuously improve it from real traces and failures.

LAOS does **not** claim to transfer the raw intelligence of a stronger model into a weaker model. It should instead make the strong Architect's decisions explicit, constrain the weaker agent's freedom, improve the agent-computer interface, and catch failures before they become accepted project truth.

---

## 3. Non-negotiable design principles

### 3.1 Architect-only master authority

- Master LAOS, the full architecture, future task graph, hidden tests, evaluator rubrics, risk decisions, signing authority, and release authority remain with the strong Architect/control plane.
- Weaker agents never receive the reusable master LAOS framework.
- Weaker agents never receive the private Architect Control Pack.
- Weaker agents never receive future actions merely because those actions exist.
- The Architect records decisions, assumptions, evidence, and concise rationale; LAOS must not depend on inaccessible private chain-of-thought.

### 3.2 One legal action at a time

- Every execution agent receives one Action Capsule.
- The capsule authorises one coherent action, not the whole project or task.
- Later actions remain unavailable until the current action is accepted.
- The runtime enforces sequence and scope; prompts merely explain it.

### 3.3 Default deny

Anything not explicitly allowed is denied, including file writes, commands, environment variables, secrets, network destinations, browser actions, external writes, deployments, and destructive operations.

### 3.4 Machine truth outranks agent claims

The order of trust is:

1. Current directly observed repository and external-system state.
2. Runtime-captured checks and evidence tied to a fresh workspace seal.
3. Signed Architect decisions and approved amendments.
4. Structured capture records with evidence.
5. Human or agent narrative.
6. Old chat, README claims, comments, and prior-agent summaries.

### 3.5 No fake production functionality

No simulated, mock, demo, placeholder, dry-run, local-only wrapper, or planned-but-unbuilt capability may be presented as production functionality. Test doubles may exist only inside isolated test paths and must be labelled as test-only.

### 3.6 Fail closed

- Invalid schema: fail.
- Missing evidence: fail.
- Unavailable required tool: blocked, not passed.
- Repository drift: stop and reconcile.
- Identity ambiguity: deny.
- Policy ambiguity: deny or escalate.
- Sandbox unavailable for a required risk tier: block.

### 3.7 Separate workflow control from operating-system isolation

LAOS controls project workflow and authority. A sandbox, disposable VM, or equivalent execution environment controls what a weaker agent process can actually access. High-risk use requires both.

### 3.8 Evidence before confidence

Every acceptance claim must identify the criterion, the observed behaviour, the exact source state, the collector, and the proof. Agent confidence is not evidence.

### 3.9 Adapt to the executor

Action size, prompt structure, repetition, examples, permitted tools, review intensity, and retry limits must be selected from a versioned model/agent profile rather than assuming all weaker agents behave alike.

### 3.10 Continuous measurement

No marketing claim such as “orders-of-magnitude improvement” is accepted without comparative, repeated, real-agent evaluation.

---

## 4. Target operating model

```text
Nilhan
  │
  │ approved objective / change / constraints
  ▼
Highly capable Software Architect AI
  │
  │ uses master LAOS privately
  ▼
Trusted LAOS Control Plane
  ├── Architect Control Pack (private full truth)
  ├── Policy and risk engine
  ├── Transactional state and audit store
  ├── Hidden checks and evaluator rubrics
  ├── Evidence and release authority
  └── Action Capsule compiler
          │
          ├── Capture Capsule ─────► weaker investigation agent
          ├── Build Capsule ───────► weaker implementation agent
          ├── Verify Capsule ──────► test/verification agent
          └── Review Capsule ──────► independent reviewer
                                      │
                                      ▼
                            Isolated execution workspace
                                      │
                                      ▼
                     Checks, evidence, diff, receipts, artifacts
                                      │
                                      ▼
                         Control plane accepts or rejects action
                                      │
                                      ▼
                              Next action unlocked
```

### 4.1 Supported engagement paths

#### New application

`Nilhan → Architect + master LAOS → private complete design → compiled task/action graph → one capsule at a time → verified release`

#### Existing or mid-build application

`Nilhan → Architect + master LAOS → capture plan → read-only capture capsules → App Intelligence Return → Architect validation and reconciliation → continuation graph → one implementation capsule at a time → verified release`

#### Repair/recovery

`Architect intake → workspace and incident seal → forensic capture → repair graph → bounded repair actions → regression and recovery proof`

#### Audit-only

`Architect audit contract → read-only capsules → evidence-backed findings → no product-code write permission`

#### Deployment-only

`Architect deployment contract → preflight checks → approval → side-effect broker → external verification → release receipt`

---

## 5. Required pack separation

LAOS v8 should produce physically separate deliverables.

### 5.1 Architect Control Pack — private

Contains:

- Full project blueprint and requirement graph.
- Complete future task and action graph.
- Hidden acceptance answers and evaluator rubrics.
- Hidden and adversarial checks.
- Risk assessments and policy decisions.
- Preservation and regression contracts.
- Capture truth and unresolved conflicts.
- Model profiles and decomposition rationale.
- Human-approval requirements.
- Release plan and attestation configuration.
- Public keys and identity configuration; never private signing keys.

This pack must never enter the weaker agent's writable workspace.

### 5.2 Agent Execution Pack — public/minimal

Contains only:

- Minimal runtime client.
- Public project invariants that always apply.
- Current repository identity and approved workspace seal.
- Public verification commands the agent is allowed to know.
- Current role rules.
- Selected, signed skills required for the current work.
- No master LAOS documents.
- No future actions.
- No hidden checks.
- No private evaluator rubrics.

### 5.3 Action Capsule — ephemeral authority

Contains:

- Capsule ID, action ID, task ID, pack ID, sequence number, nonce, issue time, expiry, and signature.
- Exactly one objective.
- Required input context and source references.
- Acceptance criteria addressed by this action.
- Allowed and forbidden paths.
- Exact permissions and tool capabilities.
- Required output schema.
- Required checks and evidence.
- Stop conditions and maximum attempts.
- Handoff format.
- No later action information.

### 5.4 Capture Execution Pack

A separate, read-only pack for existing-app investigation. It must not contain implementation authority.

### 5.5 Review Capsule

Contains the original criterion contract, final diff/state, evidence, public and hidden verification instructions, and an adversarial review mission. It should omit persuasive builder commentary where that commentary could bias the reviewer.

### 5.6 Release Attestation Pack

Contains final manifests, checksums, SBOM, provenance, signatures, test and evaluation reports, release decisions, and known limitations.

### 5.7 Leak scanner

Every public pack must be scanned before delivery for:

- Master LAOS documents.
- Architect-only files.
- Future action IDs or descriptions.
- Hidden tests and expected answers.
- Private keys, tokens, secrets, or secret values.
- Internal evaluator rubrics.
- Unapproved source snapshots.
- Stale files from a previous compilation.

A leak scan failure blocks delivery.

---

## 6. Target repository architecture

The single large runtime and compiler scripts should become a typed package with clear boundaries.

```text
LAOS_v8/
├── pyproject.toml
├── dependency.lock
├── src/laos/
│   ├── cli/
│   ├── domain/
│   ├── schemas/
│   ├── compiler/
│   ├── packs/
│   ├── policy/
│   ├── identity/
│   ├── state/
│   ├── events/
│   ├── fingerprint/
│   ├── paths/
│   ├── actions/
│   ├── prompts/
│   ├── profiles/
│   ├── capture/
│   ├── continuation/
│   ├── execution/
│   ├── commands/
│   ├── sandbox/
│   ├── evidence/
│   ├── criteria/
│   ├── review/
│   ├── side_effects/
│   ├── checkpoints/
│   ├── artifacts/
│   ├── attestations/
│   ├── telemetry/
│   ├── evals/
│   └── adapters/
├── schemas/generated/
├── policies/default/
├── templates/
│   ├── architect/
│   ├── executor/
│   ├── capture/
│   └── reviewer/
├── skills/
├── adapters/
├── migrations/v7/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   ├── concurrency/
│   ├── security/
│   ├── end_to_end/
│   ├── release/
│   └── real_agent_evals/
├── formal/
├── docs/
└── release/
```

### 6.1 Mapping from v7

| v7 component | v8 destination |
|---|---|
| `laos_runtime.py` | Split across `state`, `events`, `actions`, `commands`, `evidence`, `review`, `side_effects`, `artifacts`, and `cli` |
| `tools/compile_project_pack.py` | Typed compiler pipeline under `compiler` and `packs` |
| `tools/capture_runtime.py` | Read-only capture service under `capture` using shared fingerprint/path/schema libraries |
| `tools/compile_capture_pack.py` | Capture pack compiler |
| `tools/validate_return_pack.py` | Strict return validator with schema, signature, manifest, and evidence checks |
| `tools/compile_continuation_pack.py` | Continuation compiler that consumes an Architect-accepted capture record |
| `schemas/*` | Strict, versioned Draft 2020-12 schemas generated from canonical domain models |
| `project_pack_assets/roles` | Versioned role profiles selected by compiler |
| `project_pack_assets/adapters` | Versioned executor adapters with tested capability declarations |
| `project_pack_assets/skills` | Signed skill registry with permission and provenance manifests |
| File-based `.laos/state` | Transactional database plus human-readable exports |
| Broad `START_HERE.md` workflow | Minimal entry point that requests the current signed capsule |
| Task packet with eleven advisory steps | Enforced sequence of micro-actions |

---

## 7. Canonical domain model

All external and stored records must be represented by strict, versioned domain models. Unknown fields should be rejected unless an extension point is explicitly declared.

### 7.1 Required primary entities

- `Engagement`
- `ProjectSpec`
- `Requirement`
- `AcceptanceCriterion`
- `Invariant`
- `NonGoal`
- `RiskAssessment`
- `Task`
- `ActionDefinition`
- `ActionCapsule`
- `ActionAttempt`
- `ModelProfile`
- `AgentAdapter`
- `SkillManifest`
- `PermissionGrant`
- `PolicyDecision`
- `WorkspaceSeal`
- `RepositoryManifest`
- `ActorIdentity`
- `ActorSession`
- `ClaimLease`
- `CheckDefinition`
- `CheckExecution`
- `EvidenceRecord`
- `CriterionClosureRecord`
- `ReviewRecord`
- `SideEffectOperation`
- `ApprovalRecord`
- `CheckpointRecord`
- `ArtifactRecord`
- `AttestationRecord`
- `CaptureFact`
- `CaptureConflict`
- `CaptureAcceptanceRecord`
- `Amendment`
- `IncidentRecord`
- `EvaluationRun`
- `Event`

### 7.2 Schema rules

- JSON Schema Draft 2020-12.
- Every schema declares `$schema`, `$id`, title, version, and description.
- Closed by default using `additionalProperties: false` or `unevaluatedProperties: false` as appropriate.
- Strict types; no silent string-to-number or object-to-list conversion.
- Stable ID patterns.
- Normalised relative path formats.
- Enumerated states.
- Date-time format validation.
- Digest format validation.
- Cross-record referential integrity checked after structural validation.
- Semantic migrations for every breaking schema change.
- Golden fixture and negative fixture for every schema.
- The validator returns machine-readable error paths and human-readable explanations.

### 7.3 One source of truth for models and schemas

Use strict typed domain models as the canonical internal representation and generate external JSON Schemas from them. Add parity tests proving that:

- Every valid model serialisation validates against the generated schema.
- Every negative fixture is rejected by both model parsing and schema validation.
- Generated schemas are deterministic and checked into source control.

---

## 8. State machines

### 8.1 Project lifecycle

`DRAFT → ARCHITECT_VALIDATED → COMPILED → SEALED → EXECUTING → VERIFYING → RELEASE_CANDIDATE → RELEASED`

Special states:

`BLOCKED`, `NEEDS_RECAPTURE`, `NEEDS_AMENDMENT`, `QUARANTINED`, `ABORTED`, `SUPERSEDED`.

### 8.2 Task lifecycle

Task status should be **derived** from child action and criterion state rather than manually advanced by the agent.

`DEFINED → READY → ACTIVE → IMPLEMENTED → VERIFIED → REVIEWED → CLOSED`

The runtime computes these states. Agents cannot directly set them.

### 8.3 Action lifecycle

`LOCKED → READY → ISSUED → CLAIMED → EXECUTING → SUBMITTED → VERIFYING → ACCEPTED`

Special states:

`EXPIRED`, `BLOCKED`, `REJECTED`, `REPAIR_REQUIRED`, `NEEDS_ARCHITECT`, `CANCELLED`, `SUPERSEDED`.

### 8.4 Standard action sequence within a substantive task

1. `UNDERSTAND`
2. `PLAN`
3. `IMPLEMENT`
4. `VERIFY`
5. `EVIDENCE`
6. `HANDOFF`
7. Independent `REVIEW`
8. Optional `REPAIR`
9. `ACCEPT`

Lower-risk work may combine `VERIFY` and `EVIDENCE`; high-risk work may add security, migration, deployment, or recovery actions. The compiler decides from risk and executor profile.

### 8.5 Acceptance criterion lifecycle

`NOT_STARTED → ADDRESSED → OBSERVED → INDEPENDENTLY_VERIFIED → ACCEPTED`

Special states:

`FAILED`, `INCONCLUSIVE`, `DEFERRED_BY_APPROVAL`, `SUPERSEDED`.

No task can close while a mandatory criterion is below `ACCEPTED`.

### 8.6 Review lifecycle

`REQUESTED → ASSIGNED → IN_PROGRESS → VERDICT_RECORDED → ADJUDICATED`

### 8.7 Side-effect lifecycle

`PROPOSED → APPROVAL_REQUIRED → APPROVED → PREPARED → EXECUTING → EXECUTED → EXTERNALLY_VERIFIED → COMMITTED`

Terminal alternatives:

`DENIED`, `ABORTED`, `FAILED`, `COMPENSATED`, `MANUAL_RECONCILIATION_REQUIRED`.

### 8.8 Artifact lifecycle

`PLANNED → STAGED → BUILT → VERIFIED → ATTESTED → FROZEN → PUBLISHED`

### 8.9 Formal safety properties

Create a compact formal model for the critical state machines and verify at least these invariants:

- Action N+1 cannot become `READY` before required predecessors are `ACCEPTED`.
- Only one active claim exists for an action.
- An actor cannot review its own implementation where independence is required.
- A mandatory criterion cannot be accepted without the configured evidence level.
- A side effect cannot be committed without approval and external verification.
- A project cannot be released with unresolved mandatory criteria, open critical incidents, stale evidence, or mutable artifacts.

---

## 9. Comprehensive workstreams

## WS-00 — Preserve v7 and establish an immutable baseline

### Objective

Protect the source material and turn every known weakness into a permanent reproducible test before altering architecture.

### Work

- Preserve the original ZIP unchanged.
- Record SHA-256, byte size, entry list, and extraction manifest.
- Create a clean version-controlled working repository from the extracted source.
- Tag the exact v7 baseline.
- Run and record all shipped tests separately to avoid one long timeout masking results.
- Capture compiler output and representative new-build, capture, and continuation packs as golden fixtures.
- Reproduce and encode known failures:
  - Capture/runtime fingerprint incompatibility.
  - Malformed App Intelligence records passing validation.
  - Pre-claim forbidden change bypass.
  - Symlink write escape.
  - Concurrent claim/event race.
  - Reviewer identity spoofing.
  - Shell command execution risk.
  - Artifact/path containment cases.
- Freeze these as failing characterization tests.

### Deliverables

- `BASELINE_MANIFEST.json`
- `KNOWN_V7_DEFECTS.md`
- Characterization test suite.
- Golden v7 fixtures.
- Tagged source baseline.

### Exit gate

Every known defect is reproducible, and the original ZIP remains byte-for-byte unchanged.

---

## WS-01 — Rewrite the mission and role documentation

### Objective

Make it impossible to mistake master LAOS for a weaker-agent assignment.

### Work

- Rewrite every entry document around the Architect-first mission.
- Create separate start documents for Nilhan, Architect AI, capture agent, implementation agent, reviewer, and release verifier.
- Remove language that implies the weaker agent receives the master framework.
- Explain pack separation and what must never be shared.
- Explain new-build and existing-project workflows with concrete handoff diagrams.
- State the trust boundary and limitations plainly.
- Add a documentation consistency checker that scans for contradictory role descriptions.

### Acceptance

A reader shown only any one start document can correctly identify:

- Who receives master LAOS.
- Who designs the project.
- Who receives Action Capsules.
- What a weaker agent is forbidden to see.
- How existing-app capture precedes continuation.

---

## WS-02 — Modernise the codebase and dependency discipline

### Objective

Turn v7's large scripts into maintainable, typed, testable modules without losing portability.

### Work

- Create a proper Python package and CLI entry point.
- Define supported Python and operating-system versions.
- Introduce strict static typing.
- Pin all dependencies and hashes in a lockfile.
- Separate required core dependencies from optional sandbox, database, telemetry, and signing extras.
- Add deterministic configuration loading.
- Add structured errors with stable error codes.
- Add semantic versioning for runtime protocol, database, schema, pack, and adapter versions.
- Create migration tooling.

### Acceptance

- Clean installation from the lockfile.
- No circular imports.
- Strict type check passes.
- All public modules have tests.
- Runtime client can be packaged as a minimal signed standalone artifact.

---

## WS-03 — Strict schema and semantic validation system

### Objective

Ensure “valid” means structurally and semantically valid, not merely parseable JSON.

### Work

- Implement strict domain models and generated Draft 2020-12 schemas.
- Close all current `additionalProperties: true` schemas unless a documented extension area is required.
- Add schema registry and version negotiation.
- Validate every external file at every trust boundary.
- Add cross-reference checks for IDs, dependencies, criteria, evidence, checks, permissions, and paths.
- Add semantic checks for impossible or contradictory states.
- Add negative fixtures for wrong types, missing fields, unknown fields, invalid enums, duplicate IDs, broken references, and unsafe paths.
- Produce precise error messages.

### Acceptance

No malformed capture, blueprint, task, action, evidence, review, side-effect, or release record can enter trusted state.

---

## WS-04 — Canonical repository fingerprint and workspace sealing

### Objective

Use one versioned algorithm across capture, continuation, runtime, evidence, and release.

### Work

- Create one shared fingerprint library imported everywhere.
- Define algorithm `laos-repository-v2`.
- Canonical entry fields:
  - Normalised relative path.
  - Entry type.
  - Byte size.
  - SHA-256.
  - Executable/mode information where portable.
  - Symlink target text without following it.
- Explicitly version ignore/exclusion policy.
- Detect Unicode normalisation and case-collision issues.
- Record Git commit, branch, dirty state, submodules, and LFS pointers separately.
- Distinguish source, harness, environment, and full-workspace fingerprints.
- Hash large files by streaming; exclusions require an explicit recorded reason.
- Seal the workspace before any weaker agent receives write access.
- Recheck the seal before claim, before verification, and before acceptance.
- Add delta-capture and Architect-approved reseal workflow.

### Acceptance

- Capture → continuation → unchanged repository passes.
- One-byte tracked change fails.
- Symlink, file mode, deletion, rename, untracked file, and case collision tests behave deterministically.
- No task can hide a pre-claim modification.

---

## WS-05 — Path, archive, and filesystem hardening

### Objective

Make all path handling central, consistent, and fail closed.

### Work

- Create a canonical `SafePath`/`PathPolicy` module.
- Reject absolute paths, traversal, empty paths, device paths, Windows reserved names, case collisions, and invalid encodings.
- Resolve every parent component and verify containment.
- Reject symlink parents for controlled writes.
- Use no-follow file opens where supported and revalidate after opening to reduce race windows.
- Never follow symlinks during repository scan, evidence collection, recovery, or artifact creation.
- Harden ZIP extraction against traversal, symlinks, duplicates, zip bombs, case collisions, excessive counts, and suspicious compression ratios.
- Protect destructive compiler and recovery targets.
- Require explicit confirmation and policy for deletion.
- Add property-based and fuzz tests.

### Acceptance

All known traversal and symlink attacks fail before external content is read or written.

---

## WS-06 — Transactional state, claims, leases, and audit

### Objective

Replace mutable JSON coordination with transaction-safe state.

### Work

- Implement a `StateStore` interface.
- Use SQLite with WAL and transactions for the default single-host mode.
- Offer PostgreSQL for multi-host/distributed mode.
- Store tasks, actions, attempts, claims, criteria, checks, evidence, reviews, approvals, side effects, artifacts, incidents, policies, and events in normalised tables.
- Use unique constraints for one active claim per action and one accepted result per attempt.
- Use atomic transactions for transition plus event append.
- Add database schema migrations.
- Add integrity checks, backup, restore, and export.
- Keep Markdown/JSON human-readable views as generated exports, never canonical mutable state.
- Use an outbox table for external operations.
- Add concurrency stress tests with many competing processes.

### Acceptance

- No lost updates.
- No duplicate active claims.
- Event and materialised state cannot diverge after a committed transaction.
- Recovery from process interruption preserves a valid state.

---

## WS-07 — Authenticated actors and capability-based authority

### Objective

Stop treating typed names as identities.

### Work

- Define actor roles: owner, Architect, builder, investigator, verifier, reviewer, release verifier, and system service.
- Issue short-lived, action-bound capability tokens from the trusted control plane.
- Token claims include actor, role, session, project, pack, action, permissions, nonce, issue/expiry time, and issuer.
- Store token hashes or verification metadata, never reusable secrets.
- Use separate credentials for builder and reviewer.
- Sign packs, capsules, decisions, and release records using Ed25519 or an equivalent modern scheme.
- Keep private keys outside weaker-agent workspaces.
- Support OIDC/Sigstore identities for high-assurance CI/release operation.
- Revoke sessions and quarantine workspaces after tampering or secret exposure.

### Acceptance

- A builder cannot impersonate a reviewer by changing a string.
- Expired, replayed, altered, wrong-project, or wrong-action tokens fail.
- A weaker agent cannot mint Architect approval.

---

## WS-08 — Policy engine and risk classification

### Objective

Make permissions and release rules executable policy, not prose.

### Work

- Implement a deterministic built-in policy engine with versioned rules.
- Support an optional Open Policy Agent adapter for organisational policies.
- Calculate a minimum risk tier from data sensitivity, permissions, external effects, deployment target, migration/destructive scope, authentication, money, communications, and blast radius.
- Prevent the compiler from lowering below the calculated risk floor without signed human approval.
- Define policy profiles: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`.
- Define required gates, evidence levels, review count, sandbox tier, and human approvals for each profile.
- Record every policy decision, inputs, result, policy version, and reason.
- Unit-test and property-test policies.
- Map the threat model to contemporary agentic security risks, including prompt injection, goal hijacking, tool misuse, identity/privilege abuse, memory poisoning, skill/plugin compromise, data exfiltration, and cascading multi-agent failure.

### Acceptance

The same structured input always produces the same policy decision, and no undeclared permission is granted.

---

## WS-09 — Architect Control Pack and public execution-pack compiler

### Objective

Compile one private control product and one minimal public execution product.

### Work

- Split the compiler output physically.
- Sign both pack manifests.
- Keep future actions, hidden checks, evaluation rubrics, and private decisions only in the control pack.
- Public pack contains only runtime client, public invariants, public schemas, selected skills, adapter, and connection/configuration data needed to request a capsule.
- Remove the v7 pattern of copying all roles, all skills, all templates, and broad project documents into every implementation pack.
- Generate a leak report.
- Extract and verify each output in a clean directory.
- Add compatibility and protocol metadata.

### Acceptance

A full-text and semantic leak scan finds no future task, hidden test, or Architect-only material in the execution pack.

---

## WS-10 — Anti-Skip Action Engine

### Objective

Make step skipping technically impossible within the LAOS protocol.

### Work

- Introduce task → action → attempt hierarchy.
- Compile standard action sequences by task type and risk.
- Expose only one `READY` action to an executor session.
- Issue a signed, expiring capsule with a sequence number and nonce.
- Require structured submission for each action.
- Verify output schema, workspace seal, permissions, and stop conditions before acceptance.
- Unlock successors only inside the same transaction that accepts the predecessor.
- Enforce maximum attempts and repeated-failure signatures.
- Generate a repair action rather than allowing the reviewer to silently modify product code.
- Support Architect intervention, cancellation, supersession, and amendment.
- Provide a portable offline signed-capsule mode and a recommended managed-control-plane mode.

### Standard actions

#### UNDERSTAND

The weaker agent must state:

- Objective.
- Criteria.
- Invariants.
- Preservation rules.
- Non-goals.
- Allowed/forbidden scope.
- Unknowns.
- Planned verification.

The submission is checked deterministically and, where required, approved by the Architect using a hidden expected-understanding contract.

#### PLAN

The plan maps each criterion to files, change, checks, failure paths, evidence, and rollback. Broad or incomplete plans are rejected.

#### IMPLEMENT

Only this action grants product-code write permission. It receives a bounded path and command capability set.

#### VERIFY

Runs required public and hidden checks in a clean verifier context. Builder-authored prose cannot satisfy this action.

#### EVIDENCE

Collects and binds evidence to criteria and source seals.

#### HANDOFF

Produces a compact factual handoff, not a persuasive completion claim.

#### REVIEW

Runs under a separate identity and context.

### Acceptance

- Attempting to submit IMPLEMENT before UNDERSTAND/PLAN acceptance fails.
- Attempting action N+1 before N acceptance fails.
- Attempting out-of-scope work fails immediately or at broker boundary.
- No manual state-file edit can advance the project.

---

## WS-11 — Model profiles, calibration, prompt compiler, and context engineering

### Objective

Compile instructions for the actual executor rather than an imaginary universal agent.

### Work

- Define model/agent profiles with:
  - Adapter and model identity/version.
  - Known context limits.
  - Reliable file/action limits.
  - Tool strengths and weaknesses.
  - Prompt style.
  - Required repetition.
  - Example needs.
  - Retry and timeout limits.
  - Review intensity.
  - GUI/browser reliability.
- Create real calibration tasks in disposable repositories.
- Record observed performance and select a safe action-size ceiling.
- Recalibrate after model or adapter changes.
- Dynamically shrink later actions after failures; cautiously widen only after evidence.
- Build a compositional prompt compiler:
  - Universal authority/safety layer.
  - Project invariants.
  - Role layer.
  - Current capsule.
  - Selected skill instructions.
  - Adapter-specific formatting.
- Implement token budgets and context manifests.
- Load only context relevant to the current action.
- Cite source files/sections inside the capsule.
- Keep transcripts and large logs out of the prompt.
- Enforce that any instruction intended for another agent is emitted as one complete copy-pasteable code block.
- Discover and record the actual path and SHA-256 of the current `Universal_Desktop_Agent_Strong_Harness_Guide`; never assume its location.

### Prompt linter

Reject prompts missing or contradicting:

- Role.
- Exact objective.
- Finish line.
- Criteria.
- Invariants.
- Non-goals.
- Allowed and forbidden paths.
- Tools and permissions.
- Required outputs.
- Checks.
- Evidence.
- Stop conditions.
- Tool-unavailability behaviour.
- Final response format.
- Capsule identity and expiry.

Also reject excessive context, unresolved placeholders, multiple unrelated actions, hidden-data leakage, and instructions that authorise fake capability.

### Acceptance

Every released adapter/profile has calibration evidence and a tested prompt snapshot.

---

## WS-12 — Skill and adapter supply-chain security

### Objective

Treat skills and agent adapters as executable supply-chain components.

### Work

- Give each skill and adapter a manifest with version, hash, author/provenance, permissions, compatible runtimes, and tests.
- Sign approved skills/adapters.
- Include only selected skills in public packs.
- Prevent repository-provided skills from overriding control-plane policy.
- Add static scans for dangerous instructions, hidden network use, secret requests, broad filesystem access, and prompt injection.
- Add a quarantine process for compromised or stale skills.
- Maintain compatibility tests for each supported desktop/coding agent.

### Acceptance

Unsigned, modified, incompatible, or over-permissioned skills cannot be loaded.

---

## WS-13 — Existing-application capture and continuation rebuild

### Objective

Make capture an evidence-producing, read-only investigation controlled by the Architect.

### Work

- Mount or copy the source repository read-only for capture.
- Keep capture working files outside the source repository by default.
- Seal repository state at capture start and end.
- Split capture into bounded actions:
  1. Repository identity and environment.
  2. Architecture and dependencies.
  3. Features, UI, APIs, data, authentication, and authorisation.
  4. Commands, tests, deployment, integrations, and external systems.
  5. Issues, protected areas, risks, assumptions, unknowns, and prior claims.
  6. Reconciliation and return-pack finalisation.
- Every fact records status: `OBSERVED`, `REPRODUCED`, `INFERRED`, `CLAIMED_ONLY`, or `UNKNOWN`.
- Every non-unknown fact links to evidence.
- Deployment and live integration truth remain unknown unless directly verified.
- Support parallel read-only investigators, followed by a conflict-reconciliation action.
- Strictly validate and sign the return pack.
- Require Architect review and a signed `CaptureAcceptanceRecord` before continuation compilation.
- If the repository changed after capture, perform delta capture or full recapture according to policy.
- Continuation compiler imports only accepted facts and preserves verified behaviour/protected areas.

### Acceptance

No product-code write is possible during capture, and continuation cannot compile from an unaccepted or stale return pack.

---

## WS-14 — Command broker and clean verification runner

### Objective

Stop executing arbitrary contracted strings through the host shell.

### Work

- Store commands as an argument array, not one shell string.
- Default `shell=false`.
- Require a signed high-trust exception for shell semantics.
- Validate executable, arguments, working directory, environment names, network need, resource limits, and expected outputs.
- Execute inside the action sandbox.
- Kill the process group on timeout.
- Stream output to an immutable transcript while enforcing size limits.
- Redact secrets using value-aware and pattern-based filters.
- Record runtime image/environment digest.
- Run acceptance checks in a clean verifier workspace, separate from the builder's mutable environment.
- Store hidden checks only in the verifier/control plane.
- Treat dependency installation as an explicit permissioned operation.
- Make unavailable tools yield `BLOCKED` or `INCONCLUSIVE`, never PASS.

### Acceptance

No normal check uses `shell=True`, no secret value appears in a transcript, and verifier results are bound to an exact source seal and environment digest.

---

## WS-15 — Evidence engine and criterion-level closure

### Objective

Replace manually written “proof” with runtime-collected, criterion-linked evidence.

### Work

- Maintain an immutable/content-addressed canonical evidence store outside the weaker agent's writable area.
- Export user-readable evidence copies under `Evidence/` at the repository root.
- Define evidence types:
  - Command transcript.
  - Test result.
  - Diff/change set.
  - Browser screenshot/video/journey.
  - API request/response.
  - Database before/after record.
  - External-system receipt.
  - Performance measurement.
  - Security scan.
  - Manual observation.
  - Review verdict.
- Evidence records include producer, collector, timestamps, source seal, environment, hash, criteria, redaction state, and dependencies.
- Define evidence maturity:
  - `L0 ASSERTION`
  - `L1 MANUAL OBSERVATION`
  - `L2 RUNTIME-CAPTURED`
  - `L3 INDEPENDENT RERUN`
  - `L4 HIDDEN/ADVERSARIAL VERIFICATION`
- Risk policy sets minimum evidence level per criterion.
- Build a freshness dependency graph so only affected evidence becomes stale.
- Automatically generate claim-to-evidence and outcome-closure ledgers.
- Scan evidence for secrets, personal data, and prohibited content.
- Require negative evidence for relevant dangerous outcomes.

### Acceptance

A criterion cannot reach `ACCEPTED` from a narrative file alone, and evidence becomes stale automatically when its declared source dependencies change.

---

## WS-16 — Verification depth, negative testing, and invariant protection

### Objective

Test what must not happen as carefully as the happy path.

### Work

For each changed behaviour, require applicable tests for:

- Valid input.
- Invalid input.
- Missing input/data.
- Boundary values.
- Authentication failure.
- Authorisation failure.
- Wrong tenant/user/scope.
- Duplicate request/retry.
- Timeout.
- Partial external failure.
- Rollback/recovery.
- Data consistency.
- Concurrency.
- Regression of existing working behaviour.

Additional rules:

- Every bug fix includes a regression test that fails before the fix.
- Tests cannot be weakened, deleted, or bypassed merely to pass.
- Test changes are reviewed separately when they alter expected behaviour.
- Invariants have explicit invariant checks.
- Hidden tests include adversarial cases unknown to the builder.
- Missing credentials or services produce an honest blocked state, not fake success.

### Acceptance

The criterion matrix shows happy-path, failure-path, preservation, and negative evidence coverage where relevant.

---

## WS-17 — Independent review and adjudication

### Objective

Make review genuinely independent, criterion-based, and adversarial.

### Work

- Require a distinct authenticated reviewer session.
- Provide a read-only review sandbox.
- Give the reviewer the original requirement/criterion contract, final source/diff, checks, evidence, and risks.
- Omit or de-emphasise builder persuasion.
- Ask the reviewer to find reasons the work is incomplete or unsafe.
- Record verdict per criterion: `PASS`, `FAIL`, `INCONCLUSIVE`, `PASS_WITH_NONBLOCKERS`.
- Review for scope violations, preservation failures, test weakening, missing failure paths, weak evidence, secrets, insecure defaults, and unsupported claims.
- Reviewer cannot repair product code within the review action.
- Failed review creates a bounded repair action.
- Architect adjudicates disagreements.
- High/critical work requires multiple independent signals, such as two reviewers or one reviewer plus Architect acceptance and hidden verification.

### Acceptance

The same principal cannot both implement and independently approve the same criterion, and review verdicts are cryptographically attributable.

---

## WS-18 — Real sandbox and capability broker

### Objective

Ensure the weaker agent can access only what the current capsule authorises.

### Work

- Keep the trusted LAOS control plane outside the execution sandbox.
- Define a provider-neutral `SandboxProvider` interface.
- Implement at least one real provider for release, with high-assurance options such as gVisor or microVM-backed execution where available.
- Use an ephemeral Git worktree or copy-on-write workspace per action/attempt.
- Mount project scope read-only or read-write according to capsule permissions.
- Mount LAOS runtime and public contract read-only.
- Do not mount Architect packs, unrelated files, home directories, SSH keys, cloud credentials, browser profiles, or system secrets.
- Disable network by default.
- Use an egress proxy/domain allowlist for authorised network actions.
- Inject short-lived secrets only into the authorised process.
- Apply non-root execution, CPU, memory, disk, process, and time limits.
- Record sandbox image digest and configuration.
- For GUI desktop agents, require a disposable VM or isolated OS account for high-risk work; document lower assurance when this is impossible.
- Quarantine the workspace on policy violation.

### Acceptance

Adversarial tests cannot read/write outside the mounted scope, access denied network destinations, or obtain unrelated credentials.

---

## WS-19 — External side-effect and approval broker

### Objective

Prevent duplicate, unauthorised, or unverifiable external actions.

### Work

- Prohibit direct external writes from ordinary implementation actions.
- Route them through a host-side broker.
- Require operation type, payload hash, idempotency key, target, expected result, verification method, and compensation plan.
- Apply policy and human/Architect approval matrix.
- Use the transactional outbox pattern.
- Store external receipt/identifier.
- Verify result from the external system independently.
- Detect replay and payload changes.
- Support compensation or explicit manual reconciliation.
- Require human approval for production deployment, destructive migration, payment/spending, public publishing, email, data export, credential creation, or material scope change.

### Acceptance

Replayed requests do not duplicate effects where the target supports idempotency; otherwise LAOS detects uncertainty and requires reconciliation rather than claiming exactly-once execution.

---

## WS-20 — Checkpoints, recovery, interruption, amendments, and anti-thrashing

### Objective

Recover safely without hiding failed attempts or reverting unrelated work.

### Work

- Create immutable/content-addressed checkpoints before risky actions.
- Bind checkpoints to workspace seal, action, actor, and database state.
- Recover only through an authorised recovery action.
- Default recovery preserves unrelated files; deletion requires explicit scope.
- Record all failed approaches and normalised error signatures.
- Block repeated identical approaches after the configured limit.
- Force scope reduction, checkpoint restore, model escalation, or Architect intervention.
- Implement signed specification amendments with impact analysis, affected tasks/actions/criteria, and revalidation.
- Add interruption/restart recovery tests.

### Acceptance

A killed process can resume without corrupting state, and failed-history evidence remains visible.

---

## WS-21 — Tamper-resistant events, provenance, and attestations

### Objective

Make the origin and sequence of important decisions and artifacts independently verifiable.

### Work

- Store append-only events transactionally.
- Hash-chain events and sign periodic anchors outside the working repository.
- Prevent ordinary runtime roles from updating/deleting historical events.
- Export an audit JSONL with verification metadata.
- Produce in-toto-compatible statements and SLSA provenance for release artifacts.
- Sign artifacts and attestations using Sigstore/Cosign or offline keys according to release environment.
- Include builder identity, source materials, commands, environment digest, checks, and artifact digests.
- Clearly distinguish local tamper detection from independent provenance.

### Acceptance

Altering the source, event export, evidence, artifact, or attestation causes verification failure, and release signatures can be checked outside the build workspace.

---

## WS-22 — Deterministic artifacts, SBOM, and release truth

### Objective

Build release artifacts that are clean, reproducible where feasible, and impossible to mutate silently after verification.

### Work

- Build from a clean staging directory.
- Sort archive entries and normalise timestamps, permissions, and metadata.
- Exclude `.git`, caches, real environment files, secrets, temporary state, nested releases, and unrelated outputs.
- Generate a full content manifest.
- Generate an SPDX SBOM using the latest stable specification selected at build time.
- Record dependency licenses and vulnerability scan results.
- Verify the archive after extraction into a second clean directory.
- Run the installed/extracted self-test.
- Freeze the verified artifact and detect mutation.
- Build twice in independent clean environments and compare outputs where reproducibility is supported.
- Generate final reports from verified machine state, never from memory.
- Reopen and stat every claimed deliverable before reporting completion.
- Save deliverables to a durable user-controlled location; temporary runtime storage alone is not sufficient.

### Acceptance

Release ZIP, checksums, manifest, SBOM, provenance, signatures, reports, and extracted validation all agree.

---

## WS-23 — Observability and complete execution traces

### Objective

Make every important decision and action inspectable without flooding prompts.

### Work

- Assign trace IDs to engagement, task, action, attempt, command, check, review, side effect, and release.
- Emit structured logs, metrics, and traces.
- Correlate policy decisions, commands, evidence, and outcomes.
- Redact secrets before export.
- Track:
  - Action latency.
  - Retry count.
  - Failure signatures.
  - Block reasons.
  - Scope violations.
  - Evidence levels.
  - Reviewer disagreement.
  - Human interventions.
  - Token/context size where available.
  - Cost where available.
- Support local JSON export and optional OpenTelemetry export.
- Add a human-readable status/report generator.

### Acceptance

A failure can be traced from user objective to Architect contract, capsule, executor actions, checks, evidence, review, and final decision.

---

## WS-24 — Real weaker-agent evaluation and improvement laboratory

### Objective

Prove whether v8 makes weaker agents materially more reliable and learn from failures.

### Comparison groups

1. Weak agent with a normal broad prompt.
2. Weak agent with a static structured prompt.
3. Weak agent with LAOS v7.
4. Weak agent with v8 portable/offline capsules.
5. Weak agent with v8 managed control plane and sandbox.
6. Strong reference agent where useful.

### Benchmark families

- New CLI application.
- New full-stack web application.
- API and database application.
- Authentication/authorisation feature.
- UI implementation and browser verification.
- Existing-repo feature addition.
- Bug diagnosis and repair.
- Data migration.
- External integration.
- Deployment workflow.
- Legacy/large repository takeover.
- Interrupted multi-session work.
- Multi-agent parallel work.

### Adversarial fixtures

- Stale README and false prior-agent claims.
- Dirty repository.
- Fingerprint drift.
- Hidden failing test.
- Deleted or weakened test.
- Fake live integration.
- Missing credentials.
- Prompt injection in repository text.
- Malicious skill or adapter.
- Symlink/path traversal.
- Secret in logs.
- Competing claims.
- Event tampering.
- Identity spoofing.
- Side-effect replay.
- Artifact mutation.
- Context overload.
- Repeated failed strategy.
- Reviewer bias/summary manipulation.
- Network exfiltration attempt.

### Metrics

- End-to-end functional success.
- Mandatory criterion closure.
- Skipped required actions.
- Premature implementation.
- False completion claims accepted by harness.
- Unauthorised file or external changes.
- Regression rate.
- Test weakening.
- Evidence validity and maturity.
- Failure-path coverage.
- Recovery success.
- Repeated-approach rate.
- Reviewer accuracy and disagreement.
- Human interventions.
- Runtime, tokens, and cost.
- Variance across repeated runs.

### Method

- Use real agent executions, not simulated model responses.
- Run multiple trials per model/task.
- Blind final graders where practical.
- Preserve complete traces.
- Use hidden tests and rotating fixtures to reduce evaluation gaming.
- Report confidence intervals and failure distributions, not only averages.
- Convert every real failure into a permanent regression fixture where licensing/privacy permits.

### Release target

The release must demonstrate statistically credible improvement over v7 and broad-prompt baselines. A stretch target is at least a tenfold reduction in skipped mandatory gates and harness-accepted false completion, without sacrificing functional success. This remains a measured target, not a pre-release claim.

---

## WS-25 — CLI and operator experience

### Objective

Make the strongest workflow the easiest workflow for Nilhan and the Architect.

### Proposed command families

```text
laos architect init
laos architect validate-spec
laos architect compile
laos architect approve-understanding
laos architect approve-plan
laos architect amend

laos capture compile
laos capture issue-next
laos capture validate-return
laos capture accept

laos action next
laos action claim
laos action submit
laos action block
laos action heartbeat
laos action explain

laos check run
laos evidence inspect
laos review issue
laos review submit

laos workspace seal
laos workspace verify
laos checkpoint create
laos recover

laos side-effect propose
laos side-effect approve
laos side-effect execute
laos side-effect reconcile

laos pack verify
laos release build
laos release verify
laos release attest

laos eval run
laos eval compare
laos eval report

laos doctor
laos status
laos audit export
```

### Usability rules

- Errors explain the failed gate and exact correction.
- `status` shows only current truth.
- `next` returns only the current legal action.
- `explain` reveals policy rationale without exposing hidden future work.
- CLI supports non-interactive machine-readable JSON and clear human output.
- Destructive/high-risk commands require explicit approval records.

---

## WS-26 — Documentation, migration, and compatibility

### Objective

Ship a system that can be used correctly without relying on memory of this conversation.

### Documentation set

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
- `REAL_AGENT_EVALUATION.md`
- `LIMITATIONS_AND_HUMAN_APPROVALS.md`
- `MIGRATION_FROM_V7.md`
- `TROUBLESHOOTING.md`
- `RELEASE_AND_PROVENANCE.md`

### Migration strategy

- Never mutate the original v7 ZIP.
- Provide a v7 importer that reads blueprints, tasks, and capture returns into v8 domain models.
- Treat imported v7 data as untrusted until strict validation and Architect reconciliation.
- Recompile v7 implementation packs; do not “upgrade in place” and assume v8 guarantees.
- Map v7 task states to v8 task/action/criterion states conservatively.
- Preserve evidence hashes and provenance, but mark unsupported v7 evidence maturity accurately.
- Produce migration reports listing dropped, transformed, blocked, and manually reviewed fields.

### Compatibility

Maintain explicit compatibility matrices for:

- Pack schema.
- Runtime protocol.
- Database schema.
- Agent adapters.
- Skills.
- Sandbox providers.
- Operating systems.

---

## WS-27 — CI, security testing, and release engineering

### Objective

Make the LAOS release process itself meet the standards LAOS expects from projects.

### Automated gates

- Formatting and linting.
- Strict static typing.
- Unit tests.
- Integration tests.
- Property-based tests.
- Concurrency tests.
- State-machine/model checks.
- Fuzz tests for schemas, ZIPs, paths, and manifests.
- Security scans.
- Secret scans.
- Dependency/license/vulnerability scans.
- Coverage threshold, with higher threshold for security-critical modules.
- Mutation testing for policy, path, fingerprint, and transition logic.
- Cross-platform tests.
- Clean-package install test.
- Pack compile/extract/verify tests.
- Capture/continuation round trip.
- Deterministic artifact comparison.
- Signature and attestation verification.
- Representative real-agent evaluation suite.

### Release artifacts

- Master source ZIP.
- Minimal runtime artifacts.
- Architect/control tools.
- Checksums.
- Signatures.
- SBOM.
- SLSA/in-toto provenance.
- Content-integrity manifest.
- Build verification report.
- Security/red-team report.
- Real-agent evaluation report.
- Migration guide.
- Known limitations.
- Machine-readable release summary.

### Release rule

No release is declared complete until every claimed file exists in durable storage, is reopened, hashed, extracted where applicable, and independently verified.

---

## 10. Implementation sequence and hard gates

The upgrade should be delivered through ordered milestones. Later work must not compensate for an unsound foundation.

## Milestone 0 — Baseline and governance

Includes WS-00 and architecture decision records.

**Exit:** Original preserved; known defects are tests; target architecture approved.

## Milestone 1 — v7 emergency correctness patch

Create a narrow `v7.0.1` safety branch while v8 is built:

- Canonicalise fingerprint use.
- Enforce existing JSON schemas properly.
- Close pre-claim and symlink/path escapes where feasible.
- Remove or guard `shell=True`.
- Add missing round-trip and negative tests.
- Correct documentation overclaims.

This patch is not v8 and does not claim the new anti-skip architecture.

**Exit:** Existing v7 users are no longer exposed to known P0 correctness failures.

## Milestone 2 — v8 typed kernel

Includes WS-02 through WS-08:

- Domain models and strict schemas.
- Canonical paths and fingerprints.
- Workspace seals.
- Transactional state.
- Identity and policy.
- Formal state properties.

**Exit:** P0 security/correctness tests pass before prompt or pack work begins.

## Milestone 3 — Pack separation and Anti-Skip Engine

Includes WS-09 and WS-10.

**Exit:** A weaker agent can receive only one signed capsule, cannot access future actions, and cannot skip required predecessors.

## Milestone 4 — Model-specific prompt and skill system

Includes WS-11 and WS-12.

**Exit:** Each supported adapter/profile passes calibration, linting, leak, and prompt snapshot tests.

## Milestone 5 — Existing-app capture and continuation

Includes WS-13.

**Exit:** Read-only capture, strict return validation, Architect acceptance, and unchanged-repository continuation all pass end to end.

## Milestone 6 — Execution, evidence, review, sandbox, and side effects

Includes WS-14 through WS-20.

**Exit:** Real isolated action execution, clean verification, criterion-level evidence, independent review, recovery, and external side-effect controls pass adversarial tests.

## Milestone 7 — Provenance, artifacts, telemetry, and release UX

Includes WS-21 through WS-23 and WS-25.

**Exit:** Full traceability and externally verifiable release artifacts.

## Milestone 8 — Evaluation laboratory and documentation

Includes WS-24 and WS-26.

**Exit:** Real comparative results and complete role-specific documentation.

## Milestone 9 — Release candidate and independent red team

Includes WS-27 and an independent review of the entire deliverable.

**Exit:** All release blockers closed; final artifacts durably stored and verified.

---

## 11. Dependency map

```text
WS-00 Baseline
  ├── WS-01 Mission docs
  └── WS-02 Code modernisation
        ├── WS-03 Schemas
        ├── WS-04 Fingerprints
        ├── WS-05 Paths
        └── WS-06 State
              ├── WS-07 Identity
              └── WS-08 Policy
                    ├── WS-09 Pack separation
                    │     ├── WS-10 Anti-Skip engine
                    │     ├── WS-11 Profiles/prompts
                    │     └── WS-12 Skills/adapters
                    ├── WS-13 Capture/continuation
                    └── WS-18 Sandbox
                          ├── WS-14 Command broker
                          ├── WS-19 Side effects
                          └── WS-20 Recovery

WS-10 + WS-14 + WS-15 + WS-16 + WS-17
  └── Criterion acceptance and task closure

WS-06 + WS-07 + WS-15 + WS-17 + WS-19
  └── WS-21 Provenance
        └── WS-22 Release artifacts

All workstreams
  ├── WS-23 Telemetry
  ├── WS-24 Evals
  ├── WS-25 CLI
  ├── WS-26 Docs/migration
  └── WS-27 Release engineering
```

---

## 12. Required test matrix

### 12.1 Schema tests

- Valid examples for every version.
- Missing required field.
- Wrong type.
- Unknown field.
- Invalid enum.
- Invalid date/digest/path.
- Duplicate ID.
- Broken reference.
- Contradictory state.
- Unsupported version.
- Malformed App Intelligence files.

### 12.2 Fingerprint tests

- Unchanged round trip.
- One-byte change.
- Add/delete/rename.
- Mode change.
- Symlink target change.
- Ignored file change.
- Exclusion policy change.
- Large file.
- Unicode path.
- Case collision.
- Git submodule/LFS.
- Dirty worktree.

### 12.3 Path/archive tests

- `../` traversal.
- Absolute path.
- Windows drive/device path.
- Symlink parent.
- Symlink ZIP entry.
- Duplicate/case-colliding ZIP entries.
- Compression bomb.
- Too many entries.
- Dangerous output directory.
- Recovery deletion outside scope.

### 12.4 State/concurrency tests

- Two simultaneous claims.
- Many simultaneous claims.
- Concurrent transitions.
- Event/state atomicity.
- Process crash before/after commit.
- Lease expiry and takeover.
- Replay.
- Database corruption detection.
- Backup/restore.
- SQLite and PostgreSQL parity.

### 12.5 Action engine tests

- Skip UNDERSTAND.
- Skip PLAN.
- Execute expired capsule.
- Reuse nonce.
- Submit wrong action.
- Execute action N+1.
- Exceed attempt budget.
- Repeat failure signature.
- Modify capsule.
- Alter workspace after verification.
- Manual state edit.

### 12.6 Identity/review tests

- Builder self-review.
- Actor-name spoof.
- Wrong role.
- Wrong project/action token.
- Expired/revoked token.
- Signature alteration.
- Reviewer writes product code.
- Reviewer summary bias fixture.

### 12.7 Sandbox/command tests

- Read unrelated host file.
- Write outside mount.
- Access home/SSH/cloud credentials.
- Network to denied destination.
- Shell injection.
- Secret in command line/output.
- Fork bomb/resource exhaustion.
- Timeout child-process cleanup.
- Tool unavailable.
- Dependency install without permission.

### 12.8 Evidence tests

- Missing evidence.
- Tiny/vague narrative.
- Changed evidence.
- Stale source seal.
- Wrong criterion link.
- Secret/PII leakage.
- Fabricated screenshot metadata.
- Missing external receipt.
- Evidence dependency change.
- Builder assertion attempting to satisfy L2/L3 requirement.

### 12.9 Capture/continuation tests

- Read-only enforcement.
- Repo changes during capture.
- Partial/blocked capture.
- Unknown deployment state.
- Conflicting investigators.
- Missing evidence.
- Invalid return signature.
- Unaccepted capture.
- Stale capture.
- Delta recapture.
- Preservation contract import.

### 12.10 Side-effect tests

- Missing approval.
- Duplicate/replayed request.
- Payload changed under same idempotency key.
- External timeout after possible success.
- Verification mismatch.
- Compensation.
- Manual reconciliation.
- Credential expiry.

### 12.11 Artifact/release tests

- Secret in staging.
- Cache/nested archive inclusion.
- Nondeterministic timestamp.
- Post-verification mutation.
- Signature failure.
- SBOM mismatch.
- Provenance mismatch.
- Extracted artifact self-test.
- Missing deliverable.
- Temporary storage loss simulation.

---

## 13. Security threat model deliverables

Produce a formal threat model covering:

### Assets

- Master LAOS framework.
- Architect Control Pack.
- Project specification and future action graph.
- Hidden checks and evaluator rubrics.
- Repository and deployment credentials.
- Workspace and evidence.
- State database and event ledger.
- Signing keys and capability issuer.
- Release artifacts and attestations.

### Adversaries/failure sources

- Malicious repository content.
- Compromised dependency, skill, or adapter.
- Prompt injection.
- Hallucinating or shortcut-taking weaker agent.
- Malicious/compromised executor.
- Reviewer collusion or spoofing.
- Concurrent process race.
- Host compromise.
- Stale or false capture.
- Human error.
- Accidental artifact loss.

### Trust boundaries

- Nilhan/Architect boundary.
- Control plane/public pack boundary.
- Control plane/sandbox boundary.
- Sandbox/repository boundary.
- Runtime/external-system boundary.
- Builder/reviewer boundary.
- Build/release-verifier boundary.
- Temporary/durable-storage boundary.

### Required outputs

- Data-flow diagram.
- Abuse cases.
- Threat/control matrix.
- Residual risk register.
- Incident response playbook.
- Key and token lifecycle.
- Sandbox assurance matrix.

---

## 14. Provisional release blockers

LAOS v8.0 must not be released if any of the following remains:

- Fingerprint inconsistency.
- Schema parser without strict validation.
- Pre-claim change bypass.
- Path or symlink escape.
- Host `shell=True` as normal execution.
- Mutable JSON as canonical concurrent state.
- Actor names used as identity.
- Builder self-review accepted.
- Future action or hidden-test leakage.
- Ability to skip required actions.
- Acceptance criterion not individually tracked.
- Narrative-only evidence satisfying high-risk criteria.
- High-risk execution without a real sandbox.
- Direct unbrokered consequential external write.
- Unsigned/tamperable release artifacts presented as high assurance.
- No real weaker-agent comparison.
- Missing or contradictory role documentation.
- Claimed deliverables not reopened and verified in durable storage.

---

## 15. Performance and usability guardrails

Robustness must not become bureaucratic paralysis.

- Use risk-adaptive gates rather than maximum ceremony for every trivial action.
- Combine actions only when the executor profile and risk allow it.
- Cache immutable context and validation results safely.
- Make capsule content short and highly relevant.
- Use criterion-scoped fingerprints to avoid invalidating unrelated evidence.
- Keep the control plane eventful but the agent prompt small.
- Allow parallel actions only when paths, criteria, and side effects are proven independent.
- Provide clear blocked-state explanations and repair paths.
- Measure overhead in the evaluation suite.

---

## 16. Risk register for the upgrade itself

| Risk | Consequence | Mitigation |
|---|---|---|
| Over-engineering | Framework becomes hard to use | Risk-adaptive profiles; minimal portable mode; usability evals |
| Micro-actions too small | Excessive cost and context switching | Calibrated action-size ceiling; merge safe gates |
| Micro-actions too broad | Weak agents still skip | Profile limits; Architect review; measured skip rate |
| Sandbox incompatibility | Some projects cannot run | Provider abstraction; documented lower-assurance mode; disposable VM path |
| Hidden tests leak | Agents game acceptance | Physical separation; leak scans; verifier-only storage |
| Strong Architect unavailable mid-run | Semantic gates stall | Signed precompiled rubrics for low/moderate risk; explicit human escalation |
| Model changes | Old profiles become unsafe | Version binding and mandatory recalibration |
| Database complexity | Migration/corruption risk | Transactions, migrations, backups, integrity tests, simple schema |
| Signing/key misuse | False provenance | External key storage, rotation, revocation, identity separation |
| Evidence growth | Storage burden | Content-addressing, deduplication, retention policy, immutable summaries |
| Policy false positives | Work blocked unnecessarily | Explainable decisions, tested amendments, risk-specific policies |
| Policy false negatives | Unsafe authority | Default deny, independent red team, property tests |
| Existing repo drift | Wrong continuation plan | Workspace seals, delta capture, Architect reconciliation |
| Release artifact loss | Work disappears | Durable storage, reopen verification, checksum, optional external publication |
| Evaluation gaming | Misleading results | Hidden/rotating tasks, blinded grading, complete traces |

---

## 17. Definition of done for LAOS v8.0

LAOS v8.0 is done only when all of the following are true.

### Mission clarity

- Master LAOS is explicitly Architect-only everywhere.
- Every weaker-agent instruction is a project-specific single-action capsule.
- New-build and existing-project workflows are unambiguous.

### Correctness

- One canonical fingerprint implementation is used throughout.
- Every external record is strictly validated.
- Transactional state and concurrency invariants pass.
- Every mandatory criterion is individually closed.

### Anti-skip performance

- Required action order is technically enforced.
- Future actions are not exposed.
- Attempts to skip or manually advance fail.
- Real-agent trials show substantial improvement over v7 and normal prompts.

### Security

- Path, symlink, archive, identity, replay, prompt-injection, skill, and sandbox red-team tests pass.
- High-risk work runs in a real isolated environment.
- External effects are brokered and approved.
- Secrets remain outside prompts, logs, evidence, and artifacts.

### Evidence and review

- Acceptance uses runtime-captured, fresh evidence.
- Builder and reviewer are independently authenticated.
- Hidden/adversarial verification works.
- Review cannot silently repair and approve its own repair.

### Recovery

- Process interruption and checkpoint recovery work.
- Repeated failed approaches trigger escalation.
- Amendments preserve traceability.

### Release integrity

- Artifacts are deterministic where feasible.
- Manifest, SBOM, provenance, signatures, and checksums verify externally.
- The final ZIP is extracted and retested.
- Deliverables are present in durable storage and reopened before completion is reported.

### Documentation and migration

- Role-specific guides are complete.
- v7 migration is conservative and tested.
- Limitations and residual risks are explicit.

---

## 18. Recommended first build backlog

The first implementation work should be executed in this exact order:

1. Preserve and hash v7.
2. Create clean source repository and baseline tag.
3. Add failing test for fingerprint round trip.
4. Add failing malformed-capture schema tests.
5. Add failing pre-claim modification test.
6. Add failing symlink escape test.
7. Add failing concurrent claim/event tests.
8. Approve v8 architecture decision records.
9. Create typed package skeleton and locked dependencies.
10. Implement strict domain-model/schema foundation.
11. Implement canonical safe-path library.
12. Implement canonical fingerprint/workspace seal.
13. Implement transactional state store and migrations.
14. Implement authenticated actor/session/capability layer.
15. Implement policy and risk engine.
16. Implement project/task/action/criterion state model.
17. Implement signed Action Capsule issuance and verification.
18. Implement one-action unlock logic.
19. Implement UNDERSTAND and PLAN submissions.
20. Split Architect Control Pack from Agent Execution Pack.
21. Add leak scanner.
22. Implement sandbox provider interface and one real provider.
23. Implement argv-based command broker and clean verifier.
24. Implement evidence CAS and criterion closure.
25. Implement independent review capsule and repair loop.
26. Rebuild capture/return/continuation on shared primitives.
27. Implement side-effect broker and approvals.
28. Implement checkpoints, recovery, and amendments.
29. Implement deterministic artifact/provenance pipeline.
30. Implement telemetry and evaluation trace export.
31. Build real-agent comparison harness.
32. Run adversarial and cross-platform suites.
33. Rewrite all documentation.
34. Import representative v7 projects and validate migration.
35. Build, extract, retest, sign, attest, and durably save the release candidate.
36. Independent final review before release declaration.

---

## 19. Final recommendation

Do not attempt to “improve the prompts” first. Prompt improvements alone would preserve the main v7 weakness: the weaker agent still receives too much authority and is still trusted to remember a process.

The upgrade should begin with the trusted kernel—schemas, paths, fingerprints, seals, transactional state, identity, and policy—then build the one-action-at-a-time execution protocol on top. Capture, evidence, review, sandboxing, provenance, and evaluation should all use those same shared primitives.

The defining success of LAOS v8 will be this:

> A weak agent can forget, misunderstand, rush, bluff, or try to skip—but LAOS will reveal only the permitted action, restrict what can be changed, demand the required proof, and refuse to advance until the strong Architect's intended outcome has actually been demonstrated.
