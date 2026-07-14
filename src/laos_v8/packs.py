"""Allowlisted, physically separated, signed Stage 5 pack compiler."""

from __future__ import annotations

import hashlib
import io
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from .canonical import canonical_json
from .errors import SecurityError, ValidationError
from .models import TypedEnvelope
from .parser import strict_loads
from .safe_paths import safe_extract_zip, validate_relative_path
from .signing import ProtectedTestSigner
from .trust import TrustRegistry

PACK_MEDIA_TYPE = "application/vnd.nilhan.laos.pack-manifest.v1+json"
PackKind = Literal["architect_control", "agent_execution", "capture_execution", "review_capsule"]

_ALLOWED_PREFIXES: dict[str, tuple[str, ...]] = {
    "architect_control": ("control/", "schemas/", "public/"),
    "agent_execution": ("execution/", "schemas/", "public/"),
    "capture_execution": ("capture/", "schemas/", "public/"),
    "review_capsule": ("review/", "evidence/", "schemas/", "public/"),
}
_RESERVED = {
    "manifest.json",
    "manifest.envelope.json",
    "public/capabilities.json",
    "public/trust.json",
}


class PackEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: str = Field(min_length=1, max_length=512)
    bytes: int = Field(ge=0, le=104_857_600)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    classification: Literal["public", "internal", "restricted"]


class CapabilityManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    allowed: tuple[str, ...] = Field(max_length=256)
    denied: tuple[str, ...] = Field(min_length=1, max_length=256)
    future_actions_included: Literal[False] = False
    raw_secrets_included: Literal[False] = False
    authority: Literal["CAPSULE_ONLY"] = "CAPSULE_ONLY"


class PackManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    pack_id: str = Field(pattern=r"^pack:[a-f0-9]{32}$")
    pack_kind: PackKind
    project_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9._:-]{2,127}$")
    created_at: str
    issuer: str
    audience: str
    projection_version: Literal["1.0.0"] = "1.0.0"
    entries: tuple[PackEntry, ...] = Field(min_length=1, max_length=10_000)
    capability_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    assurance: Literal["STAGE_5_BOOTSTRAP_SIGNER_NOT_PRODUCTION_CUSTODY"]


@dataclass(frozen=True, slots=True)
class PackInput:
    path: str
    payload: bytes
    classification: Literal["public", "internal", "restricted"] = "public"


@dataclass(frozen=True, slots=True)
class PackRequest:
    pack_id: str
    pack_kind: PackKind
    project_id: str
    created_at: str
    issuer: str
    audience: str
    files: tuple[PackInput, ...]
    capabilities: CapabilityManifest
    forbidden_canaries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompiledPack:
    archive: Path
    manifest: PackManifest
    envelope: TypedEnvelope
    sha256: str


class LeakScanner:
    """Detect defined canaries and credential-like material; never claims semantic completeness."""

    _PATTERNS: ClassVar[dict[str, re.Pattern[bytes]]] = {
        "secret": re.compile(rb"(?i)(api[_-]?key|password|private[_-]?key|client[_-]?secret)\s*[:=]"),
        "hidden_check": re.compile(rb"LAOS_HIDDEN_CHECK|PRIVATE_EVALUATOR_ANSWER"),
        "future_action": re.compile(rb"LAOS_FUTURE_ACTION|NEXT_ACTION_PRIVATE"),
        "architect_only": re.compile(rb"LAOS_ARCHITECT_ONLY|MASTER_FRAMEWORK_PRIVATE"),
        "sensitive_data": re.compile(rb"LAOS_SENSITIVE_DATA|BEGIN PRIVATE DATA"),
    }

    def scan(self, path: str, payload: bytes, *, canaries: tuple[str, ...], public_pack: bool) -> None:
        for canary in canaries:
            if canary.encode("utf-8") in payload:
                raise SecurityError(
                    "seeded leak canary detected",
                    code="PACK_LEAK_CANARY",
                    context={"path": path},
                )
        for category, pattern in self._PATTERNS.items():
            if pattern.search(payload) and (public_pack or category == "secret"):
                raise SecurityError(
                    "pack leak policy matched",
                    code="PACK_LEAK_DETECTED",
                    context={"path": path, "category": category},
                )


def _allowed(pack_kind: PackKind, path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES[pack_kind])


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(files.items(), key=lambda item: item[0].encode("utf-8")):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, payload)
    return stream.getvalue()


class PackCompiler:
    def __init__(self, signer: ProtectedTestSigner, scanner: LeakScanner | None = None) -> None:
        if signer.key_purpose != "pack_manifest":
            raise SecurityError("pack compiler requires a pack-manifest key", code="PACK_SIGNER_PURPOSE_DENIED")
        self.signer = signer
        self.scanner = scanner or LeakScanner()

    def compile(self, request: PackRequest, destination: Path) -> CompiledPack:
        if destination.exists():
            raise ValidationError("pack destination already exists", code="PACK_DESTINATION_EXISTS")
        public_pack = request.pack_kind != "architect_control"
        seen: set[str] = set()
        material: dict[str, bytes] = {}
        entries: list[PackEntry] = []
        for item in request.files:
            path = validate_relative_path(item.path).as_posix()
            if path in _RESERVED or not _allowed(request.pack_kind, path):
                raise SecurityError("file is outside the pack projection", code="PACK_PROJECTION_DENIED")
            key = path.casefold()
            if key in seen:
                raise SecurityError("duplicate pack path", code="PACK_PATH_COLLISION")
            seen.add(key)
            if public_pack and item.classification != "public":
                raise SecurityError("non-public data entered a public pack", code="PACK_CLASSIFICATION_DENIED")
            self.scanner.scan(path, item.payload, canaries=request.forbidden_canaries, public_pack=public_pack)
            digest = hashlib.sha256(item.payload).hexdigest()
            entries.append(
                PackEntry(path=path, bytes=len(item.payload), sha256=digest, classification=item.classification)
            )
            material[path] = item.payload
        capabilities = canonical_json(request.capabilities)
        self.scanner.scan(
            "public/capabilities.json",
            capabilities,
            canaries=request.forbidden_canaries,
            public_pack=public_pack,
        )
        material["public/capabilities.json"] = capabilities
        entries.append(
            PackEntry(
                path="public/capabilities.json",
                bytes=len(capabilities),
                sha256=hashlib.sha256(capabilities).hexdigest(),
                classification="public",
            )
        )
        trust_payload = canonical_json(
            {
                "record_version": "1.0.0",
                "key_id": self.signer.trust_root.key_id,
                "public_key_b64": self.signer.trust_root.public_key_b64,
                "purpose": "pack_manifest",
                "assurance": "PUBLIC_VERIFICATION_MATERIAL_REQUIRES_EXTERNAL_PIN",
            }
        )
        material["public/trust.json"] = trust_payload
        entries.append(
            PackEntry(
                path="public/trust.json",
                bytes=len(trust_payload),
                sha256=hashlib.sha256(trust_payload).hexdigest(),
                classification="public",
            )
        )
        manifest = PackManifest(
            pack_id=request.pack_id,
            pack_kind=request.pack_kind,
            project_id=request.project_id,
            created_at=request.created_at,
            issuer=request.issuer,
            audience=request.audience,
            entries=tuple(sorted(entries, key=lambda item: item.path.encode("utf-8"))),
            capability_digest=f"sha256:{hashlib.sha256(capabilities).hexdigest()}",
            assurance="STAGE_5_BOOTSTRAP_SIGNER_NOT_PRODUCTION_CUSTODY",
        )
        manifest_bytes = canonical_json(manifest)
        envelope = self.signer.sign(
            manifest_bytes,
            payload_type=PACK_MEDIA_TYPE,
            key_purpose="pack_manifest",
            issuer=request.issuer,
            audience=request.audience,
            issued_at=request.created_at,
            expires_at=None,
        )
        material["manifest.json"] = manifest_bytes
        material["manifest.envelope.json"] = canonical_json(envelope)
        archive_bytes = _zip_bytes(material)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive_bytes)
        return CompiledPack(destination, manifest, envelope, f"sha256:{hashlib.sha256(archive_bytes).hexdigest()}")


def verify_pack(
    archive: Path,
    *,
    trust: TrustRegistry,
    expected_kind: PackKind,
    expected_project: str,
    expected_issuer: str,
    expected_audience: str,
    now: datetime | None = None,
) -> PackManifest:
    with tempfile.TemporaryDirectory(prefix="laos-pack-verify-") as temporary:
        root = Path(temporary)
        extracted = safe_extract_zip(archive, root)
        required = {
            "manifest.json",
            "manifest.envelope.json",
            "public/capabilities.json",
            "public/trust.json",
        }
        if not required.issubset(extracted):
            raise SecurityError("pack metadata is incomplete", code="PACK_METADATA_MISSING")
        manifest_bytes = (root / "manifest.json").read_bytes()
        envelope_bytes = (root / "manifest.envelope.json").read_bytes()
        envelope = TypedEnvelope.model_validate(strict_loads(envelope_bytes), strict=True)
        if canonical_json(envelope) != envelope_bytes:
            raise SecurityError("pack envelope is not canonical", code="PACK_ENVELOPE_NONCANONICAL")
        verifier = trust.verifier_for(envelope, purpose="pack_manifest", now=now or datetime.now(UTC))
        verified = verifier.verify(
            envelope,
            expected_purpose="pack_manifest",
            expected_payload_type=PACK_MEDIA_TYPE,
            expected_issuer=expected_issuer,
            expected_audience=expected_audience,
        )
        if verified != manifest_bytes:
            raise SecurityError("signed manifest payload differs", code="PACK_MANIFEST_SUBSTITUTED")
        raw_manifest = strict_loads(manifest_bytes)
        if canonical_json(raw_manifest) != manifest_bytes:
            raise SecurityError("pack manifest is not canonical", code="PACK_MANIFEST_NONCANONICAL")
        manifest = PackManifest.model_validate_json(manifest_bytes, strict=True)
        if manifest.pack_kind != expected_kind or manifest.project_id != expected_project:
            raise SecurityError("pack identity binding mismatch", code="PACK_BINDING_MISMATCH")
        if (
            manifest.issuer != envelope.issuer
            or manifest.audience != envelope.audience
            or manifest.created_at != envelope.issued_at
        ):
            raise SecurityError("pack manifest context differs from its envelope", code="PACK_CONTEXT_BINDING_MISMATCH")
        expected_paths = {entry.path for entry in manifest.entries} | {"manifest.json", "manifest.envelope.json"}
        if set(extracted) != expected_paths:
            raise SecurityError("pack contains unmanifested content", code="PACK_UNMANIFESTED_CONTENT")
        for entry in manifest.entries:
            target = root / entry.path
            payload = target.read_bytes()
            if len(payload) != entry.bytes or hashlib.sha256(payload).hexdigest() != entry.sha256:
                raise SecurityError("pack content digest mismatch", code="PACK_CONTENT_TAMPERED")
        capability_payload = (root / "public/capabilities.json").read_bytes()
        if f"sha256:{hashlib.sha256(capability_payload).hexdigest()}" != manifest.capability_digest:
            raise SecurityError("capability manifest digest mismatch", code="PACK_CAPABILITY_TAMPERED")
        raw_capabilities = strict_loads(capability_payload)
        if canonical_json(raw_capabilities) != capability_payload:
            raise SecurityError("capability manifest is not canonical", code="PACK_CAPABILITY_NONCANONICAL")
        CapabilityManifest.model_validate_json(capability_payload, strict=True)
        return manifest
