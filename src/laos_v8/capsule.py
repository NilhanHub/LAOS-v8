"""Minimal signed, expiring, actor-bound Stage 3 Action Capsules."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from .canonical import canonical_json
from .errors import AuthorizationDenied, SecurityError, ValidationError
from .models import ActionCapsule, Role, TypedEnvelope
from .signing import EnvelopeVerifier, ProtectedTestSigner
from .state import CanonicalState

CAPSULE_MEDIA_TYPE = "application/vnd.nilhan.laos.action-capsule.v1+json"


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("capsule timestamp is invalid", code="CAPSULE_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValidationError("capsule timestamp lacks UTC offset", code="CAPSULE_TIME_INVALID")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class VerifiedCapsule:
    capsule: ActionCapsule
    envelope: TypedEnvelope
    token_hash: str


class CapsuleAuthority:
    def __init__(self, signer: ProtectedTestSigner, *, issuer: str, audience: str) -> None:
        self.signer = signer
        self.issuer = issuer
        self.audience = audience

    def issue(
        self,
        *,
        project_id: str,
        actor_id: str,
        role: Role,
        action_definition_digest: str,
        base_seal: str,
        policy_digest: str,
        profile_digest: str,
        skill_digest: str,
        state_version: int,
        attempt_sequence: int,
        issued_at: str,
        expires_at: str,
        revocation_epoch: int,
    ) -> TypedEnvelope:
        if _parse_utc(expires_at) <= _parse_utc(issued_at):
            raise ValidationError("capsule expiry must follow issue time", code="CAPSULE_TIME_INVALID")
        capsule_id = f"capsule:{secrets.token_hex(16)}"
        capsule = ActionCapsule(
            record_id=capsule_id,
            project_id=project_id,
            created_at=issued_at,
            capsule_id=capsule_id,
            issuer_id=self.issuer,
            actor_id=actor_id,
            role=role,
            audience=self.audience,
            action_definition_digest=action_definition_digest,
            base_seal=base_seal,
            policy_digest=policy_digest,
            profile_digest=profile_digest,
            skill_digest=skill_digest,
            state_version=state_version,
            attempt_sequence=attempt_sequence,
            issued_at=issued_at,
            expires_at=expires_at,
            revocation_epoch=revocation_epoch,
        )
        payload = canonical_json(capsule)
        return self.signer.sign(
            payload,
            payload_type=CAPSULE_MEDIA_TYPE,
            key_purpose="capsule",
            issuer=self.issuer,
            audience=self.audience,
            issued_at=issued_at,
            expires_at=expires_at,
        )


def verify_and_redeem(
    envelope: TypedEnvelope,
    *,
    verifier: EnvelopeVerifier,
    state: CanonicalState,
    expected_issuer: str,
    expected_audience: str,
    expected_actor: str,
    expected_project_id: str,
    expected_role: Role,
    expected_action_definition_digest: str,
    expected_base_seal: str,
    expected_policy_digest: str,
    expected_profile_digest: str,
    expected_skill_digest: str,
    expected_state_version: int,
    expected_attempt_sequence: int,
    required_revocation_epoch: int,
    now: datetime | None = None,
) -> VerifiedCapsule:
    def deny(code: str, detail: object | None = None) -> None:
        state.record_event(
            aggregate_id=None,
            actor_id=expected_actor,
            event_code="CAPSULE_AUTHORIZATION_DENIED",
            outcome="denied",
            error_code=code,
            detail=detail,
        )

    try:
        payload = verifier.verify(
            envelope,
            expected_purpose="capsule",
            expected_payload_type=CAPSULE_MEDIA_TYPE,
            expected_issuer=expected_issuer,
            expected_audience=expected_audience,
        )
    except SecurityError as exc:
        deny(exc.code)
        raise AuthorizationDenied("capsule signature context was denied", code=exc.code) from exc
    try:
        capsule = ActionCapsule.model_validate_json(payload, strict=True)
    except Exception as exc:
        deny("CAPSULE_PAYLOAD_INVALID")
        raise AuthorizationDenied("signed capsule payload is invalid", code="CAPSULE_PAYLOAD_INVALID") from exc
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if current < _parse_utc(capsule.issued_at) or current >= _parse_utc(capsule.expires_at):
        deny("CAPSULE_EXPIRED_OR_NOT_YET_VALID")
        raise AuthorizationDenied("capsule is not currently valid", code="CAPSULE_EXPIRED_OR_NOT_YET_VALID")
    bindings = {
        "issuer": capsule.issuer_id == expected_issuer,
        "actor": capsule.actor_id == expected_actor,
        "project": capsule.project_id == expected_project_id,
        "role": capsule.role == expected_role,
        "audience": capsule.audience == expected_audience,
        "action_definition": capsule.action_definition_digest == expected_action_definition_digest,
        "base_seal": capsule.base_seal == expected_base_seal,
        "policy": capsule.policy_digest == expected_policy_digest,
        "profile": capsule.profile_digest == expected_profile_digest,
        "skill": capsule.skill_digest == expected_skill_digest,
        "state_version": capsule.state_version == expected_state_version,
        "attempt_sequence": capsule.attempt_sequence == expected_attempt_sequence,
        "revocation_epoch": capsule.revocation_epoch == required_revocation_epoch,
        "envelope_issued_at": envelope.issued_at == capsule.issued_at,
        "envelope_expires_at": envelope.expires_at == capsule.expires_at,
    }
    if not all(bindings.values()):
        mismatches = [key for key, value in bindings.items() if not value]
        deny("CAPSULE_BINDING_MISMATCH", {"mismatches": mismatches})
        raise AuthorizationDenied(
            "capsule binding mismatch",
            code="CAPSULE_BINDING_MISMATCH",
            context={"mismatches": mismatches},
        )
    token_hash = hashlib.sha256(canonical_json(envelope.model_dump(mode="json"))).hexdigest()
    state.redeem_capsule(capsule.capsule_id, capsule.actor_id, capsule.attempt_sequence, token_hash)
    return VerifiedCapsule(capsule, envelope, token_hash)
