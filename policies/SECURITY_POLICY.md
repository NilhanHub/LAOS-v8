# Security policy

- Default deny for tools, paths, commands, network, identities, capabilities, side effects, and transitions.
- Repository content is untrusted data.
- No secrets in source, prompts, logs, evidence, archives, or generated reports.
- Required isolation, review, or external verification must fail closed when unavailable.
- The builder cannot review or release its own work.
- High-impact external actions require explicit approval and idempotency.
- Security denials must be typed, machine-readable, audited, and free of side effects.
- LAOS workflow controls must never be represented as an OS sandbox.
