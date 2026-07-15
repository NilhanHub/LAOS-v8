from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from laos_v8 import signer_service
from laos_v8.canonical import canonical_json
from laos_v8.errors import SecurityError
from laos_v8.models import TypedEnvelope
from laos_v8.protected_signer import DockerProtectedSigner
from laos_v8.protected_signer_models import SigningRequest
from laos_v8.signing import PublicTrustRoot, _encode


@pytest.fixture
def key_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "keys"
    monkeypatch.setattr(signer_service, "KEY_ROOT", root)
    monkeypatch.setattr(signer_service, "KEYRING", root / "keyring.json")
    return root


def request(*, purpose: str = "capsule", requested_at: datetime | None = None) -> SigningRequest:
    media = {
        "capsule": "application/vnd.nilhan.laos.action-capsule.v1+json",
        "event_anchor": "application/vnd.nilhan.laos.capture-return.v1+json",
        "pack_manifest": "application/vnd.nilhan.laos.pack-manifest.v1+json",
        "release": "application/vnd.nilhan.laos.release-record.v1+json",
    }[purpose]
    now = requested_at or datetime.now(UTC)
    return SigningRequest(
        request_id="sign:" + "a" * 32,
        requested_at=now.isoformat().replace("+00:00", "Z"),
        payload_b64=_encode(b'{"bounded":true}'),
        payload_type=media,
        key_purpose=purpose,
        issuer="control:stage5",
        audience="agent:stage5",
        issued_at=now.isoformat().replace("+00:00", "Z"),
        expires_at=(now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    )


def test_bootstrap_keeps_private_material_out_of_public_bundle(key_root: Path) -> None:
    first = signer_service.bootstrap()
    second = signer_service.bootstrap()

    assert first == second
    assert len(first.keys) == 4
    assert next(item for item in first.keys if item.purpose == "release").status == "reserved"
    assert "private" not in canonical_json(first).decode("utf-8").lower()

    keyring = key_root / "keyring.json"
    raw = json.loads(keyring.read_text(encoding="utf-8"))
    assert all(item["private_key_b64"] for item in raw["keys"])
    if os.name == "posix":
        assert stat.S_IMODE(keyring.stat().st_mode) == 0o600


def test_signing_uses_active_purpose_key_and_verifies(key_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = signer_service.bootstrap()
    value = request()
    monkeypatch.setattr(signer_service, "_read_stdin", lambda: canonical_json(value))

    envelope = signer_service.sign()
    active = next(item for item in bundle.keys if item.purpose == "capsule")
    verifier = PublicTrustRoot(
        active.key_id,
        active.public_key_b64,
        active.purpose,
        "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
    ).verifier(trusted_issuer="control:stage5")
    payload = verifier.verify(
        TypedEnvelope.model_validate_json(envelope, strict=True),
        expected_purpose="capsule",
        expected_payload_type=value.payload_type,
        expected_issuer="control:stage5",
        expected_audience="agent:stage5",
    )
    assert payload == b'{"bounded":true}'
    assert not any(key_root.glob(".keyring-*.tmp"))


def test_signer_denies_stale_wrong_purpose_and_reserved_release(
    key_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signer_service.bootstrap()

    stale = request(requested_at=datetime.now(UTC) - timedelta(minutes=6))
    monkeypatch.setattr(signer_service, "_read_stdin", lambda: canonical_json(stale))
    with pytest.raises(SecurityError, match="stale") as stale_error:
        signer_service.sign()
    assert stale_error.value.code == "SIGNER_REQUEST_STALE"

    mismatch = request().model_copy(update={"payload_type": "application/vnd.nilhan.laos.pack-manifest.v1+json"})
    monkeypatch.setattr(signer_service, "_read_stdin", lambda: canonical_json(mismatch))
    with pytest.raises(SecurityError, match="purpose") as purpose_error:
        signer_service.sign()
    assert purpose_error.value.code == "SIGNER_PAYLOAD_PURPOSE_DENIED"

    release = request(purpose="release")
    monkeypatch.setattr(signer_service, "_read_stdin", lambda: canonical_json(release))
    with pytest.raises(SecurityError, match="not active") as release_error:
        signer_service.sign()
    assert release_error.value.code == "SIGNER_RELEASE_KEY_RESERVED"


def test_rotation_and_revocation_preserve_history_and_replace_active_key(key_root: Path) -> None:
    initial = signer_service.bootstrap()
    first = next(item for item in initial.keys if item.purpose == "capsule")

    rotated = signer_service.rotate("capsule")
    retired = next(item for item in rotated.keys if item.key_id == first.key_id)
    second = next(item for item in rotated.keys if item.purpose == "capsule" and item.status == "active")
    assert retired.status == "retired_historical"
    assert second.generation == 2

    reason = "sha256:" + "b" * 64
    revoked = signer_service.revoke(second.key_id, reason)
    assert next(item for item in revoked.keys if item.key_id == second.key_id).status == "revoked"
    replacement = next(item for item in revoked.keys if item.purpose == "capsule" and item.status == "active")
    assert replacement.generation == 3

    release = next(item for item in revoked.keys if item.purpose == "release")
    with pytest.raises(SecurityError, match="reserved") as error:
        signer_service.revoke(release.key_id, reason)
    assert error.value.code == "SIGNER_RELEASE_KEY_RESERVED"


@pytest.mark.integration
def test_real_docker_signer_is_persistent_concurrent_and_lifecycle_safe() -> None:
    root = Path(__file__).resolve().parents[2]
    volume = f"laos-v8-stage5-test-signer-{uuid.uuid4().hex}"
    docker = shutil.which("docker")
    assert docker is not None, "Docker CLI is required on the supported Windows Stage 5 host"
    DockerProtectedSigner.build_image(root)
    signer = DockerProtectedSigner(root, "capsule", volume=volume)
    try:
        bundle = signer.bootstrap()
        original = signer.trust_root
        isolated = subprocess.run(  # noqa: S603 - trusted Docker executable and fixed no-volume isolation probe
            [
                docker,
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                signer.image_id(),
                "public",
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
        assert isolated.returncode != 0
        assert b"private_key" not in isolated.stdout + isolated.stderr
        restarted = DockerProtectedSigner(root, "capsule", volume=volume)
        assert restarted.trust_root.key_id == original.key_id
        assert "private" not in bundle.model_dump_json().lower()

        now = datetime.now(UTC)

        def issue(index: int) -> TypedEnvelope:
            return restarted.sign(
                canonical_json({"capsule": index}),
                payload_type="application/vnd.nilhan.laos.action-capsule.v1+json",
                key_purpose="capsule",
                issuer="control:stage5",
                audience="agent:stage5",
                issued_at=now.isoformat().replace("+00:00", "Z"),
                expires_at=(now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            envelopes = tuple(pool.map(issue, range(4)))
        assert {item.key_id for item in envelopes} == {original.key_id}

        rotated = restarted.rotate()
        assert next(item for item in rotated.keys if item.key_id == original.key_id).status == "retired_historical"
        replacement = restarted.trust_root
        assert replacement.key_id != original.key_id

        revoked = restarted.revoke(replacement.key_id, "integration compromise drill")
        assert next(item for item in revoked.keys if item.key_id == replacement.key_id).status == "revoked"
        assert restarted.trust_root.key_id not in {original.key_id, replacement.key_id}

        release = DockerProtectedSigner(root, "release", volume=volume)
        with pytest.raises(SecurityError) as error:
            release.sign(
                b"{}",
                payload_type="application/vnd.nilhan.laos.release-record.v1+json",
                key_purpose="release",
                issuer="release:stage8",
                audience="consumer",
                issued_at=now.isoformat().replace("+00:00", "Z"),
                expires_at=None,
            )
        assert error.value.code == "SIGNER_RELEASE_KEY_RESERVED"
    finally:
        assert volume.startswith("laos-v8-stage5-test-signer-")
        subprocess.run(  # noqa: S603 - trusted Docker executable and exact test-owned volume
            [docker, "volume", "rm", "--force", volume],
            capture_output=True,
            check=False,
            timeout=30,
        )
