# ADR-0010: Typed signing envelope and key lifecycle

- Status: **Accepted for the ephemeral Stage 3 test trust root; production lifecycle remains open**

Authority records use typed domain separation over exact payload bytes. Capsule, event-anchor, and release key purposes remain separate, with pinned trust bootstrap, rotation, revocation, anti-downgrade, historical verification, and compromise recovery.

Stage 3 implements Ed25519 capsule signing with an in-memory non-exportable test key and pinned public trust root.
Production storage, rotation, external anchoring, and compromise recovery remain owned by later stages.
