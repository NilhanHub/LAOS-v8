"""Signed protected-check bundles stored outside builder workspaces."""

from __future__ import annotations

import hashlib
import os
import stat
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json, content_digest
from .errors import SecurityError, ValidationError
from .models import TypedEnvelope
from .safe_paths import SafeRoot
from .signing import PublicTrustRoot, Signer

MEDIA_TYPE = "application/vnd.nilhan.laos.event-anchor.protected-check-bundle.v1+json"


class ProtectedCheckEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: str = Field(pattern=r"^[A-Za-z0-9._/-]+$")
    bytes: int = Field(ge=1, le=10_485_760)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ProtectedCheckBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    bundle_id: str = Field(pattern=r"^check-bundle:[a-f0-9]{32}$")
    bundle_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    entries: tuple[ProtectedCheckEntry, ...] = Field(min_length=1, max_length=256)
    argv: tuple[str, ...] = Field(min_length=1, max_length=64)
    issuer: str
    audience: str
    issued_at: str
    envelope: TypedEnvelope

    @model_validator(mode="after")
    def paths_are_unique(self) -> ProtectedCheckBundle:
        paths = [item.path.casefold() for item in self.entries]
        if len(paths) != len(set(paths)):
            raise ValueError("PROTECTED_CHECK_PATH_COLLISION")
        return self


def _unsigned(bundle_id: str, entries: tuple[ProtectedCheckEntry, ...], argv: tuple[str, ...]) -> dict[str, object]:
    return {
        "record_version": "1.0.0",
        "bundle_id": bundle_id,
        "entries": [item.model_dump() for item in entries],
        "argv": list(argv),
    }


class ProtectedCheckStore:
    def __init__(self, root: Path) -> None:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root = SafeRoot(root)

    def provision(
        self,
        files: tuple[Path, ...],
        *,
        argv: tuple[str, ...],
        signer: Signer,
        issuer: str,
        audience: str,
        issued_at: str,
    ) -> ProtectedCheckBundle:
        if signer.key_purpose != "event_anchor" or not argv:
            raise ValidationError("protected-check signer or command is invalid", code="PROTECTED_CHECK_INPUT_INVALID")
        bundle_id = f"check-bundle:{uuid.uuid4().hex}"
        directory = self.root.for_write(bundle_id.removeprefix("check-bundle:"))
        directory.mkdir(mode=0o700)
        checks = directory / "checks"
        checks.mkdir(mode=0o700)
        entries: list[ProtectedCheckEntry] = []
        seen: set[str] = set()
        for source in files:
            path = source.resolve(strict=True)
            info = path.lstat()
            name = path.name
            if path.is_symlink() or not stat.S_ISREG(info.st_mode) or name.casefold() in seen:
                raise SecurityError("protected-check input is unsafe", code="PROTECTED_CHECK_INPUT_UNSAFE")
            seen.add(name.casefold())
            payload = path.read_bytes()
            if not payload or len(payload) > 10_485_760:
                raise ValidationError("protected-check size is invalid", code="PROTECTED_CHECK_SIZE_INVALID")
            target = checks / name
            target.write_bytes(payload)
            os.chmod(target, stat.S_IREAD)
            entries.append(
                ProtectedCheckEntry(path=name, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            )
        ordered = tuple(sorted(entries, key=lambda item: item.path.encode("utf-8")))
        unsigned = _unsigned(bundle_id, ordered, argv)
        bundle_digest = content_digest(unsigned)
        envelope = signer.sign(
            canonical_json(unsigned),
            payload_type=MEDIA_TYPE,
            key_purpose="event_anchor",
            issuer=issuer,
            audience=audience,
            issued_at=issued_at,
            expires_at=None,
        )
        bundle = ProtectedCheckBundle(
            bundle_id=bundle_id,
            bundle_digest=bundle_digest,
            entries=ordered,
            argv=argv,
            issuer=issuer,
            audience=audience,
            issued_at=issued_at,
            envelope=envelope,
        )
        (directory / "bundle.json").write_bytes(canonical_json(bundle))
        os.chmod(directory / "bundle.json", stat.S_IREAD)
        return bundle

    def verify(
        self,
        bundle_id: str,
        *,
        trust: PublicTrustRoot,
        expected_issuer: str,
        expected_audience: str,
    ) -> ProtectedCheckBundle:
        relative = bundle_id.removeprefix("check-bundle:")
        bundle_payload = self.root.read_bytes(f"{relative}/bundle.json", max_bytes=2_000_000)
        bundle = ProtectedCheckBundle.model_validate_json(bundle_payload, strict=True)
        unsigned = _unsigned(bundle.bundle_id, bundle.entries, bundle.argv)
        if content_digest(unsigned) != bundle.bundle_digest:
            raise SecurityError("protected-check bundle digest changed", code="PROTECTED_CHECK_TAMPERED")
        payload = trust.verifier(trusted_issuer=expected_issuer).verify(
            bundle.envelope,
            expected_purpose="event_anchor",
            expected_payload_type=MEDIA_TYPE,
            expected_issuer=expected_issuer,
            expected_audience=expected_audience,
        )
        if payload != canonical_json(unsigned):
            raise SecurityError("protected-check signed payload changed", code="PROTECTED_CHECK_TAMPERED")
        for entry in bundle.entries:
            payload = self.root.read_bytes(f"{relative}/checks/{entry.path}", max_bytes=10_485_760)
            if len(payload) != entry.bytes or hashlib.sha256(payload).hexdigest() != entry.sha256:
                raise SecurityError("protected-check file digest changed", code="PROTECTED_CHECK_TAMPERED")
        return bundle
