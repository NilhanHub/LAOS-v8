# Recovery state

Recorded: `2026-07-12T16:10:01+00:00`

## Confirmed surviving truth

- Original LAOS v7 archive: `/mnt/data/LAOS_v7.0_Complete_System(1).zip`
- SHA-256: `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`
- Bytes: `388876`
- ZIP entries: `155`
- Safe archive assessment: **PASS**
- Shipped v7 tests passed individually: **14 / 14**
- Imported design inputs: **8**

## What does not survive

No prior v8 runtime source tree, executable test suite, SQLite schema, pack compiler, Action Engine, release ZIP, build report, or signed release evidence is treated as present. Earlier descriptions of those capabilities are design input and defect history only.

## Current repository status

This repository implements **Milestone 0 only**: baseline preservation, requirements traceability, known-defect specifications, threat model, architecture decisions, policies, and verification tooling. It does not claim a working LAOS v8 runtime.

## Rebuild source

The repository can be reconstructed from the preserved v7 archive, the design-input manifest, and the files committed in this Git history. The original v7 archive remains separately intact and a byte-identical read-only copy is retained under `baseline/source/`.

## Next legal engineering milestone

Milestone 1: create the separate LAOS v7.0.1 emergency correctness branch and executable regressions for canonical fingerprinting, strict schema validation, pre-claim drift, safe paths, symlink escapes, and command execution.

## Git baseline

- Milestone 0 content commit: `bae9f8b930d6a150351fd0c0e17cfbcfadc9c227`
- Completion tag: `stage0-complete`
- Resolve the completion commit with `git rev-parse stage0-complete`.
