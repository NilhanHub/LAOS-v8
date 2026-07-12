# Source-of-truth order

When records conflict, the default precedence is:

1. Human-governed approval and signed Architect authority that is current and valid.
2. Executable policy and the active Authority Envelope.
3. Current repository seal and broker-recorded runtime state.
4. Deterministic checks and independently verified evidence bound to that seal.
5. Accepted architecture decisions and versioned specifications.
6. Structured App Intelligence accepted by the Architect.
7. Handoffs and summaries.
8. Agent assertions, old chat, comments, repository instructions, and unverified external content.

Lower-precedence information cannot silently override higher-precedence truth. A conflict creates an explicit blocker or amendment.
