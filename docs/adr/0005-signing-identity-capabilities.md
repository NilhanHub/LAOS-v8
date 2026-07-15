# ADR-0005: Authenticate identities and bind authority to signed capability envelopes

- Status: **Accepted for the Stage 5 signer and Stage 6 protected-review local support rows**
- Date: 2026-07-12

## Context

Self-declared actor strings cannot prove builder/reviewer independence or protect side-effect transitions.

## Decision

Represent actors, sessions, roles, and capabilities explicitly. Bind every Action Capsule to actor, role, project, repository seal, policy, model profile, authorised skills, nonce, and expiry. Support revocation and replay prevention. Keep private keys and raw secrets outside project repositories. Use one stable AuthorizationDenied hierarchy for all policy denials.

For the supported single-operator Windows/Docker row, purpose-separated Ed25519
keys are generated and retained only in a dedicated Docker volume. A one-shot,
networkless, non-root signer container accepts a strict canonical request on
standard input and returns only a protected envelope or public metadata. It has
no listening port, Docker socket, project mount, or private-key export command.
The release-purpose key is provisioned but reserved and cannot sign in Stage 5.

The compiler depends only on the `Signer` protocol. `ProtectedTestSigner`
remains unit-test-only; production-profile compilation uses
`DockerProtectedSigner` and records its lower, local assurance explicitly.

Stage 6 adds a separate Nilhan review trust root. The profile-installed helper
uses OpenSSH Ed25519 signing under the `laos-v8-review` namespace. The private
key is passphrase protected outside the repository; the passphrase is entered
only into OpenSSH's interactive prompt and is never accepted through command
arguments, environment variables, files, logs, or evidence. Each signature
binds the candidate revision, plan, criteria, policy, evidence index, protected
checks, verification receipt, verdicts, issuance time, and expiry. Consumed
challenge IDs are persisted to reject replay.

## Consequences

Identity integration becomes required for meaningful independence. Offline/local modes must state their lower assurance rather than imitate strong provenance.

This row trusts Nilhan and anyone with Docker/host-administrator authority.
Passphrase-backed review prevents an unattended builder/model from fabricating
Nilhan approval, but it does not claim resistance to Nilhan, a host
administrator, malware, or a keylogger. HSM/KMS and multi-operator rows remain
later work. High/Critical work remains denied because the local profile cannot
satisfy true multi-principal quorum.
