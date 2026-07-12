# ADR-0005: Authenticate identities and bind authority to signed capability envelopes

- Status: **Accepted at the architectural level**
- Date: 2026-07-12

## Context

Self-declared actor strings cannot prove builder/reviewer independence or protect side-effect transitions.

## Decision

Represent actors, sessions, roles, and capabilities explicitly. Bind every Action Capsule to actor, role, project, repository seal, policy, model profile, authorised skills, nonce, and expiry. Support revocation and replay prevention. Keep private keys and raw secrets outside project repositories. Use one stable AuthorizationDenied hierarchy for all policy denials.

## Consequences

Identity integration becomes required for meaningful independence. Offline/local modes must state their lower assurance rather than imitate strong provenance.
