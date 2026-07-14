"""Versioned public trust metadata with purpose separation and anti-rollback."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal

from .errors import SecurityError, ValidationError
from .models import KeyPurpose, TypedEnvelope
from .signing import EnvelopeVerifier, PublicTrustRoot


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("trust timestamp is invalid", code="TRUST_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValidationError("trust timestamp lacks an offset", code="TRUST_TIME_INVALID")
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class PublicTrustRecord:
    trust_root: PublicTrustRoot
    issuer: str
    purpose: KeyPurpose
    valid_from: str
    valid_until: str
    status: Literal["active", "reserved", "revoked", "retired_historical"] = "active"
    revoked_at: str | None = None
    generation: int = 1
    alpha_test_root: bool = False

    def __post_init__(self) -> None:
        if self.trust_root.key_purpose != self.purpose:
            raise ValidationError("trust-root purpose mismatch", code="TRUST_PURPOSE_MISMATCH")
        if _utc(self.valid_until) <= _utc(self.valid_from):
            raise ValidationError("trust validity window is invalid", code="TRUST_TIME_INVALID")


class TrustRegistry:
    """Public keys only. Signing keys remain outside this registry and every pack."""

    def __init__(self, *, version: int = 1) -> None:
        if version < 1:
            raise ValidationError("trust version must be positive", code="TRUST_VERSION_INVALID")
        self.version = version
        self._records: dict[str, PublicTrustRecord] = {}

    def add(self, record: PublicTrustRecord) -> None:
        if record.trust_root.key_id in self._records:
            raise SecurityError("duplicate trust key ID", code="TRUST_DUPLICATE_KEY")
        self._records[record.trust_root.key_id] = record

    def replace_snapshot(self, *, version: int, records: tuple[PublicTrustRecord, ...]) -> None:
        if version <= self.version:
            raise SecurityError("trust metadata rollback denied", code="TRUST_ROLLBACK_DENIED")
        keys = [record.trust_root.key_id for record in records]
        if len(keys) != len(set(keys)):
            raise SecurityError("duplicate trust key ID", code="TRUST_DUPLICATE_KEY")
        self.version = version
        self._records = {record.trust_root.key_id: record for record in records}

    def revoke(self, key_id: str, *, revoked_at: str) -> None:
        record = self._records.get(key_id)
        if record is None:
            raise SecurityError("unknown trust key", code="TRUST_KEY_UNKNOWN")
        if _utc(revoked_at) < _utc(record.valid_from):
            raise ValidationError("revocation predates key validity", code="TRUST_TIME_INVALID")
        self._records[key_id] = replace(record, status="revoked", revoked_at=revoked_at)
        self.version += 1

    def retire_alpha_roots(self, *, retired_at: str) -> int:
        changed = 0
        for key_id, record in tuple(self._records.items()):
            if record.alpha_test_root and record.status == "active":
                self._records[key_id] = replace(
                    record,
                    status="retired_historical",
                    revoked_at=retired_at,
                )
                changed += 1
        if changed:
            self.version += 1
        return changed

    def verifier_for(
        self,
        envelope: TypedEnvelope,
        *,
        purpose: KeyPurpose,
        now: datetime,
        historical: bool = False,
    ) -> EnvelopeVerifier:
        record = self._records.get(envelope.key_id)
        if record is None:
            raise SecurityError("signature key is unknown", code="TRUST_KEY_UNKNOWN")
        if record.purpose != purpose or envelope.key_purpose != purpose:
            raise SecurityError("signature key purpose mismatch", code="TRUST_PURPOSE_MISMATCH")
        current = now.astimezone(UTC)
        if current < _utc(record.valid_from) or current >= _utc(record.valid_until):
            raise SecurityError("trust metadata is not currently valid", code="TRUST_EXPIRED")
        if record.status != "active" and not historical:
            raise SecurityError("trust key cannot authorize current work", code="TRUST_KEY_REVOKED")
        if historical and record.revoked_at is not None and _utc(envelope.issued_at) >= _utc(record.revoked_at):
            raise SecurityError("signature postdates key revocation", code="TRUST_KEY_REVOKED")
        return record.trust_root.verifier(trusted_issuer=record.issuer)

    def public_snapshot(self) -> dict[str, object]:
        return {
            "record_version": "1.0.0",
            "trust_version": self.version,
            "keys": [
                {
                    "key_id": record.trust_root.key_id,
                    "public_key_b64": record.trust_root.public_key_b64,
                    "purpose": record.purpose,
                    "issuer": record.issuer,
                    "valid_from": record.valid_from,
                    "valid_until": record.valid_until,
                    "status": record.status,
                    "revoked_at": record.revoked_at,
                    "generation": record.generation,
                    "alpha_test_root": record.alpha_test_root,
                }
                for record in sorted(self._records.values(), key=lambda item: item.trust_root.key_id)
            ],
        }
