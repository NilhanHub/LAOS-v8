# ADR-0006: Treat OS isolation as a provider with fail-closed policy

- Status: **Accepted**
- Date: 2026-07-12

## Context

Prompt rules and repository-delta checks cannot prevent a process from accessing host files, credentials, or networks.

## Decision

Define a sandbox-provider interface for containers, VMs, microVMs, or managed coding sandboxes. Policy declares the isolation properties an action requires. High-risk work blocks when no validated provider satisfies them. At least one real provider must be tested before v8 release.

## Consequences

Some environments will support only low-assurance actions. LAOS must degrade by blocking, not by silently pretending equivalent isolation.
