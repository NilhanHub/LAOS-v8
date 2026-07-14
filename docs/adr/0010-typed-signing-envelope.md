# ADR-0010: Typed signing envelope and key lifecycle

- Status: **Accepted protected-envelope v2 and local protected-signer lifecycle; broader custody remains open**

## Decision

LAOS signs an RFC 8785 canonical protected statement, not a context-free payload.
Protected-envelope v2 authenticates the envelope version, algorithm, key ID and
purpose, payload type and exact encoding, subject digest, issuer, audience,
issue time, and expiry before any consumer uses those fields as authority.
Typed domain separation remains mandatory for every signed object class.

Trust-registry verifiers are bound to the issuer registered with the key.
Caller-supplied issuer, audience, purpose, and time expectations are additional
restrictions; they cannot broaden the registry grant. Pack manifests must agree
with the authenticated envelope issuer, audience, and creation time.

## Compatibility

Serialized envelope v1 is unsupported and fails closed. This intentional
breaking change is acceptable while v8 remains unreleased; no persisted v1
envelope was found. The public signer and verifier calling keywords remain
stable.

## Boundary

Stage 5 has a production-capable local signer for its accepted single-operator
Windows/Docker row. Capsule, event-anchor, and pack-manifest keys are active and
purpose-separated; the release key is reserved for Stage 8. Rotation retires
the prior public key for historical verification, revocation replaces a
compromised active key, and production trust excludes Alpha test roots.

The private key volume is outside compiler and agent workspaces, but Docker or
host administrators remain trusted. External anchoring, KMS/HSM custody,
protected reviewer identity, multi-operator quorum, and full incident recovery
remain assigned to later stages.
