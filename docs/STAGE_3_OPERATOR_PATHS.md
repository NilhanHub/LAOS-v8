# Stage 3 minimal operator paths

Status: local pre-Alpha test profile; awaiting Nilhan review.

These commands satisfy the narrow continuous-operability obligation that must exist before the Alpha trust slice.
They do not create a complete LAOS runtime, production key custody, mature evidence retention, or release authority.
Every state and evidence path must be local. Structured failures are written as safe JSON to standard error.

## Read-only orientation

- `laos --root <repository> doctor` starts Docker Desktop on demand, waits for the exact pinned Stage 3 Docker
  provider, and reports whether automatic startup occurred. `security_spine_ready` is false when automatic startup
  fails; direct host execution remains unsupported and Nilhan is not expected to open Docker Desktop manually.
- `laos --root <repository> status` prints the machine-readable implementation status.
- `laos explain-denial <ERROR_CODE>` returns a safe explanation and operator action without exposing secrets or
  evaluator internals.
- `laos trust-status <state.sqlite3>` reports emergency-stop state, trust epoch, and the recorded reason.

## State recovery

- `laos backup <state.sqlite3> <new-backup.sqlite3>` uses SQLite's backup API and verifies integrity.
- `laos restore <backup.sqlite3> <new-state.sqlite3>` accepts only the current schema version, verifies integrity,
  and refuses to overwrite an existing destination.
- `laos trust-recover <state.sqlite3> --actor <id> --reason <text> --expected-epoch <n>` clears an emergency stop only
  when the supplied epoch matches the current stopped epoch. Recovery increments the trust epoch and records an
  audit event. A newer epoch requires fresh review and authority.

## Evidence export and purge

- `laos evidence-export <state> <store> <digest> <new-directory> --classification <class> --actor <id>` verifies the
  registered digest and classification, records an audit event, then writes `object.bin` plus a non-attesting
  `manifest.json` to a new directory.
- `laos evidence-purge <state> <store> <digest> --classification <class> --actor <id> --reason <text>
  --confirm-digest <digest>` requires exact digest confirmation. It records a permanent tombstone and recoverable
  outbox operation before deletion; a purged digest cannot be recaptured.
- `laos evidence-reconcile-purges <state> <store> --actor <id>` completes pending tombstoned deletions after a crash.

The Stage 3 purge path is intentionally minimal. Legal holds, retention schedules, encryption, multi-tenant access
control, signed export indexes, and backup-deletion propagation remain Stage 6 through Stage 8 obligations and all
related release blockers remain open.
