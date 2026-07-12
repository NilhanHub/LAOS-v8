# ADR-0002: Separate immutable release material from mutable runtime state

- Status: **Accepted**
- Date: 2026-07-12

## Context

A prior reported v8 failure included a live SQLite database in an immutable pack manifest. Normal runtime mutation then invalidated static integrity.

## Decision

The LAOS release ships code, schemas, migrations, policies, templates, prompts, and documentation only. Each project initializes mutable state under its own runtime directory after installation. Databases, WAL/SHM files, locks, claims, leases, logs, and generated evidence indexes are excluded from static release manifests and archives.

## Consequences

Verification uses separate static-release, installed-harness, project-runtime, evidence, artifact, and provenance manifests. Tools must never blur these categories.
