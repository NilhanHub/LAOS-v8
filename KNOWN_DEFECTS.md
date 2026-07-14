# Known defects and mandatory regressions

Baseline recorded: `2026-07-12T16:10:01+00:00`  
LAOS v7 archive SHA-256: `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`

This register distinguishes confirmed v7 defects, architectural gaps, known limitations, prior reported v8 failures whose source no longer survives, and process failures. A prior report is not treated as proof of current implementation.

## REG-001 — Capture/runtime repository fingerprint algorithms disagree

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `capture_runtime.py; laos_runtime.py`
- Target milestone: **1**

**Reproduction specification**

1. Capture an unchanged repository with v7.
2. Compile a continuation pack from the validated return.
3. Install the pack in the unchanged repository.
4. Run repository baseline verification.

**Required v8 result**

The unchanged repository passes using one versioned canonical algorithm.

## REG-002 — Capture and runtime fingerprint ignore rules are not shared

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `capture_runtime.py; laos_runtime.py`
- Target milestone: **1**

**Reproduction specification**

1. Choose files covered differently by the two ignore implementations.
2. Capture the repository.
3. Calculate the implementation-runtime fingerprint.
4. Compare the results.

**Required v8 result**

All workflows import the same manifest implementation and exclusions.

## REG-003 — App Intelligence JSON Schemas are shipped but not enforced

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `capture_runtime.py; validate_return_pack.py`
- Target milestone: **1**

**Reproduction specification**

1. Create required JSON files containing syntactically valid but structurally invalid values.
2. Set the completion flags expected by heuristic validation.
3. Run capture validation and return-pack validation.

**Required v8 result**

Strict Draft 2020-12 validation fails with precise schema diagnostics.

## REG-004 — Pre-claim forbidden changes can become the task baseline

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py claim_task/save_task_baseline`
- Target milestone: **3**

**Reproduction specification**

1. Modify a forbidden or unrelated tracked file before claiming a READY task.
2. Claim the task.
3. Complete an allowed edit.
4. Run changed-file validation.

**Required v8 result**

Claim is denied because workspace state differs from the Architect-approved seal.

## REG-005 — Symlink writes can escape repository observation

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `project_manifest and path handling`
- Target milestone: **3**

**Reproduction specification**

1. Create a symlink within an allowed directory pointing outside the repository.
2. Write through the symlink.
3. Run repository delta and scope validation.

**Required v8 result**

The path broker rejects the resolved external target before any write occurs.

## REG-006 — Project manifests silently skip symlink entries

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py project_manifest`
- Target milestone: **3**

**Reproduction specification**

1. Add a symlink inside the repository.
2. Generate a project manifest.
3. Observe that no link record is present.

**Required v8 result**

Manifests represent the link itself without following its target, or reject it by policy.

## REG-007 — Task lock creation is check-then-write rather than exclusive

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py claim_task`
- Target milestone: **3**

**Reproduction specification**

1. Start two claim processes at the same time for one READY task.
2. Force both processes past the existence check.
3. Inspect lock, state, and event records.

**Required v8 result**

A transactional uniqueness constraint permits exactly one claim.

## REG-008 — JSON state updates are non-transactional and vulnerable to lost updates

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py mutable JSON state`
- Target milestone: **3**

**Reproduction specification**

1. Run two state-changing operations concurrently.
2. Allow both to read the same old state.
3. Observe one writer overwriting the other.

**Required v8 result**

SQLite transactions preserve both valid operations or reject one deterministically.

## REG-009 — Event append is not transactionally serialized

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py append_event`
- Target milestone: **3**

**Reproduction specification**

1. Append events concurrently.
2. Have both processes read the same previous hash.
3. Inspect the resulting chain.

**Required v8 result**

Events are ordered and linked inside one transaction.

## REG-010 — Atomic writes use predictable fixed temporary names

- Severity: **P1**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py atomic_write`
- Target milestone: **3**

**Reproduction specification**

1. Invoke two writes to the same JSON path concurrently.
2. Observe both use the same .tmp path.
3. Inspect errors or lost state.

**Required v8 result**

Transactional storage or unique durable temporary files eliminate collisions.

## REG-011 — Reviewer independence relies on self-declared strings

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `record_review and actor fields`
- Target milestone: **3**

**Reproduction specification**

1. Implement as actor builder-a.
2. Submit review as actor reviewer-b from the same identity and process.
3. Observe the string comparison accepts apparent separation.

**Required v8 result**

Authenticated capabilities prevent the builder identity from reviewing its own work.

## REG-012 — Side-effect lifecycle has no role-based authorization

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `side_effect_transition`
- Target milestone: **12**

**Reproduction specification**

1. Claim as a builder.
2. Advance an operation through EXTERNALLY_VERIFIED and COMMITTED as the builder.
3. Observe no role authorization denial.

**Required v8 result**

Only capabilities authorised for each transition may advance it.

## REG-013 — Contracted commands execute with shell=True

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `laos_runtime.py run_check`
- Target milestone: **9**

**Reproduction specification**

1. Create a blueprint check containing shell metacharacters.
2. Run the check.
3. Observe shell interpretation.

**Required v8 result**

Commands execute as frozen argv arrays; shell use requires exceptional policy.

## REG-014 — Identifier-to-path conversion lacks strict identifier contracts

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `locks, baselines, checkpoints, evidence paths`
- Target milestone: **3**

**Reproduction specification**

1. Supply identifiers or paths containing traversal or separator characters.
2. Reach the filesystem construction path.
3. Observe insufficient early rejection.

**Required v8 result**

Typed identifier and safe-path validation rejects the input before filesystem use.

## REG-015 — Compiler force deletion lacks robust dangerous-target protection

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `compile_project_pack.py --force`
- Target milestone: **3**

**Reproduction specification**

1. Invoke compilation with --force and a dangerous existing output target such as a source root or important parent.
2. Observe destructive removal is not guarded by a comprehensive safety policy.

**Required v8 result**

Dangerous roots, ancestors, source paths, and protected directories are always rejected.

## REG-016 — Artifact and checkpoint collection can encounter unsafe link semantics

- Severity: **P0**
- Classification: `CONFIRMED_V7`
- Affected area: `artifact/checkpoint collection`
- Target milestone: **3**

**Reproduction specification**

1. Place links in an authorised collection path.
2. Build an artifact or checkpoint.
3. Inspect whether external or unexpected content can be captured.

**Required v8 result**

Collection uses lstat-style policy and never follows an external target.

## REG-017 — Continuation guidance references a reconciliation path not guaranteed in the generated pack

- Severity: **P1**
- Classification: `CONFIRMED_V7`
- Affected area: `continuation documentation/compiler output`
- Target milestone: **8**

**Reproduction specification**

1. Compile a continuation pack with repository drift guidance.
2. Inspect generated tasks.
3. Compare the recommended TASK-000/setup procedure with tasks actually present.

**Required v8 result**

Guidance and generated executable workflow always agree.

## REG-018 — Task-level state can mask partially completed acceptance criteria

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 task lifecycle`
- Target milestone: **10**

**Reproduction specification**

1. Create a task with several acceptance criteria.
2. Satisfy checks/evidence for only a subset.
3. Use broad task-level gates to advance.

**Required v8 result**

Each criterion has independent current proof and review before task closure.

## REG-019 — Manual evidence can be structurally present but semantically weak

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 evidence records`
- Target milestone: **10**

**Reproduction specification**

1. Write vague evidence over the minimum byte threshold.
2. Register its hash.
3. Attempt to pass the evidence gate.

**Required v8 result**

Behavioural proof is runtime-generated or independently verified at the required maturity.

## REG-020 — A weaker agent receives too much process at once and can skip steps

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 task packets and entry instructions`
- Target milestone: **6**

**Reproduction specification**

1. Give the complete multi-step task packet to a weak executor.
2. Observe it move directly to implementation or completion without all intermediate obligations.

**Required v8 result**

Only one signed legal Action Capsule is issued at a time.

## REG-021 — No mandatory machine-checked understanding gate exists

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 workflow`
- Target milestone: **6**

**Reproduction specification**

1. Let an agent claim and start a task without restating objective, invariants, non-goals, uncertainty, or verification.
2. Observe implementation is permitted.

**Required v8 result**

No edit authority exists until structured understanding passes.

## REG-022 — No mandatory criterion-mapped planning gate exists

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 workflow`
- Target milestone: **6**

**Reproduction specification**

1. Start implementation without mapping each acceptance criterion to files, checks, failure paths, and evidence.
2. Observe the runtime allows it.

**Required v8 result**

Implementation is locked until a validated plan covers every criterion.

## REG-023 — Master and weaker-agent trust zones are not physically enforced

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 packaging model`
- Target milestone: **5**

**Reproduction specification**

1. Inspect generated materials available to the weaker agent.
2. Look for broad project strategy, future tasks, or master framework content.

**Required v8 result**

Execution packs are separately built and leak-scanned.

## REG-024 — No real operating-system sandbox is enforced by LAOS itself

- Severity: **P0**
- Classification: `KNOWN_LIMITATION`
- Affected area: `v7 runtime`
- Target milestone: **9**

**Reproduction specification**

1. Run the agent process with ordinary host filesystem/network permissions.
2. Access resources outside the intended repository.

**Required v8 result**

High-risk execution fails closed unless a tested sandbox provider supplies the required isolation.

## REG-025 — Local event hash chain is not externally authenticated

- Severity: **P1**
- Classification: `CONFIRMED_V7`
- Affected area: `event chain and anchor`
- Target milestone: **13**

**Reproduction specification**

1. Modify historical events.
2. Recompute later hashes and the local anchor using repository write access.
3. Observe local consistency can be restored.

**Required v8 result**

Important ledger tips and attestations are signed or anchored outside builder authority.

## REG-026 — No stable typed security error hierarchy exists

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 LaosError`
- Target milestone: **2**

**Reproduction specification**

1. Trigger distinct authorization, validation, state, and integrity failures.
2. Observe they share a generic error type without stable machine code.

**Required v8 result**

AuthorizationDenied and other stable typed errors are returned consistently.

## REG-027 — Immutable release verification previously included a mutable SQLite database

- Severity: **P0**
- Classification: `PRIOR_V8_REPORTED`
- Affected area: `lost prior v8 implementation`
- Target milestone: **13**

**Reproduction specification**

1. Initialize a project runtime database inside the release tree.
2. Generate the static release manifest.
3. Modify runtime state.
4. Verify the static pack.

**Required v8 result**

Only migrations and initialization code ship; mutable databases remain project-local and outside static manifests.

## REG-028 — Unauthorized side-effect verification previously raised the wrong exception category

- Severity: **P0**
- Classification: `PRIOR_V8_REPORTED`
- Affected area: `lost prior v8 implementation`
- Target milestone: **12**

**Reproduction specification**

1. Use a builder capability to request EXTERNALLY_VERIFIED.
2. Inspect exception type, error code, audit event, external call count, and state.

**Required v8 result**

AuthorizationDenied is raised; denial is audited; no external action or transition occurs.

## REG-029 — Evidence-manifest hardening was not followed by a final complete test run

- Severity: **P0**
- Classification: `PROCESS_FAILURE`
- Affected area: `prior lost v8 work`
- Target milestone: **16**

**Reproduction specification**

1. Change evidence-manifest validation.
2. Publish a completion claim without rerunning the complete suite.
3. Observe verification gap.

**Required v8 result**

Any relevant change invalidates prior test evidence and requires complete rerun.

## REG-030 — Previously claimed v8 release artifacts were not durably preserved or reopened

- Severity: **P0**
- Classification: `PROCESS_FAILURE`
- Affected area: `prior session artifact loss`
- Target milestone: **16**

**Reproduction specification**

1. Create or claim a release artifact in temporary storage.
2. Allow runtime cleanup/reset.
3. Attempt to retrieve the artifact.
4. Observe no durable verified copy.

**Required v8 result**

Durability, existence, stat, hash, extraction, retest, and reopen checks are hard release gates.

## REG-031 — No extracted-release full-suite retest was completed for prior v8 work

- Severity: **P0**
- Classification: `PROCESS_FAILURE`
- Affected area: `prior v8 report`
- Target milestone: **16**

**Reproduction specification**

1. Build a release archive.
2. Do not extract to a clean location and rerun all verification.
3. Observe source-tree results are incorrectly treated as release proof.

**Required v8 result**

The extracted artifact independently passes the complete suite.

## REG-032 — No real sandbox provider was tested in prior v8 work

- Severity: **P0**
- Classification: `PRIOR_V8_REPORTED`
- Affected area: `prior v8 report`
- Target milestone: **9**

**Reproduction specification**

1. Configure a high-risk action requiring isolation.
2. Run where no validated provider is available.

**Required v8 result**

The action blocks; release requires at least one real tested provider.

## REG-033 — No real comparative weaker-model evaluation was completed

- Severity: **P1**
- Classification: `CONFIRMED_GAP`
- Affected area: `release evidence and prior reports`
- Target milestone: **14**

**Reproduction specification**

1. Inspect release evidence for repeated real-agent baseline, v7, and v8 trials.
2. Observe normal software tests but no behavioural comparison matrix.

**Required v8 result**

A reproducible real-agent evaluation report supports any performance claim.

## REG-034 — Documentation can overstate enforcement and completeness

- Severity: **P1**
- Classification: `CONFIRMED_GAP`
- Affected area: `v7 documentation and prior v8 claims`
- Target milestone: **15**

**Reproduction specification**

1. Compare stated guarantees with implemented boundaries and test evidence.
2. Identify procedural controls described as technical guarantees.

**Required v8 result**

Documentation is generated/reviewed against verified capability and explicit limitations.

## REG-035 — Duplicate entry documents increase ambiguity and cognitive load

- Severity: **P2**
- Classification: `CONFIRMED_V7`
- Affected area: `FOR_NILHAN.md and START_HERE_FOR_NILHAN.md`
- Target milestone: **15**

**Reproduction specification**

1. Hash both files.
2. Observe identical content with separate authoritative-looking names.

**Required v8 result**

One canonical role entry point exists; archived aliases are clearly non-authoritative.

## REG-036 — Repository content can contain prompt-injection-like instructions

- Severity: **P0**
- Classification: `THREAT_GAP`
- Affected area: `agent context handling`
- Target milestone: **4**

**Reproduction specification**

1. Place instructions in repository documentation asking the agent to ignore Architect policy or exfiltrate data.
2. Present them during investigation or implementation.

**Required v8 result**

Context provenance and policy prevent untrusted content from increasing authority.

## REG-037 — No resource or cost circuit breaker is enforced

- Severity: **P1**
- Classification: `DESIGN_GAP`
- Affected area: `v7 runtime`
- Target milestone: **7**

**Reproduction specification**

1. Cause repeated commands or failed approaches.
2. Observe no global attempt, cost, or resource budget enforcement.

**Required v8 result**

Action and project budgets block runaway retries and denial-of-wallet behaviour.

## REG-038 — No capability revocation or policy/model/skill drift guard exists

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `v7 runtime`
- Target milestone: **5**

**Reproduction specification**

1. Issue work authority.
2. Change repository seal, policy, model profile, or authorised skills.
3. Attempt to reuse old authority.

**Required v8 result**

Outstanding capsules become invalid and cannot be replayed.

## REG-039 — No formal uncertainty ledger prevents guesses becoming project truth

- Severity: **P1**
- Classification: `DESIGN_GAP`
- Affected area: `capture and handoff workflow`
- Target milestone: **6**

**Reproduction specification**

1. Record an unknown in prose.
2. Allow a later prompt or plan to treat it as fact without resolution evidence.

**Required v8 result**

Unknowns have explicit state, provenance, owner, resolution, and acceptance.

## REG-040 — Static and mutable manifests are not formally separated in v7

- Severity: **P0**
- Classification: `DESIGN_GAP`
- Affected area: `release/runtime layout`
- Target milestone: **13**

**Reproduction specification**

1. Mix generated runtime records with harness or artifact integrity inputs.
2. Change runtime state.
3. Observe static integrity becomes unstable or ambiguous.

**Required v8 result**

Separate immutable release, static harness, runtime state, evidence, and artifact manifests.

## REG-041 — Protected authority and time fields were outside the envelope signature

- Scan finding: `LAOS-S5-F-001`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Change issuer, audience, issue time, or expiry while
retaining the signature; the vulnerable verifier accepted the altered context.

**Regression evidence:** Protected-envelope v2 and its golden vector authenticate
the complete authority/time statement. See
`tests/stage3/test_capsule_and_signing.py` and
`tests/stage5/test_action_engine.py`. Legacy v1 fails closed.

## REG-042 — Trusted key registration did not constrain the claimed issuer

- Scan finding: `LAOS-S5-F-002`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Register a key for one issuer, sign an envelope that
claims another issuer, and verify the pack through the trust registry.

**Regression evidence:** Trust-created verifiers carry the registered issuer and
deny cross-issuer use with `TRUST_ISSUER_MISMATCH`; see
`tests/stage5/test_packs_and_trust.py`.

## REG-043 — Windows `.GIT` aliases could install an executing Git configuration

- Scan finding: `LAOS-S5-F-003`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Supply `.GIT/config` and `.gitattributes` in a
template so `git add` invokes a malicious clean filter on Windows.

**Regression evidence:** Unicode-normalized, case-folded complete-template
validation denies `.git`/`.laos` aliases, case collisions, Windows ambiguous
names, and unsafe Git configuration. Writes use no-follow atomic operations and
Git runs without system/global configuration or hooks. See
`tests/stage5/test_core_workflows.py`.

## REG-044 — Future capture timestamps bypassed freshness checks

- Scan finding: `LAOS-S5-F-004`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Sign a capture whose fact timestamp is far in the
future; freshness arithmetic treated it as current.

**Regression evidence:** Initial and continuation validation share one chronology
validator, allow at most 300 seconds of positive skew, and deny future facts,
invalid ordering, stale facts, or completion after envelope issuance. See
`tests/stage5/test_capture_security.py`.

## REG-045 — Stage 3 generation failure could preserve an older PASS

- Scan finding: `LAOS-S5-F-005`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Leave a PASS at the evidence path, then fail Docker
startup before the old generator writes replacement evidence.

**Regression evidence:** The generator atomically publishes `IN_PROGRESS` before
collection and replaces it with `FAIL` on every exception. Current verification
requires the expected run ID and source revision. See
`tests/stage5/test_evidence_integrity.py`.

## REG-046 — Stage 5 checkpoint trusted mutable self-asserted evidence

- Scan finding: `LAOS-S5-F-006`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Replace repository evidence fields with fabricated
PASS values that were not tied to a current execution or source revision.

**Regression evidence:** Candidate receipts bind the run, commit/tree, fixed
command arrays, exit codes, sanitized transcript hashes, and artifact hashes;
Docker readiness is checked live. Approval remains a separate Nilhan-authored
receipt. See `tests/stage5/test_evidence_integrity.py`.

## REG-047 — Stage 5 coverage verification allowed criterion substitution

- Scan finding: `LAOS-S5-F-007`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_SCAN`
- Affected revision: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- Status: `REMEDIATION_VERIFIED_AWAITING_NILHAN_REVIEW`

**Original reproduction:** Duplicate one passing coverage row while omitting a
different required criterion; the vulnerable row-count check still passed.

**Regression evidence:** The Stage 5 verifier requires the exact unique
`S5-01` through `S5-14` map, expected milestone/status pairs, and the active
Revision 1.1 plan hash. See `tests/stage5/test_evidence_integrity.py`.

## REG-048 — Stage 5 approval accepted an unauthenticated Nilhan name

- Scan candidate: `CAND-001`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Supply an ordinary review JSON file that names
Nilhan and matches the candidate identifiers; the verifier produced approval.

**Regression evidence:** Review verification now binds the candidate tag,
source parent, and exact receipt blob, then fails closed with
`PROTECTED_NILHAN_REVIEW_AUTHENTICATION_NOT_IMPLEMENTED`. Protected Nilhan
authentication remains Stage 6 work.

## REG-049 — Candidate command PASS rows were self-asserted

- Scan candidate: `CAND-002`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Replace every command argument array with invented
values while retaining PASS-shaped rows; candidate verification accepted them.

**Regression evidence:** The receipt must match one exact ordered, run-bound
command map and declares `producer_authentication=NONE_STAGE6_OPEN`. It is
builder-asserted bootstrap evidence, not an authenticated execution attestation.

## REG-050 — Current Stage 3 evidence could bind dirty bytes to clean Git IDs

- Scan candidate: `CAND-006`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Modify working-tree code, run the standalone
generator, and observe evidence attributed to unchanged HEAD and tree IDs.

**Regression evidence:** Current generation and verification require a clean
worktree and an evidence path outside the repository before collectors run.

## REG-051 — Full current Stage 3 verification accepted hand-authored collectors

- Scan candidate: `CAND-007`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Hand-author PASS-shaped Docker, state, signing, and
operator rows without running collectors; full current verification accepted it.

**Regression evidence:** Full current mode regenerates the run-bound evidence
with the fixed generator before verification. Historical mode cannot emit a
current PASS.

## REG-052 — Review did not bind source, evidence commit, and receipt blob

- Scan candidate: `CAND-010`
- Severity: **P2**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Point the candidate tag at an unrelated commit while
using independently matching receipt fields; the structural checks accepted it.

**Regression evidence:** The tagged evidence commit must have exactly one
parent equal to the source commit and contain the exact candidate receipt blob.
Approval still requires the unimplemented protected Nilhan authentication.

## REG-053 — Substring filtering could hide unrelated dirty files

- Scan candidate: `CAND-004`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Choose `s` as the output name so substring filtering
also removed a dirty `src/file.py` status row.

**Regression evidence:** The builder parses NUL-delimited Git status records
and exempts only one exact normalized output path.

## REG-054 — Receipt output could overwrite a just-hashed package

- Scan candidate: `CAND-005`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Select a package path as receipt output; the final
atomic JSON write replaced the artifact after its digest was recorded.

**Regression evidence:** In-repository output is restricted to the exact
untracked Stage 5 Evidence JSON path. Tracked and colliding paths are denied.

## REG-055 — Stale Stage 3 evidence could still claim current PASS

- Scan candidate: `CAND-008`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Present otherwise valid current evidence completed
in the distant past; no maximum age prevented PASS.

**Regression evidence:** Current evidence must complete within 15 minutes of
verification and is regenerated immediately before the full verifier runs.

## REG-056 — Candidate verification skipped claimed package artifacts

- Scan candidate: `CAND-009`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Supply absent package files and fabricated package
hashes; the verifier explicitly skipped both rows.

**Regression evidence:** Ephemeral packages are no longer claimed as retained
candidate artifacts. The exact `uv build` invocation remains a command gate;
release artifact custody remains open for Stage 8.

## REG-057 — Signed capture events could predate their request

- Scan candidate: `CAND-011`
- Severity: **P3**
- Classification: `CONFIRMED_V8_STAGE5_REMEDIATION_DIFF_SCAN`
- Affected revision: `2e213deb096382151206c035a5f1143687002fcc`
- Status: `REMEDIATION_IMPLEMENTED_VERIFICATION_PENDING`

**Original reproduction:** Sign facts, completion, and envelope issuance that
all predate request issuance; the continuation path accepted them.

**Regression evidence:** Validated capture state carries request issuance and
both initial validation and continuation deny pre-request events with
`CAPTURE_BEFORE_REQUEST_ISSUED`. Exactly 300 seconds of positive skew remains
allowed by policy; 301 seconds remains denied.

