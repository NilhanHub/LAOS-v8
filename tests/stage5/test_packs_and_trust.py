from __future__ import annotations

import zipfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from laos_v8.errors import DuplicateKeyError, SecurityError
from laos_v8.packs import (
    CapabilityManifest,
    PackCompiler,
    PackInput,
    PackRequest,
    verify_pack,
)
from laos_v8.signing import ProtectedTestSigner
from laos_v8.trust import PublicTrustRecord, TrustRegistry

ISSUED = "2026-07-13T00:00:00Z"


def trust_for(signer: ProtectedTestSigner, *, alpha: bool = False) -> TrustRegistry:
    registry = TrustRegistry()
    registry.add(
        PublicTrustRecord(
            signer.trust_root,
            "authority:stage5",
            "pack_manifest",
            "2026-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
            alpha_test_root=alpha,
        )
    )
    return registry


def request(kind: str, path: str, payload: bytes = b'{"task":"bounded"}') -> PackRequest:
    return PackRequest(
        pack_id="pack:" + "a" * 32,
        pack_kind=kind,  # type: ignore[arg-type]
        project_id="project:stage5",
        created_at=ISSUED,
        issuer="authority:stage5",
        audience="consumer:stage5",
        files=(PackInput(path, payload),),
        capabilities=CapabilityManifest(
            allowed=("WORKSPACE_READ",),
            denied=("NETWORK", "RAW_SECRETS", "FUTURE_ACTIONS", "UNMEDIATED_WRITE"),
        ),
        forbidden_canaries=("SEED_FUTURE_9d7e", "SEED_HIDDEN_41af", "SEED_SECRET_b2c1"),
    )


@pytest.mark.parametrize(
    ("kind", "path"),
    (
        ("architect_control", "control/plan.json"),
        ("agent_execution", "execution/task.json"),
        ("capture_execution", "capture/request.json"),
        ("review_capsule", "review/criterion.json"),
    ),
)
def test_physically_separate_signed_pack_round_trip(tmp_path: Path, kind: str, path: str) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    archive = tmp_path / f"{kind}.zip"
    compiled = PackCompiler(signer).compile(request(kind, path), archive)
    manifest = verify_pack(
        archive,
        trust=trust_for(signer),
        expected_kind=kind,  # type: ignore[arg-type]
        expected_project="project:stage5",
        expected_issuer="authority:stage5",
        expected_audience="consumer:stage5",
        now=datetime(2026, 7, 14, tzinfo=UTC),
    )
    assert manifest.pack_id == compiled.manifest.pack_id
    with zipfile.ZipFile(archive) as source:
        names = set(source.namelist())
        assert path in names
        assert {"manifest.json", "manifest.envelope.json", "public/capabilities.json", "public/trust.json"} <= names
        all_bytes = b"".join(source.read(name) for name in names)
    assert b"PRIVATE KEY" not in all_bytes


def test_pack_is_reproducible_for_same_request(tmp_path: Path) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    compiler = PackCompiler(signer)
    first = compiler.compile(request("agent_execution", "execution/task.json"), tmp_path / "one.zip")
    second = compiler.compile(request("agent_execution", "execution/task.json"), tmp_path / "two.zip")
    assert first.sha256 == second.sha256
    assert first.archive.read_bytes() == second.archive.read_bytes()


def test_trusted_key_cannot_claim_another_registered_issuer(tmp_path: Path) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    archive = tmp_path / "issuer-substitution.zip"
    PackCompiler(signer).compile(request("agent_execution", "execution/task.json"), archive)
    registry = TrustRegistry()
    registry.add(
        PublicTrustRecord(
            signer.trust_root,
            "authority:lower",
            "pack_manifest",
            "2026-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
        )
    )
    with pytest.raises(SecurityError) as denied:
        verify_pack(
            archive,
            trust=registry,
            expected_kind="agent_execution",
            expected_project="project:stage5",
            expected_issuer="authority:stage5",
            expected_audience="consumer:stage5",
            now=datetime(2026, 7, 14, tzinfo=UTC),
        )
    assert denied.value.code == "TRUST_ISSUER_MISMATCH"


@pytest.mark.parametrize(
    "payload",
    (
        b"SEED_FUTURE_9d7e",
        b"LAOS_HIDDEN_CHECK: answer",
        b"MASTER_FRAMEWORK_PRIVATE",
        b"api_key = value",
        b"BEGIN PRIVATE DATA",
    ),
)
def test_public_pack_leaks_fail_closed(tmp_path: Path, payload: bytes) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    with pytest.raises(SecurityError) as denied:
        PackCompiler(signer).compile(
            request("agent_execution", "execution/task.txt", payload),
            tmp_path / "denied.zip",
        )
    assert denied.value.code in {"PACK_LEAK_CANARY", "PACK_LEAK_DETECTED"}
    assert not (tmp_path / "denied.zip").exists()


def test_projection_classification_and_signer_purpose_are_enforced(tmp_path: Path) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    compiler = PackCompiler(signer)
    with pytest.raises(SecurityError) as wrong_prefix:
        compiler.compile(request("agent_execution", "control/master.md"), tmp_path / "prefix.zip")
    assert wrong_prefix.value.code == "PACK_PROJECTION_DENIED"
    restricted = request("agent_execution", "execution/task.json")
    restricted = replace(restricted, files=(PackInput("execution/task.json", b"{}", "restricted"),))
    with pytest.raises(SecurityError) as wrong_class:
        compiler.compile(restricted, tmp_path / "classification.zip")
    assert wrong_class.value.code == "PACK_CLASSIFICATION_DENIED"
    with pytest.raises(SecurityError) as wrong_signer:
        PackCompiler(ProtectedTestSigner("release"))
    assert wrong_signer.value.code == "PACK_SIGNER_PURPOSE_DENIED"


def test_content_and_manifest_tampering_fail(tmp_path: Path) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    source = tmp_path / "source.zip"
    PackCompiler(signer).compile(request("agent_execution", "execution/task.json"), source)
    with zipfile.ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files["execution/task.json"] = b'{"task":"substituted"}'
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(tampered, "w") as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    with pytest.raises(SecurityError) as content_error:
        verify_pack(
            tampered,
            trust=trust_for(signer),
            expected_kind="agent_execution",
            expected_project="project:stage5",
            expected_issuer="authority:stage5",
            expected_audience="consumer:stage5",
            now=datetime(2026, 7, 14, tzinfo=UTC),
        )
    assert content_error.value.code == "PACK_CONTENT_TAMPERED"


def test_unknown_revoked_expired_rollback_and_alpha_retirement(tmp_path: Path) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    compiled = PackCompiler(signer).compile(
        request("agent_execution", "execution/task.json"),
        tmp_path / "pack.zip",
    )
    unknown = TrustRegistry()
    unknown.add(
        PublicTrustRecord(
            ProtectedTestSigner("pack_manifest").trust_root,
            "authority:stage5",
            "pack_manifest",
            "2026-01-01T00:00:00Z",
            "2030-01-01T00:00:00Z",
        )
    )
    with pytest.raises(SecurityError) as missing:
        unknown.verifier_for(compiled.envelope, purpose="pack_manifest", now=datetime(2026, 7, 14, tzinfo=UTC))
    assert missing.value.code == "TRUST_KEY_UNKNOWN"

    registry = trust_for(signer, alpha=True)
    registry.revoke(signer.key_id, revoked_at="2027-01-01T00:00:00Z")
    with pytest.raises(SecurityError) as revoked:
        registry.verifier_for(compiled.envelope, purpose="pack_manifest", now=datetime(2028, 1, 1, tzinfo=UTC))
    assert revoked.value.code == "TRUST_KEY_REVOKED"
    historical = registry.verifier_for(
        compiled.envelope,
        purpose="pack_manifest",
        now=datetime(2028, 1, 1, tzinfo=UTC),
        historical=True,
    )
    assert historical.key_id == signer.key_id
    with pytest.raises(SecurityError) as expired:
        registry.verifier_for(
            compiled.envelope,
            purpose="pack_manifest",
            now=datetime(2031, 1, 1, tzinfo=UTC),
            historical=True,
        )
    assert expired.value.code == "TRUST_EXPIRED"
    with pytest.raises(SecurityError) as rollback:
        registry.replace_snapshot(version=registry.version, records=())
    assert rollback.value.code == "TRUST_ROLLBACK_DENIED"

    active = trust_for(ProtectedTestSigner("pack_manifest"), alpha=True)
    assert active.retire_alpha_roots(retired_at="2027-01-01T00:00:00Z") == 1
    assert active.public_snapshot()["keys"][0]["status"] == "retired_historical"  # type: ignore[index]


@pytest.mark.parametrize("mutation", ("duplicate", "noncanonical"))
def test_pack_json_duplicate_keys_and_encoding_variants_fail_closed(tmp_path: Path, mutation: str) -> None:
    signer = ProtectedTestSigner("pack_manifest")
    source = tmp_path / "source.zip"
    PackCompiler(signer).compile(request("agent_execution", "execution/task.json"), source)
    with zipfile.ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    envelope = files["manifest.envelope.json"]
    if mutation == "duplicate":
        envelope = envelope.replace(b'"algorithm":"Ed25519"', b'"algorithm":"Ed25519","algorithm":"Ed25519"')
    else:
        envelope = b" " + envelope
    files["manifest.envelope.json"] = envelope
    changed = tmp_path / f"{mutation}.zip"
    with zipfile.ZipFile(changed, "w") as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    expected_error = DuplicateKeyError if mutation == "duplicate" else SecurityError
    with pytest.raises(expected_error):
        verify_pack(
            changed,
            trust=trust_for(signer),
            expected_kind="agent_execution",
            expected_project="project:stage5",
            expected_issuer="authority:stage5",
            expected_audience="consumer:stage5",
            now=datetime(2026, 7, 14, tzinfo=UTC),
        )
