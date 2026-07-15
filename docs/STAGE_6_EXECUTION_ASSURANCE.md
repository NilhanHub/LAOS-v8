# Stage 6 execution-assurance boundary

Stage 6 implements Revision 1.1 Milestones 9–11 for the supported local
Windows/Docker row. Docker is the only qualifying sandbox. It supports Low and
Moderate risk work with read-only source, no network or credentials, bounded
resources, protected checks, clean verification, encrypted evidence custody,
criterion-level closure, Git compare-and-swap promotion, and passphrase-backed
Nilhan review.

Nilhan remains the sole human reviewer. Separate model sessions, actor names,
workspaces, or roles controlled by Codex do not create independent principals.
The quorum validator requires Nilhan plus two genuinely distinct verifier trust
roots for High/Critical work. That quorum is not enrolled in this support row,
so High/Critical operations fail closed with `QUORUM_UNAVAILABLE`.

The Stage 4 real weak-AI proposal is replayed as immutable input through the
Stage 6 clean-verification, protected-check, custody, and criterion pipeline.
No new model profile is released. Real secrets, egress, host fallback, managed
sandbox providers, microVM providers, and distributed state remain outside
this stage.

Stage 6 completion requires a candidate produced from a clean reconstruction
and a protected OpenSSH signature from Nilhan. Until that signature is verified,
the status is `PASS_AWAITING_NILHAN_PROTECTED_REVIEW`; LAOS v8 remains incomplete
and unreleased, and all release blockers remain open.
