# ADR-0014: Evidence custody and external anchoring

- Status: **Stage 6 encrypted Docker custody implemented; protected Nilhan review pending**

## Stage 5 decision

Evidence generation publishes a versioned `IN_PROGRESS` receipt before work
begins and atomically replaces it with `FAIL` or
`PASS_AWAITING_NILHAN_REVIEW`. The receipt binds a unique run ID, source
commit/tree, generator version, fixed command arrays, start/end times, exit
codes, sanitized transcript hashes, and retained artifact hashes. Any exception
replaces an earlier PASS at the selected output path. Ephemeral package files
are represented by the exact `uv build` command gate, not falsely presented as
retained release artifacts.

Current-evidence verification requires the expected run ID and source revision,
a clean worktree, regeneration by the fixed collector immediately before
verification, and completion within a 15-minute freshness window. Historical
inspection is explicitly labelled and cannot produce a current PASS.

Stage 5 bootstrap receipts declare `producer_authentication=NONE_STAGE6_OPEN`.
Their command rows are builder assertions constrained to one exact run-bound
argument map; they are not authenticated execution attestations. An ordinary
JSON file naming Nilhan cannot record `APPROVED`. Machine approval fails closed
with `PROTECTED_NILHAN_REVIEW_AUTHENTICATION_NOT_IMPLEMENTED` until Stage 6
provides protected review identity and custody. The candidate tag still binds
the evidence commit's sole parent to the source commit and the exact receipt
blob so later protected review cannot substitute another revision.

## Stage 6 decision

Canonical Stage 6 evidence is written by a one-shot, networkless, non-root
Docker custodian into a dedicated data volume. A separate key volume contains
the AES-256-GCM key and is mounted read-only after bootstrap. Per-object
associated data binds criterion, classification, source/result seals,
collector/version, policy, redaction, evidence level, timestamp, and plaintext
digest. Project-facing evidence consists of sanitized records and an
event-anchor-signed index; builders cannot write the canonical store through
the supported broker path.

Restricted, personal, secret, and raw evidence expires after 30 days. Public
and internal structured records, signed indexes, verdicts, and purge tombstones
remain for the project lifetime. A verified protected Nilhan review may place
or release a legal hold. Purge deletes the canonical object and retains a
non-rebindable tombstone; reconciliation reports missing or orphaned objects.
Likely credential/private-key material is rejected before persistence.

Historical Stage 1–5 evidence remains byte-for-byte unchanged and retains its
original bootstrap assurance. Stage 6 does not retroactively upgrade it.

## Remaining boundary

Custody is local Docker-volume custody under the supported single-operator
trust boundary, not cloud/KMS, hostile-administrator, or disaster-recovery
escrow. External event anchoring and release custody remain later-stage work.
RB-011 through RB-014 receive Stage 6 mitigation evidence but remain formally
OPEN until the Stage 10 release-blocker gate.
