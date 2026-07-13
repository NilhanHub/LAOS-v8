"""Typed Ed25519 envelopes using an explicitly test-only protected signer."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import signature_domain
from .errors import SecurityError, ValidationError
from .models import TypedEnvelope


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError as exc:
        raise ValidationError("invalid base64url envelope value", code="ENVELOPE_BASE64_INVALID") from exc


@dataclass(frozen=True, slots=True)
class TestTrustRoot:
    key_id: str
    public_key_b64: str
    key_purpose: Literal["capsule", "event_anchor", "release"]
    assurance: str = "STAGE_3_TEST_ONLY_NOT_PRODUCTION"

    def verifier(self) -> EnvelopeVerifier:
        return EnvelopeVerifier(
            self.key_id,
            Ed25519PublicKey.from_public_bytes(_decode(self.public_key_b64)),
            self.key_purpose,
        )


class ProtectedTestSigner:
    """In-memory Stage 3 signer; private key bytes are never exported."""

    def __init__(self, key_purpose: Literal["capsule", "event_anchor", "release"] = "capsule") -> None:
        self._key = Ed25519PrivateKey.generate()
        self.key_purpose = key_purpose
        public = self._key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.key_id = f"key:{hashlib.sha256(public).hexdigest()[:32]}"

    @property
    def trust_root(self) -> TestTrustRoot:
        public = self._key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return TestTrustRoot(self.key_id, _encode(public), self.key_purpose)

    def sign(
        self,
        payload: bytes,
        *,
        payload_type: str,
        key_purpose: Literal["capsule", "event_anchor", "release"],
        issuer: str,
        audience: str,
        issued_at: str,
        expires_at: str | None,
    ) -> TypedEnvelope:
        if key_purpose != self.key_purpose:
            raise SecurityError("test signer key purpose mismatch", code="SIGNER_KEY_PURPOSE_DENIED")
        subject = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        signature = self._key.sign(signature_domain(key_purpose, payload_type, payload))
        return TypedEnvelope(
            payload_type=payload_type,
            payload=_encode(payload),
            algorithm="Ed25519",
            key_id=self.key_id,
            key_purpose=key_purpose,
            issuer=issuer,
            audience=audience,
            subject_digest=subject,
            issued_at=issued_at,
            expires_at=expires_at,
            signature=_encode(signature),
        )


class EnvelopeVerifier:
    def __init__(
        self,
        key_id: str,
        public_key: Ed25519PublicKey,
        key_purpose: Literal["capsule", "event_anchor", "release"],
    ) -> None:
        self.key_id = key_id
        self.public_key = public_key
        self.key_purpose = key_purpose

    def verify(
        self,
        envelope: TypedEnvelope,
        *,
        expected_purpose: str,
        expected_payload_type: str,
        expected_issuer: str,
        expected_audience: str,
    ) -> bytes:
        if envelope.algorithm != "Ed25519" or envelope.key_id != self.key_id:
            raise SecurityError("signature key or algorithm is not trusted", code="SIGNATURE_KEY_DENIED")
        if envelope.key_purpose != expected_purpose or expected_purpose != self.key_purpose:
            raise SecurityError("signature key purpose mismatch", code="SIGNATURE_PURPOSE_MISMATCH")
        if envelope.payload_type != expected_payload_type:
            raise SecurityError("signed payload type mismatch", code="SIGNATURE_TYPE_MISMATCH")
        if envelope.issuer != expected_issuer or envelope.audience != expected_audience:
            raise SecurityError("signed issuer or audience mismatch", code="SIGNATURE_CONTEXT_MISMATCH")
        payload = _decode(envelope.payload)
        observed = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if observed != envelope.subject_digest:
            raise SecurityError("signed subject digest mismatch", code="SIGNATURE_SUBJECT_MISMATCH")
        try:
            self.public_key.verify(
                _decode(envelope.signature),
                signature_domain(envelope.key_purpose, envelope.payload_type, payload),
            )
        except InvalidSignature as exc:
            raise SecurityError("envelope signature is invalid", code="SIGNATURE_INVALID") from exc
        return payload
