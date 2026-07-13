# Stage 1 decision — v7 fixture-only track

- Decision date: 2026-07-13
- Decision owner: Nilhan
- Implementer: Codex
- Independent Stage 1 reviewer: Nilhan
- Decision: do not build or claim a v7.0.1 maintenance release during Stage 1.
- Assurance label: `BOOTSTRAP`

## Rationale

Nilhan selected the fixture-only path so the v8 rebuild is not delayed by a v7 maintenance release. The original v7.0 archive remains immutable and its known weaknesses remain baseline facts.

## Consequences

- No v7.0.1 correctness, release, or support claim is made.
- Relevant v7 weaknesses are captured as reproducible compatibility/regression fixtures.
- Each required repair remains open and is assigned to its owning v8 implementation stage.
- This decision is bound to Git history, hashes, command transcripts, and an annotated review-candidate tag. It is not represented as production v8 cryptographic signing.
- Stage 1 cannot receive a completion tag until Nilhan reviews the generated candidate evidence.

