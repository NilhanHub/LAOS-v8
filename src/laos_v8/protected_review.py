"""Passphrase-backed Nilhan review challenges and fail-closed quorum checks."""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json, content_digest
from .errors import ReviewError, SecurityError, ValidationError

REVIEW_NAMESPACE: Final[Literal["laos-v8-review"]] = "laos-v8-review"


def _stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewError("review time is invalid", code="REVIEW_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise ReviewError("review time lacks offset", code="REVIEW_TIME_INVALID")
    return parsed.astimezone(UTC)


class ReviewCapsule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    candidate_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_tree: str = Field(pattern=r"^[a-f0-9]{40}$")
    plan_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    policy_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    criteria_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    evidence_index_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    check_bundle_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    verification_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    criterion_ids: tuple[str, ...] = ()
    builder_narrative_included: Literal[False] = False


class ReviewChallenge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    challenge_id: str = Field(pattern=r"^review-challenge:[a-f0-9]{32}$")
    reviewer_id: Literal["nilhan"] = "nilhan"
    namespace: Literal["laos-v8-review"] = REVIEW_NAMESPACE
    capsule: ReviewCapsule
    issued_at: str
    expires_at: str

    @model_validator(mode="after")
    def chronology_is_valid(self) -> ReviewChallenge:
        if _time(self.expires_at) <= _time(self.issued_at):
            raise ValueError("REVIEW_CHALLENGE_CHRONOLOGY_INVALID")
        return self

    @classmethod
    def issue(cls, capsule: ReviewCapsule, *, now: datetime, lifetime: timedelta) -> ReviewChallenge:
        if lifetime <= timedelta(0) or lifetime > timedelta(hours=1):
            raise ValidationError("review challenge lifetime is invalid", code="REVIEW_CHALLENGE_LIFETIME_INVALID")
        return cls(
            challenge_id=f"review-challenge:{uuid.uuid4().hex}",
            capsule=capsule,
            issued_at=_stamp(now),
            expires_at=_stamp(now + lifetime),
        )

    def canonical_bytes(self) -> bytes:
        return canonical_json(self)


class ProtectedReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    review_id: str = Field(pattern=r"^protected-review:[a-f0-9]{32}$")
    reviewer_id: Literal["nilhan"]
    challenge_id: str
    challenge_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    public_key_fingerprint: str
    namespace: Literal["laos-v8-review"] = REVIEW_NAMESPACE
    verdicts: dict[str, Literal["ACCEPT", "REJECT"]]
    signature_b64: str
    verified_at: str
    approval_assurance: Literal["PASSPHRASE_PROTECTED_OPENSSH_ED25519"] = "PASSPHRASE_PROTECTED_OPENSSH_ED25519"


class ReviewerKeyManager:
    """Interactive helper; passphrases are entered only into OpenSSH prompts."""

    def __init__(self, key_path: Path | None = None) -> None:
        self.key_path = (key_path or (Path.home() / ".laos" / "reviewer" / "id_ed25519")).resolve(strict=False)
        ssh_keygen = shutil.which("ssh-keygen")
        if ssh_keygen is None:
            raise SecurityError("OpenSSH ssh-keygen is unavailable", code="REVIEWER_OPENSSH_UNAVAILABLE")
        self.ssh_keygen: str = ssh_keygen

    def enroll_interactive(self) -> Path:
        if self.key_path.exists() or self.key_path.with_suffix(self.key_path.suffix + ".pub").exists():
            raise SecurityError("reviewer key already exists", code="REVIEWER_KEY_EXISTS")
        self.key_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        completed = subprocess.run(  # noqa: S603 - trusted OpenSSH executable; passphrase stays on inherited TTY
            [self.ssh_keygen, "-t", "ed25519", "-a", "100", "-f", str(self.key_path), "-C", "nilhan-laos-v8-review"],
            check=False,
        )
        if completed.returncode:
            raise SecurityError("reviewer key enrolment failed", code="REVIEWER_KEY_ENROLLMENT_FAILED")
        return self.key_path.with_suffix(self.key_path.suffix + ".pub")

    def sign_interactive(self, challenge_path: Path) -> Path:
        if not self.key_path.is_file() or not challenge_path.is_file():
            raise ValidationError("review key or challenge is missing", code="REVIEW_SIGN_INPUT_MISSING")
        signature = challenge_path.with_suffix(challenge_path.suffix + ".sig")
        signature.unlink(missing_ok=True)
        completed = subprocess.run(  # noqa: S603 - trusted OpenSSH executable; passphrase stays on inherited TTY
            [self.ssh_keygen, "-Y", "sign", "-f", str(self.key_path), "-n", REVIEW_NAMESPACE, str(challenge_path)],
            check=False,
        )
        if completed.returncode or not signature.is_file():
            raise SecurityError("protected review signing failed", code="REVIEW_SIGNING_FAILED")
        return signature


class ProtectedReviewVerifier:
    def __init__(self, reviewer_id: str, public_key: str, *, registry_path: Path | None = None) -> None:
        if reviewer_id != "nilhan" or not public_key.startswith("ssh-ed25519 "):
            raise ValidationError("reviewer trust root is invalid", code="REVIEW_TRUST_ROOT_INVALID")
        self.reviewer_id = reviewer_id
        self.public_key = public_key.strip()
        ssh_keygen = shutil.which("ssh-keygen")
        if ssh_keygen is None:
            raise SecurityError("OpenSSH ssh-keygen is unavailable", code="REVIEWER_OPENSSH_UNAVAILABLE")
        self.ssh_keygen: str = ssh_keygen
        self._used: set[str] = set()
        self.registry_path = registry_path.resolve(strict=False) if registry_path is not None else None

    def _registered_challenges(self) -> set[str]:
        if self.registry_path is None or not self.registry_path.exists():
            return set()
        if self.registry_path.is_symlink() or not self.registry_path.is_file():
            raise SecurityError("review replay registry is unsafe", code="REVIEW_REGISTRY_UNSAFE")
        try:
            value = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SecurityError("review replay registry is invalid", code="REVIEW_REGISTRY_INVALID") from exc
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise SecurityError("review replay registry is invalid", code="REVIEW_REGISTRY_INVALID")
        return set(value)

    def _remember(self, challenge_id: str) -> None:
        self._used.add(challenge_id)
        if self.registry_path is None:
            return
        registered = self._registered_challenges()
        registered.add(challenge_id)
        self.registry_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.registry_path.parent / f".{self.registry_path.name}.{uuid.uuid4().hex}.tmp"
        temporary.write_bytes(canonical_json(sorted(registered)))
        os.replace(temporary, self.registry_path)

    def _fingerprint(self) -> str:
        with tempfile.TemporaryDirectory(prefix="laos-review-key-") as temporary:
            public = Path(temporary) / "reviewer.pub"
            public.write_text(self.public_key + "\n", encoding="utf-8")
            completed = subprocess.run(  # noqa: S603 - trusted OpenSSH executable and temporary public key
                [self.ssh_keygen, "-lf", str(public), "-E", "sha256"],
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
        if completed.returncode or "SHA256:" not in completed.stdout:
            raise SecurityError("reviewer public key fingerprint failed", code="REVIEW_TRUST_ROOT_INVALID")
        fingerprint: str = next(item for item in completed.stdout.split() if item.startswith("SHA256:"))
        return fingerprint

    def verify_and_record(
        self,
        challenge: ReviewChallenge,
        signature_b64: str,
        *,
        verdicts: dict[str, Literal["ACCEPT", "REJECT"]],
        now: datetime,
    ) -> ProtectedReviewRecord:
        digest = content_digest(challenge)
        if challenge.challenge_id in self._used or challenge.challenge_id in self._registered_challenges():
            raise ReviewError("review challenge was already consumed", code="REVIEW_CHALLENGE_REPLAY")
        if now.astimezone(UTC) > _time(challenge.expires_at):
            raise ReviewError("review challenge expired", code="REVIEW_CHALLENGE_EXPIRED")
        if now.astimezone(UTC) < _time(challenge.issued_at) - timedelta(minutes=5):
            raise ReviewError("review challenge is future-dated", code="REVIEW_CHALLENGE_FUTURE")
        if challenge.capsule.criterion_ids and set(verdicts) != set(challenge.capsule.criterion_ids):
            raise ReviewError("review verdicts do not cover every criterion", code="REVIEW_CRITERIA_INCOMPLETE")
        try:
            signature = base64.b64decode(signature_b64, validate=True)
        except ValueError as exc:
            raise ReviewError("review signature encoding is invalid", code="REVIEW_SIGNATURE_INVALID") from exc
        with tempfile.TemporaryDirectory(prefix="laos-review-verify-") as temporary:
            root = Path(temporary)
            allowed = root / "allowed_signers"
            signature_file = root / "challenge.sig"
            allowed.write_text(f"{self.reviewer_id} {self.public_key}\n", encoding="utf-8")
            signature_file.write_bytes(signature)
            completed = subprocess.run(  # noqa: S603 - trusted OpenSSH verifier and structured fixed argv
                [
                    self.ssh_keygen,
                    "-Y",
                    "verify",
                    "-f",
                    str(allowed),
                    "-I",
                    self.reviewer_id,
                    "-n",
                    REVIEW_NAMESPACE,
                    "-s",
                    str(signature_file),
                ],
                input=challenge.canonical_bytes(),
                capture_output=True,
                check=False,
                timeout=15,
            )
        if completed.returncode:
            raise ReviewError("review signature did not verify", code="REVIEW_SIGNATURE_INVALID")
        self._remember(challenge.challenge_id)
        return ProtectedReviewRecord(
            review_id=f"protected-review:{uuid.uuid4().hex}",
            reviewer_id="nilhan",
            challenge_id=challenge.challenge_id,
            challenge_digest=digest,
            public_key_fingerprint=self._fingerprint(),
            verdicts=verdicts,
            signature_b64=signature_b64,
            verified_at=_stamp(now),
        )


class QuorumParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    principal_id: str
    role: Literal["human", "verifier"]
    key_id: str
    session_id: str
    workspace_id: str
    controller_id: str


def require_quorum(participants: tuple[QuorumParticipant, ...], *, risk: str) -> None:
    if risk not in {"high", "critical"}:
        return
    for field in ("principal_id", "key_id", "session_id", "workspace_id", "controller_id"):
        values = [getattr(item, field) for item in participants]
        if len(values) != len(set(values)):
            raise ReviewError(
                "quorum participants share controlling authority or context",
                code="FALSE_INDEPENDENCE",
                context={"shared_field": field},
            )
    humans = [item for item in participants if item.role == "human" and item.principal_id == "nilhan"]
    verifiers = [item for item in participants if item.role == "verifier"]
    if len(humans) != 1 or len(verifiers) < 2:
        raise ReviewError("required high-risk quorum is unavailable", code="QUORUM_UNAVAILABLE")
