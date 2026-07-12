# ADR-0004: Canonical typed models plus strict Draft 2020-12 boundary schemas

- Status: **Proposed; finalize in Milestone 2 after dependency review**
- Date: 2026-07-12

## Context

v7 ships useful schemas but its validators largely check JSON parsing and heuristics. Multiple hand-maintained interpretations can drift.

## Decision

Maintain one versioned model registry. Trusted external records validate against strict JSON Schema Draft 2020-12 contracts at every boundary; semantic validation then enforces references, graph rules, state transitions, and authority. The implementation method for generating or synchronizing Python types and schemas will be chosen in Milestone 2 after current-library research and proof-of-concept tests.

## Consequences

No trusted format is accepted by “best effort.” Schema and model migrations are explicit and tested. This ADR deliberately avoids naming a dependency before that review.
