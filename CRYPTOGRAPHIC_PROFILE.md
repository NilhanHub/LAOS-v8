# LAOS v8 cryptographic record profile — Stage 2

Status: contract frozen for Stage 2; signing and protected key custody are not implemented yet.

- Content hashing uses RFC 8785 JCS UTF-8 bytes and SHA-256, represented as `sha256:<lowercase hex>`.
- Signed JSON is carried as exact canonical payload bytes in a typed DSSE-compatible envelope; raw ambiguous JSON is never signed.
- Pre-authentication encoding uses DSSE PAE over an explicit LAOS media type.
- Key purposes are separate: `capsule`, `event_anchor`, and `release`.
- The algorithm allowlist contains Ed25519 only. Algorithm substitution and unknown key purposes fail closed.
- Envelopes bind version, payload type, issuer, audience, subject digest, key ID, key purpose, issued time, optional expiry, and signature.
- Public verification must later pin trust roots, issuer, audience, subject, purpose, version, revocation state, and anti-downgrade policy.
- Stage 2 defines serialization and validation only. It does not create production keys, sign authority, or claim DSSE/Sigstore release conformance.

Golden vectors are in `schemas/golden/canonicalization-v1.json`.
