# Coding policy

1. Prefer small, cohesive modules with explicit public interfaces.
2. Production behaviour must be real; no mock, fake, demo, placeholder, silent dry-run, or simulated success path may be presented as implemented functionality.
3. Every security-sensitive boundary uses default-deny and stable typed errors.
4. Filesystem, command, identity, state, evidence, side-effect, and artifact operations go through their designated broker/module rather than ad-hoc calls.
5. No broad refactor is mixed into a bounded feature or security repair without an approved amendment.
6. Source must be readable, documented at public boundaries, and free of unresolved markers.
7. Time, randomness, identity, filesystem, network, and subprocess dependencies must be injectable where required for deterministic tests.
