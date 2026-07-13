# LAOS v8 Stage 4 performance-budget candidate

Status: **APPROVED AND FROZEN BY NILHAN FOR THE ALPHA REFERENCE ROW**

The eight-trial local pilot observed model-call times of roughly 3.1–3.8 seconds for two trivial development tasks. These observations are not production SLOs. The following conservative low-risk Alpha ceilings are proposed:

| Metric | Candidate ceiling |
|---|---:|
| Local model | Exact pinned model blob; loopback only; no tools |
| Generated tokens | 1,024 per call |
| Model-call timeout | 120 seconds |
| Model output | 65,536 bytes |
| Bounded repair | 1 per capsule; a further attempt requires a new capsule |
| Writable files | 1 explicitly named source path |
| Write payload | 65,536 bytes |
| Sandbox check | 60 seconds, 256 MiB, 32 processes, 1 CPU |
| Sandbox output | 1 MiB per stream |
| Network, raw secrets, side effects | 0 allowed |
| Evidence object | 1 GiB hard ceiling; task-specific lower bounds preferred |
| Human review | 30 minutes for this low-risk slice |

Repository, pack, state, suite, flake, and release budgets remain as stated in `PERFORMANCE_BUDGETS.md` until measured by their owning later stages. Approval of this file freezes only the Alpha reference row; it does not create a production performance claim.
