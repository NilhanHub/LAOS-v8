# ADR-0001: Separate Architect and weaker-agent trust zones

- Status: **Accepted for v8 architecture**
- Date: 2026-07-12

## Context

LAOS exists so a highly capable Software Architect AI can convert full-project reasoning into bounded work for weaker agents. Giving a weaker agent the master framework, full future plan, hidden checks, or signing authority defeats that mission and makes instruction skipping and overreach more likely.

## Decision

Produce physically separate Architect Control, Agent Execution, Capture, and Review Packs. Issue one signed Action Capsule at a time. Use allowlist packaging and deterministic leakage scans. Repository content is untrusted data and cannot modify authority.

## Consequences

Pack compilation, storage, distribution, and tests become more complex. That complexity is accepted because role separation is a core safety property, not optional documentation.
