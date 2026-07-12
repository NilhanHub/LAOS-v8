# Limitations register — Milestone 0

1. **No LAOS v8 runtime exists in this repository yet.** This milestone contains baselines, requirements, decisions, policies, and regression specifications only.
2. The prior reported v8 source and test trees are not present and are not treated as recoverable implementation.
3. The original v7 test suite passed when its 14 tests were executed individually in this environment. The all-in-one validator exceeded the available long-running command window and is not presented as a completed full-run result.
4. No v8 JSON model implementation, SQLite database, identity provider, policy engine, Action Capsule engine, sandbox provider, evidence broker, side-effect broker, release builder, or evaluation laboratory has been implemented.
5. No real sandbox provider has been tested for v8.
6. No real weaker-agent comparative evaluation has been performed for v8.
7. Cryptographic libraries, model/schema tooling, database settings, and provider integrations still require current primary-source dependency research in their implementation milestones.
8. Threat-model controls are requirements, not current guarantees.
9. The Stage 0 source archive is a planning/baseline deliverable, not an installable LAOS release.
