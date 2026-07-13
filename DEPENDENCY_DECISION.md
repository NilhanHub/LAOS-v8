# Stage 2 dependency decision

Reviewed: 2026-07-13

## Selected

- Pydantic 2.13.4 — strict typed models and Draft 2020-12 schema generation; MIT.
- jsonschema 4.26.0 — independent Draft 2020-12 validation and format checking; MIT.
- rfc8785 0.1.4 — RFC 8785 canonical bytes; Apache-2.0. It is beta and therefore isolated behind `laos_v8.canonical`, covered by golden vectors, and replaceable without changing the profile.
- Hypothesis 6.156.6 — property and malformed-input testing; MPL-2.0, development only.
- pytest 9.1.1, mypy 2.2.0, Ruff 0.15.21, coverage 7.15.1, build 1.5.1 — pinned development/build tools.
- Hatchling 1.31.0 — pinned build backend.

Direct and transitive resolution is frozen in `uv.lock`. Updates require primary-source review, complete validation, lock refresh, threat-model review, and later SBOM/provenance refresh.

## Rejected for this stage

- Custom JSON-schema implementation: unnecessary correctness risk.
- Raw `json.dumps(sort_keys=True)` as canonicalization: not RFC 8785.
- A cryptography library: Stage 2 freezes the envelope and preimage contract but does not handle production keys or signatures.
- SQLite WAL on the current Python runtime: linked SQLite 3.50.4 does not meet the Revision 1.1 fixed-version profile, so diagnostics select rollback-journal `DELETE` mode.
