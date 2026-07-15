"""Versioned models and Docker client for protected Stage 6 evidence custody."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json, content_digest
from .errors import SecurityError, ValidationError
from .models import TypedEnvelope
from .sandbox import DockerSandbox
from .signing import PublicTrustRoot, Signer

if TYPE_CHECKING:
    from .protected_review import ProtectedReviewRecord

DEFAULT_CUSTODIAN_IMAGE = "laos-v8-evidence-custodian:stage6"
DEFAULT_KEY_VOLUME = "laos-v8-stage6-custody-keys-v1"
DEFAULT_DATA_VOLUME = "laos-v8-stage6-custody-data-v1"
Classification = Literal["public", "internal", "restricted", "personal", "secret"]


class EvidenceLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class RetentionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    classification: Classification
    raw: bool
    retention_days: int | None = Field(default=None, ge=1, le=30)
    disposition: Literal["project_lifetime", "delete_after_retention"]

    @classmethod
    def for_evidence(cls, classification: Classification, *, raw: bool) -> RetentionPolicy:
        sensitive = raw or classification in {"restricted", "personal", "secret"}
        return cls(
            classification=classification,
            raw=raw,
            retention_days=30 if sensitive else None,
            disposition="delete_after_retention" if sensitive else "project_lifetime",
        )


class CustodyStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, arbitrary_types_allowed=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    payload: bytes = Field(min_length=1, max_length=2_000_000)
    criterion_id: str = Field(pattern=r"^criterion:[A-Za-z0-9._:-]+$")
    classification: Classification
    collector: str = Field(min_length=1, max_length=256)
    collector_version: str = Field(min_length=1, max_length=64)
    source_seal: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    result_seal: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    policy_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    redaction_method: str = Field(min_length=1, max_length=128)
    evidence_level: EvidenceLevel
    created_at: datetime
    raw: bool = False

    @model_validator(mode="after")
    def timestamp_is_aware(self) -> CustodyStoreRequest:
        if self.created_at.tzinfo is None:
            raise ValueError("CUSTODY_TIME_OFFSET_REQUIRED")
        return self


class CustodiedEvidenceObject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    object_id: str = Field(pattern=r"^object:[a-f0-9]{64}$")
    plaintext_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    ciphertext_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    bytes: int = Field(ge=1, le=2_000_000)
    criterion_id: str
    classification: Classification
    collector: str
    collector_version: str
    source_seal: str
    result_seal: str
    policy_digest: str
    redaction_method: str
    evidence_level: EvidenceLevel
    created_at: str
    expires_at: str | None
    custody_assurance: Literal["STAGE_6_DOCKER_ENCRYPTED_SINGLE_OPERATOR"] = (
        "STAGE_6_DOCKER_ENCRYPTED_SINGLE_OPERATOR"
    )


class LegalHold(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    hold_id: str = Field(pattern=r"^hold:[a-f0-9]{32}$")
    object_id: str = Field(pattern=r"^object:[a-f0-9]{64}$")
    authorization_digest: str = Field(pattern=r"^review:sha256:[a-f0-9]{64}$")
    placed_at: str
    released_at: str | None = None
    release_authorization_digest: str | None = Field(default=None, pattern=r"^review:sha256:[a-f0-9]{64}$")


class PurgeTombstone(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    object_id: str = Field(pattern=r"^object:[a-f0-9]{64}$")
    plaintext_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    reason_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    purged_at: str


class SignedEvidenceIndex(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    index_id: str = Field(pattern=r"^index:[a-f0-9]{64}$")
    object_ids: tuple[str, ...]
    source_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    event_anchor_envelope_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    envelope: TypedEnvelope


class EvidenceCustodian(Protocol):
    def capture(self, request: CustodyStoreRequest) -> CustodiedEvidenceObject: ...

    def fetch(self, object_id: str) -> bytes: ...

    def purge(self, object_id: str, *, reason_digest: str) -> PurgeTombstone: ...


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class DockerEvidenceCustodian:
    """Argument-safe client; production calls always use the isolated container."""

    def __init__(
        self,
        root: Path,
        *,
        image: str = DEFAULT_CUSTODIAN_IMAGE,
        key_volume: str = DEFAULT_KEY_VOLUME,
        data_volume: str = DEFAULT_DATA_VOLUME,
        docker: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.root = root.resolve(strict=True)
        self.image = image
        self.key_volume = key_volume
        self.data_volume = data_volume
        self.docker = docker if docker is not None else (shutil.which("docker") or "")
        self.timeout_seconds = timeout_seconds
        for value in (key_volume, data_volume):
            allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            if not value or any(character not in allowed for character in value):
                raise ValidationError("custodian volume name is invalid", code="CUSTODY_VOLUME_NAME_INVALID")

    def image_id(self) -> str:
        completed = subprocess.run(  # noqa: S603 - structured trusted Docker argv
            [self.docker, "image", "inspect", "--format", "{{.Id}}", self.image],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        value = completed.stdout.strip()
        if completed.returncode or not value.startswith("sha256:"):
            raise SecurityError("evidence custodian image is unavailable", code="CUSTODY_IMAGE_UNAVAILABLE")
        return value

    @classmethod
    def build_image(cls, root: Path, *, image: str = DEFAULT_CUSTODIAN_IMAGE) -> str:
        docker = shutil.which("docker") or ""
        if not docker:
            raise SecurityError("Docker CLI is unavailable", code="CUSTODY_DOCKER_UNAVAILABLE")
        DockerSandbox(docker).ensure_available()
        completed = subprocess.run(  # noqa: S603 - structured trusted Docker argv
            [
                docker, "build", "--pull=false", "--tag", image, "--file",
                str(root / "custodian" / "Dockerfile"), str(root),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=600,
        )
        if completed.returncode:
            raise SecurityError("evidence custodian image build failed", code="CUSTODY_IMAGE_BUILD_FAILED")
        return cls(root, image=image, docker=docker).image_id()

    def build_command(
        self,
        operation: str,
        *,
        mutable_data: bool,
        mutable_keys: bool,
        root_user: bool = False,
        extra: tuple[str, ...] = (),
    ) -> list[str]:
        key_mount = f"type=volume,src={self.key_volume},dst=/keys" + ("" if mutable_keys else ",readonly")
        data_mount = f"type=volume,src={self.data_volume},dst=/custody" + ("" if mutable_data else ",readonly")
        capabilities = ["--cap-drop", "ALL"]
        if root_user:
            capabilities.extend(("--cap-add", "CHOWN"))
        return [
            self.docker,
            "run",
            "--rm",
            "--interactive",
            "--network",
            "none",
            "--read-only",
            *capabilities,
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "32",
            "--memory",
            "256m",
            "--cpus",
            "0.5",
            "--user",
            "0:0" if root_user else "65532:65532",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=16m",  # noqa: S108 - isolated container tmpfs
            "--mount",
            key_mount,
            "--mount",
            data_mount,
            self.image,
            operation,
            *extra,
        ]

    def _run(
        self,
        operation: str,
        *,
        stdin: bytes = b"",
        mutable_data: bool = False,
        mutable_keys: bool = False,
        root_user: bool = False,
        extra: tuple[str, ...] = (),
    ) -> bytes:
        if not self.docker:
            raise SecurityError("Docker CLI is unavailable", code="CUSTODY_DOCKER_UNAVAILABLE")
        DockerSandbox(self.docker).ensure_available()
        command = self.build_command(
            operation,
            mutable_data=mutable_data,
            mutable_keys=mutable_keys,
            root_user=root_user,
            extra=extra,
        )
        command[command.index(self.image)] = self.image_id()
        completed = subprocess.run(  # noqa: S603 - structured Docker argv; no shell
            command,
            input=stdin,
            capture_output=True,
            check=False,
            timeout=self.timeout_seconds,
        )
        if completed.returncode:
            code = "CUSTODY_INVOCATION_FAILED"
            try:
                code = str(json.loads(completed.stderr)["error"]["code"])
            except (KeyError, TypeError, ValueError, UnicodeDecodeError):
                pass
            raise SecurityError("evidence custodian denied the request", code=code)
        return completed.stdout.strip()

    def bootstrap(self) -> dict[str, object]:
        for volume in (self.key_volume, self.data_volume):
            subprocess.run([self.docker, "volume", "create", volume], check=True, capture_output=True, timeout=30)  # noqa: S603
        self._run("prepare-volumes", mutable_data=True, mutable_keys=True, root_user=True)
        value: object = json.loads(self._run("bootstrap", mutable_data=True, mutable_keys=True))
        if not isinstance(value, dict):
            raise SecurityError("custodian bootstrap response is invalid", code="CUSTODY_RESPONSE_INVALID")
        return {str(key): item for key, item in value.items()}

    def capture(self, request: CustodyStoreRequest) -> CustodiedEvidenceObject:
        wire = request.model_dump(mode="json", exclude={"payload"})
        wire["created_at"] = _utc(request.created_at)
        wire["payload_b64"] = base64.urlsafe_b64encode(request.payload).rstrip(b"=").decode("ascii")
        return CustodiedEvidenceObject.model_validate_json(
            self._run("store", stdin=canonical_json(wire), mutable_data=True), strict=True
        )

    def doctor(self) -> dict[str, object]:
        value: object = json.loads(self._run("doctor"))
        if not isinstance(value, dict):
            raise SecurityError("custodian doctor response is invalid", code="CUSTODY_RESPONSE_INVALID")
        return {str(key): item for key, item in value.items()}

    def fetch(self, object_id: str) -> bytes:
        value: object = json.loads(
            self._run("fetch", mutable_data=True, extra=("--object-id", object_id))
        )
        if not isinstance(value, dict) or not isinstance(value.get("payload_b64"), str):
            raise SecurityError("custodian fetch response is invalid", code="CUSTODY_RESPONSE_INVALID")
        encoded = value["payload_b64"]
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))

    def place_legal_hold(self, object_id: str, review: ProtectedReviewRecord) -> LegalHold:
        authorization = "review:" + content_digest(review)
        return LegalHold.model_validate_json(
            self._run(
                "hold",
                mutable_data=True,
                extra=("--object-id", object_id, "--authorization-digest", authorization),
            ),
            strict=True,
        )

    def release_legal_hold(self, hold_id: str, review: ProtectedReviewRecord) -> LegalHold:
        authorization = "review:" + content_digest(review)
        return LegalHold.model_validate_json(
            self._run(
                "release-hold",
                mutable_data=True,
                extra=("--hold-id", hold_id, "--authorization-digest", authorization),
            ),
            strict=True,
        )

    def purge(self, object_id: str, *, reason_digest: str) -> PurgeTombstone:
        return PurgeTombstone.model_validate_json(
            self._run(
                "purge",
                mutable_data=True,
                extra=("--object-id", object_id, "--reason-digest", reason_digest),
            ),
            strict=True,
        )

    def reconcile_purges(self) -> dict[str, int]:
        value: object = json.loads(self._run("reconcile", mutable_data=True))
        if not isinstance(value, dict) or any(not isinstance(item, int) for item in value.values()):
            raise SecurityError("custodian reconciliation response is invalid", code="CUSTODY_RESPONSE_INVALID")
        return {str(key): int(item) for key, item in value.items()}


def sign_evidence_index(
    objects: tuple[CustodiedEvidenceObject, ...],
    *,
    source_commit: str,
    signer: Signer,
    issuer: str,
    audience: str,
    issued_at: str,
) -> SignedEvidenceIndex:
    if signer.key_purpose != "event_anchor" or not objects:
        raise ValidationError("evidence index signing input is invalid", code="EVIDENCE_INDEX_INPUT_INVALID")
    object_ids = tuple(sorted({item.object_id for item in objects}))
    if len(object_ids) != len(objects):
        raise ValidationError("evidence index contains duplicate objects", code="EVIDENCE_INDEX_DUPLICATE")
    unsigned = {"record_version": "1.0.0", "object_ids": list(object_ids), "source_commit": source_commit}
    index_id = "index:" + content_digest(unsigned).removeprefix("sha256:")
    payload = canonical_json({**unsigned, "index_id": index_id})
    envelope = signer.sign(
        payload,
        payload_type="application/vnd.nilhan.laos.event-anchor.evidence-index.v1+json",
        key_purpose="event_anchor",
        issuer=issuer,
        audience=audience,
        issued_at=issued_at,
        expires_at=None,
    )
    return SignedEvidenceIndex(
        index_id=index_id,
        object_ids=object_ids,
        source_commit=source_commit,
        event_anchor_envelope_digest=content_digest(envelope),
        envelope=envelope,
    )


def verify_evidence_index(
    index: SignedEvidenceIndex,
    *,
    trust: PublicTrustRoot,
    expected_issuer: str,
    expected_audience: str,
) -> None:
    unsigned = {
        "record_version": "1.0.0",
        "object_ids": list(index.object_ids),
        "source_commit": index.source_commit,
    }
    expected_id = "index:" + content_digest(unsigned).removeprefix("sha256:")
    if expected_id != index.index_id or content_digest(index.envelope) != index.event_anchor_envelope_digest:
        raise SecurityError("evidence index digest changed", code="EVIDENCE_INDEX_TAMPERED")
    expected_payload = canonical_json({**unsigned, "index_id": expected_id})
    observed = trust.verifier(trusted_issuer=expected_issuer).verify(
        index.envelope,
        expected_purpose="event_anchor",
        expected_payload_type="application/vnd.nilhan.laos.event-anchor.evidence-index.v1+json",
        expected_issuer=expected_issuer,
        expected_audience=expected_audience,
    )
    if observed != expected_payload:
        raise SecurityError("evidence index signed payload changed", code="EVIDENCE_INDEX_TAMPERED")
