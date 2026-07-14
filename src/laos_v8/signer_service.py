"""One-shot key service used only inside the hardened signer container."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .canonical import canonical_json
from .errors import LaosError, SecurityError, ValidationError
from .models import KeyPurpose
from .protected_signer_models import SignerPublicBundle, SigningRequest
from .signing import _decode, _encode, sign_envelope

KEY_ROOT = Path(os.environ.get("LAOS_SIGNER_KEY_ROOT", "/keys"))
KEYRING = KEY_ROOT / "keyring.json"
MAX_STDIN_BYTES = 2_800_000
MAX_REQUEST_SKEW_SECONDS = 300
PURPOSE_MEDIA_PREFIXES: dict[KeyPurpose, tuple[str, ...]] = {
    "capsule": ("application/vnd.nilhan.laos.action-capsule.",),
    "event_anchor": (
        "application/vnd.nilhan.laos.capture-return.",
        "application/vnd.nilhan.laos.event-anchor.",
    ),
    "pack_manifest": ("application/vnd.nilhan.laos.pack-manifest.",),
    "release": ("application/vnd.nilhan.laos.release-record.",),
}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("signer timestamp is invalid", code="SIGNER_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValidationError("signer timestamp lacks offset", code="SIGNER_TIME_INVALID")
    return parsed.astimezone(UTC)


def _read_stdin() -> bytes:
    payload = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(payload) > MAX_STDIN_BYTES:
        raise SecurityError("signer request is too large", code="SIGNER_REQUEST_TOO_LARGE")
    return payload


def _load() -> dict[str, Any]:
    try:
        metadata = KEYRING.lstat()
    except FileNotFoundError as exc:
        raise SecurityError("signer keyring is unavailable", code="SIGNER_NOT_BOOTSTRAPPED") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise SecurityError("signer keyring path is unsafe", code="SIGNER_KEYRING_UNSAFE")
    if os.name == "posix" and metadata.st_mode & 0o077:
        raise SecurityError("signer keyring permissions are unsafe", code="SIGNER_KEYRING_PERMISSIONS")
    try:
        value = json.loads(KEYRING.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SecurityError("signer keyring is invalid", code="SIGNER_KEYRING_INVALID") from exc
    if not isinstance(value, dict) or not isinstance(value.get("keys"), list):
        raise SecurityError("signer keyring is invalid", code="SIGNER_KEYRING_INVALID")
    return value


def _write(value: dict[str, Any]) -> None:
    KEY_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = KEY_ROOT / f".keyring-{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(canonical_json(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, KEYRING)
        os.chmod(KEYRING, 0o600)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _new_key(purpose: KeyPurpose, generation: int, status: str) -> dict[str, Any]:
    private = Ed25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return {
        "key_id": f"key:{hashlib.sha256(public).hexdigest()[:32]}",
        "private_key_b64": _encode(private_bytes),
        "public_key_b64": _encode(public),
        "purpose": purpose,
        "generation": generation,
        "status": status,
        "created_at": _now(),
        "retired_at": None,
        "revoked_at": None,
        "revocation_reason_digest": None,
    }


def _public(keyring: dict[str, Any]) -> SignerPublicBundle:
    keys = [{name: value for name, value in raw.items() if name != "private_key_b64"} for raw in keyring["keys"]]
    return SignerPublicBundle.model_validate(
        {
            "signer_instance_id": keyring["signer_instance_id"],
            "assurance": "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
            "keys": tuple(keys),
        },
        strict=True,
    )


def bootstrap() -> SignerPublicBundle:
    if KEYRING.exists():
        return _public(_load())
    keyring = {
        "record_version": "1.0.0",
        "signer_instance_id": f"signer:{uuid.uuid4().hex}",
        "keys": [
            _new_key("capsule", 1, "active"),
            _new_key("event_anchor", 1, "active"),
            _new_key("pack_manifest", 1, "active"),
            _new_key("release", 1, "reserved"),
        ],
    }
    _write(keyring)
    return _public(keyring)


def sign() -> bytes:
    request = SigningRequest.model_validate_json(_read_stdin(), strict=True)
    now = datetime.now(UTC)
    if abs((now - _utc(request.requested_at)).total_seconds()) > MAX_REQUEST_SKEW_SECONDS:
        raise SecurityError("signing request is stale or future-dated", code="SIGNER_REQUEST_STALE")
    if not request.payload_type.startswith(PURPOSE_MEDIA_PREFIXES[request.key_purpose]):
        raise SecurityError("payload type is not allowed for key purpose", code="SIGNER_PAYLOAD_PURPOSE_DENIED")
    keyring = _load()
    matches = [
        item
        for item in keyring["keys"]
        if item["purpose"] == request.key_purpose and item["status"] == "active"
    ]
    if len(matches) != 1:
        code = "SIGNER_RELEASE_KEY_RESERVED" if request.key_purpose == "release" else "SIGNER_ACTIVE_KEY_UNAVAILABLE"
        raise SecurityError("signing key is not active", code=code)
    selected = matches[0]
    private = Ed25519PrivateKey.from_private_bytes(_decode(selected["private_key_b64"]))
    envelope = sign_envelope(
        private,
        _decode(request.payload_b64),
        key_id=selected["key_id"],
        payload_type=request.payload_type,
        key_purpose=request.key_purpose,
        issuer=request.issuer,
        audience=request.audience,
        issued_at=request.issued_at,
        expires_at=request.expires_at,
    )
    return canonical_json(envelope)


def rotate(purpose: KeyPurpose) -> SignerPublicBundle:
    if purpose == "release":
        raise SecurityError("release key activation is reserved for Stage 8", code="SIGNER_RELEASE_KEY_RESERVED")
    keyring = _load()
    active = [item for item in keyring["keys"] if item["purpose"] == purpose and item["status"] == "active"]
    if len(active) != 1:
        raise SecurityError("active signing key is unavailable", code="SIGNER_ACTIVE_KEY_UNAVAILABLE")
    active[0]["status"] = "retired_historical"
    active[0]["retired_at"] = _now()
    generation = max(item["generation"] for item in keyring["keys"] if item["purpose"] == purpose) + 1
    keyring["keys"].append(_new_key(purpose, generation, "active"))
    _write(keyring)
    return _public(keyring)


def revoke(key_id: str, reason_digest: str) -> SignerPublicBundle:
    if not reason_digest.startswith("sha256:") or len(reason_digest) != 71:
        raise ValidationError("revocation reason digest is invalid", code="SIGNER_REVOCATION_REASON_INVALID")
    keyring = _load()
    matches = [item for item in keyring["keys"] if item["key_id"] == key_id]
    if len(matches) != 1:
        raise SecurityError("signer key is unknown", code="SIGNER_KEY_UNKNOWN")
    selected = matches[0]
    if selected["status"] == "reserved":
        raise SecurityError("reserved release key cannot be changed in Stage 5", code="SIGNER_RELEASE_KEY_RESERVED")
    was_active = selected["status"] == "active"
    selected["status"] = "revoked"
    selected["revoked_at"] = _now()
    selected["revocation_reason_digest"] = reason_digest
    if was_active:
        generation = max(item["generation"] for item in keyring["keys"] if item["purpose"] == selected["purpose"]) + 1
        keyring["keys"].append(_new_key(selected["purpose"], generation, "active"))
    _write(keyring)
    return _public(keyring)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="laos-protected-signer")
    parser.add_argument(
        "command",
        choices=("prepare-volume", "bootstrap", "public", "doctor", "sign", "rotate", "revoke"),
    )
    parser.add_argument("--purpose", choices=("capsule", "event_anchor", "pack_manifest", "release"))
    parser.add_argument("--key-id")
    parser.add_argument("--reason-digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-volume":
            get_effective_user_id = getattr(os, "geteuid", None)
            change_owner = getattr(os, "chown", None)
            if get_effective_user_id is None or change_owner is None or get_effective_user_id() != 0:
                raise SecurityError("volume preparation requires container root", code="SIGNER_VOLUME_PREPARE_DENIED")
            KEY_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
            change_owner(KEY_ROOT, 0, 0)
            os.chmod(KEY_ROOT, 0o700)
            change_owner(KEY_ROOT, 65532, 65532)
            output = canonical_json({"status": "PASS"})
        elif args.command == "bootstrap":
            output = canonical_json(bootstrap())
        elif args.command in {"public", "doctor"}:
            output = canonical_json(_public(_load()))
        elif args.command == "sign":
            output = sign()
        elif args.command == "rotate":
            if args.purpose is None:
                raise ValidationError("rotation purpose is required", code="SIGNER_PURPOSE_REQUIRED")
            output = canonical_json(rotate(args.purpose))
        else:
            if args.key_id is None or args.reason_digest is None:
                raise ValidationError("revocation key and reason are required", code="SIGNER_REVOCATION_INPUT_REQUIRED")
            output = canonical_json(revoke(args.key_id, args.reason_digest))
        sys.stdout.buffer.write(output + b"\n")
        return 0
    except LaosError as exc:
        sys.stderr.buffer.write(canonical_json(exc.as_dict()) + b"\n")
        return 1
    except Exception:
        error = SecurityError("protected signer failed closed", code="SIGNER_INTERNAL_FAILURE")
        sys.stderr.buffer.write(canonical_json(error.as_dict()) + b"\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
