# ADR-0003: Use transactional SQLite for local control-plane state

- Status: **Accepted for local v8 execution**
- Date: 2026-07-12

## Context

Independent JSON read-modify-write operations cannot safely coordinate concurrent agents, claims, events, evidence, and side effects.

## Decision

Use SQLite with explicit migrations, foreign keys, uniqueness constraints, transactional state transitions, and tested journal/recovery settings for local execution. Distributed execution requires an external transactional store or lease service; local SQLite locks will not be advertised as distributed coordination.

## Consequences

Database initialization and migrations become first-class tested code. No live database ships in the immutable release.
