# LAOS v8 threat model — draft

Drafted: `2026-07-12T16:10:01+00:00`

## Security objective

Prevent a weaker execution agent, untrusted repository content, a compromised tool, a concurrency race, or a mistaken operator from silently expanding authority or turning incomplete work into accepted truth.

## Protected assets

- Architect-only plans, decisions, hidden checks, signing material, and acceptance answers.
- Repository source, tests, data, credentials, deployment configuration, and protected behaviour.
- Runtime state, identities, capabilities, action sequence, evidence, reviews, and side-effect receipts.
- Release artifacts, checksums, provenance, evaluation results, and human trust.

## Actors and trust zones

- Nilhan / human authority.
- Highly capable Software Architect AI / control plane.
- Weaker investigator, builder, tester, reviewer, recovery agent, and release verifier.
- Trusted LAOS kernel, policy engine, identity provider, evidence broker, and artifact builder.
- Untrusted repository content, dependencies, tools, model outputs, external services, and archives.
- OS sandbox and external audit/provenance stores.

## Trust assumptions

1. The Architect AI can still make mistakes; critical consequences require independent controls or human approval.
2. A language-model instruction is never an OS security boundary.
3. Repository content is data, not authority.
4. The builder workspace is not trusted to preserve canonical evidence or signing keys.
5. A local hash chain controlled by one actor is tamper-evident only within that trust boundary.

## Threat register

| ID | Threat | Attack path | Impact | Required controls | Mandatory test |
|---|---|---|---|---|---|
| TM-001 | Master-plan leakage | Architect-only strategy or hidden tests enter an execution pack | Weak agent can game checks or act outside intended scope | Separate packs, leak scan, allowlist packaging | Pack leakage adversarial suite |
| TM-002 | Instruction hierarchy confusion | Repository text impersonates Architect instructions | Agent follows untrusted prompt injection | Signed authority envelope and provenance labels | Injected README cannot expand authority |
| TM-003 | Action skipping | Weak agent jumps directly to implementation or completion | Incomplete or unsafe work | One active capsule and transition guards | Out-of-order transition denial |
| TM-004 | Capsule replay | Old authorised action is reused after completion or drift | Duplicate or stale actions | Nonce, expiry, revocation, one-time redemption | Replay test |
| TM-005 | Policy drift | Policy changes while old capsule remains valid | Work proceeds under obsolete controls | Policy hash binding and invalidation | Policy-change revocation test |
| TM-006 | Model/skill drift | Executor or skills change after calibration | Unsafe prompt size or tool authority | Profile and skill hash binding | Drift invalidation test |
| TM-007 | Pre-claim mutation | Builder changes files before baseline capture | Forbidden changes become invisible | Architect workspace seal before authority | Pre-claim edit regression |
| TM-008 | Path traversal | Malicious identifiers or paths escape root | External file read/write/delete | Resolved containment and strict identifiers | Traversal corpus |
| TM-009 | Symlink/junction escape | Allowed path resolves outside repository | Host data modification or exfiltration | No-follow path broker and sandbox mounts | Symlink escape regression |
| TM-010 | Archive traversal or bombs | Unsafe ZIP members or extreme expansion | Overwrite, denial of service, resource exhaustion | Safe archive inspector, quotas, no links | Malicious archive corpus |
| TM-011 | Concurrent double claim | Two workers acquire one action | Conflicting edits and state | Transactional unique claim/lease | Concurrency race test |
| TM-012 | Lost state update | Concurrent JSON writes overwrite changes | Corrupt workflow truth | SQLite transaction boundaries | Parallel state update test |
| TM-013 | Event-chain fork | Concurrent event appends share previous hash | Ambiguous audit history | Serialized transaction and external anchor | Concurrent append test |
| TM-014 | Identity spoofing | Builder types a reviewer name | Self-review presented as independent | Authenticated identities and capabilities | Builder self-review denial |
| TM-015 | Capability theft | Token or key is copied from workspace | Unauthorized action | Secrets outside repo, scoped expiry, revocation | Stolen expired/revoked token test |
| TM-016 | Command injection | Shell metacharacters interpreted in contracted command | Arbitrary execution | argv command broker, shell default-deny | Injection corpus |
| TM-017 | Dangerous command misuse | Agent runs destructive Git, filesystem, or privilege commands | Data loss or compromise | Policy denylist/allowlist and approvals | Dangerous command tests |
| TM-018 | Network exfiltration | Agent sends source or secrets externally | Confidentiality loss | Network default-deny and destination allowlist | Blocked egress test |
| TM-019 | Secret persistence | Credentials enter prompts, logs, evidence, or artifacts | Credential compromise | Ephemeral injection, redaction, secret scan | Canary secret test |
| TM-020 | Evidence fabrication | Agent writes convincing but false proof | False completion | Broker-generated evidence and independent rerun | Vague/fabricated evidence rejection |
| TM-021 | Evidence staleness | Source changes after successful check | Old proof accepted | Seal/check/evidence freshness binding | Post-check edit invalidation |
| TM-022 | Evidence tampering | Builder edits transcript or screenshot | False proof | CAS hash, external escrow, verifier | Mutation regression |
| TM-023 | Test weakening | Builder edits tests to make work pass | Regression hidden | Protected tests and independent hidden checks | Test weakening detection |
| TM-024 | Hidden-test leakage | Hidden checks included in builder pack | Agent overfits validation | Separate verifier trust zone | Leak scan and package inventory |
| TM-025 | Criterion omission | Broad task pass hides unimplemented requirement | Partial feature accepted | Criterion ledger and closure rules | Missing criterion denial |
| TM-026 | Reviewer persuasion bias | Reviewer receives builder narrative as primary truth | Weak independent challenge | Review Capsule centered on contract and repository | Adversarial review protocol test |
| TM-027 | Side-effect replay | External operation executed more than once | Duplicate payment/deploy/email | Idempotency and receipt verification | Replay test |
| TM-028 | Unauthorized side-effect verification | Builder marks its own external action verified | False external truth | Capability-gated transitions | AuthorizationDenied regression |
| TM-029 | Partial external failure | Operation succeeds partly then runtime crashes | Unknown or inconsistent external state | Prepared/executed receipts, recovery and compensation | Crash-point tests |
| TM-030 | Checkpoint poisoning | Checkpoint contains unsafe or stale content | Bad recovery state | Content-addressed snapshot and safe extraction | Tampered checkpoint test |
| TM-031 | Recovery over-delete | Restore removes unrelated files | Data loss | Dry run and explicit delete-extra authority | Recovery deletion test |
| TM-032 | Release state contamination | Mutable database included in static manifest | Integrity failures after normal use | Static/runtime physical separation | Mutable DB exclusion regression |
| TM-033 | Artifact post-verification mutation | ZIP changes after checksum generation | Untrusted deliverable | Freeze, final-location reopen and rehash | Mutation test |
| TM-034 | Non-durable artifact | Temporary cleanup removes deliverable | Release loss | Durability gate and external location verification | Cleanup/retrieval drill |
| TM-035 | Supply-chain compromise | Dependency, build tool, or skill is malicious | Code execution or tainted release | Pinned hashes, SBOM, provenance, review | Dependency integrity test |
| TM-036 | Denial of wallet/resources | Agent loops or launches excessive work | Cost and availability impact | Attempt, time, CPU, memory and cost budgets | Circuit-breaker test |
| TM-037 | Unknown-to-fact drift | Unresolved assumption becomes accepted truth | Wrong architecture or behaviour | Uncertainty Ledger and provenance | Unknown promotion denial |
| TM-038 | Evaluation gaming | System optimized to public benchmark only | Misleading performance claims | Hidden tasks, repeated trials, independent grading | Holdout benchmark |
| TM-039 | Documentation overclaim | Docs say enforced when control is procedural | Unsafe operator trust | Capability-to-doc traceability and limitations | Documentation audit |
| TM-040 | Architect compromise | Highest-authority actor is malicious or mistaken | System-wide unsafe delegation | Approvals, critical quorum, signed audit, least privilege | Critical-operation quorum test |

## Initial risk posture

Milestone 0 contains no execution runtime and therefore does not claim these controls exist. P0 threats remain open until their target milestones deliver executable controls and passing adversarial tests.

## Review triggers

- Any change to trust zones, state stores, identity, signing, sandbox providers, command execution, evidence custody, side-effect authority, or release construction.
- Any new executor model, tool adapter, external service, or deployment environment.

## Revision 1.1 reconciliation

`THREAT_REGISTER.json` is the machine-readable Stage 1 register. It preserves TM-001 through TM-040 and adds TM-041 through TM-050 for repository promotion, model-provider transfer, Windows path TOCTOU/aliases, indeterminate side effects, audit anchoring, cryptographic context confusion, privileged offline denial, holdout contamination, evidence privacy, and trust-compromise recovery.

All 50 threats remain `OPEN`. Creating a fixture, ADR, or plan entry does not close a threat. Closure requires the owning implementation stage, current evidence, and required independent review.
- Any incident, evaluation failure, bypass, or material change to the repository threat surface.
