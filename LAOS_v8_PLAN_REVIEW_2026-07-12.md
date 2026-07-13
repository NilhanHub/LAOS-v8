# LAOS v8 execution-plan review

**Review date:** 2026-07-12  
**Reviewed artifact:** `LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md`  
**Stage 0 plan snapshot SHA-256:** `1b0517c1e85332bd393d4173c0000966eb5f7382f3bef58e2efbfccec7937779`  
**Disposition:** Core direction approved; execution order and several security/evaluation contracts materially revised before Milestone 1.

## Executive assessment

The original plan is an unusually strong requirements and assurance catalogue. Its best qualities are its honesty about missing implementation, default-deny posture, separation of Architect and executor material, evidence-first acceptance, transactional intent, independent review, safe-release discipline, and explicit recognition that workflow rules are not OS isolation.

It was not yet an executable program. Several early exit gates depended on brokers, signing, evidence, review, or side-effect systems scheduled much later. It also attempted to build most of the platform before testing the central hypothesis that one bounded action and criterion-linked proof materially improve weaker-agent outcomes.

Revision 1.1 keeps the mission and strongest controls, but changes the program from a horizontal subsystem build into a sequence of enforced end-to-end increments.

## Evidence reviewed

- The 1,513-line Stage 0 execution and release plan.
- Stage 0 completion record and build report.
- Stage 0 requirements ledger: 210 requirements.
- Regression catalogue: 40 regressions.
- Threat model: 40 threats.
- Seven Stage 0 ADRs.
- v8 implementation backlog and v7 baseline evidence.
- Independent architecture, security, delivery, and evaluation critiques.
- Current primary specifications for JSON Schema, signed/canonical records, SQLite WAL, SLSA, Sigstore, and update trust.

The sealed Stage 0 package was not changed. The standalone plan records how its revision must be imported and reconciled into a reconstructed v8 Git repository.

## Principal findings

### P0 — Fix before real-agent execution

1. **The enforcement topology was undefined.** The plan did not state how agents were prevented from bypassing LAOS and using host files, commands, networks, credentials, or browsers directly.
2. **Milestone dependencies were circular.** Examples included side-effect authorization in Milestone 2, signed seals in Milestone 3, capsule revocation in Milestone 4, real calibration in Milestone 7, and technically read-only capture in Milestone 8 before the owning systems existed.
3. **Repository mutation and canonical state had no promotion transaction.** An implementation action necessarily changes the source, but the plan used one generic seal and did not define candidate workspaces, base/result lineage, clean reconstruction, locked promotion, or crash reconciliation.
4. **The Action state machine combined definition, authorization, execution, verification, and acceptance lifecycles.** That made retries, revocation, consumption, and review ambiguous.
5. **The decisive vertical experiment came too late.** Evaluation was scheduled after nearly the whole platform, creating a high risk of an elegant but unvalidated framework.
6. **Real-agent evaluation was not a defensible confirmatory study.** It lacked a primary estimand, fair resource matching, dataset partitions, power/sample method, uncertainty, blinded grading, stopping rules, and contamination controls.

### P1 — Fix before consequential side effects or release candidate

1. Architect output was too close to signing and release authority. Signing authenticates a bad decision; it does not make the decision safe.
2. Package separation was described more clearly than process, OS-principal, storage, and protocol separation.
3. Crypto requirements lacked typed domain separation, exact bytes, trust bootstrap, key purpose, rotation, revocation, compromise recovery, and anti-downgrade rules.
4. “Immediate revocation” was incompatible with offline capsules.
5. Path containment lacked check/use race resistance and detailed Windows junction, reparse, ADS, hard-link, UNC/device, case, and alias behavior.
6. Structured argv was treated too optimistically: repository tests, builds, package scripts, hooks, and binaries are arbitrary code even without a shell.
7. Sandbox qualification lacked provider-specific assurance requirements and mandatory conformance on each claimed host.
8. Secret redaction was emphasized more than secret non-exposure and credential brokering.
9. External side effects lacked an indeterminate outcome and safe reconciliation model.
10. Local audit chains were described more strongly than their actual tamper-evidence guarantee.
11. Privacy, evidence retention/purge, trust-compromise recovery, platform support, performance budgets, migration, and operator UX appeared too late or too vaguely.
12. The new-application workflow was claimed but had no complete implementation milestone.
13. The release blockers, definition of done, and evaluation requirements contradicted one another in several places.

## Material improvements applied

### Execution and scope

- Added a portable, digest-based baseline identity and current Stage 0 status.
- Added explicit v8.0 non-goals and a per-environment capability/support matrix.
- Added Bootstrap, Alpha, Beta, RC, and GA meanings without treating pre-releases as completion.
- Added `MUST_V8_0`, `SHOULD_V8_0`, and `DEFER_V8_X` scope tiers.
- Made v7.0.1 conditional on actual operational need while preserving regression fixtures.
- Added a mandatory Security Spine before any real agent sees untrusted content.
- Added an Alpha Vertical Trust Slice and go/no-go scope freeze.
- Replaced the horizontal 32-step order with a dependency-correct vertical delivery spine.

### Architecture and correctness

- Defined a concrete deployment/enforcement contract and permission-to-broker matrix.
- Added the model-provider boundary: prompt/context transfer, retention/training/region policy, built-in tools, data classes, consent, and transmission canaries are mediated just like network and browser actions.
- Made all model output, including Architect output, an untrusted proposal.
- Defined base/result/workspace/source/evidence seal scopes.
- Added isolated Git clones, hardened Git configuration, broker-owned deltas, `PromotionIntent`, clean reconstruction, compare-and-swap promotion, seal equality, and crash reconciliation.
- Split ActionDefinition, ActionCapsule, ActionAttempt, ReviewRecord, and AcceptanceCriterion lifecycles.
- Added normative transition tables, same-transaction audit events, and transactional outbox requirements.
- Scoped v8.0 fully assured mutation to Git repositories unless a non-Git protocol is separately proven.
- Kept the first implementation a modular monolith and required abstractions to earn their cost.

### Security and privacy

- Added complete mediation, TCB inventory, connected/offline assurance, and strong reviewer-independence requirements.
- Added a typed signature-envelope and full key-lifecycle profile.
- Added exactly-once capsule redemption and anti-replay semantics.
- Limited offline v8.0 to verification/read-only; privileged dispatch and global replay/revocation claims require connected mediation.
- Added race-safe, final-handle filesystem requirements and Windows-specific adversarial cases.
- Added sandbox assurance profiles, egress/redirect/DNS/metadata controls, and browser-side-effect policy.
- Added credential brokering, non-inherited short-lived handles, and encoded-exfiltration tests.
- Replaced “immutable” local logs with honest tamper-evident language and required external anchoring for critical records.
- Added pre-persistence data classification, minimization, encryption/access, retention, export, purge, and backup-deletion rules.
- Added kill switch, mass revocation, quarantine, key rotation, trust rebootstrap, revalidation, and re-attestation drills.

### Side effects and releases

- Added `OUTCOME_UNKNOWN`, reconciliation, compensation, provider operation IDs, and no automatic retry for irreversible indeterminate effects.
- Required exact SLSA/in-toto and signer/issuer/builder verification claims rather than “style” language.
- Added consumer rollback/freeze protection and explicit no-updater behavior when update metadata is absent.
- Added independent reproducible builds or byte-level documented exceptions that remove the claim.
- Replaced narrative blockers with stable `RB-001` through `RB-025` and a machine-readable Release Gate Matrix.
- Made critical findings and non-waivable gates unwaivable.

### Evaluation and operability

- Defined primary efficacy and safety endpoints, fair resource-matched and realistic end-to-end analyses, and bounded claims.
- Added a treatment-independent outer sandbox so broad-prompt/v7 baselines remain safe without receiving the measured v8 controls.
- Added development, locked validation, and sealed final-holdout partitions.
- Added power/sample planning, randomization, blinded dual grading, uncertainty, multiplicity handling, stopping rules, and safety quarantine.
- Changed the evaluation exit gate from “obtain a positive result” to “complete and report a valid study.”
- Required red-team and behavior-affecting fixes before candidate freeze and final holdout; any post-holdout behavior change requires a new untouched holdout.
- Required a new untouched holdout after redesign rather than tuning and rerunning the same final benchmark.
- Moved CLI, clean-install journeys, migration, support matrix, incident recovery, and performance budgets into continuous workstreams beginning before Alpha.

## Recommended immediate next action

Do not begin broad implementation from the three files in the outer folder. First:

1. Reconstruct the verified Stage 0 Git repository from its baseline ZIP or Git bundle.
2. Verify the Stage 0 tag, source manifest, and completion evidence.
3. Import plan revision 1.1 as a new commit without changing the Stage 0 tag or package.
4. Update the requirements ledger, threat model, ADRs, implementation backlog, scope ledger, and blocker matrix to trace every material amendment.
5. Make the conditional v7.0.1 decision.
6. Build only the revised dependency spine through the Security Spine and Alpha Vertical Trust Slice.
7. Use the Alpha evidence to decide whether the rest of v8 deserves to be built as currently conceived.

## Final verdict

The stronger v8 plan is viable enough to proceed, but only after this sequencing and contract correction. Its central idea remains compelling. The revised program now forces an early answer to the important question: can LAOS actually mediate a weaker agent, produce trustworthy evidence, and improve outcomes at an acceptable operational cost? If the Alpha cannot do that, the program should simplify or stop before investing in the full platform.
