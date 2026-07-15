# ADR-0006: Treat OS isolation as a provider with fail-closed policy

- Status: **Accepted; Docker Linux/amd64 Stage 6 low/moderate profile exercised**
- Date: 2026-07-12
- Lifecycle amendment: 2026-07-14

## Context

Prompt rules and repository-delta checks cannot prevent a process from accessing host files, credentials, or networks.

## Decision

Define a sandbox-provider interface for containers, VMs, microVMs, or managed coding sandboxes. Policy declares the isolation properties an action requires. High-risk work blocks when no validated provider satisfies them. At least one real provider must be tested before v8 release.

The first provider is the digest-pinned Docker profile in `SANDBOX_PROFILE.json`. It is networkless, read-only,
non-root, capability-free, `no-new-privileges`, resource-limited, and mounts only the candidate workspace read-only.

Stage 6 formalizes `SandboxProvider`, `CommandSpec`, `ExecutionReceipt`, and
`SandboxAssuranceProfile`. Structured argument arrays, relative working
directories, explicit environment allowlists, pinned image identity, bounded
resources/output, read-only source, disposable writable output, and cleanup are
mandatory. Protected checks are mounted read-only only for the clean-verifier
role in a distinct disposable workspace. No shell exception is enabled for the
local support row.

On the supported Windows profile, provider lifecycle is also mediated. LAOS probes the real trusted Docker CLI,
starts Docker Desktop programmatically when the engine is stopped, waits for readiness, and leaves it running. A
profile-wide argument-preserving wrapper gives other Codex repositories the same behavior. Startup failure blocks
the action and never authorizes direct host execution.

## Consequences

Some environments will support only low-assurance actions. LAOS must degrade by blocking, not by silently pretending
equivalent isolation. Docker startup is idempotent and may be requested concurrently, but LAOS never stops a shared
engine automatically.

Docker is the only qualifying Stage 6 provider. The local provider remains
test-only/unassured; managed and microVM providers remain deferred. Network,
real credentials, host execution fallback, and High/Critical actions are
denied. This is the supported single-operator Windows/Docker boundary, not a
claim against the host administrator.
