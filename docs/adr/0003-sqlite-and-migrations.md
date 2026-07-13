# ADR-0003: Use transactional SQLite for local control-plane state

- Status: **Local Stage 3 state exercised; migration lifecycle remains open**
- Date: 2026-07-12

## Context

Independent JSON read-modify-write operations cannot safely coordinate concurrent agents, claims, events, evidence, and side effects.

## Decision

Use SQLite with explicit migrations, foreign keys, uniqueness constraints, transactional state transitions, and tested journal/recovery settings for local execution. Distributed execution requires an external transactional store or lease service; local SQLite locks will not be advertised as distributed coordination.

The Stage 3 Windows profile uses rollback-journal `DELETE`, `synchronous=FULL`, and a 30-second busy timeout. WAL is
not enabled because the linked SQLite 3.50.4 runtime is not a documented fixed WAL-reset release.
New databases and same-version backup/restore are tested. Unknown, unversioned, and older state schemas fail closed;
forward, backward, interrupted, and corrupted migration coverage remains a later milestone obligation.

## Consequences

Database initialization and migrations become first-class tested code. No live database ships in the immutable release.
