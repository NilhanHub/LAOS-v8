# ADR-0010: Typed signing envelope and key lifecycle

- Status: **Accepted protected-envelope v2 for the ephemeral test trust root; production lifecycle remains open**

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

Stage 5 continues to use `ProtectedTestSigner`, an in-memory test signer. This
decision does not supply production key custody, rotation operations, external
anchoring, or compromise recovery. Those release gates remain open and require
Nilhan's independent review.
