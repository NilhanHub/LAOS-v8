# ADR-0014: Evidence custody and external anchoring

- Status: **Partial run-bound bootstrap receipts in Stage 5; protected custody and anchoring remain proposed for Stage 6**

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

## Remaining boundary

These receipts improve freshness and tamper detection inside the bootstrap
repository, but they are still builder-generated and repository-visible.
Canonical evidence must ultimately be broker-controlled and content-addressed
outside builder write authority; critical event heads and release decisions
still require independent external anchors. Authenticated Nilhan review,
protected producer identity, and execution outside builder control are not
claimed. RB-011, RB-012, RB-013, and RB-017 remain open.
