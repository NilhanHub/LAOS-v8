# LAOS v8 provisional pre-Alpha performance budgets

These values are conservative circuit breakers for development and test activity. They are not production
service-level objectives, performance claims, or permission to run an agent. Revision 1.1 requires the Alpha pilot
to measure, recalibrate, and freeze the final numeric budgets at the go/no-go review.

| Metric | Provisional circuit breaker | Stage 2 interpretation |
|---|---:|---|
| Repository manifest | 100,000 entries, 1 GiB input, 60 seconds, 2 GiB peak memory | Reject larger work until profiled and approved. |
| Pack build | 100 MiB output or 60 seconds | Stop; do not silently emit an oversized pack. |
| State operation | 250 ms p95 target, 30 second busy timeout | Future SQLite work must measure this; no Stage 2 state-store claim. |
| Sandbox startup | 60 seconds | Future sandbox work must fail closed after the limit. |
| Evidence growth | 1 GiB per action | Stop before exceeding the boundary. |
| Full verification suite | 30 minutes | Investigate before expanding the suite or timeout. |
| Flake rate | 0 accepted flakes | A nondeterministic gate is a failed gate. |
| Model tokens | 200,000 per action | Future capsules must set a lower task-specific bound where possible. |
| Model cost | USD 25 per action | Future execution must stop or require renewed authority. |
| Retries | 3 per action | A fourth attempt requires a new diagnosis and authority. |
| Human review | 120 minutes per action | Split or redesign the action rather than overload the reviewer. |

Safety constraints, authorization gates, evidence custody, and release blockers always take precedence over these
numeric limits. Exceeding a budget never authorizes degraded validation or reduced review.
