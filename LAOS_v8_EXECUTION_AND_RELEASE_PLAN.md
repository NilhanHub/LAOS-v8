# LAOS v8.0 — Comprehensive Execution, Recovery, and Release Plan

**Original plan date:** 2026-07-12  
**Current revision:** 1.1 — post-Stage-0 architecture, security, delivery, and evaluation review  
**Revision date:** 2026-07-12  
**Plan status:** Stage 0 is verified complete; this is the reviewed execution baseline for Milestones 1–16. It does not claim that the LAOS v8 runtime has been implemented or released.  
**Primary owner:** Nilhan  
**Primary operator:** Highly capable Software Architect AI  
**Execution users:** Weaker investigation, implementation, testing, verification, and review agents  
**Authoritative v7 artifact:** `LAOS_v7.0_Complete_System.zip`, SHA-256 `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`  
**Verified Stage 0 package:** `LAOS_v8_STAGE_0_COMPLETE_PACKAGE.zip`  
**Stage 0 plan snapshot SHA-256:** `1b0517c1e85332bd393d4173c0000966eb5f7382f3bef58e2efbfccec7937779`

The immutable Stage 0 package retains the original plan snapshot. This revised standalone plan supersedes that snapshot for future implementation only after it is imported into the v8 working repository, assigned a new content hash, and reconciled with the requirements ledger, threat model, ADRs, and implementation backlog. The Stage 0 archive and its manifests must not be rewritten.

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

### 1.4 Verified Stage 0 status

Stage 0 is complete and independently packaged. Its completion record states:

- Milestone 0 status: `PASS`.
- v7 tests: 14 of 14 passed.
- Requirements ledger: 210 requirements, of which 7 are baselined and 203 remain planned.
- Regression catalogue: 40 items.
- Threat scenarios: 40.
- Architecture decisions: 7.
- v8 runtime implemented: `false`.
- v8 release published: `false`.

The Stage 0 baseline is historical evidence, not the active development checkout. Before Milestone 1 begins, the operator must reconstruct and verify the working repository from `LAOS_v8_STAGE_0_BASELINE.zip` or `LAOS_v8_STAGE_0_BASELINE.git.bundle`, import this reviewed plan, and record the resulting commit and manifest. Environment-specific `/mnt/data/...` paths in historical records are provenance only; artifact identity is established by filename, digest, manifest, and Git identity rather than by an ephemeral path.

### 1.5 Source-of-truth order after this review

When records disagree, the order is:

1. Physically present artifact bytes, cryptographic digests, and independently reproduced observations.
2. The active v8 Git revision and its machine-readable implementation, blocker, and requirement ledgers.
3. Accepted ADRs and signed policy records applicable to that revision.
4. This reviewed execution plan.
5. Stage 0 design inputs and historical plans.
6. Narrative status messages and prior chat.

No plan statement overrides contradictory machine truth. A plan revision changes intended work; it does not retroactively change Stage 0 evidence or implementation status.

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

### 2.1 v8.0 scope boundaries and non-goals

LAOS v8.0 must make strong claims only inside an explicit support and assurance matrix. The initial release is a single-owner, single-host control plane coordinating disposable execution and verification workspaces. The following are not implicit v8.0 promises:

- Distributed or multi-host coordination. SQLite is not a distributed lock or lease service.
- Multi-tenant isolation or protection from a malicious host administrator, kernel, hypervisor, or human trust-root owner.
- Universal support for every operating system, filesystem, model, tool, sandbox, browser, or external service.
- Proof that a model is aligned, truthful, or incapable of malicious behavior.
- Confidentiality merely because a pack is signed or physically separate.
- Exactly-once delivery to arbitrary external systems.
- Safe execution of untrusted repository build or test code outside a qualifying sandbox.
- Preservation or disclosure of private chain-of-thought. LAOS records decisions, concise rationale, evidence, uncertainty, and provenance—not hidden reasoning traces.

The v8.0 support matrix must name the exact host OS, filesystem semantics, Python, Git, SQLite, sandbox provider and version, executor profiles, workflow families, and external adapters that were conformance-tested. Unsupported combinations must be rejected or clearly labeled lower assurance; they must not inherit claims from a tested combination.

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
- A default-deny external side-effect protocol that safely rejects unsupported production effects; real production adapters are separate optional claims.
- Deterministic release creation and independent verification.
- Real comparative weaker-agent evaluation.

A large prompt pack, documentation-only design, or partially implemented runtime is not LAOS v8.

### 3.1 Delivery channels are not completion claims

The program may publish clearly labeled proof artifacts before v8.0:

1. **Bootstrap build** — contracts and deterministic fixtures only; no real-agent safety claim.
2. **Alpha trust spine** — one low-risk, end-to-end workflow in a disposable repository with network and external side effects denied.
3. **Beta** — supported new-build and existing-application workflows, one qualifying sandbox, recovery, migration rehearsal, and an operator CLI.
4. **Release candidate** — feature-frozen, red-teamed, migration-tested, provenance-complete, and evaluated on a sealed holdout.
5. **v8.0 release** — all non-waivable release blockers closed for every claimed support-matrix row.

Each pre-release must say what is absent, which assurance level it provides, and whether it is safe only for disposable fixtures. “Alpha,” “beta,” or “RC” must never be shortened to “LAOS v8 complete.”

### 3.2 Capability claims and adapters

The immutable GA capability classification is:

| Capability | v8.0 classification | GA rule |
|---|---|---|
| New-build compiler from accepted objective to sealed genesis repository and first action | `MANDATORY_V8_0` | Cannot be removed by the support matrix |
| Existing-application capture, Architect fact acceptance, and continuation | `MANDATORY_V8_0` | Cannot be removed by the support matrix |
| One-action execution, brokered checks, criterion evidence, independent review, promotion, recovery, migration, and release verification | `MANDATORY_V8_0` | Must pass every claimed environment row |
| External side-effect broker protocol and deny-all behavior for unsupported adapters | `MANDATORY_V8_0` | Unsupported production effects fail closed with no external dispatch |
| Any named real production side-effect adapter | `OPTIONAL_CLAIM` | Claim only after provider-specific real non-production conformance, crash/reconciliation, approval, and incident tests |
| Additional sandbox providers, distributed state, automatic non-interference, and extra external adapters | `DEFERRED` unless promoted before Alpha scope freeze | No GA claim without promotion and full gates |

The support matrix may restrict platforms, providers, and environments for a mandatory core capability; it may not delete that capability from v8.0 GA. A missing mandatory capability yields Alpha, Beta, RC, or technical preview—not v8.0 GA.

The core may provide interfaces for sandboxes, identity providers, evidence stores, and external side effects, but an interface is not a working integration. A release may claim support only for an adapter that has:

- A named version and immutable implementation digest.
- A declared assurance profile and failure model.
- Provider-specific conformance and adversarial tests.
- An operator-visible limitation and incident procedure.
- A row in the machine-readable release-gate and support matrices.

For v8.0, one fully tested implementation per mandatory boundary is enough. Additional providers, a distributed state backend, automatic non-interference analysis, and production-grade external adapters are deferrable unless the scope ledger classifies them as `MUST_V8_0`.

---

## 4. Non-negotiable engineering principles

### 4.1 Architect-only master authority

The Architect sees the entire project. The weaker agent sees only the current signed Action Capsule and stable public rules.

### 4.2 One legal action at a time

Future actions must not merely be marked “do not start.” They must be absent from the executor deliverable until issued. Encryption or signing may protect transport and authenticity, but it is not a substitute for omission and broker-enforced current-action state.

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

### 4.11 Model output is never security authority

Every model output—including output from the Architect AI—is an untrusted proposal until strict parsing, deterministic policy, state-transition guards, and any required human or independent approvals accept it. Models never hold raw signing keys or directly invoke privileged state transitions. A protected signer or capability service signs only a validated, policy-approved envelope.

### 4.12 Complete mediation and a small trusted computing base

Every claimed permission must map to a mandatory enforcement point. Filesystem mutation, command execution, network access, secret use, browser actions, evidence custody, review acceptance, signing, release publication, and external side effects must pass through a broker or isolated provider the agent cannot bypass. Direct host access is an unsupported, unassured mode.

The trusted computing base must be explicitly inventoried and minimized. Package boundaries inside one Python process are not physical isolation. Each support profile must identify the processes, OS principals, writable stores, keys, communication channels, and bypass assumptions that constitute its actual trust boundary.

### 4.13 Authenticity is not confidentiality or correctness

A valid signature proves that an authorized key signed exact bytes under a defined context. It does not prove that the payload is wise, safe, secret, current, or policy-compliant. Private information must be omitted through allowlisted typed projection; signing and leak scanning are defense-in-depth controls, not confidentiality mechanisms.

### 4.14 Repository changes use base/result lineage

Implementation necessarily changes a repository. Every attempt therefore has an immutable `base_seal`, a disposable candidate workspace, an authorized delta, and a `result_seal`. Checks and evidence bind to the result; review binds to both base and result; promotion creates the next authoritative seal. A generic “current seal” is insufficient.

### 4.15 External outcomes may be indeterminate

LAOS must never claim exactly-once external execution when a provider cannot guarantee it. Timeouts, crashes, and lost receipts can leave an operation in doubt. Idempotency, transactional outbox records, provider operation IDs, reconciliation, and manual escalation are required; irreversible indeterminate actions are never retried automatically.

### 4.16 Complexity must earn its place

The initial implementation is a modular monolith with explicit trust-boundary interfaces. A new service, package, abstraction, or provider is added only when required by a tested security boundary, a second real implementation, or measured operability need. Empty architecture scaffolding is not milestone progress. Scope additions after the Alpha trust spine require removing equivalent v8.0 scope, deferring another item, or documenting a newly validated release blocker.

### 4.17 Privacy and data minimization apply before transmission or persistence

Prompts, repository content, tool output, screenshots, API interactions, database observations, logs, and evaluation traces may contain personal, proprietary, or secret data. Classification, minimization, redaction, provider policy, operator consent, access control, encryption where needed, retention, export, and deletion rules apply before data is sent to a model/provider or persisted as evidence—not merely during final packaging.

---

## 5. Target trust architecture

```text
Nilhan
  │
  ▼
Highly capable Software Architect AI
  │ proposes decisions using master LAOS privately
  ▼
Deterministic Control Plane / Reference Monitor
  ├── Complete blueprint and App Intelligence
  ├── Full task/action graph
  ├── Hidden checks and evaluator rubrics
  ├── Strict validation, policy, risk, and approval rules
  ├── Transactional state and audit records
  ├── Protected signer/capability service
  └── Human/quorum gates for critical authority
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

Pack construction must use an allowlisted typed projection from canonical state. The leak scanner is a required second line of defense, but its success cannot prove the absence of semantically equivalent or encoded private information.

### 5.2 Deployment and enforcement contract

Before kernel implementation, ADRs must define the first supported topology. The default target is a local control plane with separate disposable builder and verifier workspaces. The contract must identify, at minimum:

| Boundary | Required owner | Mandatory mediation | Builder access |
|---|---|---|---|
| Canonical state and policy | Control-plane process | Authenticated transactional API | No direct write |
| Signing and trust roots | Protected signer, OS keystore, KMS, or offline release signer | Typed signing request after policy approval | No key or signing API access except scoped capsule proof |
| Authoritative repository | Promotion service or operator-controlled Git repository | Base/result-seal promotion protocol | Read-only base; edits only in disposable candidate workspace |
| Commands and filesystem mutation | Command/workspace broker inside a qualifying sandbox | Structured request plus capability check | No direct host path |
| Network and browser | Egress/browser broker | Destination, method, data class, and side-effect policy | Denied unless granted |
| Model invocation | Model-call broker or explicitly unassured direct provider | Provider/account/endpoint identity, allowed data class, minimization, retention/training/region policy, built-in tools, and operator consent | Only scoped prompt/context; no ambient tools or disallowed data |
| Secrets | Credential broker | Audience-bound operation or short-lived handle | Raw secret absent by default |
| Canonical evidence | Evidence broker/escrow | Broker capture and content addressing | No direct write |
| Independent review | Fresh verifier principal and workspace | Review capsule and protected verdict API | No builder credentials or write authority |
| Release publication | Independent release verifier and signer | Release-gate matrix and human/quorum approval | No builder publication authority |

The contract must specify process boundaries, OS identities, authenticated protocols, storage permissions, encryption needs, failure behavior, and whether each component shares a host. If the implementation cannot force an operation through its enforcement point, the corresponding assurance claim is unsupported.

### 5.3 Connected and offline assurance

- **Connected mode:** the broker checks current policy, revocation, repository lineage, approval, and capability state at claim and again before every privileged dispatch. Immediate revocation may be claimed only in this mode and only within a measured propagation bound.
- **Offline mode:** v8.0 permits verification and read-only inspection only; an offline capsule cannot authorize filesystem mutation, command/network/browser dispatch, raw secret access, review acceptance, promotion, side effects, or release. Offline mode cannot provide global one-time redemption or immediate revocation. A future device-bound/monotonic offline authority profile requires a separate threat model and support row.
- **Independent review:** a different display name is insufficient. The reviewer must use a distinct authenticated principal, credential or key, fresh session for critical work, separate writable workspace, and no builder or issuer authority over its own verdict.

### 5.4 Model-provider boundary

Remote Architect and executor calls are external data transfers and tool-capability boundaries. Every claimed provider row must record provider, account/tenant, endpoint and region, transport, retention and training policy, abuse/telemetry handling, supported data classifications, redaction/minimization transform, built-in tool policy, incident contact, and operator consent. Provider aliases and policies are versioned inputs that can invalidate a support row.

Model calls must pass through a broker that records the approved data classes and strips disallowed secrets, private plan material, evaluator answers, and repository classes before transmission. Provider-hosted browsing, code execution, connectors, memory, file upload, or other built-in tools are disabled unless they are separately mediated and represented in the permission-to-enforcement matrix. Direct SaaS-agent use outside that broker is explicitly unassured. A local-only/no-remote-transmission mode is a distinct support row.

Canary tests must demonstrate that forbidden secrets, private-plan markers, evaluator answers, and disallowed repository data are not transmitted, retained in LAOS telemetry, or exposed through provider tools under the claimed configuration.

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

### 6.2 Source layout is not a trust boundary

The directory tree in this plan is a logical source map, not a requirement to create every directory before its behavior exists. The project may remain one source repository and one developer environment, but release artifacts must enforce dependency and content boundaries:

- **Protocol artifact:** public schemas, record definitions, verification rules, and no private plan material.
- **Control artifact:** private compiler, policy, canonical state, signing client, evaluation administration, and Architect-only resources.
- **Runner artifact:** minimal agent-side capsule verification and communication code.
- **Broker artifact:** workspace, command, network, secret, and sandbox mediation.
- **Verifier artifact:** clean reconstruction, checks, evidence verification, and review support.

The final packaging form may be separate wheels, executables, or images after a proof of concept. Whatever form is selected, import-boundary tests and content inventories must prove that runner and execution deliverables cannot import or contain private control-plane modules, keys, future actions, or hidden evaluators.

### 6.3 Product, workspace, runtime, and evidence truth

LAOS must maintain distinct digests rather than one overloaded repository hash:

- `SourceSeal` — governed product source and protected tests under a versioned inclusion policy.
- `BaseSeal` — the authoritative source state from which an action begins.
- `ResultSeal` — reconstructed base plus the submitted authorized delta.
- `WorkspaceSeal` — candidate workspace state, including relevant generated or untracked files.
- `EvidenceObjectDigest` — canonical evidence bytes held outside builder write authority.
- `EvidenceExportSeal` — the signed, noncanonical project-facing `Evidence/` view.
- `RuntimeStateSnapshot` — a separately governed backup/recovery object, never a static release artifact.

The canonical fingerprint specification must define path byte representation, ordering, Unicode and case behavior, file modes, line-ending treatment, Git LFS, submodules, sparse checkouts, ignored and untracked files, Windows junctions/reparse points, and unsupported filesystem behavior. Cross-platform golden vectors must prove equivalent implementations agree.

---

## 7. Canonical domain model

All trusted records must have strict, versioned models and Draft 2020-12 JSON Schemas generated or checked from one canonical model source.

Minimum entities:

- `Engagement`
- `ProductObjective`
- `NewBuildRequest`
- `BlueprintAcceptanceRecord`
- `GenesisRepositoryRecord`
- `ProjectBlueprint`
- `Requirement`
- `AcceptanceCriterion`
- `Task`
- `ActionDefinition`
- `ActionCapsule`
- `ActionAttempt`
- `PromotionIntent`
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

These are logical record types, not a mandate for one module, class hierarchy, service, or database table per noun. Aggregate ownership must be chosen to preserve transactional invariants and keep the first implementation small. At minimum, the model must also represent base/result seal lineage, capsule redemption, policy decisions, key and revocation epochs, transactional outbox entries, support claims, data classification, and evaluation protocol identity; these may be fields or owned child records rather than new top-level aggregates.

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
- Reject duplicate JSON object names before ordinary parsing can overwrite them.
- Enforce maximum byte size, nesting depth, string length, collection length, and reference count at every untrusted boundary.
- Define exact formats for UTC timestamps, durations, counters, digests, paths, and integers that must round-trip across implementations.
- Use explicit normalization rules; never silently normalize signed text, identifiers, Unicode, paths, or line endings after validation.
- Pass the official validator conformance suite plus LAOS boundary, parser-differential, and resource-exhaustion cases for the selected schema implementation.

### 7.2 Signed and hashed record profile

Raw, ambiguously serialized JSON must not be signed. Milestone 2 must select and freeze one reviewed envelope profile with:

- Exact payload bytes and media type.
- Domain separation between capsule, policy, evidence, review, artifact, event-anchor, and release signatures.
- Envelope version, algorithm allowlist, issuer, audience, subject digest, key ID, issued time, expiry where applicable, and anti-downgrade rules.
- Duplicate-key rejection and strict UTF-8/I-JSON-compatible boundaries where JSON is used.
- Key bootstrap, pinning, rotation, revocation, compromise recovery, and historical verification rules.

A DSSE-compatible envelope or an equivalently reviewed typed-signature standard is preferred over a custom raw-signature format. Deterministic JSON used for content hashing must use a fully specified canonicalization implementation with cross-language golden vectors. Capsule-signing, event-anchoring, and release-signing keys must be separated by purpose; release authority requires human or independently authenticated quorum approval.

---

## 8. Formal state machines

### 8.0 Normative transition specification

The diagrams below are summaries. Before implementation, each aggregate must have a machine-readable transition table containing:

- Command and current state.
- Authenticated actor and required capability.
- Preconditions, policy decision, source/state version, and approval requirements.
- Atomic writes and emitted event.
- Idempotency and replay behavior.
- Failure, timeout, crash, retry, revocation, and reconciliation path.
- Resulting state and invariants.

State and its audit event must commit in the same transaction. Task and engagement status should be derived from child records where practical rather than independently mutable. No transition may rely on an agent merely reporting that it happened.

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

“Action” is split into aggregates with different owners and lifecycles:

```text
ActionDefinition: DRAFT → VALIDATED → SUPERSEDED

ActionCapsule: ISSUED → ACTIVE → CONSUMED
                         ↘ EXPIRED | REVOKED

ActionAttempt: CREATED → RUNNING → SUBMITTED → VERIFIED
                    ↘ FAILED | ABORTED | REPAIR_REQUIRED

ReviewRecord: PENDING → ACCEPTED | REJECTED | DISPUTED
```

Capsule redemption and attempt creation are one transaction protected by a unique capsule ID, action sequence, and state version. A capsule cannot be reused simply because the actor, project, and seal are unchanged. Submission records the base seal, authorized patch or artifact, and result seal. Verification reconstructs the candidate independently from the base plus submission.

### 8.3.1 Authoritative repository promotion

For v8.0, the fully assured path should initially support Git repositories only unless a non-Git protocol is separately proven:

```text
PromotionIntent: PREPARED → APPLYING → REF_UPDATED → VERIFIED → FINALIZED
                              ↘ RECONCILIATION_REQUIRED
```

1. Lock and identify the authoritative `base_seal`, expected old ref/commit, target ref, attempt ID, and state version.
2. Create an isolated disposable clone with its own Git object/config/ref store. A linked worktree is allowed only if the shared Git common directory and authoritative refs/config are unreachable or provably read-only to the builder.
3. Let the agent edit only the isolated candidate through the broker. Disable or isolate hooks, filters, credential helpers, alternates, and repository configuration that could execute or reach the authoritative store.
4. Submit a broker-owned content-addressed delta and artifact inventory; do not trust a builder-created commit as the promoted authority.
5. Reconstruct the candidate from the trusted base plus broker-owned delta in a fresh verifier clone and compute `result_seal` and verified tree digest.
6. Bind checks, evidence, and review to both base and result. A positive review moves criteria only to `PROMOTION_PENDING`, never directly to final acceptance.
7. Persist a `PromotionIntent` containing attempt ID, expected old ref/commit, verified result tree digest, target ref, state version, and idempotency key before crossing the database/Git boundary.
8. Have the promotion service create the trusted tree/commit with hooks and filters disabled, then update the authoritative ref using compare-and-swap against the expected old commit.
9. Recompute the authoritative source seal from the updated ref and require exact equality with the independently verified `result_seal` before finalizing state.
10. Finalize criterion/task acceptance, produce the next authoritative seal, revoke stale capsules, and record promotion evidence only after Git and database reconciliation agree.
11. On drift, conflict, mismatch, or crash, enter `RECONCILIATION_REQUIRED`; never silently merge or infer acceptance. Require explicit rebase/amendment or safe rollback/forward completion.

Crash injection must cover every boundary between submission, evidence, review, promotion, Git commit, state commit, and capsule revocation. Reconciliation must make an accepted-but-unpromoted or promoted-but-unrecorded result observable and recoverable.

Every control-plane Git invocation uses a hardened profile: a pinned Git binary, isolated HOME and configuration, sanitized environment, disabled hooks, pagers, editors, credential helpers, signing commands, fsmonitor, external diff/merge drivers, and repository-defined clean/smudge/process filters. LFS, submodule, alternate-object-store, and network operations are never automatic; they require separate brokered import logic and immutable provenance. The promotion service consumes validated objects/deltas and constructs the trusted commit without executing repository-controlled helpers. Malicious `.git/config`, `.gitattributes`, hook, filter, LFS, submodule, alternates, and environment tests are mandatory.

### 8.4 Standard substantive action sequence

```text
UNDERSTAND → PLAN → IMPLEMENT/REPAIR → VERIFY → EVIDENCE → HANDOFF → REVIEW
```

No later action may be claimed until the predecessor is accepted or a signed amendment changes the sequence.

The gates are mandatory, but risk policy decides whether UNDERSTAND and PLAN require separate capsules or may be structurally submitted and accepted in one low-risk session. A fast path may reduce ceremony; it may not omit validation, criterion mapping, scope limits, checks, or stop conditions.

### 8.5 Acceptance criterion

```text
NOT_STARTED → IMPLEMENTED → EVIDENCE_READY → VERIFIED
→ INDEPENDENTLY_REVIEWED → PROMOTION_PENDING → ACCEPTED
```

`STALE` is a nonterminal invalidation state reached when relevant source, policy, criterion, checker, or evidence changes. Recovery from `STALE` requires fresh proof; it is never an automatic return to `ACCEPTED`.

### 8.6 Side effect

```text
PROPOSED → APPROVAL_REQUIRED → APPROVED → PREPARED → DISPATCHING
→ EXECUTED → EXTERNALLY_VERIFIED → COMMITTED
```

Indeterminate and recovery paths:

```text
DISPATCHING → OUTCOME_UNKNOWN → RECONCILING
RECONCILING → EXECUTED | FAILED | COMPENSATION_REQUIRED | MANUAL_RECONCILIATION
COMPENSATION_REQUIRED → COMPENSATED | MANUAL_RECONCILIATION
```

Terminal alternatives are `DENIED`, `ABORTED`, known `FAILED`, `COMPENSATED`, and `MANUAL_RECONCILIATION`. `COMMITTED` means LAOS has recorded a provider-reconciled, externally verified final outcome and completed its local obligations; it does not mean the remote effect and local database were one atomic transaction.

`PREPARED` creates a transactional outbox record containing the canonical target, operation, payload digest, credential identity, approval, policy, repository seal, provider idempotency key, expiry, and reconciliation method. If dispatch may have occurred but no authoritative receipt exists, the only safe state is `OUTCOME_UNKNOWN`; irreversible operations in that state must not retry automatically.

### 8.7 Release artifact

```text
PLANNED → BUILT → HASHED → EXTRACTED → RETESTED → ATTESTED
→ FROZEN → PUBLISHING → PUBLISHED
```

Publication also needs `PUBLICATION_UNKNOWN` and `RECONCILIATION_REQUIRED` alternatives when an external store may have accepted an artifact but the local receipt was lost. Consumer verification must reject unauthorized signer identity, expired or revoked trust metadata, version rollback, and a signature whose artifact, subject, issuer, or audience does not match expected policy.

---

## 9. Program milestones

The work is ordered so that later features cannot hide an unsafe foundation.

### 9.0 Milestone contract and dependency discipline

Every milestone record in the active requirements ledger must include:

- `depends_on` and an entry gate.
- `MUST_V8_0`, `SHOULD_V8_0`, or `DEFER_V8_X` scope classification.
- Concrete deliverables and non-goals.
- Named owner, reviewer, external dependency, and estimate range.
- Functional, security, performance, operability, and migration acceptance criteria where applicable.
- Required evidence, independent verifier, and rollback/recovery procedure.
- Open cross-subsystem requirements that cannot close until a later integration milestone.

A milestone gate applies only to capabilities implemented by that milestone. Earlier milestones may define contracts and test them against minimal fakes, but they may not claim integrated enforcement by a subsystem that does not exist. Cross-subsystem requirements remain `OPEN` in the ledger until the owning integration gate passes.

### 9.0.1 Bootstrap assurance policy

The program cannot use v8 evidence, review, signing, and provenance machinery before that machinery exists. Until those subsystems are independently accepted:

- Evidence is labeled `BOOTSTRAP` and consists of external CI outputs, Git commits/tags, immutable manifests, command transcripts, and named independent review.
- “Freeze” means an immutable Git tag plus an evidence snapshot, not an assertion that a local file can never change.
- Critical bootstrap gates are rerun through the completed v8 evidence, review, and attestation path before release.
- A later change requires an amendment and impact analysis; it never silently preserves an earlier PASS.

### 9.0.2 Mandatory Security Spine Gate

No real weaker-agent calibration, repository capture, untrusted build/test command, or implementation action may run until a minimum enforcement spine exists and passes adversarial tests. This gate may implement narrow slices from later milestones earlier than their full feature completion. It requires:

1. A documented deployment/enforcement contract and support matrix.
2. Strict protocol models and stable error/result envelopes.
3. Transactional state plus same-transaction audit events and capsule redemption.
4. Base/result seals and a disposable candidate workspace.
5. Authenticated identity, a protected test signer, current policy checks, expiry, and revocation semantics appropriate to connected mode.
6. A structured command/workspace broker and one real qualifying sandbox provider.
7. Network denial, no raw secrets, resource limits, and emergency stop.
8. A governed model-call path or an explicitly local-only row, with data classification/minimization, provider policy, built-in tool denial, and transmission canaries.
9. Broker-captured evidence and a separate clean verifier workspace.

Offline unit tests, schema tests, pack construction, and fixture generation may precede this gate. Real agent activity against untrusted content may not.

### 9.0.3 Alpha Vertical Trust Slice

Immediately after the Security Spine Gate—and before full pack variants, automatic profile adaptation, external side effects, or advanced provenance—the program must complete one end-to-end low-risk slice:

1. Initialize one disposable fixture Git repository containing a known defect.
2. Define one task and one independently testable criterion.
3. Issue one typed, signed, expiring capsule to one authenticated execution session.
4. Redeem it exactly once and create an isolated disposable candidate clone with no writable/shared Git control data.
5. Permit one bounded edit through the broker while denying out-of-scope writes, network, secrets, and future actions.
6. Run one deterministic check in the qualifying sandbox.
7. Reconstruct and verify base plus patch in a clean workspace.
8. Capture broker-owned evidence bound to the result seal.
9. Obtain a verdict from a distinct authenticated reviewer and either promote or return one bounded repair.
10. Demonstrate denial of replay, self-review, stale-base promotion, evidence mutation, out-of-root access, and unauthorized command execution.
11. Inject a crash at redemption, submission, verification, and promotion boundaries and reconcile safely.

The result may be published only as an Alpha proof artifact. A small randomized development-set pilot must then compare a broad prompt, a resource-matched structured prompt, v7, and the Alpha trust slice. The pilot is for architecture pruning and budget setting; it cannot support the final efficacy claim.

### 9.0.4 Go/no-go and scope-freeze decision

After the Alpha pilot, Nilhan and an independent reviewer must decide whether to:

- Continue the architecture substantially unchanged.
- Simplify or replace controls that did not prevent observed failures.
- Defer nonessential scope.
- Stop the v8 program if the trust spine cannot mediate the executor or if cost and friction overwhelm the benefit.

At this point the `MUST_V8_0` scope freezes. A new MUST item requires removing equivalent scope, moving an existing item to `DEFER_V8_X`, or documenting a newly validated non-waivable release blocker.

### 9.0.5 Continuous operability, migration, and performance workstreams

CLI, documentation, migration discovery, security incident handling, and performance measurement begin with the kernel and continue through every milestone; they are not postponed to Milestone 15. Before Alpha, the program must create:

- A supported host/Python/Git/SQLite/filesystem/sandbox matrix.
- `PERFORMANCE_BUDGETS.md` with measurement definitions and conservative pre-Alpha safety/cost circuit breakers for manifest time/memory, pack size and latency, state transitions under contention, sandbox startup, evidence growth, full-suite duration, flake rate, tokens, cost, retries, and human minutes.
- A v7 feature-parity and migration matrix with copy-on-write import, dry run, deterministic mapping report, unknown-field quarantine, idempotent rerun, rollback, and coexistence rules.
- A minimal `doctor`, `status`, denial-explanation, backup/restore, evidence export/purge, and trust-recovery operator path.

Before Alpha, scope tiers and budgets are provisional except for non-negotiable safety constraints and the minimum experiment. The Alpha pilot sets the numeric performance budgets and final `MUST_V8_0` scope. Those values freeze at the go/no-go review and may not change after the sealed evaluation charter freezes.

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

### Entry decision

First reconstruct the Stage 0 Git repository, verify its tag and manifests, import plan revision 1.1, and reconcile the requirements ledger, threat model, ADRs, backlog, and blocker ledger. Then make a time-boxed decision:

- If v7 remains operationally used, build and independently release v7.0.1 from a separate branch without modifying the original v7 archive.
- If v7 is not used operationally, do not let a maintenance release block v8. Extract the failing regression fixtures and compatibility expectations into v8, record the no-release decision, and proceed.

### Work

Items 1–12 are implemented in v7 only on the maintenance-release track. On the fixture-only track, the same numbered behaviors are captured as reproducible failing/compatibility fixtures for v8; they are not repaired in v7 and must not be reported as closed.

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
13. Create a v7-to-v8 feature-parity and migration fixture matrix.
14. If a v7.0.1 artifact is published, give it its own clean-build, safe-extraction, checksum, manifest, regression, and durable-publication gate.

### Exit gate

Shared exit requirements:

- The active v8 repository records this reviewed plan and reconciled machine-readable ledgers.
- The v7-to-v8 feature-parity/migration matrix and reproducible regression fixtures exist.

Maintenance-release path:

- An unchanged captured repository passes continuation freshness verification, a one-byte tracked change fails, malformed App Intelligence cannot pass, and pre-claim/symlink regressions are closed.
- A separately verified v7.0.1 artifact exists and remains clearly distinct from v8 and the immutable v7.0 source.

Fixture-only path:

- The original failing/weak v7 behavior remains recorded as baseline evidence; no v7.0.1 correctness or release claim is made.
- A signed no-release decision identifies the reason, imported fixtures, compatibility expectations, and v8 milestones that own each repair.

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
10. Select the supported platform matrix and record exact Python, Git, filesystem, and SQLite behavior.
11. Run dependency proofs of concept for schema validation, strict duplicate-key parsing, typed models, migrations, signing envelopes, and property testing before committing to libraries.
12. Pin direct and transitive dependencies, build tools, CI actions, and base images by reviewed version or digest with hashed lock material.
13. Define the signed/hashed record profile, error-code registry, transition-table format, and cross-language golden vectors.
14. Start CI on every supported development platform; do not wait for release-candidate work.
15. If SQLite WAL is enabled, require a runtime containing the upstream WAL-reset fix and verify the actual linked SQLite version at startup and in CI. At this revision, upstream identifies 3.51.3+ and fixed backports 3.50.7/3.44.6; implementation must re-check the advisory rather than infer safety from a version string alone. Older or unverified runtimes must use a safe fallback or remain unsupported.

### Mandatory contract regression

At this milestone the complete side-effect subsystem does not exist. The kernel must nevertheless prove, using a minimal in-memory adapter, that an unauthorized builder attempting the future side-effect-verification transition would:

- Be denied before any external operation.
- Produce `AuthorizationDenied` or its stable serialized equivalent.
- Record a security event.
- Leave the side-effect record unchanged except for the denied attempt audit entry.

This closes only the error, transition, and serialization contract. The integrated regression remains `OPEN` until the identity, policy, transactional event, and side-effect broker are implemented and is rerun in Milestone 12.

### Exit gate

- All models, schemas, migrations, and error contracts pass unit and property tests.
- Unknown or malformed trusted records fail closed.
- Authorization error contracts are stable and consistent across implemented kernel boundaries; unimplemented subsystem integrations remain explicitly open.
- The support matrix, crypto profile, dependency decision record, CI, and platform golden vectors exist.

---

# Milestone 3 — Repository truth, safe paths, identity, and transactional state

### Objective

Create trustworthy execution foundations that cannot be bypassed through timing, path tricks, concurrency, or self-declared identities.

### Work

#### Repository truth

1. Implement one canonical manifest algorithm covering regular files, symlink objects, byte size, SHA-256, mode, and Git truth where available.
2. Define one versioned ignore policy.
3. Detect additions, deletions, modifications, mode changes, link-target changes, and case collisions.
4. Implement distinct source, base, result, workspace, and evidence-export seals with lineage.
5. Content-address seals now; use only the protected test signer required by the Security Spine until Milestone 5 completes production key management.
6. Define binding contracts for future capsules, check runs, evidence objects, and reviews; close each integration only in its owning milestone.
7. Make stale source automatically invalidate dependent proof.
8. Define and implement isolated candidate clones, broker-owned deltas, clean reconstruction, `PromotionIntent`, Git compare-and-swap ref update, authoritative-seal equality, conflict handling, crash reconciliation, and rollback/forward-completion protocol.
9. Support fully assured promotion for Git repositories first; label non-Git mutation unsupported until separately proven.
10. Publish cross-platform golden vectors covering Git LFS, submodules, sparse checkout, untracked and ignored files, line endings, case, Unicode, modes, junctions, reparse points, hooks, filters, alternates, linked-worktree common directories, and trusted commit construction.

#### Safe paths

11. Use handle-relative, no-follow filesystem operations rather than check-then-open path strings. If a claimed platform lacks a race-safe primitive, mutation requires an isolation/mount boundary that makes replacement impossible; otherwise that mutation support row is unsupported.
12. On POSIX, use dirfd/`openat2`-equivalent containment where available; on Windows, validate final handles and reparse-point behavior and reject UNC/device paths, alternate data streams, short-name aliases, and unexpected hard links according to policy.
13. Reject absolute external paths, `..`, symlink/junction/reparse escapes, concurrent link swaps, mount changes, and unsafe archives.
14. Enforce read, write, test, evidence, artifact, and runtime areas separately.
15. Add safe extraction limits for entry count, total size, ratio, nesting, duplicate names, case collisions, links, and decompression resource use.

#### Transactional state

16. Use SQLite as the default single-host canonical state store on a local filesystem only; network filesystems and distributed coordination are unsupported.
17. Enable foreign keys and transactional state transitions; append the corresponding audit event in the same transaction.
18. Add a transactional outbox for operations that cross the database boundary.
19. Use WAL only after verifying a fixed SQLite runtime, documented durability settings, checkpoint policy, busy handling, local-filesystem support, crash recovery, and backup behavior.
20. Add schema migrations, integrity checks, backup/recovery, state-fork, rollback, and clock-rollback tests.
21. Store aggregates so their invariants can commit atomically; normalization must not fragment one invariant across unreliable transactions.
22. Use unique constraints to prevent double claims, capsule replay, and duplicate idempotency keys.
23. Use compare-and-swap version fields where needed.
24. Use database time or carefully bounded monotonic lease logic; do not rely only on untrusted agent wall-clock values. Define clock-skew and rollback behavior.
25. Generate human-readable JSON/Markdown views from the database; never use them as canonical mutable state.

#### Identity and capabilities

26. Implement authenticated actor identities and short-lived capability grants.
27. Separate Architect, builder, investigator, tester, verifier, reviewer, approver, signer, and release-verifier roles.
28. Store only token hashes or external identity references.
29. Support expiry and connected-mode revocation with measured propagation behavior.
30. Bind actions to issuer, actor, role, project, broker/provider audience, action-definition digest, base seal, policy version, state version, capsule ID, attempt sequence, issue time, expiry, and revocation epoch.
31. Define independence levels. Distinct names or roles sharing an account, key, session, writable workspace, or controlling principal do not count as independent.

### Exit gate

- Two workers cannot claim the same action.
- A changed repository cannot be hidden by claiming after the edit.
- An authorized edit produces a new result seal, verifies in a clean reconstruction, and promotes only if its base is still authoritative.
- Path and symlink escapes are denied.
- Actor-name spoofing cannot satisfy role separation.
- Crash/restart tests preserve valid state or fail safely.
- State and its audit event cannot diverge; outbox reconciliation covers database/filesystem boundary failures.
- The Security Spine uses only supported local SQLite and filesystem configurations.

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
4. Define invalidation semantics when policy or model profiles change and enforce them against the Security Spine's minimal test grants. Full Action Capsule integration closes in Milestone 5.
5. Add human-approval requirements for irreversible or consequential operations.
6. Add critical-task quorum rules with at least two genuinely independent verifications plus any required human approval. Architect adjudication may resolve ordinary disputes but cannot substitute for critical quorum.
7. Add resource budgets for time, CPU, memory, processes, network, token use, and retry count.
8. Add circuit breakers for repeated failures and cascading errors.
9. Add taint labels for untrusted repository text, external content, user-provided data, and generated instructions.
10. Ensure repository content can never override signed control-plane instructions.
11. Create a permission-to-enforcement-point matrix for every claimed capability and identify any bypassable path as unsupported.
12. Return a structured policy decision containing rule IDs, inputs, allow/deny result, obligations, and safe operator explanation without exposing hidden evaluator content or secrets.
13. Treat Architect decisions as proposals subject to policy. Architect adjudication cannot override human/quorum requirements, non-waivable policy, or sandbox requirements.
14. Protect policy rollback and downgrade using monotonic versions or externally anchored epochs.
15. Define a trusted approval UI/API isolated from model and tool output. It displays normalized target, operation, data class, credential identity, maximum cost/consequence, expiry, and payload digest; uses step-up authentication for consequential actions; prevents Unicode/bidirectional/hidden-field confusion; and signs the exact displayed transaction.

### Exit gate

- Every implemented control-plane and broker boundary denies by code; capabilities whose enforcement brokers do not yet exist remain unclaimed and fail closed at the Security Spine.
- Policy changes revoke incompatible Security Spine test authority; the full capsule regression remains open until Milestone 5.
- Critical operations cannot proceed without the required approvals and isolation.
- The enforcement-point matrix has no undocumented bypass for the Alpha support profile.

---

# Milestone 5 — Pack separation, signing, and leak prevention

### Objective

Compile physically separate trust-zone packages from allowlisted public projections and close the defined leakage paths in the threat model. The program must not claim that a general-purpose scanner can prove the absence of every semantic or covert leak.

### Work

1. Implement Architect Control Pack compilation.
2. Implement Agent Execution Pack compilation.
3. Implement Capture Execution Pack compilation.
4. Implement Review Capsule compilation.
5. Implement single Action Capsule issuance.
6. Sign pack manifests and capsules using the reviewed typed-envelope profile selected in Milestone 2; Ed25519 may be the primitive but must not be used as an ambiguous raw JSON signature.
7. Keep private signing keys outside generated packs.
8. Include public verification material only where needed.
9. Add capsule ID, issuer, audience, action-definition digest, attempt sequence, state version, issue time, expiry, revocation epoch, base seal, actor binding, role, permissions, policy digest, profile digest, skill digest, and criteria.
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
13. Construct execution packs from allowlisted typed projections; never subtract private fields from a full control-plane object.
14. Implement separate capsule, event-anchor, and release key purposes; key IDs, bootstrap/pinning, rotation, revocation publication, compromise response, historical verification, and anti-rollback behavior are mandatory.
15. Test unknown and substituted keys, algorithm downgrade, duplicate keys, encoding variants, cross-object signature reuse, revoked keys, expired trust metadata, wrong issuer/audience/subject, and concurrent capsule redemption.
16. Retire the Alpha test trust root before Beta: revoke it and every derived capsule/approval, remove it from production verifier trust, prevent continuity from Alpha to production roots, and preserve it only as explicitly historical test evidence.

### Exit gate

- The weaker-agent pack contains only fields allowed by its versioned public projection; seeded future-action, hidden-check, secret, and evaluator canaries are absent.
- Modifying any signed pack or capsule causes verification failure.
- A capsule cannot be replayed against another project, actor, repository seal, policy version, or time window.
- In connected privileged mode, the same capsule cannot be redeemed twice within one valid time window. Offline v8.0 has no privileged redemption path.
- Key substitution, signature-context confusion, downgrade, revoked trust, and release/capsule key-purpose confusion fail closed.
- Alpha-root signatures are rejected by Beta/RC/GA verifiers and cannot authorize migration, review, side effects, or release.

---

# Milestone 6 — Anti-Skip Action Engine

### Objective

Make skipping deterministic state and policy gates impossible at mediated boundaries and make heuristic or semantic omissions visible for Architect/reviewer adjudication.

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
4. Deterministically reject missing required fields, unmapped criteria, invalid references, and out-of-scope content. Treat semantic vagueness as a heuristic finding requiring Architect or reviewer adjudication; do not claim it is fully machine-decidable.
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
12. Keep mutation actions serialized by default for v8.0. A non-interference analyzer may enable parallel work only after disjoint writes, compatible reads, independent criteria, base/result-seal merge semantics, and side-effect independence are demonstrated; otherwise defer it to v8.x.
13. Classify every control as deterministic machine enforcement, OS/sandbox enforcement, heuristic detection, Architect adjudication, or independent review. Documentation and release claims must use the correct class.

### Exit gate

- A weaker agent cannot claim IMPLEMENT before UNDERSTAND and PLAN are accepted.
- A later action cannot be revealed or used early.
- The action engine refuses a close request with an incomplete criterion according to the current contract; integrated evidence and independent-review closure remains open until Milestones 10 and 11.
- Repeated identical failure triggers repair, reduction, recovery, or Architect escalation.
- The Alpha Vertical Trust Slice passes before full workflow expansion continues.

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
3. Implement offline profile fixtures first. Run small real calibration actions only after the Security Spine Gate passes, in disposable supported workspaces with broker-owned evidence.
4. Record observed compliance, skip rate, scope adherence, tool use, and evidence quality.
5. Reduce action size automatically when performance degrades.
6. Escalate tasks that exceed a profile’s demonstrated safety ceiling.
7. Implement a prompt linter that rejects missing role, goal, finish line, scope, checks, evidence, stop conditions, unavailable-tool handling, or final response format.
8. Deterministically detect unresolved placeholders, size limits, forbidden permissions, and structural contradictions where possible; label broader semantic contradiction detection as heuristic and require adjudication.
9. Create context manifests distinguishing:
   - Signed instruction
   - Trusted project truth
   - Evidence
   - Untrusted repository content
   - Untrusted external content
10. Compact handoffs without deleting blockers, conflicts, or uncertainty.
11. Add an explicit uncertainty ledger; unresolved facts stay unknown until resolved.
12. Record exact provider, model identifier or snapshot, tool versions, settings, prompt/profile digest, date, and environment for every calibration. A provider alias without a stable snapshot is treated as drift-prone.
13. Keep development/calibration tasks separate from the locked validation and sealed final-holdout evaluation partitions.

### Exit gate

- Every prompt snapshot passes linting.
- Each released profile has calibration evidence.
- Oversized work is decomposed automatically.
- A model profile cannot silently grant more authority than policy allows.
- No real calibration ran before the qualifying enforcement and evidence path existed.

---

# Milestone 8 — New-build compiler and existing-application capture/continuation

### Objective

Implement both claimed Architect workflows: compile a new product objective into a governed first action, and let weaker investigators gather existing-application evidence without alteration before the Architect validates continuation work.

Real capture is prohibited until the Security Spine Gate and a read-only sandbox profile pass. Before that gate, this milestone may implement and test capture contracts only against trusted fixtures.

### Work

#### Existing-application capture and continuation

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
13. Treat repository-supplied build, test, package-manager, Git hook, IDE task, binary, and script execution as arbitrary untrusted code. “Read-only investigation” does not make those commands low risk; they require a qualifying sandbox and network/secret denial.
14. Bind each accepted fact to source evidence, capture tool/version, base seal, data classification, and expiry/freshness rule.
#### New-build compiler

15. Define strict `ProductObjective` and `NewBuildRequest` contracts containing goals, users, constraints, non-goals, data classes, risk posture, target support environment, and unresolved decisions.
16. Require an authenticated Architect proposal and human acceptance record for the blueprint, requirement/criterion graph, security boundaries, budget, and initial scope. Model prose alone cannot create the project authority.
17. Version, validate, and supersede blueprints explicitly; reject cycles, orphan criteria, unresolved mandatory decisions, stale acceptance, and silent requirement loss.
18. Select scaffolds/templates only from a reviewed, content-addressed registry with toolchain, dependency, license, provenance, and compatibility metadata. Repository-supplied or mutable remote templates cannot become trusted genesis input.
19. Have the control plane create an isolated genesis Git repository, sanitized Git configuration, trusted initial tree/commit, `SourceSeal`, and `BaseSeal`; the weaker agent never creates the authoritative genesis state.
20. Make compile, retry, and recovery idempotent. Partial initialization is quarantined and either safely resumed from its intent record or destroyed without affecting another project.
21. Issue the first capsule only from the sealed genesis commit and accepted blueprint digest.
22. Test mutable/template substitution, duplicate generation, partial initialization, stale blueprint, cross-project path collision, malicious Git configuration, missing provenance, and unsealed first-action denial.
23. Produce a blueprint-to-genesis-to-first-action trace and compare it with the required v7 new-build behavior in the feature-parity matrix.

### Exit gate

- Capture cannot modify product code.
- A malformed or stale return cannot pass.
- The Architect acceptance record distinguishes accepted, rejected, conflicted, and unknown facts.
- An unchanged repository passes continuation verification; drift blocks it.
- New-build and existing-application workflows each pass their own end-to-end round trip. If either is missing, the artifact remains a pre-release or technical preview and cannot be v8.0 GA.

---

# Milestone 9 — Command broker, sandbox, and clean verifier

### Objective

Prevent weaker agents from obtaining arbitrary host authority and make every command reproducible and attributable.

The narrow broker and one qualifying provider required by the Security Spine are built before real agent work. This milestone matures that implementation; it is not the first point at which isolation appears.

### Work

1. Replace shell strings with structured executable-and-argument arrays.
2. Treat every executable—including package-manager scripts, compilers, tests, Git hooks, repository binaries, interpreters, and browser automation—as arbitrary code whose risk comes from behavior, not shell syntax alone.
3. Require explicit working directory, environment allowlist, timeout, resource limit, process/child-process policy, executable identity, and network policy.
4. Deny dangerous operations by default, including destructive root deletion, privilege escalation, hard reset/clean, disk operations, host socket/device access, and download-pipe-shell patterns.
5. Allow shell semantics only through a separately approved high-trust exception inside a qualifying sandbox; a signature alone is insufficient.
6. Stream output into tamper-evident transcripts with size controls, classification, and secret containment/redaction.
7. Implement provider interface for:
   - Local low-risk execution for explicitly trusted fixtures only, labeled unassured and excluded from untrusted-agent claims
   - Docker/container execution
   - Managed sandbox execution
   - Future microVM provider
8. Define a signed `SandboxAssuranceProfile` covering provider/image digest, rootless or non-root execution, capability drop, no-new-privileges, syscall/device/socket policy, read-only root filesystem, mounts, resource quotas, network/DNS/metadata denial, process limits, teardown, host-sharing assumptions, and provider version.
9. High-risk actions must fail closed when no qualifying sandbox is available. Ordinary containers must not be labeled equivalent to VM/microVM isolation without evidence.
10. Mount only the intended candidate repository and required ephemeral paths; never mount the control plane, signer, evidence escrow, host container socket, credential stores, or authoritative repository.
11. Run as non-root with no privilege escalation.
12. Prefer a credential broker that performs the approved operation without revealing raw secrets. When exposure is unavoidable, use audience-bound, per-command, short-lived, non-inherited handles rather than broad environment variables.
13. Disable network by default. An egress broker must validate DNS resolution, redirects, proxies, IPv4/IPv6 targets, private/link-local/loopback ranges, cloud metadata endpoints, destination identity, method, and payload data class at each hop.
14. Apply the same side-effect and egress controls to browser automation; a browser is not a read-only network client.
15. Run acceptance checks in a clean verifier workspace, principal, and context separate from the builder’s mutable workspace.
16. Add mandatory provider-specific conformance tests for every provider and host-platform row claimed by the release, including Windows/WSL/Docker Desktop behavior where applicable.
17. Test encoded/chunked exfiltration, child-process inheritance, crash dumps, artifact leakage, DNS rebinding, redirects, proxy bypass, metadata access, socket/device mounts, sandbox teardown, and resource exhaustion.

### Exit gate

- No general `shell=True` path exists for normal checks.
- A high-risk action cannot fall back silently to host execution.
- Commands, environment, outputs, exit status, and source seal are fully recorded.
- Clean verification detects builder-environment-only success.
- Every claimed provider passes its complete assurance profile in the claimed host environment; “where available” cannot waive conformance.
- No real capture, calibration, or implementation run predates the recorded Security Spine PASS.

---

# Milestone 10 — Evidence engine and criterion-level closure

### Objective

Replace agent-written completion claims with fresh, automatic, criterion-linked proof.

### Work

1. Create the repository-root `Evidence/` folder in every managed project.
2. Store canonical evidence in a broker-controlled, content-addressed area not writable by the builder; expose signed read-only indexes or redacted copies under `Evidence/`. The project-facing folder is explicitly noncanonical.
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
12. Classify and minimize evidence before persistence. Define encryption-at-rest, access-control, retention, legal/consent, export, purge, tombstone, and backup-deletion behavior for source, screenshots, API data, database observations, prompts, and model traces.
13. Prefer structured observations and hashes over raw captures. Store raw sensitive material only when a criterion requires it and policy permits it.
14. Detect builder writes to the project-facing `Evidence/` view, but do not confuse that view with canonical proof or product-source truth.
15. Record collector version, environment, data classification, redaction method, source/result seal, criterion, policy, and chain of custody for every evidence object.

### Exit gate

- A task cannot close on prose alone.
- Stale evidence is rejected.
- Every mandatory criterion has current proof at the required level.
- Evidence tampering or missing objects causes verification failure.
- Retention and purge tests prove that sensitive evidence is neither silently retained nor deleted while a release/legal hold requires it.

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
6. Ensure the reviewer is a distinct authenticated principal, credential/key, writable workspace, and authority domain. Critical review always uses a fresh context; lower-risk reuse must be explicit policy.
7. Give the reviewer the original criterion contract, final source, evidence, and authorized hidden checks—not a persuasive builder narrative.
8. Instruct reviewers to try to disprove completion.
9. Record a verdict for each criterion.
10. Prevent review actions from silently repairing product code.
11. Return defects to bounded repair actions.
12. Require Architect adjudication for ordinary disagreements, but do not allow the Architect to bypass non-waivable policy, human approval, or critical quorum.
13. Require dual review or quorum for critical tasks.
14. Prevent an issuer, builder, reviewer, parent delegator, or shared controlling principal from counting as multiple members of its own quorum.
15. Protect grader and hidden-check independence from the Architect implementation context during confirmatory evaluation.

### Exit gate

- A builder cannot review or accept its own work.
- Review covers every mandatory criterion.
- Test weakening, hidden-check alteration, and unsupported evidence are detected.
- Critical-risk work satisfies quorum policy.
- The release records the independence level actually achieved; local role labels are never presented as organizational or hardware independence.

---

# Milestone 12 — Side effects, approvals, recovery, and anti-thrashing

### Objective

Control consequential external actions and make interruption or failure recoverable.

### Work

#### Side effects

1. Implement the full side-effect lifecycle.
2. Require proposer, approver, executor, independent verifier, idempotency key, payload digest, expected result, verification method, receipt, and compensation plan where applicable.
3. Use the transactional outbox and provider-native idempotency where available; persist provider operation IDs and reconcile before any retry. Do not promise exactly-once execution.
4. Require human or governed approval for production deployment, spending, email/public publishing, data export, destructive migration, credential creation, and irreversible cloud operations.
5. Keep unauthorized attempts as auditable denial events.
6. Use the stable `AuthorizationDenied` contract for all role failures.
7. Bind approval to the canonical target, operation, payload digest, credential identity, base/result seal, policy, adapter, expiry, and maximum consequence. Material change invalidates approval.
8. Require approval through the trusted display/signing channel. Model prose, terminal output, screenshots, or agent-generated forms are never the authorization surface; the signed display digest must match the dispatched transaction.
9. Implement `OUTCOME_UNKNOWN`, reconciliation, and compensation states. Irreversible indeterminate operations never retry automatically.
10. Name the external adapters actually supported by v8.0. If none pass real non-production conformance and crash testing, release only the mandatory deny-all broker protocol and state clearly that production side effects are unsupported.

#### Recovery

11. Create immutable/content-addressed checkpoints before risky actions.
12. Scope checkpoints to authorized paths and record the repository seal.
13. Implement safe recovery that does not delete unrelated files.
14. Add claim leases and heartbeats.
15. Reclaim expired work safely.
16. Track failed-approach signatures.
17. Escalate repeated identical failures.
18. Support signed amendments, task reopening, recapture, and manual reconciliation.

#### Security incident and trust recovery

19. Implement an emergency stop that freezes capsule issuance, privileged dispatch, side effects, and publication.
20. Support mass revocation of capsules, approvals, sessions, credentials, and affected trust roots.
21. Quarantine candidate workspaces and preserve tamper-evident forensic material without contaminating canonical evidence.
22. Define compromise playbooks for the Architect account, control-plane host, signer, evidence broker, sandbox provider, identity provider, release key, and external adapter.
23. Rotate keys and secrets, restore from an externally anchored recovery point, revalidate accepted state, reissue authority, and publish revocation/re-attestation records.
24. Run tabletop and executable drills; every incident yields regression candidates and an explicit notification/ownership record.

### Exit gate

- Side effects cannot bypass approval, identity, idempotency, or external verification.
- Unauthorized verification produces the correct security exception and no state advance.
- Interrupted actions recover without losing accepted history.
- Repeated failure cannot loop indefinitely.
- Crash tests before dispatch, after dispatch, and before receipt persistence enter the correct known or indeterminate state without unsafe automatic retry.
- Compromise drills demonstrate kill switch, revocation, quarantine, trust rebootstrap, and externally verifiable recovery.

---

# Milestone 13 — Tamper-evident events, artifacts, provenance, and release truth

### Objective

Make the release independently verifiable and prevent mutable runtime data from contaminating static integrity claims.

### Work

#### Event and provenance records

1. Append events transactionally.
2. Hash-chain event exports.
3. Sign critical decisions, packs, capsules, artifacts, and release records.
4. Anchor critical event heads outside the working repository at a bounded cadence using an independent key/store, transparency log, or WORM target. Local hash chains alone are only tamper-evident within the compromised host boundary.
5. Detect truncation, gaps, forks, rollback, stale anchors, inconsistent tree heads, and anchor outage. Critical issuance or release must block when its required anchoring assurance is unavailable.
6. Produce a version-pinned in-toto-compatible attestation and an exact, declared SLSA Build/Source track target rather than vague “SLSA-style” provenance.
7. Use a selected Sigstore/Cosign identity-and-issuer policy, KMS/offline-key policy, or equivalent reviewed profile. Verification must check the expected identity, issuer, artifact digest, predicate, audience, timestamp/transparency material, and trust root—not signature validity alone.
8. Define consumer-side update metadata with authorized version, expiry, trust-root rotation, rollback and freeze protection, or explicitly state that v8.0 has no automatic update mechanism.

#### Static versus mutable separation

9. Define an immutable release inclusion policy.
10. Exclude all live runtime files, including SQLite databases, WAL/SHM files, locks, leases, logs, current evidence indexes, caches, and temporary output.
11. Ship only database migrations and initialization code.
12. Add tests proving that release manifests never include mutable runtime state.
13. Add tests proving that an extracted release initializes a new runtime database after installation.

#### Deterministic release build

14. Build source ZIP and wheel from a clean staging directory using pinned builders, CI actions, tools, dependencies, and base-image digests.
15. Exclude `.git`, caches, real environment files, secrets, nested releases, unrelated outputs, and live runtime data.
16. Generate a complete content manifest and signed source/revision identity.
17. Generate and validate an SBOM in a named versioned format.
18. Build the release twice in independent clean environments and require bit-for-bit reproducibility for artifacts declared reproducible. Any exception must be byte-diffed, explained, entered in the limitations register, and must remove the reproducibility claim for that artifact.
19. Safely extract the ZIP into a second clean directory.
20. Run the full validation and test suite from the extracted ZIP.
21. Install the wheel in a fresh virtual environment and run smoke and resource tests.
22. Hash, sign, and attest the artifacts through a signer isolated from the builder.
23. Freeze artifacts after verification.
24. Reopen and stat every claimed file after transfer to durable storage and before completion is reported.
25. Generate a machine-readable release summary from verified truth only.
26. Verify consumer policy using an independently installed verifier and pinned trust roots outside the build workspace.

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
- Audit truncation, fork, stale-anchor, key-rotation, and anchor-outage tests pass for critical records.
- Consumer verification rejects wrong signer identity/issuer, unapproved builder, predicate mismatch, version rollback, expired trust metadata, and freeze attacks.

---

# Milestone 14 — Real weaker-agent evaluation laboratory

### Objective

Run a valid, preregistered experiment that quantifies what LAOS improves, what it worsens, where it fails, and the uncertainty around those results. This milestone must report null or negative results just as completely as positive ones.

### Entry gate

The sealed holdout must not open until:

- Milestone 15 operator, migration, support-matrix, privacy, documentation, and performance exits pass.
- Feature scope is frozen and the pre-evaluation red team, provider conformance, migration rehearsal, incident drills, and all behavior-affecting fixes are complete.
- Exact source, policy, prompt, profile, schema, grader, sandbox-image, dependency, tool, model/provider, and evaluation-harness digests are frozen.
- An independent evaluation owner confirms the charter, partitions, sample size, analysis, and stopping rules.

Any behavior-affecting change after holdout opening invalidates `RB-023` and `RB-024` and requires a new untouched holdout. Evaluation-harness unit/integration tests may be rerun; the final holdout may not be reopened or rerun for the same claim.

### Evaluation charter

A draft charter exists before the Alpha pilot. After pilot variance and operability data are available—but before any sealed holdout is opened—the independent evaluation owner freezes:

- **Primary efficacy estimand:** the difference in independently graded full-task success between LAOS v8 and a resource-matched structured-prompt baseline in the preregistered model-task-environment population.
- **Co-primary safety endpoint:** accepted false-completion or unauthorized scope/side-effect escape rate.
- **Secondary endpoints:** criterion closure, skipped gates, premature implementation, out-of-scope changes, regression, evidence truthfulness, recovery, human intervention, wall time, tokens, infrastructure use, cost, and variance.
- The minimum practically important effect, non-inferiority margin where applicable, safety floor, cost ceiling, sample-size/power method, statistical tests, confidence intervals, multiplicity strategy, exclusions, missing-run treatment, and stopping rules.
- Exact executor models, provider/version identifiers, tools, settings, host/sandbox profiles, task families, and dates to which claims will be bounded.

The study must have at least 80% power for its preregistered minimum practical efficacy effect unless the charter justifies a different target. Rare safety outcomes use exact interval bounds and adversarial coverage rather than treating zero observed failures as proof of zero risk.

For every claimed critical-risk/support-matrix row, the charter defines the safety denominator and maximum acceptable rate. Sample size must make the preregistered one-sided exact upper confidence bound fall below that rate; otherwise that row remains unsupported. Aggregate improvement cannot hide a failed task family, executor, environment, or risk-tier safety floor.

### Comparison groups

1. Normal broad prompt.
2. Static structured prompt.
3. LAOS v7.
4. LAOS v8 action-controlled execution.
5. Stronger reference executor where useful.

Two analyses are required:

1. **Resource-matched causal comparison:** same executor, requirements, tools, workspace freshness, wall-time/token/cost ceiling, retries, and human-assistance policy; orchestration is the intervention.
2. **Realistic end-to-end comparison:** each workflow operates normally, but every Architect, executor, reviewer, verifier, recovery, infrastructure, and human cost is included.

The stronger executor is a ceiling/reference, not a causal baseline. If the program claims which v8 control causes improvement, preregistered component ablations are required.

The historical predecessor baseline is the exact original v7.0 artifact and digest recorded in Section 1. If v7.0.1 is built, it is a separately named stronger-predecessor condition with its own frozen artifact digest. Both baseline selections, applicable task families, unsupported-capability treatment, exact prompts, tools, adapters, and compatibility shims are fixed before results are visible; v7.0.1 may not silently replace v7.0 after evaluation starts.

### Treatment-independent safety envelope

Every experimental condition runs inside the same experiment-owned outer VM/sandbox with no real secrets, restricted egress, resource ceilings, disposable state, and synthetic or non-production side-effect targets. This outer containment protects the operator and is not part of the measured LAOS intervention. Inside it, each condition uses its native orchestration; only the v8 condition receives LAOS capsule, policy, evidence, and review controls. This prevents both unsafe unrestricted baselines and contamination of the causal comparison.

### Dataset partitions and contamination control

1. **Development/calibration set:** visible and reusable for implementation and profile tuning.
2. **Locked validation set:** limited recorded access for pre-release decisions.
3. **Sealed final holdout:** controlled by an evaluator who is not implementing LAOS and never used for tuning the current release.

A final-holdout failure may become a regression only after the study and release decision are frozen. It may not be repaired and rerun for the same claim. Release attestations contain corpus hashes, provenance, environment manifests, results, and privacy-reviewed traces—not active hidden graders, answers, or reusable secret datasets. Sensitive or licensed evaluation material remains encrypted or escrowed until retired.

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

1. Use real agents and real tool execution in fresh workspaces and model contexts.
2. Use randomized paired or blocked assignment by task, repository, executor, and risk family.
3. Perform a development pilot to estimate variance, then lock the power calculation and final analysis before opening the holdout.
4. Keep hidden checks, graders, answers, and holdout task details outside the executor, Architect implementer, and profile-tuning contexts.
5. Grade intermediate traces and tool calls, not only final responses.
6. Use blinded dual grading and adjudication for subjective outcomes; report inter-rater reliability.
7. Record exact prompts, profile digests, models, tools, settings, environments, costs, time, exclusions, retries, and human interventions.
8. Report effect sizes and 95% confidence intervals. Apply the preregistered metric hierarchy or multiplicity correction.
9. Version model profiles and detect model-behavior drift over time.
10. Separate technical security/correctness readiness from efficacy claims and marketing language.
11. Freeze the sample size unless preregistered sequential efficacy/futility boundaries are used. Do not peek for favorable stopping or create unplanned exclusions.
12. Stop and quarantine immediately after an uncontained destructive action, secret exposure, cross-root write, sandbox escape, or unauthorized external effect. Resume only under an amended protocol with a new untouched holdout for any new final claim.
13. Preserve failures as candidates, but do not contaminate the current sealed evaluation by tuning and rerunning them.

### Exit gate

- The preregistered study completes without unresolved protocol violations and reports all results, including null or negative outcomes.
- The Release Attestation Pack contains protocol, corpus hashes, provenance, environment manifests, aggregate results, uncertainty, deviations, and privacy-reviewed traces without leaking active hidden graders, answers, licensed data, or sensitive project content.
- A positive efficacy claim is permitted only if the predefined practical and statistical thresholds pass. Claims are limited to evaluated models, versions, task families, tools, budgets, and environments.
- If efficacy is inconclusive or negative but technical safety/correctness gates pass, the release decision must either redesign and run a new sealed study or use an explicitly limited technical-preview label. It may not claim that v8 improves weaker-agent performance.
- Any “orders-of-magnitude” claim requires the preregistered metric, denominator, uncertainty, and independently reproducible data to support that exact magnitude.

---

# Milestone 15 — Documentation, migration, and operator experience

### Objective

Finish and reconcile the operator, migration, and documentation workstream that began with the kernel. Correct use must be obvious to Nilhan, the Architect AI, weaker agents, reviewers, and release verifiers before—not after—real evaluation.

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
- `DEPLOYMENT_AND_ENFORCEMENT_CONTRACT.md`
- `SUPPORTED_ENVIRONMENTS.json`
- `PERFORMANCE_BUDGETS.md`
- `INCIDENT_AND_TRUST_RECOVERY.md`
- `DATA_CLASSIFICATION_RETENTION_AND_PURGE.md`
- `CRYPTOGRAPHIC_PROFILE.md`
- `RELEASE_GATE_MATRIX.json`

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
10. Provide task-based clean-install acceptance tests for initialize, `doctor`, `status`, issue/revoke/inspect capsule, explain denial, resume after crash, backup/restore, rotate/recover trust, export/purge evidence, and dry-run/perform migration.
11. Publish the v7.0/v7.0.1 compatibility and end-of-support policy.
12. Label every security control as deterministic, sandbox-enforced, heuristic, adjudicated, or independently reviewed; documentation must not promote a weaker class into a stronger claim.

### Exit gate

- Every role can follow its path without reading private material.
- Documentation has no broken internal references.
- The mission and trust separation are unmistakable in every entry point.
- A new operator succeeds on the supported Windows and/or Linux rows without unpublished setup knowledge, and every failure produces an actionable, non-secret diagnostic.

---

# Milestone 16 — Pre-evaluation red team and post-evaluation durable publication

### Objective

Red-team and freeze the exact candidate before the sealed evaluation, then publish only that evaluated revision through an independent final verification path. Section 14's vertical order governs: the pre-evaluation portion of this milestone runs before Milestone 14 opens its holdout.

### Work

#### Pre-evaluation candidate freeze

1. Run all unit, property, integration, end-to-end, concurrency, security, sandbox, packaging, and evaluation-harness suites without opening or executing the sealed final holdout.
2. Run static typing, linting, dependency audit, secret scan, malicious-archive tests, provider conformance, operator journeys, performance gates, migration/rollback/coexistence rehearsal, evidence retention/purge, and compromise recovery drills.
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
4. Fix all behavior-affecting findings, rerun impacted gates, and repeat independent review until the candidate is eligible to freeze.
5. Freeze exact source, policy, prompt, profile, schema, grader, sandbox-image, dependency, tool, model/provider, and evaluation-harness digests; then hand the candidate to the independent Milestone 14 evaluation owner.

#### Post-evaluation publication

6. After Milestone 14 passes `RB-023` and `RB-024`, build final artifacts from that exact evaluated revision in clean pinned environments.
7. Extract and retest the ZIP and install/retest the wheel without reopening or rerunning the sealed final holdout.
8. Verify every claimed sandbox/provider row and signatures/attestations outside the build tree.
9. Confirm no private Architect material or secrets exist in execution packs.
10. Reopen the final ZIP, checksum, manifest, SBOM, provenance, release report, evaluation linkage, and summary.
11. Copy final deliverables to durable storage and run the retrieval drill.
12. Evaluate every stable blocker ID and support-matrix row through protected canonical blocker state and the signed Release Gate Matrix view.
13. Confirm that Critical findings and non-waivable gates have no exception. High findings require independent security review plus release-authority and human-quorum acceptance or the affected support row remains disabled. Lower-severity accepted risk names the human owner, exact scope, rationale, compensating controls, expiry, and revalidation trigger.
14. Produce the final release decision with limitations and evaluation results.
15. If any post-evaluation change can affect runtime behavior, prompts, policy, profiles, dependencies, sandbox behavior, models, graders, or measured outcomes, invalidate `RB-023`/`RB-024`; freeze a new candidate and use a new untouched holdout.

### Exit gate

Every release blocker in Section 12 is closed, every claimed support-matrix row passes its gates, and every final artifact is physically present in durable storage, retrieved, reopened, hashed, and independently verified.

---

## 10. Cross-cutting security improvements

The following controls apply to every milestone:

1. **Prompt-injection boundary:** repository files, issue text, web pages, and tool output are untrusted data, never authority.
2. **Capability revocation:** connected-mode outstanding authority can be revoked within its measured propagation bound; offline v8.0 is verification/read-only and makes no immediate-revocation or global one-time-use claim.
3. **Policy-drift guard:** capsule validity includes policy, model-profile, skill-registry, and repository-seal digests.
4. **Skill supply-chain security:** every skill and adapter has a version, hash, provenance, permissions, compatibility declaration, and tests.
5. **Secret lifecycle:** secrets are short-lived, scoped, redacted from transcripts, and never stored in packs or evidence.
6. **Data minimization:** execution packs contain only the data needed for the current role and action.
7. **Resource abuse prevention:** quotas and circuit breakers prevent denial-of-wallet and runaway work.
8. **Cascading-failure containment:** one failed agent or external system cannot automatically authorize broader work.
9. **Independent acceptance:** critical changes require the configured genuinely independent verifier quorum and any required human approval; one Architect decision cannot replace it.
10. **No hidden downgrade:** unavailable verification or sandbox features produce BLOCKED, not a weaker silent fallback.
11. **Audit export:** a complete, signed, privacy-conscious trace can be exported for future Architect sessions and independent review.
12. **Schema evolution:** trusted records can be migrated explicitly; unknown future versions are never guessed.
13. **Architect containment:** Architect output is validated as an untrusted proposal and cannot directly access signing keys, privileged dispatch, release authority, or non-waivable overrides.
14. **Reference-monitor completeness:** every permission maps to a mandatory broker/provider and a bypass test.
15. **Race-safe filesystem access:** containment is enforced at the opened handle and final object, including platform-specific link/reparse behavior—not only on a pre-resolved string.
16. **Cryptographic profile:** typed domain-separated envelopes, strict parsing, trust bootstrap, rotation, revocation, anti-downgrade, and compromise recovery are versioned and tested.
17. **Repository lineage:** accepted work is reconstructed from base plus authorized delta and promoted under lock; evidence binds to the result seal.
18. **Indeterminate external effects:** in-doubt operations reconcile before retry and irreversible effects never retry automatically.
19. **Egress integrity:** DNS, redirects, proxies, private/metadata targets, browser actions, and encoded exfiltration are governed at each hop.
20. **Tamper-evident honesty:** local chains are not called immutable; critical heads are independently anchored and checked for gaps, forks, and rollback.
21. **Trust recovery:** kill switch, quarantine, revocation, key rotation, re-attestation, and incident drills are release requirements.
22. **Assurance-scoped claims:** each claim is limited to the exact conformance-tested host, provider, adapter, model profile, and workflow row.

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
- Duplicate JSON object names rejected before parsing.
- Oversized/deep input and reference-explosion limits enforced.
- Signed-envelope domain, encoding, algorithm, issuer, audience, subject, and key-purpose confusion rejected.

### 11.2 Repository truth

- Same repository produces same manifest.
- One-byte change detected.
- Add, delete, rename, mode change, and symlink-target change detected.
- Case collision rejected.
- Ignore-policy change invalidates seal.
- Capture and continuation use the same algorithm.
- Pre-claim edit detected.
- Evidence/runtime directories do not invalidate product-source truth under the defined policy.
- Base plus authorized patch deterministically produces the recorded result seal.
- Stale-base promotion and conflicting authoritative changes are rejected.
- Git LFS, submodule, sparse-checkout, case, Unicode, mode, ignored/untracked, junction, and reparse golden vectors agree on every supported platform.
- Hardened Git invocations ignore/reject malicious repository/system config, hooks, filters, credential/signing helpers, pagers/editors, fsmonitor, alternates, LFS/submodule network actions, and unsafe environment variables.

### 11.3 Paths and archives

- `..` traversal rejected.
- Absolute external path rejected.
- Symlink escape rejected.
- ZIP traversal rejected.
- Duplicate/case-colliding entries rejected.
- Symlink archive entry handled safely.
- Zip bomb and excessive-file-count protections enforced.
- Artifact collection cannot follow external links.
- Concurrent link/reparse swap cannot win between validation and open.
- Windows UNC/device paths, alternate data streams, hard links, short-name aliases, and unexpected reparse points follow explicit fail-closed policy.

### 11.4 State and concurrency

- Double claim prevented.
- Lost update prevented.
- Duplicate idempotency key prevented.
- Lease expiry handled safely.
- Crash during transition rolls back or reconciles.
- Event append is serialized.
- Migration rollback and backup restore tested.
- Generated views cannot overwrite canonical state.
- State transition and corresponding audit event cannot commit separately.
- Transactional outbox reconciles database/filesystem/provider boundary crashes.
- Database rollback, fork, clock rollback, WAL checkpoint starvation, and unsupported SQLite runtime/filesystem are detected or blocked.

### 11.5 Identity and policy

- Self-declared actor name is insufficient.
- Expired/revoked token denied.
- Wrong role denied.
- Wrong project/seal denied.
- Policy change invalidates capsule.
- Builder cannot review itself.
- Unauthorized side-effect verification returns `AuthorizationDenied`.
- Denial produces an audit event and no state advance.
- Concurrent redemption of one capsule yields exactly one attempt.
- Offline mode cannot claim immediate revocation.
- Unknown/substituted/revoked key, algorithm downgrade, wrong key purpose, wrong issuer/audience/subject, and trust-root rollback are denied.
- Trusted approval display rejects model/terminal spoofing, Unicode/bidirectional ambiguity, hidden fields, mismatched display/dispatch digests, and missing step-up authentication.

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
- Candidate edits cannot mutate the authoritative checkout directly.
- Clean reconstruction from base plus patch matches the submitted result seal.
- Crash at submit/verify/promote/state-commit boundaries reconciles without ambiguous accepted state.

### 11.7 Pack separation

- Architect-only data absent from execution pack.
- Future tasks absent.
- Hidden checks absent.
- Private keys absent.
- Pack tampering detected.
- Leak scanner catches seeded secrets and hidden-answer text.
- Extracted pack verifies independently.
- Allowlisted projection tests prove private control-plane fields cannot be selected even if new private fields are added.

### 11.8 Capture and continuation

- Capture is read-only.
- Investigator cannot deploy or repair.
- Evidence-free claims rejected.
- Unknowns preserved.
- Stale capture rejected.
- Architect acceptance required.
- Unchanged continuation succeeds.
- Changed repository requires recapture or signed amendment.
- Untrusted repository scripts, tests, hooks, and binaries never execute outside the qualifying sandbox.
- New-build compiler round trip produces blueprint, criteria, task graph, initial repository contract, and first valid capsule.

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
- Provider assurance profile blocks host sockets/devices, privilege escalation, unapproved mounts, metadata services, DNS/redirect/proxy bypass, and child-process escape.
- Credential broker avoids raw secret exposure where supported; encoded/chunked leakage canaries are detected or contained.
- Browser navigation and form submission obey network and side-effect policy.
- Model-call broker enforces provider/account/endpoint, allowed data class, minimization, retention/training/region policy, consent, and built-in tool denial; private-plan, evaluator-answer, secret, and disallowed-source canaries are not transmitted.

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
- Evidence classification, encryption/access, retention, export, purge, legal hold, and backup deletion behave as policy declares.
- Builder mutation of the noncanonical `Evidence/` view cannot alter canonical proof.

### 11.11 Side effects and recovery

- Approval required where policy says so.
- Duplicate LAOS capsule redemption and local dispatch are prevented. Provider-level duplication is bounded by the adapter's declared idempotency guarantee; otherwise the operation enters `OUTCOME_UNKNOWN` and reconciles before retry.
- External verification requires independent role.
- Failed operation remains uncommitted.
- Compensation record required where applicable.
- Checkpoint restore preserves unrelated files.
- Expired claim safely reclaimed.
- Recovery retains accepted audit history.
- Crash before dispatch, after external acceptance, and before receipt persistence enters the correct known or `OUTCOME_UNKNOWN` state.
- Indeterminate irreversible operations never auto-retry; reconciliation and compensation paths are exercised.
- Kill switch, mass revocation, quarantine, signer/evidence/provider compromise, trust rebootstrap, and re-attestation drills pass.

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
- Exact SLSA/in-toto predicate, expected builder identity, signer identity/issuer, timestamp/transparency proof, and consumer policy verify.
- Audit truncation, gap, fork, stale anchor, anchor outage, key rotation, release rollback, and freeze attacks fail closed according to the assurance profile.
- Independent rebuilds are byte-identical for reproducible artifacts or have an explicit byte-level exception that removes the claim.

### 11.13 Real-agent evaluation

- Multiple agents and repeated runs.
- Fixed datasets and hidden graders.
- Trace-level grading.
- Skip, scope, false-completion, evidence, regression, recovery, and cost metrics.
- Model-profile drift detection.
- No simulated execution presented as real evaluation.
- Randomized paired/blocked assignment, preregistered primary endpoints, power calculation, fixed stopping rule, confidence intervals, and metric hierarchy are followed.
- Development, validation, and sealed holdout partitions remain uncontaminated.
- Subjective grading reports blinded dual-review agreement and adjudication.
- Resource-matched and realistic end-to-end cost analyses both include all model, verifier, infrastructure, and human work.

---

## 12. Absolute release blockers

LAOS v8.0 must not be released while any of the following is true:

1. **RB-001 — Unsupported trust boundary:** the deployment/enforcement contract, trusted computing base, or support matrix is missing or contradicted by implementation.
2. **RB-002 — Bypassable mediation:** a claimed filesystem, command, network, browser, secret, signing, evidence, review, publication, or side-effect permission can bypass its enforcement point.
3. **RB-003 — Architect direct authority:** a model process can directly access signing keys, privileged state transitions, non-waivable overrides, or release authority.
4. **RB-004 — Private-pack leakage:** seeded master LAOS, future actions, hidden tests, private evaluator answers, Architect notes, secrets, or personal data appear in an execution deliverable, or pack construction is not an allowlisted projection.
5. **RB-005 — Early or replayed authority:** in a connected privileged support row, a weaker agent can obtain the next action early, redeem a capsule twice, use authority outside the measured revocation bound or after expiry, or use it under the wrong actor, audience, project, base seal, state, policy, profile, or key purpose; or offline v8.0 permits any privileged redemption/dispatch.
6. **RB-006 — Malformed canonical state:** a malformed, duplicate-key, oversized, unknown-version, semantically invalid, or unauthenticated trusted record can enter canonical state.
7. **RB-007 — Repository identity ambiguity:** capture/continuation fingerprints disagree, pre-claim drift can be hidden, cross-platform golden vectors disagree, or base/result lineage is incomplete.
8. **RB-008 — Unsafe promotion:** the builder can mutate the authoritative checkout directly, stale-base promotion succeeds, or filesystem/database crashes can leave an accepted result ambiguous.
9. **RB-009 — Filesystem/archive escape:** a supported-platform path, archive, symlink, junction, reparse, hard-link, alias, or concurrent-swap escape remains possible.
10. **RB-010 — State race or fork:** two workers can claim/advance the same action, state and audit event can diverge, or rollback/fork/clock anomalies can silently change authority.
11. **RB-011 — False independence:** typed actor names or shared principals, credentials, contexts, workspaces, or controlling authority can impersonate independent roles or quorum.
12. **RB-012 — Unsupported closure:** a mandatory criterion can close without current result-seal-bound evidence and required independent review, or the builder can alter protected/hidden tests.
13. **RB-013 — Unsafe execution:** arbitrary repository code or a dangerous command can run through unrestricted host access, or high-risk work silently proceeds without a conformance-tested sandbox.
14. **RB-014 — Unsafe egress, model transfer, or secrets:** network/browser/model-provider policy can be bypassed, cloud metadata or disallowed targets are reachable, built-in provider tools escape mediation, or credentials/private data leak through prompts, provider retention, processes, evidence, artifacts, or allowed channels.
15. **RB-015 — Unsafe side effects:** external effects can bypass approval, idempotency, reconciliation, or independent verification; an indeterminate irreversible operation can retry automatically; or unauthorized verification raises the wrong error or advances state.
16. **RB-016 — Mutable release contamination:** SQLite, WAL/SHM, locks, logs, leases, caches, current indexes, secrets, or other live runtime state appears in an immutable release or static content manifest.
17. **RB-017 — Evidence/audit weakness:** evidence mutation passes, canonical evidence is builder-writable, critical audit truncation/fork/rollback passes, or required external anchoring is absent.
18. **RB-018 — Artifact/provenance failure:** ZIP/wheel extraction, installation, full retest, SBOM, provenance, signature identity/predicate verification, reproducibility claim, consumer policy, rollback protection, or durable retrieval fails.
19. **RB-019 — Broken operator contract:** required documentation points to nonexistent files, a supported clean install cannot complete operator journeys, or capability claims exceed the support matrix.
20. **RB-020 — Migration failure:** supported v7 import, dry run, mapping report, idempotent rerun, rollback/coexistence, or migration rehearsal fails.
21. **RB-021 — Unrecoverable trust compromise:** kill switch, revocation, quarantine, key/secret rotation, external recovery point, revalidation, and re-attestation drills do not recover safely.
22. **RB-022 — Critical or uncontrolled High security finding:** a Critical finding is open, or a High finding lacks independent security review plus release-authority and human-quorum acceptance. Critical is non-waivable. An unaccepted High disables every affected support row. Any accepted High or lower-severity risk is signed and bound to exact code/environment/evidence digests, with named ownership, scope, compensating controls, expiry, and revalidation trigger.
23. **RB-023 — Invalid or missing evaluation:** the preregistered sealed evaluation has not completed, has unresolved protocol violations, or its materials/results cannot be independently audited without exposing active hidden content.
24. **RB-024 — v8.0 efficacy/safety floor not met:** the predefined v8.0 minimum efficacy, safety, non-inferiority, and resource thresholds are not met. An inconclusive or negative system may remain a technical preview but cannot be declared v8.0 GA or claim improved weaker-agent performance.
25. **RB-025 — Missing final artifacts:** a claimed final deliverable is absent from durable storage or has not been retrieved, reopened, hashed, safely extracted where applicable, and independently verified after final transfer.

Protected transactional blocker state is authoritative; the builder has no write authority to status, waiver, evidence binding, or support-row closure. `RELEASE_GATE_MATRIX.json` is a schema-validated, content-addressed, noncanonical release view generated from that state. Every row records blocker ID, release channel, support environment, criterion, automated check, evidence digests, owner, independent verifier, waiverability, expiry, and status.

At decision time, an independent release verifier plus the required human/quorum authority signs the matrix digest and exact candidate/support-state digest. `ReleaseRecord`, provenance, and final attestation bind that signed digest. Any builder mutation, missing evidence object, unapproved waiver, stale candidate binding, or matrix/state mismatch is itself a release blocker. Narrative summaries are generated from the signed view.

---

## 13. Definition of done

LAOS v8.0 is done only when all of the following are true:

### Mission

- The Architect-only mission is clear in every entry point.
- Weaker agents receive only minimal public context and one current capsule.
- Architect model output remains an untrusted proposal until deterministic and required human/quorum controls accept it.

### Correctness

- Strict schemas and semantic validation are universal.
- Canonical fingerprinting passes complete round trips.
- Transactional state and concurrency tests pass.
- Base/result seal lineage, clean reconstruction, locked promotion, and crash reconciliation pass.

### Anti-skip behavior

- Mandatory action order is enforced.
- Every criterion is independently tracked and proven.
- Attempts, stop conditions, and escalation work.

### Security

- Paths, archives, identities, policies, commands, sandboxes, secrets, skills, and side effects are enforced by code.
- Every claimed capability is completely mediated in its supported environment.
- Critical threat-model and red-team findings are closed. High findings have independent security review plus release-authority/human-quorum disposition or the affected support row is disabled. Every accepted risk is signed and bound to exact code/environment/evidence digests with ownership, scope, compensating controls, expiry, and revalidation triggers.

### Evidence and review

- Evidence is automatic, current, criterion-linked, and tamper-evident.
- Review is authenticated and independent.
- Critical event heads and release decisions are externally anchored and independently verified according to their assurance profile.

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
- The preregistered v8.0 efficacy, safety, non-inferiority, and resource thresholds pass; otherwise the artifact remains a limited technical preview.
- Every claim is bounded to the exact evaluated models, versions, tasks, tools, budgets, adapters, and environments.

### Documentation

- All required documents exist, are internally consistent, and contain no broken references.
- Migration from v7 is tested and explained.
- Clean-install operator, incident-recovery, evidence-retention/purge, and trust-rotation journeys pass on every supported platform row.

---

## 14. Recommended implementation order

The active dependency graph and machine-readable milestone records are authoritative. The first implementation should follow this vertical sequence:

1. Verify Stage 0, reconstruct the Git repository, import plan revision 1.1, and reconcile all ledgers without modifying the sealed Stage 0 package.
2. Make the conditional v7.0.1 decision; import regression and migration fixtures regardless.
3. Provisionally classify `MUST_V8_0`/`SHOULD_V8_0`/`DEFER_V8_X` scope and conservative circuit breakers; freeze only the deployment/enforcement contract, support assumptions needed for Alpha, TCB, and permission-to-enforcement map.
4. Implement the minimal package, strict protocol/parser/schema profile, stable errors, machine-readable transition tables, dependency locks, platform CI, and migration discovery.
5. Implement transactional SQLite state, same-transaction audit events, unique capsule redemption, outbox, migrations, backup/recovery, and clock/rollback/fork protections.
6. Implement source/base/result/workspace seals, race-safe paths and archives, isolated disposable Git clones, broker-owned deltas, clean reconstruction, CAS promotion, and crash reconciliation.
7. Implement minimum authenticated identity, protected test signing, connected policy checks, revocation, and a narrow typed capsule issuer/verifier/redemption path with structured result envelopes.
8. Implement the minimum workspace/command/egress broker, one conformance-tested sandbox, no-secret default, emergency stop, and broker evidence capture.
9. Pass the mandatory Security Spine Gate before running any real weaker agent against untrusted content.
10. Expand the minimal capsule path with only enough UNDERSTAND/PLAN/IMPLEMENT phases, criterion tracking, clean verification, and independent review to complete the Alpha Vertical Trust Slice.
11. Run the randomized development-set Alpha pilot; set performance budgets, prune architecture, make the go/no-go decision, and freeze v8.0 scope.
12. Mature typed signed packs, allowlisted projection, key lifecycle, leak defense, action attempts, repair/amendment, prompt linting, and bounded model profiles.
13. Implement and dogfood minimal CLI/docs/operator journeys continuously.
14. Implement both new-build compilation and existing-application capture/continuation against the proven enforcement spine.
15. Mature evidence custody, privacy/retention, independent review/quorum, checkpoints, recovery, anti-thrashing, and migration tooling.
16. Implement only the external side-effect adapters retained in `MUST_V8_0`, with outbox, indeterminate outcomes, reconciliation, compensation, and real non-production conformance. Otherwise ship the protocol as unsupported for production.
17. Implement incident/trust recovery, external event anchoring, deterministic artifacts, SBOM, exact provenance/signature profile, consumer verification, and rollback/freeze protection.
18. Freeze the evaluation charter, holdout custody, models, budgets, graders, sample size, analysis, and stopping rules without opening the holdout.
19. Feature-freeze; complete documentation, operator and migration rehearsals, provider conformance, performance gates, compromise drills, and independent red team; fix all behavior-affecting findings; then freeze the exact candidate digests.
20. Run the sealed preregistered evaluation once on that exact candidate, report every result, and make the efficacy/claim decision without tuning on the holdout.
21. Build and verify only that evaluated revision. Packaging/distribution-surface findings may be fixed only if they cannot affect runtime behavior or evaluation; otherwise invalidate the result and use a new untouched holdout.
22. Reproduce from clean pinned environments, sign outside the builder, close every stable blocker, transfer to durable storage, retrieve, reopen, extract/install, retest without reopening the final holdout, and independently verify before declaring v8.0.

The horizontal subsystem descriptions in Section 9 remain requirements catalogues. This ordered spine governs when integrated claims may be made and removes the former cycles in which early gates depended on later brokers, evidence, signing, side effects, or review systems.

---

## 15. New improvements added beyond the earlier master plan

The following refinements should be explicitly added to v8:

1. **No runtime database in any release artifact:** only migrations and initialization code ship.
2. **Stable security exception contract:** every authorization denial uses one typed hierarchy and machine-readable code.
3. **Authority Envelope:** every capsule is bound to issuer, authenticated actor, role, project, broker/provider audience, action-definition digest, base seal, state version, policy, model profile, skills, capsule ID, attempt sequence, issue time, expiry, and revocation epoch.
4. **Uncertainty Ledger:** unknown facts cannot silently become assumptions or requirements.
5. **Context provenance labels:** agents can distinguish signed instructions, trusted truth, evidence, and untrusted content.
6. **Capability revocation:** connected privileged capsules can be invalidated within a measured propagation bound; offline v8.0 remains verification/read-only.
7. **Policy/model/skill drift guard:** changes invalidate incompatible outstanding capsules.
8. **Non-interference analysis:** parallel work is allowed only when independence is proven.
9. **Critical-task quorum:** high-impact work requires the configured genuinely independent verifier quorum and any required human approval; Architect adjudication cannot substitute for critical quorum.
10. **Secret lifecycle controls:** ephemeral injection, redaction, and non-persistence.
11. **Resource and cost circuit breakers:** prevent runaway attempts and denial-of-wallet.
12. **Degradation without deception:** unavailable components block affected actions rather than silently weakening assurance.
13. **Replayable trace bundles:** checks and decisions can be independently reconstructed where technically feasible.
14. **Schema/version migration discipline:** no guessing when trusted record formats evolve.
15. **Profile drift monitoring:** model behavior is recalibrated as providers and models change.
16. **Evidence escrow:** canonical proof is held outside the builder’s write authority while a signed project-facing index remains under the root `Evidence/` folder.
17. **External release verification:** signatures and attestations must be verifiable outside the build workspace.
18. **Artifact durability gate:** existence, stat, hash, extraction, and retest are performed after the artifact is moved to its final durable location.
19. **Security Spine before agents:** no real calibration, capture, or implementation against untrusted content before identity, policy, broker, sandbox, evidence, and emergency-stop mediation exists.
20. **Alpha vertical proof:** the smallest real base-to-result-to-review-to-promotion workflow is proven before horizontal platform expansion.
21. **Architect output is untrusted:** deterministic policy and protected human/quorum gates sit between every model and privileged authority.
22. **Base/result promotion protocol:** agents edit isolated disposable clones; accepted broker-owned deltas are cleanly reconstructed and promoted with Git compare-and-swap under authoritative control.
23. **Separated action aggregates:** definition, capsule, attempt, review, and criterion lifecycles no longer share one ambiguous state machine.
24. **Typed cryptographic envelope:** domain separation, exact bytes, trust bootstrap, key purpose, rotation, revocation, anti-downgrade, and compromise recovery replace “sign JSON” ambiguity.
25. **Race-safe cross-platform paths:** final-handle containment and Windows reparse/alias semantics are part of the supported-platform contract.
26. **Indeterminate side effects:** outbox, `OUTCOME_UNKNOWN`, reconciliation, and no automatic irreversible retry replace implied exactly-once behavior.
27. **Tamper-evident language and external anchors:** local chains no longer overclaim immutability.
28. **Preregistered evaluation:** primary estimands, fair baselines, partitions, power, uncertainty, stopping rules, and holdout contamination controls govern efficacy claims.
29. **Machine-readable release gates:** stable blocker IDs and per-environment support rows replace narrative-only release decisions.
30. **Incident and trust recovery:** kill switch, mass revocation, quarantine, key rotation, recovery points, revalidation, and re-attestation are release-tested.
31. **Continuous operator and migration work:** CLI, docs, migration, platform support, and performance budgets begin before Alpha rather than after evaluation.

---

## 16. Program risk register

| Risk | Consequence | Required mitigation |
|---|---|---|
| Scope becomes too large | Endless rebuild | Scope tiers; Alpha go/no-go; MUST scope freeze; equivalent-scope rule; defer speculative providers and distributed features |
| Framework becomes too complex | Weaker agents and operators fail to use it | Modular monolith; Alpha vertical proof; continuous operator tests; abstractions require a real boundary or second implementation |
| Overcontrol slows simple work | Excessive friction | Risk-tiered profiles and low-risk fast path without weakening core truth |
| False sense of security | Unsafe high-risk use | Clear OS-sandbox boundary and tested provider requirement |
| Mediation can be bypassed | Signed instructions do not constrain the agent | Deployment/enforcement contract; permission-to-broker matrix; direct host mode unsupported; bypass tests |
| Architect becomes confused deputy | Signed unsafe model decision gains authority | Treat all model output as proposal; protected signer; deterministic policy; human/quorum gates for critical authority |
| State corruption or races | Invalid project truth | Supported local SQLite only; transactions, constraints, same-transaction events, backups, integrity and crash tests; distributed store deferred |
| Repository and database diverge | Accepted state does not match source | Isolated clones; broker-owned deltas; base/result seals; clean reconstruction; Git CAS promotion; outbox and crash reconciliation |
| Prompt injection | Goal hijack or tool misuse | Signed authority, untrusted-content labels, default deny |
| Model-provider transfer bypasses local controls | Source/private data leaves approved boundary or provider tools gain authority | Model-call broker; data-class policy; minimization; provider/region/retention row; built-in tool denial; transmission canaries |
| Hidden information leaks | Weaker agent gains plan/evaluator answers | Physical pack separation and leak scanner |
| Agent/model behavior changes | Profiles become unsafe | Versioned calibration and drift monitoring |
| Evidence storage grows without bound | Cost and maintenance burden | Content addressing, deduplication, retention policy, summaries |
| Evidence captures sensitive data | Privacy, secret, or contractual breach | Pre-persistence classification/minimization; credential broker; access/encryption; retention/export/purge tests |
| Release artifact disappears | Work is lost or falsely claimed | Durable storage, reopen/hash/extract gates, optional external publication |
| Sandbox unavailable | High-risk tests unverified | CI/managed provider requirement; fail closed |
| Real-agent eval unavailable | Performance claim unproven | Release limitations remain explicit; no unsupported numerical claim |
| Cryptographic keys share compromised host | Provenance weak | External KMS/OIDC or offline key; external anchor/verifier |
| Local audit is truncated or forked | False history appears valid | Same-transaction events; independently anchored heads; gap/fork/rollback checks; incident freeze |
| External outcome is unknown | Unsafe duplicate payment/deploy/email | Transactional outbox; provider idempotency; reconciliation; no automatic irreversible retry |
| Evaluation overfits or stops selectively | Misleading efficacy claim | Development/validation/holdout partitions; preregistration; power; fixed stopping; blinded grading; all-result reporting |
| Support claim exceeds tested environment | Unsafe portability assumption | Machine-readable support matrix and per-provider/platform release gates |
| Test suite becomes slow or flaky | False confidence and poor iteration | Test tiers, deterministic fixtures, time budgets, flake quarantine with no silent ignore |

---

## 17. Release outputs

The final durable release set must include:

- `LAOS_v8.0_Complete_System.zip`
- `LAOS_v8.0_Complete_System.zip.sha256`
- Python wheel
- Source archive
- Signed immutable source revision or verified Git bundle sufficient to reconstruct it
- Content-integrity manifest
- SBOM
- Provenance statement
- Signature/attestation envelope
- Cryptographic profile and consumer verification policy
- Support and sandbox-assurance matrices
- Machine-readable Release Gate Matrix with all blockers closed
- Full automated test report
- Extracted-release test report
- Sandbox conformance report
- Security and red-team report
- Real-agent evaluation report
- Preregistered evaluation protocol, deviations, corpus/environment hashes, analysis code, and privacy-reviewed results
- Migration report
- Incident/trust-recovery and durable-retrieval drill report
- Known limitations
- Machine-readable release summary
- Final human-readable release report

No completion statement may be issued until each listed file that is claimed has been reopened from its final storage path and verified.

---

## 18. Final execution rule

The upgrade must proceed as a sequence of verified milestones, not as one enormous generation.

At the end of every milestone:

1. Run its defined tests.
2. Record evidence under the root `Evidence/` view and protected canonical evidence store when available; otherwise use the labeled Bootstrap Assurance Policy.
3. Update the requirements, threat, defect, scope, support, performance, migration, and release-gate ledgers affected by the change.
4. Perform an independent review at the assurance level currently available and record that level honestly.
5. Freeze the milestone result with a Git tag, immutable evidence snapshot, hashes, open-dependency list, and impact map.
6. Rerun every affected prior gate rather than assuming an old PASS survived architectural, policy, model, dependency, or platform drift.
7. Begin dependent work only after the entry gate passes. Narrow slices from later subsystem milestones may be pulled forward solely to satisfy the Security Spine or Alpha Vertical Trust Slice and must not be misreported as full subsystem completion.

At the end of the Alpha, Beta, and RC channels, explicitly reconsider whether the remaining scope is still necessary. The plan is a controlled hypothesis, not an obligation to implement every idea after evidence makes it unnecessary.

That process is itself the first real proof that LAOS v8 follows the discipline it is designed to impose on weaker agents.

---

## 19. Normative standards baseline and review triggers

This revision uses the following primary references as design inputs. They are not floating dependencies: Milestone 2 must record the exact profile/version adopted, and RC must re-check for security-relevant changes without silently upgrading formats.

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) for external record validation, plus the selected validator's official conformance suite.
- [RFC 8785 — JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html) when canonical JSON is selected for content hashing. Signed envelopes should prefer typed domain separation rather than raw canonical-JSON signatures.
- [DSSE — Dead Simple Signing Envelope](https://github.com/secure-systems-lab/dsse) or an equivalently reviewed typed-envelope standard for signing exact payload bytes under an authenticated payload type.
- [SQLite WAL documentation](https://sqlite.org/wal.html), including the same-host filesystem constraint, checkpoint/durability behavior, and the WAL-reset fix requirements documented for affected SQLite releases.
- [SLSA specification v1.2](https://slsa.dev/spec/v1.2/) as the current review baseline for explicit Build and Source track claims. LAOS must declare the exact achieved track/level and verification policy rather than say only “SLSA-style.”
- [Sigstore identity-based signing and verification](https://docs.sigstore.dev/cosign/signing/overview/) when Sigstore/Cosign is selected; verification policy must pin expected identity, issuer, artifact/predicate, trust roots, and transparency/timestamp material.
- [The Update Framework specification](https://theupdateframework.github.io/specification/latest/) as a design reference for trust-root rotation, version rollback, and freeze protections if LAOS distributes update metadata.

Review is triggered by a change to any selected schema/signature/provenance format, cryptographic primitive or library, Python-bundled SQLite version, host filesystem, sandbox/provider implementation, identity issuer, trust root, build platform, or consumer verification policy. A review updates the dependency/standards ADR, golden vectors, threat model, migration rules, and impacted release gates before new authority is issued.

### 19.1 Revision 1.1 review disposition

The review approved the plan's core mission, evidence discipline, default-deny posture, private/public pack separation, and release honesty. It changed the execution strategy because the original plan had circular milestone dependencies and delayed decisive evidence. The material amendments are:

- A concrete deployment/enforcement contract and mandatory mediation model.
- A Security Spine before real-agent activity.
- An Alpha end-to-end vertical slice and go/no-go scope freeze.
- Base/result repository lineage and locked promotion.
- Separate definition, capsule, attempt, review, and criterion state machines.
- A typed cryptographic/key-lifecycle profile and bounded offline revocation claim.
- Race-safe filesystem, sandbox, egress, secret, privacy, incident, and indeterminate-side-effect requirements.
- A preregistered, fair, contamination-resistant evaluation design.
- Stable machine-readable release blockers and per-environment capability claims.
- Continuous CLI, migration, performance, and operator work rather than a late documentation phase.

This is an improved plan, not implementation evidence. Milestones 1–16 remain unbuilt until the reconstructed v8 repository proves otherwise.
