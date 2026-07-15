"""One-shot encrypted evidence service; production entrypoint runs only in Docker."""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .canonical import canonical_json
from .errors import EvidenceError, LaosError, SecurityError, ValidationError
from .evidence_custody import (
    CustodiedEvidenceObject,
    CustodyStoreRequest,
    EvidenceLevel,
    LegalHold,
    PurgeTombstone,
    RetentionPolicy,
)

KEY_ROOT = Path(os.environ.get("LAOS_CUSTODY_KEY_ROOT", "/keys"))
DATA_ROOT = Path(os.environ.get("LAOS_CUSTODY_DATA_ROOT", "/custody"))
KEY_FILE = KEY_ROOT / "custody.key"
INDEX_FILE = DATA_ROOT / "index.json"
LOCK_FILE = DATA_ROOT / ".custody.lock"
MAX_STDIN_BYTES = 2_800_000
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
)


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _safe_regular(path: Path, *, code: str) -> bytes:
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or (os.name == "posix" and info.st_mode & 0o077):
        raise SecurityError("custody file is unsafe", code=code)
    return path.read_bytes()


@contextlib.contextmanager
def _locked() -> Iterator[None]:
    DATA_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle = LOCK_FILE.open("a+b")
    try:
        if os.name == "posix":
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
        yield
    finally:
        if os.name == "posix":
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]
        handle.close()


def _atomic_write(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def _empty_index() -> dict[str, Any]:
    return {"record_version": "1.0.0", "objects": {}, "holds": {}, "tombstones": {}}


def _load_index() -> dict[str, Any]:
    if not INDEX_FILE.exists():
        return _empty_index()
    try:
        value = json.loads(_safe_regular(INDEX_FILE, code="CUSTODY_INDEX_UNSAFE"))
    except (OSError, ValueError) as exc:
        raise SecurityError("custody index is invalid", code="CUSTODY_INDEX_INVALID") from exc
    if not isinstance(value, dict) or value.get("record_version") != "1.0.0":
        raise SecurityError("custody index is invalid", code="CUSTODY_INDEX_INVALID")
    return value


def _save_index(value: dict[str, Any]) -> None:
    _atomic_write(INDEX_FILE, canonical_json(value))


def bootstrap() -> dict[str, object]:
    with _locked():
        KEY_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
        DATA_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not KEY_FILE.exists():
            _atomic_write(KEY_FILE, AESGCM.generate_key(bit_length=256))
        key = _safe_regular(KEY_FILE, code="CUSTODY_KEY_UNSAFE")
        if len(key) != 32:
            raise SecurityError("custody key is invalid", code="CUSTODY_KEY_INVALID")
        if not INDEX_FILE.exists():
            _save_index(_empty_index())
    return {
        "status": "PASS",
        "record_version": "1.0.0",
        "key_id": "key:" + hashlib.sha256(key).hexdigest()[:32],
        "assurance": "STAGE_6_DOCKER_ENCRYPTED_SINGLE_OPERATOR",
    }


def doctor() -> dict[str, object]:
    key = _safe_regular(KEY_FILE, code="CUSTODY_KEY_UNSAFE")
    if len(key) != 32:
        raise SecurityError("custody key is invalid", code="CUSTODY_KEY_INVALID")
    index = _load_index()
    return {
        "status": "PASS",
        "record_version": "1.0.0",
        "key_id": "key:" + hashlib.sha256(key).hexdigest()[:32],
        "object_count": len(index["objects"]),
        "active_hold_count": len([item for item in index["holds"].values() if item["released_at"] is None]),
        "tombstone_count": len(index["tombstones"]),
        "assurance": "STAGE_6_DOCKER_ENCRYPTED_SINGLE_OPERATOR",
    }


def _binding(request: CustodyStoreRequest, plaintext_digest: str) -> dict[str, object]:
    return {
        "record_version": request.record_version,
        "criterion_id": request.criterion_id,
        "classification": request.classification,
        "collector": request.collector,
        "collector_version": request.collector_version,
        "source_seal": request.source_seal,
        "result_seal": request.result_seal,
        "policy_digest": request.policy_digest,
        "redaction_method": request.redaction_method,
        "evidence_level": request.evidence_level.value,
        "created_at": _stamp(request.created_at),
        "raw": request.raw,
        "plaintext_digest": plaintext_digest,
    }


def store(request: CustodyStoreRequest) -> CustodiedEvidenceObject:
    if any(pattern.search(request.payload) for pattern in SECRET_PATTERNS):
        raise SecurityError("unredacted secret material is denied", code="CUSTODY_SECRET_MATERIAL_DENIED")
    retention = RetentionPolicy.for_evidence(request.classification, raw=request.raw)
    plaintext_digest = "sha256:" + hashlib.sha256(request.payload).hexdigest()
    binding = _binding(request, plaintext_digest)
    associated_data = canonical_json(binding)
    object_id = "object:" + hashlib.sha256(associated_data).hexdigest()
    with _locked():
        index = _load_index()
        if object_id in index["tombstones"]:
            raise EvidenceError("purged evidence cannot be rebound", code="CUSTODY_OBJECT_PURGED")
        existing = index["objects"].get(object_id)
        if existing is not None:
            public = {name: existing[name] for name in CustodiedEvidenceObject.model_fields}
            return CustodiedEvidenceObject.model_validate(public, strict=True)
        key = _safe_regular(KEY_FILE, code="CUSTODY_KEY_UNSAFE")
        nonce = os.urandom(12)
        encrypted = nonce + AESGCM(key).encrypt(nonce, request.payload, associated_data)
        filename = f"{object_id.removeprefix('object:')}.bin"
        target = DATA_ROOT / "objects" / filename
        _atomic_write(target, encrypted)
        expires = request.created_at + timedelta(days=retention.retention_days) if retention.retention_days else None
        record = CustodiedEvidenceObject(
            object_id=object_id,
            plaintext_digest=plaintext_digest,
            ciphertext_digest="sha256:" + hashlib.sha256(encrypted).hexdigest(),
            bytes=len(request.payload),
            criterion_id=request.criterion_id,
            classification=request.classification,
            collector=request.collector,
            collector_version=request.collector_version,
            source_seal=request.source_seal,
            result_seal=request.result_seal,
            policy_digest=request.policy_digest,
            redaction_method=request.redaction_method,
            evidence_level=request.evidence_level,
            created_at=_stamp(request.created_at),
            expires_at=_stamp(expires) if expires else None,
        )
        stored = record.model_dump(mode="json")
        stored["binding"] = binding
        stored["relative_path"] = f"objects/{filename}"
        index["objects"][object_id] = stored
        _save_index(index)
        return record


def fetch(object_id: str) -> bytes:
    with _locked():
        index = _load_index()
        if object_id in index["tombstones"]:
            raise EvidenceError("evidence object was purged", code="CUSTODY_OBJECT_PURGED")
        stored = index["objects"].get(object_id)
        if stored is None:
            raise EvidenceError("evidence object is missing", code="CUSTODY_OBJECT_MISSING")
        encrypted = _safe_regular(DATA_ROOT / stored["relative_path"], code="CUSTODY_OBJECT_UNSAFE")
        if "sha256:" + hashlib.sha256(encrypted).hexdigest() != stored["ciphertext_digest"]:
            raise EvidenceError("evidence ciphertext digest changed", code="CUSTODY_CIPHERTEXT_TAMPERED")
        try:
            payload = AESGCM(_safe_regular(KEY_FILE, code="CUSTODY_KEY_UNSAFE")).decrypt(
                encrypted[:12], encrypted[12:], canonical_json(stored["binding"])
            )
        except InvalidTag as exc:
            raise EvidenceError("evidence authentication failed", code="CUSTODY_AUTHENTICATION_FAILED") from exc
        if "sha256:" + hashlib.sha256(payload).hexdigest() != stored["plaintext_digest"]:
            raise EvidenceError("evidence plaintext digest changed", code="CUSTODY_PLAINTEXT_TAMPERED")
        return payload


def place_hold(object_id: str, authorization_digest: str) -> LegalHold:
    with _locked():
        index = _load_index()
        if object_id not in index["objects"]:
            raise EvidenceError("evidence object is missing", code="CUSTODY_OBJECT_MISSING")
        hold = LegalHold(
            hold_id=f"hold:{uuid.uuid4().hex}",
            object_id=object_id,
            authorization_digest=authorization_digest,
            placed_at=_stamp(_now()),
        )
        index["holds"][hold.hold_id] = hold.model_dump(mode="json")
        _save_index(index)
        return hold


def release_hold(hold_id: str, authorization_digest: str) -> LegalHold:
    with _locked():
        index = _load_index()
        value = index["holds"].get(hold_id)
        if value is None:
            raise EvidenceError("legal hold is missing", code="CUSTODY_HOLD_MISSING")
        hold = LegalHold.model_validate(value, strict=True)
        if hold.released_at is not None:
            raise EvidenceError("legal hold is already released", code="CUSTODY_HOLD_ALREADY_RELEASED")
        released = hold.model_copy(
            update={"released_at": _stamp(_now()), "release_authorization_digest": authorization_digest}
        )
        index["holds"][hold_id] = released.model_dump(mode="json")
        _save_index(index)
        return released


def purge(object_id: str, *, reason_digest: str) -> PurgeTombstone:
    with _locked():
        index = _load_index()
        stored = index["objects"].get(object_id)
        if stored is None:
            raise EvidenceError("evidence object is missing", code="CUSTODY_OBJECT_MISSING")
        active = [
            value
            for value in index["holds"].values()
            if value["object_id"] == object_id and value["released_at"] is None
        ]
        if active:
            raise SecurityError("evidence object has an active legal hold", code="CUSTODY_LEGAL_HOLD_ACTIVE")
        tombstone = PurgeTombstone(
            object_id=object_id,
            plaintext_digest=stored["plaintext_digest"],
            reason_digest=reason_digest,
            purged_at=_stamp(_now()),
        )
        (DATA_ROOT / stored["relative_path"]).unlink(missing_ok=True)
        del index["objects"][object_id]
        index["tombstones"][object_id] = tombstone.model_dump(mode="json")
        _save_index(index)
        return tombstone


def reconcile_purges() -> dict[str, int]:
    with _locked():
        index = _load_index()
        expected = {value["relative_path"] for value in index["objects"].values()}
        observed = {
            path.relative_to(DATA_ROOT).as_posix()
            for path in (DATA_ROOT / "objects").glob("*.bin")
            if path.is_file()
        } if (DATA_ROOT / "objects").exists() else set()
        return {"orphaned_objects": len(observed - expected), "missing_objects": len(expected - observed)}


def _read_wire() -> dict[str, Any]:
    payload = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(payload) > MAX_STDIN_BYTES:
        raise ValidationError("custody request is too large", code="CUSTODY_REQUEST_TOO_LARGE")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValidationError("custody request is invalid", code="CUSTODY_REQUEST_INVALID")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="laos-evidence-custodian")
    parser.add_argument(
        "command",
        choices=(
            "prepare-volumes", "bootstrap", "doctor", "store", "fetch", "hold", "release-hold", "purge",
            "reconcile",
        ),
    )
    parser.add_argument("--object-id")
    parser.add_argument("--hold-id")
    parser.add_argument("--authorization-digest")
    parser.add_argument("--reason-digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-volumes":
            get_effective_user_id = getattr(os, "geteuid", None)
            change_owner = getattr(os, "chown", None)
            if os.name != "posix" or get_effective_user_id is None or get_effective_user_id() != 0:
                raise SecurityError("volume preparation requires container root", code="CUSTODY_PREPARE_DENIED")
            if change_owner is None:
                raise SecurityError("volume ownership control is unavailable", code="CUSTODY_PREPARE_DENIED")
            for root in (KEY_ROOT, DATA_ROOT):
                root.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(root, 0o700)
                change_owner(root, 65532, 65532)
            output: Any = {"status": "PASS"}
        elif args.command == "bootstrap":
            output = bootstrap()
        elif args.command == "doctor":
            output = doctor()
        elif args.command == "store":
            wire = _read_wire()
            encoded = wire.pop("payload_b64")
            padding = "=" * (-len(encoded) % 4)
            wire["payload"] = base64.urlsafe_b64decode(encoded + padding)
            wire["created_at"] = datetime.fromisoformat(str(wire["created_at"]).replace("Z", "+00:00"))
            wire["evidence_level"] = EvidenceLevel(str(wire["evidence_level"]))
            output = store(CustodyStoreRequest.model_validate(wire, strict=True))
        elif args.command == "fetch":
            output = {"payload_b64": base64.urlsafe_b64encode(fetch(str(args.object_id))).decode("ascii")}
        elif args.command == "hold":
            output = place_hold(str(args.object_id), str(args.authorization_digest))
        elif args.command == "release-hold":
            output = release_hold(str(args.hold_id), str(args.authorization_digest))
        elif args.command == "purge":
            output = purge(str(args.object_id), reason_digest=str(args.reason_digest))
        else:
            output = reconcile_purges()
        sys.stdout.buffer.write(canonical_json(output) + b"\n")
        return 0
    except LaosError as exc:
        sys.stderr.buffer.write(canonical_json(exc.as_dict()) + b"\n")
        return 1
    except Exception:
        error = SecurityError("evidence custodian failed closed", code="CUSTODY_INTERNAL_FAILURE")
        sys.stderr.buffer.write(canonical_json(error.as_dict()) + b"\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
