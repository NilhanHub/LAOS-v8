"""Argument-safe client for the one-shot local Docker protected signer."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .canonical import canonical_json
from .errors import SecurityError
from .models import KeyPurpose, TypedEnvelope
from .protected_signer_models import SignerPublicBundle, SigningRequest
from .sandbox import DockerSandbox
from .signing import PublicTrustRoot, SignerAssurance, _encode

DEFAULT_IMAGE_TAG = "laos-v8-protected-signer:stage5"
DEFAULT_VOLUME = "laos-v8-stage5-signer-keys-v1"


class DockerProtectedSigner:
    """Purpose-bound signer whose private key exists only in a Docker volume."""

    assurance: SignerAssurance = "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR"

    def __init__(
        self,
        root: Path,
        key_purpose: KeyPurpose,
        *,
        image: str = DEFAULT_IMAGE_TAG,
        volume: str = DEFAULT_VOLUME,
        timeout_seconds: int = 60,
    ) -> None:
        self.root = root.resolve(strict=True)
        self.key_purpose = key_purpose
        self.image = image
        self.volume = volume
        self.timeout_seconds = timeout_seconds
        self._docker = shutil.which("docker") or ""
        if not self._docker:
            raise SecurityError("Docker CLI is unavailable", code="SIGNER_DOCKER_UNAVAILABLE")

    def _run(
        self,
        command: str,
        *,
        stdin: bytes = b"",
        mutable: bool = False,
        root_user: bool = False,
        extra: tuple[str, ...] = (),
    ) -> bytes:
        DockerSandbox(self._docker).ensure_available(timeout_seconds=180)
        image_id = self.image_id()
        mount = f"type=volume,src={self.volume},dst=/keys"
        if not mutable:
            mount += ",readonly"
        capabilities = ["--cap-drop", "ALL"]
        if root_user:
            capabilities.extend(("--cap-add", "CHOWN"))
        argv = [
            self._docker,
            "run",
            "--rm",
            "--interactive",
            "--network",
            "none",
            "--read-only",
            *capabilities,
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "32",
            "--memory",
            "256m",
            "--cpus",
            "0.5",
            "--user",
            "0:0" if root_user else "65532:65532",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=16m",  # noqa: S108 - isolated container tmpfs, not a host path
            "--mount",
            mount,
            image_id,
            command,
            *extra,
        ]
        try:
            completed = subprocess.run(  # noqa: S603 - trusted Docker executable and structured fixed argv
                argv,
                input=stdin,
                capture_output=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SecurityError("protected signer invocation failed", code="SIGNER_INVOCATION_FAILED") from exc
        if completed.returncode:
            code = "SIGNER_INVOCATION_FAILED"
            try:
                decoded = json.loads(completed.stderr)
                error = decoded.get("error", decoded)
                if isinstance(error, dict):
                    code = str(error.get("code", code))
            except (UnicodeDecodeError, ValueError, AttributeError):
                pass
            raise SecurityError("protected signer denied the request", code=code)
        if len(completed.stdout) > 3_000_000:
            raise SecurityError("protected signer output is too large", code="SIGNER_OUTPUT_TOO_LARGE")
        return completed.stdout.strip()

    def image_id(self) -> str:
        completed = subprocess.run(  # noqa: S603 - trusted Docker executable and structured fixed argv
            [self._docker, "image", "inspect", "--format", "{{.Id}}", self.image],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
            timeout=15,
        )
        image_id = completed.stdout.strip()
        if completed.returncode or not image_id.startswith("sha256:"):
            raise SecurityError("protected signer image is unavailable", code="SIGNER_IMAGE_UNAVAILABLE")
        return image_id

    @classmethod
    def build_image(cls, root: Path, *, image: str = DEFAULT_IMAGE_TAG) -> str:
        docker = shutil.which("docker") or ""
        if not docker:
            raise SecurityError("Docker CLI is unavailable", code="SIGNER_DOCKER_UNAVAILABLE")
        DockerSandbox(docker).ensure_available(timeout_seconds=180)
        repository = root.resolve(strict=True)
        signer_root = repository / "signer"
        completed = subprocess.run(  # noqa: S603 - trusted Docker executable and structured fixed argv
            [
                docker,
                "build",
                "--pull=false",
                "--tag",
                image,
                "--file",
                str(signer_root / "Dockerfile"),
                str(repository),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=600,
        )
        if completed.returncode:
            raise SecurityError("protected signer image build failed", code="SIGNER_IMAGE_BUILD_FAILED")
        inspected = subprocess.run(  # noqa: S603 - trusted Docker executable and structured fixed argv
            [docker, "image", "inspect", "--format", "{{.Id}}", image],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        image_id = inspected.stdout.strip()
        if inspected.returncode or not image_id.startswith("sha256:"):
            raise SecurityError("protected signer image identity is unavailable", code="SIGNER_IMAGE_UNAVAILABLE")
        return image_id

    def bootstrap(self) -> SignerPublicBundle:
        subprocess.run(  # noqa: S603 - trusted Docker executable and structured fixed argv
            [self._docker, "volume", "create", self.volume],
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        self._run("prepare-volume", mutable=True, root_user=True)
        return SignerPublicBundle.model_validate_json(self._run("bootstrap", mutable=True), strict=True)

    def public_bundle(self) -> SignerPublicBundle:
        return SignerPublicBundle.model_validate_json(self._run("public"), strict=True)

    @property
    def trust_root(self) -> PublicTrustRoot:
        bundle = self.public_bundle()
        matches = [item for item in bundle.keys if item.purpose == self.key_purpose and item.status == "active"]
        if len(matches) != 1:
            raise SecurityError("active signer key is unavailable", code="SIGNER_ACTIVE_KEY_UNAVAILABLE")
        selected = matches[0]
        return PublicTrustRoot(selected.key_id, selected.public_key_b64, selected.purpose, self.assurance)

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
            raise SecurityError("protected signer key purpose mismatch", code="SIGNER_KEY_PURPOSE_DENIED")
        request = SigningRequest(
            request_id=f"sign:{uuid.uuid4().hex}",
            requested_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            payload_b64=_encode(payload),
            payload_type=payload_type,
            key_purpose=key_purpose,
            issuer=issuer,
            audience=audience,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        return TypedEnvelope.model_validate_json(self._run("sign", stdin=canonical_json(request)), strict=True)

    def rotate(self) -> SignerPublicBundle:
        return SignerPublicBundle.model_validate_json(
            self._run("rotate", mutable=True, extra=("--purpose", self.key_purpose)),
            strict=True,
        )

    def revoke(self, key_id: str, reason: str) -> SignerPublicBundle:
        reason_digest = f"sha256:{hashlib.sha256(reason.encode('utf-8')).hexdigest()}"
        return SignerPublicBundle.model_validate_json(
            self._run(
                "revoke",
                mutable=True,
                extra=("--key-id", key_id, "--reason-digest", reason_digest),
            ),
            strict=True,
        )

    def doctor(self) -> dict[str, object]:
        bundle = SignerPublicBundle.model_validate_json(self._run("doctor"), strict=True)
        return {
            "status": "PASS",
            "image_id": self.image_id(),
            "volume": self.volume,
            "signer_instance_id": bundle.signer_instance_id,
            "keys": [
                {"key_id": item.key_id, "purpose": item.purpose, "generation": item.generation, "status": item.status}
                for item in bundle.keys
            ],
            "assurance": self.assurance,
        }
