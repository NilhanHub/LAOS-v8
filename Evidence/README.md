# Evidence

## Bootstrap evidence policy

Stage 1 and Stage 2 review, clean-reconstruction, and completion records are retained as historical Bootstrap
evidence. Stage 3 adds the dependency amendment, local Security Spine profile, verifier output, and clean candidate
evidence. `STAGE_3_LOCAL_SECURITY_PROFILE.json` includes a real pinned Docker isolation probe and local operator-path
tests; it does not constitute production attestation.

These records do not constitute production v8 evidence custody or production cryptographic signing. Stage 3 remains
`AWAITING_NILHAN_REVIEW` until Nilhan records independent review.

This folder is intentionally present at the repository root. Stage 0 baseline and verification evidence may be stored here. Future project runtimes will place signed indexes and approved project-facing evidence under a root Evidence folder while protecting canonical proof from builder mutation.
