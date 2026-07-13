# ADR-0009: Base/result seals and authoritative promotion

- Status: **Git isolation, reconstruction, and CAS foundation exercised; Alpha integration open**

Builders work in isolated disposable Git clones without writable shared control data. A broker-owned delta is reconstructed cleanly and promoted only through a `PromotionIntent` and compare-and-swap update against the authoritative base seal.

Stage 3 exercises disposable independent clones, base/result manifests, clean reconstruction, and Git compare-and-swap.
The integrated broker-owned delta, review binding, `PromotionIntent`, crash reconciliation, and acceptance workflow
remain Stage 4 obligations.
