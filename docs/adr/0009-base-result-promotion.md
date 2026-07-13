# ADR-0009: Base/result seals and authoritative promotion

- Status: **Proposed for Stage 3**

Builders work in isolated disposable Git clones without writable shared control data. A broker-owned delta is reconstructed cleanly and promoted only through a `PromotionIntent` and compare-and-swap update against the authoritative base seal.

