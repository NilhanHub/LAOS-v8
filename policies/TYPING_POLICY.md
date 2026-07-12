# Typing policy

1. Supported Python versions and type-checker configuration will be finalized in Milestone 2; the intended baseline is modern Python with strict static checking.
2. Public functions, data records, error types, and state transitions require complete annotations.
3. `Any`, unchecked casts, and untyped dictionaries at trusted boundaries require written justification.
4. External JSON is never treated as a typed object until schema and semantic validation pass.
5. Identifier, path, digest, timestamp, state, role, capability, and version concepts should use explicit value types rather than interchangeable strings.
