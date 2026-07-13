from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from laos_v8.capsule import CapsuleAuthority, verify_and_redeem
from laos_v8.errors import AuthorizationDenied, SecurityError
from laos_v8.models import Role
from laos_v8.signing import ProtectedTestSigner
from laos_v8.state import CanonicalState


def issue(authority: CapsuleAuthority, digest: str, now_values: dict[str, str]):
    return authority.issue(
        project_id="project:stage3",
        actor_id="actor:builder",
        role=Role.BUILDER,
        action_definition_digest=digest,
        base_seal=digest,
        policy_digest=digest,
        profile_digest=digest,
        skill_digest=digest,
        state_version=0,
        attempt_sequence=1,
        issued_at=now_values["past"],
        expires_at=now_values["future"],
        revocation_epoch=0,
    )


def test_test_signer_cannot_cross_key_purpose() -> None:
    signer = ProtectedTestSigner(key_purpose="capsule")
    with pytest.raises(SecurityError) as captured:
        signer.sign(
            b'{"value":1}',
            payload_type="test",
            key_purpose="release",
            issuer="actor:architect",
            audience="broker:stage3",
            issued_at="2026-07-13T00:00:00Z",
            expires_at=None,
        )
    assert captured.value.code == "SIGNER_KEY_PURPOSE_DENIED"


def test_signed_capsule_is_bound_expiring_and_single_use(
    tmp_path: Path, digest: str, now_values: dict[str, str]
) -> None:
    signer = ProtectedTestSigner()
    authority = CapsuleAuthority(signer, issuer="actor:architect", audience="broker:stage3")
    envelope = issue(authority, digest, now_values)
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        verified = verify_and_redeem(
            envelope,
            verifier=signer.trust_root.verifier(),
            state=state,
            expected_issuer="actor:architect",
            expected_audience="broker:stage3",
            expected_actor="actor:builder",
            expected_project_id="project:stage3",
            expected_role=Role.BUILDER,
            expected_action_definition_digest=digest,
            expected_base_seal=digest,
            expected_policy_digest=digest,
            expected_profile_digest=digest,
            expected_skill_digest=digest,
            expected_state_version=0,
            expected_attempt_sequence=1,
            required_revocation_epoch=0,
            now=datetime(2026, 7, 13, tzinfo=UTC),
        )
        assert verified.capsule.role is Role.BUILDER
        with pytest.raises(AuthorizationDenied) as captured:
            verify_and_redeem(
                envelope,
                verifier=signer.trust_root.verifier(),
                state=state,
                expected_issuer="actor:architect",
                expected_audience="broker:stage3",
                expected_actor="actor:builder",
                expected_project_id="project:stage3",
                expected_role=Role.BUILDER,
                expected_action_definition_digest=digest,
                expected_base_seal=digest,
                expected_policy_digest=digest,
                expected_profile_digest=digest,
                expected_skill_digest=digest,
                expected_state_version=0,
                expected_attempt_sequence=1,
                required_revocation_epoch=0,
                now=datetime(2026, 7, 13, tzinfo=UTC),
            )
        assert captured.value.code == "CAPSULE_REPLAY_DENIED"
        denied = state.connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_code = 'CAPSULE_REPLAY_DENIED'"
        ).fetchone()[0]
        assert denied == 1


def test_capsule_tamper_wrong_context_and_expiry_fail(tmp_path: Path, digest: str, now_values: dict[str, str]) -> None:
    signer = ProtectedTestSigner()
    authority = CapsuleAuthority(signer, issuer="actor:architect", audience="broker:stage3")
    envelope = issue(authority, digest, now_values)
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        with pytest.raises(AuthorizationDenied):
            verify_and_redeem(
                envelope,
                verifier=signer.trust_root.verifier(),
                state=state,
                expected_issuer="actor:architect",
                expected_audience="broker:wrong",
                expected_actor="actor:builder",
                expected_project_id="project:stage3",
                expected_role=Role.BUILDER,
                expected_action_definition_digest=digest,
                expected_base_seal=digest,
                expected_policy_digest=digest,
                expected_profile_digest=digest,
                expected_skill_digest=digest,
                expected_state_version=0,
                expected_attempt_sequence=1,
                required_revocation_epoch=0,
            )
        with pytest.raises(AuthorizationDenied):
            verify_and_redeem(
                envelope,
                verifier=signer.trust_root.verifier(),
                state=state,
                expected_issuer="actor:architect",
                expected_audience="broker:stage3",
                expected_actor="actor:builder",
                expected_project_id="project:stage3",
                expected_role=Role.BUILDER,
                expected_action_definition_digest=digest,
                expected_base_seal=digest,
                expected_policy_digest=digest,
                expected_profile_digest=digest,
                expected_skill_digest=digest,
                expected_state_version=0,
                expected_attempt_sequence=1,
                required_revocation_epoch=0,
                now=datetime(2026, 7, 15, tzinfo=UTC),
            )
        tampered = envelope.model_copy(update={"signature": "A" * 86})
        with pytest.raises(SecurityError):
            signer.trust_root.verifier().verify(
                tampered,
                expected_purpose="capsule",
                expected_payload_type=envelope.payload_type,
                expected_issuer="actor:architect",
                expected_audience="broker:stage3",
            )
