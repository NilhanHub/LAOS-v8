from __future__ import annotations

import shutil
import subprocess
import uuid

# ruff: noqa: S603
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from laos_v8 import custody_service
from laos_v8.errors import EvidenceError, SecurityError
from laos_v8.evidence_custody import (
    CustodyStoreRequest,
    DockerEvidenceCustodian,
    EvidenceLevel,
    RetentionPolicy,
    sign_evidence_index,
    verify_evidence_index,
)
from laos_v8.signing import ProtectedTestSigner


@pytest.fixture
def custody_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    key = tmp_path / "keys"
    data = tmp_path / "data"
    monkeypatch.setattr(custody_service, "KEY_ROOT", key)
    monkeypatch.setattr(custody_service, "DATA_ROOT", data)
    monkeypatch.setattr(custody_service, "KEY_FILE", key / "custody.key")
    monkeypatch.setattr(custody_service, "INDEX_FILE", data / "index.json")
    monkeypatch.setattr(custody_service, "LOCK_FILE", data / ".custody.lock")
    return key, data


def _request(payload: bytes = b'{"status":"PASS"}', **updates: object) -> CustodyStoreRequest:
    now = datetime.now(UTC).replace(microsecond=0)
    values: dict[str, object] = {
        "payload": payload,
        "criterion_id": "criterion:stage6-custody",
        "classification": "restricted",
        "collector": "collector:pytest",
        "collector_version": "1.0.0",
        "source_seal": "sha256:" + "a" * 64,
        "result_seal": "sha256:" + "b" * 64,
        "policy_digest": "sha256:" + "c" * 64,
        "redaction_method": "structured-minimization-v1",
        "evidence_level": EvidenceLevel.L3,
        "created_at": now,
    }
    values.update(updates)
    return CustodyStoreRequest(**values)


def test_custody_encrypts_payload_and_binds_associated_data(custody_roots: tuple[Path, Path]) -> None:
    _, data = custody_roots
    custody_service.bootstrap()
    record = custody_service.store(_request())
    object_path = data / "objects" / f"{record.object_id.removeprefix('object:')}.bin"
    assert object_path.is_file()
    assert b'"status":"PASS"' not in object_path.read_bytes()
    assert custody_service.fetch(record.object_id) == b'{"status":"PASS"}'

    ciphertext = bytearray(object_path.read_bytes())
    ciphertext[-1] ^= 1
    object_path.write_bytes(ciphertext)
    with pytest.raises(EvidenceError, match="ciphertext") as error:
        custody_service.fetch(record.object_id)
    assert error.value.code == "CUSTODY_CIPHERTEXT_TAMPERED"


def test_retention_hold_purge_and_tombstone(custody_roots: tuple[Path, Path]) -> None:
    custody_service.bootstrap()
    record = custody_service.store(_request())
    assert record.expires_at is not None
    assert datetime.fromisoformat(record.expires_at.replace("Z", "+00:00")) - datetime.fromisoformat(
        record.created_at.replace("Z", "+00:00")
    ) == timedelta(days=30)

    hold = custody_service.place_hold(record.object_id, "review:sha256:" + "d" * 64)
    with pytest.raises(SecurityError, match="legal hold") as held:
        custody_service.purge(record.object_id, reason_digest="sha256:" + "e" * 64)
    assert held.value.code == "CUSTODY_LEGAL_HOLD_ACTIVE"
    custody_service.release_hold(hold.hold_id, "review:sha256:" + "f" * 64)
    tombstone = custody_service.purge(record.object_id, reason_digest="sha256:" + "e" * 64)
    assert tombstone.object_id == record.object_id
    with pytest.raises(EvidenceError) as missing:
        custody_service.fetch(record.object_id)
    assert missing.value.code == "CUSTODY_OBJECT_PURGED"
    assert custody_service.reconcile_purges()["orphaned_objects"] == 0


def test_retention_policy_and_secret_minimization_are_fail_closed(custody_roots: tuple[Path, Path]) -> None:
    custody_service.bootstrap()
    public = custody_service.store(_request(classification="public", redaction_method="none"))
    assert public.expires_at is None
    assert RetentionPolicy.for_evidence("personal", raw=False).retention_days == 30

    with pytest.raises(SecurityError, match="secret") as secret:
        custody_service.store(_request(payload=b"-----BEGIN PRIVATE KEY-----\nnot-real"))
    assert secret.value.code == "CUSTODY_SECRET_MATERIAL_DENIED"


def test_docker_custodian_uses_separate_key_and_data_volumes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    client = DockerEvidenceCustodian(root, key_volume="keys-test", data_volume="data-test", docker="docker")
    command = client.build_command("doctor", mutable_data=False, mutable_keys=False)
    joined = "\n".join(command)
    assert "src=keys-test,dst=/keys,readonly" in joined
    assert "src=data-test,dst=/custody,readonly" in joined
    assert "--network\nnone" in joined
    assert "/var/run/docker.sock" not in joined


def test_signed_index_binds_objects_and_source(custody_roots: tuple[Path, Path]) -> None:
    custody_service.bootstrap()
    record = custody_service.store(_request())
    signer = ProtectedTestSigner("event_anchor")
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    index = sign_evidence_index(
        (record,),
        source_commit="a" * 40,
        signer=signer,
        issuer="control:stage6",
        audience="reviewer:nilhan",
        issued_at=now,
    )
    verify_evidence_index(
        index,
        trust=signer.trust_root,
        expected_issuer="control:stage6",
        expected_audience="reviewer:nilhan",
    )
    with pytest.raises(SecurityError) as tampered:
        verify_evidence_index(
            index.model_copy(update={"source_commit": "b" * 40}),
            trust=signer.trust_root,
            expected_issuer="control:stage6",
            expected_audience="reviewer:nilhan",
        )
    assert tampered.value.code == "EVIDENCE_INDEX_TAMPERED"


@pytest.mark.integration
def test_real_docker_custodian_encrypts_persists_and_purges() -> None:
    root = Path(__file__).resolve().parents[2]
    docker = shutil.which("docker")
    assert docker is not None, "Docker CLI is required on the supported Stage 6 Windows host"
    suffix = uuid.uuid4().hex
    key_volume = f"laos-v8-stage6-test-custody-keys-{suffix}"
    data_volume = f"laos-v8-stage6-test-custody-data-{suffix}"
    DockerEvidenceCustodian.build_image(root)
    client = DockerEvidenceCustodian(root, key_volume=key_volume, data_volume=data_volume, docker=docker)
    try:
        assert client.bootstrap()["status"] == "PASS"
        record = client.capture(_request())
        assert client.fetch(record.object_id) == b'{"status":"PASS"}'
        assert client.doctor()["object_count"] == 1
        tombstone = client.purge(record.object_id, reason_digest="sha256:" + "e" * 64)
        assert tombstone.object_id == record.object_id
        assert client.reconcile_purges() == {"orphaned_objects": 0, "missing_objects": 0}
    finally:
        for volume in (key_volume, data_volume):
            subprocess.run(
                [docker, "volume", "rm", "--force", volume],
                capture_output=True,
                check=False,
                timeout=30,
            )
