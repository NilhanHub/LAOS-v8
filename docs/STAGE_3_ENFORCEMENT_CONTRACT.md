# LAOS v8 Stage 3 deployment and enforcement contract

Status: Stage 3 local Security Spine test profile; awaiting independent review.

This contract does not claim a complete LAOS v8 runtime, production key custody, production side effects, distributed
coordination, or support for unmediated host execution.

## Supported topology

- Host: Windows 11 local NTFS workspace, CPython 3.11–3.14, Git repository, one host control-plane process.
- State: one local SQLite database using foreign keys, `synchronous=FULL`, `busy_timeout=30000`, and rollback-journal
  `DELETE`. WAL is not enabled on the locally linked SQLite 3.50.4 runtime.
- Candidate: disposable `git clone --no-local --no-hardlinks`, detached at an accepted base commit, with an independent
  `.git` directory and explicit line-ending policy.
- Executor: Docker Desktop Linux/amd64 container using the digest-pinned profile in `SANDBOX_PROFILE.json`.
- Provider lifecycle: Docker Desktop is started automatically on demand, readiness is verified before dispatch, and
  the shared engine remains running afterward.
- Risk: the local Docker test row is limited to low and moderate actions; high and critical actions fail closed.
- Model path: deterministic local-only test adapter. External model transmission and built-in tools are unsupported.
- Evidence: host broker-owned content-addressed storage outside the executor workspace.
- Verification: a separately authenticated principal and a second clean clone.

## Trusted computing base

The host Python control plane, SQLite, Git, Docker Engine/Desktop, the pinned container image, the local filesystem,
the host OS identity, and the protected in-memory Stage 3 test signer form the test-profile trusted computing base.
The executor process, repository text, model output, command output, and evidence submissions are untrusted.

## Mandatory mediation

The executor receives only a read-only candidate mount. It has no mount for canonical state, signing material,
evidence custody, the authoritative Git repository, host credentials, Docker control, or private planning material.
All writes are brokered with normalized relative paths. Commands use structured argv inside the container. Network is
`none`; the container is non-root, read-only, capability-free, and resource-limited. Policy or emergency-stop denial
occurs before broker dispatch.

The supported Windows mutation row relies on this isolation boundary: the untrusted executor cannot write or replace
host path components, while the single host broker exclusively owns mutation. `SafeRoot` rejects reparse points,
hard links, device/UNC/ADS paths, and traversal before atomic replacement. General concurrent host-writer mutation
without final-handle containment is unsupported; broader race-safe cross-platform path support remains open.

## Failure behavior

- Missing Docker installation, failed automatic Docker Desktop startup, an unverified image, stale policy, stale
  repository seal, expired/replayed capsule, wrong identity, path escape, unavailable evidence custody, or an
  emergency stop blocks the affected action.
- SQLite network paths and distributed coordination are rejected.
- Non-Git authoritative mutation, offline privileged operation, raw-secret injection, external model calls, production
  side effects, and critical work without quorum remain unsupported.
- A database/filesystem boundary operation uses the transactional outbox; exactly-once execution is not claimed.

## Review boundary

Stage 3 tests use deterministic actors and a protected ephemeral test signer. No real weaker agent is run against
untrusted content in this stage. Stage 4 owns the first Alpha vertical trust slice and real bounded agent experiment.
