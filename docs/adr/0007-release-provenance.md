# ADR-0007: Deterministic release construction and externally verifiable provenance

- Status: **Accepted**
- Date: 2026-07-12

## Context

A completion narrative is not release proof, and prior v8 artifacts were lost or unverified.

## Decision

Build releases from a clean checkout and clean staging directory. Generate static integrity manifests, checksums, SBOM, provenance, limitations, test and evaluation reports, and appropriate signatures/attestations. Move final artifacts to durable storage, reopen them, verify hashes and listings, safely extract them elsewhere, and rerun the full suite before declaring completion.

## Consequences

Release takes longer and may fail late. That is preferable to publishing an unverifiable or missing artifact.
