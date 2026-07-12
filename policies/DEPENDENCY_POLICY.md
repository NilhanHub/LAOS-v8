# Dependency policy

1. Use the standard library where it materially improves auditability without sacrificing correctness.
2. Third-party dependencies require a documented need, current primary-source review, compatible license, maintenance assessment, pinned version strategy, and security scan.
3. Lockfiles and reproducible installation inputs must be committed; release builds use hashes where supported.
4. Download-and-execute installation patterns are prohibited.
5. Build, test, schema, cryptography, sandbox, and provenance dependencies are part of the threat model.
6. Dependency updates require tests, SBOM refresh, and provenance refresh.
