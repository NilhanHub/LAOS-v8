# ADR-0013: Indeterminate side-effect outcomes

- Status: **Proposed for Stage 7**

External operations use a transactional outbox and provider idempotency where available. Loss of a receipt after dispatch enters `OUTCOME_UNKNOWN`; irreversible operations are reconciled and never retried automatically.

