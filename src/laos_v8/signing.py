"""Typed Ed25519 envelopes and the common protected-signer contract."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Literal, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import signature_domain
from .errors import SecurityError, ValidationError
from .models import KeyPurpose, ProtectedEnvelope, TypedEnvelope


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError as exc:
        raise ValidationError("invalid base64url envelope value", code="ENVELOPE_BASE64_INVALID") from exc


SignerAssurance = Literal[
    "STAGE_3_TEST_ONLY_NOT_PRODUCTION",
    "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
]


@dataclass(frozen=True, slots=True)
class PublicTrustRoot:
    key_id: str
    public_key_b64: str
    key_purpose: KeyPurpose
    assurance: SignerAssurance

    def verifier(self, *, trusted_issuer: str | None = None) -> EnvelopeVerifier:
        return EnvelopeVerifier(
            self.key_id,
            Ed25519PublicKey.from_public_bytes(_decode(self.public_key_b64)),
            self.key_purpose,
            trusted_issuer=trusted_issuer,
        )


class Signer(Protocol):
    """Minimum signer surface accepted by control-plane compilers."""

    key_purpose: KeyPurpose
    assurance: SignerAssurance

    @property
    def trust_root(self) -> PublicTrustRoot: ...

    def sign(
        self,
        payload: bytes,
        *,
        payload_type: str,
        key_purpose: KeyPurpose,
        issuer: str,
        audience: str,
        issued_at: str,
        expires_at: str | None,
    ) -> TypedEnvelope: ...


def sign_envelope(
    private_key: Ed25519PrivateKey,
    payload: bytes,
    *,
    key_id: str,
    payload_type: str,
    key_purpose: KeyPurpose,
    issuer: str,
    audience: str,
    issued_at: str,
    expires_at: str | None,
) -> TypedEnvelope:
    """Create the one canonical v2 envelope shared by every signer backend."""
    encoded_payload = _encode(payload)
    statement = ProtectedEnvelope(
        payload_type=payload_type,
        payload=encoded_payload,
        algorithm="Ed25519",
        key_id=key_id,
        key_purpose=key_purpose,
        issuer=issuer,
        audience=audience,
        subject_digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
        issued_at=issued_at,
        expires_at=expires_at,
    )
    signature = private_key.sign(signature_domain(statement))
    return TypedEnvelope.model_validate(
        {**statement.model_dump(mode="json"), "signature": _encode(signature)},
        strict=True,
    )


class ProtectedTestSigner:
    """In-memory Stage 3 signer; private key bytes are never exported."""

    def __init__(self, key_purpose: KeyPurpose = "capsule") -> None:
        self._key = Ed25519PrivateKey.generate()
        self.key_purpose = key_purpose
        self.assurance: SignerAssurance = "STAGE_3_TEST_ONLY_NOT_PRODUCTION"
        public = self._key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.key_id = f"key:{hashlib.sha256(public).hexdigest()[:32]}"

    @property
    def trust_root(self) -> PublicTrustRoot:
        public = self._key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return PublicTrustRoot(self.key_id, _encode(public), self.key_purpose, self.assurance)

    def sign(
        self,
        payload: bytes,
        *,
        payload_type: str,
        key_purpose: KeyPurpose,
        issuer: str,
        audience: str,
        issued_at: str,
        expires_at: str | None,
    ) -> TypedEnvelope:
        if key_purpose != self.key_purpose:
            raise SecurityError("test signer key purpose mismatch", code="SIGNER_KEY_PURPOSE_DENIED")
        return sign_envelope(
            self._key,
            payload,
            key_id=self.key_id,
            payload_type=payload_type,
            key_purpose=key_purpose,
            issuer=issuer,
            audience=audience,
            issued_at=issued_at,
            expires_at=expires_at,
        )


class EnvelopeVerifier:
    def __init__(
        self,
        key_id: str,
        public_key: Ed25519PublicKey,
        key_purpose: KeyPurpose,
        *,
        trusted_issuer: str | None = None,
    ) -> None:
        self.key_id = key_id
        self.public_key = public_key
        self.key_purpose = key_purpose
        self.trusted_issuer = trusted_issuer

    def verify(
        self,
        envelope: TypedEnvelope,
        *,
        expected_purpose: str,
        expected_payload_type: str,
        expected_issuer: str,
        expected_audience: str,
    ) -> bytes:
        if envelope.envelope_version != "2.0.0":
            raise SecurityError("legacy or unknown envelope version is denied", code="SIGNATURE_VERSION_DENIED")
        if envelope.algorithm != "Ed25519" or envelope.key_id != self.key_id:
            raise SecurityError("signature key or algorithm is not trusted", code="SIGNATURE_KEY_DENIED")
        if envelope.key_purpose != expected_purpose or expected_purpose != self.key_purpose:
            raise SecurityError("signature key purpose mismatch", code="SIGNATURE_PURPOSE_MISMATCH")
        if envelope.payload_type != expected_payload_type:
            raise SecurityError("signed payload type mismatch", code="SIGNATURE_TYPE_MISMATCH")
        payload = _decode(envelope.payload)
        observed = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if observed != envelope.subject_digest:
            raise SecurityError("signed subject digest mismatch", code="SIGNATURE_SUBJECT_MISMATCH")
        statement = ProtectedEnvelope.model_validate(
            envelope.model_dump(mode="json", exclude={"signature"}),
            strict=True,
        )
        try:
            self.public_key.verify(
                _decode(envelope.signature),
                signature_domain(statement),
            )
        except InvalidSignature as exc:
            raise SecurityError("envelope signature is invalid", code="SIGNATURE_INVALID") from exc
        if self.trusted_issuer is not None and envelope.issuer != self.trusted_issuer:
            raise SecurityError("signature key issuer mismatch", code="TRUST_ISSUER_MISMATCH")
        if envelope.issuer != expected_issuer or envelope.audience != expected_audience:
            raise SecurityError("signed issuer or audience mismatch", code="SIGNATURE_CONTEXT_MISMATCH")
        return payload
