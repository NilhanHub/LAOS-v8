# Stage 4 go/no-go and v8.0 scope-freeze candidate

Status: **AWAITING NILHAN AND A SECOND INDEPENDENT REVIEWER**

## Recommended decision

Continue the architecture substantially unchanged, with two calibrated simplifications:

1. Keep the executor text-only and broker-mediated. The experiment demonstrated that weak or malformed outputs fail safely without repository authority.
2. Use `qwen2.5-coder:1.5b` as the minimum local development reference row for this fixture. The 0.5B row failed the protected criterion twice and was never promoted.

Do not claim an efficacy advantage. In the corrected eight-trial development pilot, all four conditions passed 2/2 on two trivial tasks. The sample is intentionally too small and easy to distinguish prompt quality. Its useful result is that the comparison harness, resource ceiling, and containment work; it does not show LAOS improves task success.

## Scope-freeze candidate

Freeze the existing `MUST_V8_0` entries in `SCOPE_LEDGER.json` without adding a new MUST item. Continue to defer additional sandbox providers, distributed state, automatic non-interference, and external model adapters unless an equivalent MUST item is removed or a new non-waivable blocker is validated.

The Alpha pulled forward only the minimum task, capsule, workspace, verification, evidence, review, and promotion slices. It does not close the later full workflow, custody, side-effect, release, or evaluation milestones.

## Review questions

- Nilhan: approve, request bounded changes, or stop?
- Second independent reviewer: confirm that the trust spine mediated the model, that the failure evidence is honest, and that cost/friction does not overwhelm the demonstrated safety benefit.
- If approved, record both identities and decisions before marking Stage 4 complete or authorizing Stage 5.
