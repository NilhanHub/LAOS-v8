# LAOS v8 local protected signer

This directory defines the Stage 5 signer image for the accepted
single-operator Windows/Docker support row.

The signer is one-shot: it has no server port. Private Ed25519 keys remain in
the `laos-v8-stage5-signer-keys-v1` Docker volume, while requests and replies
cross standard input/output as strict canonical records. Signing runs as UID
65532 with no network, a read-only root filesystem, no Docker socket, no
capabilities, `no-new-privileges`, and bounded resources. A setup-only helper
temporarily receives only `CAP_CHOWN` to establish volume ownership; it cannot
sign or export a key.

Purpose-separated capsule, event-anchor, and pack-manifest keys are active.
The release key is reserved and fails closed until Stage 8. Rotation,
revocation, and historical public verification retain public lifecycle data;
there is deliberately no private-key export or restore operation.

This is not hostile-administrator isolation. Nilhan and Docker/host
administrators are trusted by this support row. KMS/HSM, protected reviewer
identity, multi-operator quorum, and external anchoring remain later work.
