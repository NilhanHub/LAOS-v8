from __future__ import annotations

import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from laos_v8.errors import SecurityError, ValidationError
from laos_v8.policy import ResourceBudget
from laos_v8.protected_checks import ProtectedCheckStore
from laos_v8.sandbox import CommandSpec, DockerSandbox
from laos_v8.signing import ProtectedTestSigner


def test_builder_cannot_request_protected_check_mount(tmp_path: Path) -> None:
    source = tmp_path / "source"
    checks = tmp_path / "checks"
    source.mkdir()
    checks.mkdir()
    with pytest.raises(ValidationError, match="verifier") as error:
        CommandSpec(
            argv=("python", "-V"),
            workspace=source,
            protected_check_workspace=checks,
            execution_role="builder",
            budget=ResourceBudget(),
        )
    assert error.value.code == "PROTECTED_CHECK_MOUNT_DENIED"


def test_protected_check_bundle_is_signed_immutable_and_tamper_evident(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    check = source / "test_hidden.py"
    check.write_text("assert 2 + 2 == 4\n", encoding="utf-8")
    store_root = tmp_path / "protected-store"
    signer = ProtectedTestSigner("event_anchor")
    store = ProtectedCheckStore(store_root)
    now = datetime.now(UTC).replace(microsecond=0)
    bundle = store.provision(
        (check,),
        argv=("python", "/protected_checks/test_hidden.py"),
        signer=signer,
        issuer="control:stage6",
        audience="verifier:clean",
        issued_at=now.isoformat().replace("+00:00", "Z"),
    )
    verified = store.verify(
        bundle.bundle_id,
        trust=signer.trust_root,
        expected_issuer="control:stage6",
        expected_audience="verifier:clean",
    )
    assert verified.bundle_digest == bundle.bundle_digest

    stored_check = store_root / bundle.bundle_id.removeprefix("check-bundle:") / "checks" / "test_hidden.py"
    stored_check.chmod(stat.S_IWRITE | stat.S_IREAD)
    stored_check.write_text("assert False\n", encoding="utf-8")
    with pytest.raises(SecurityError, match="digest") as tampered:
        store.verify(
            bundle.bundle_id,
            trust=signer.trust_root,
            expected_issuer="control:stage6",
            expected_audience="verifier:clean",
        )
    assert tampered.value.code == "PROTECTED_CHECK_TAMPERED"


def test_verifier_mount_is_read_only_and_separate(tmp_path: Path) -> None:
    source = tmp_path / "source"
    checks = tmp_path / "checks"
    source.mkdir()
    checks.mkdir()
    spec = CommandSpec(
        argv=("python", "/protected_checks/check.py"),
        workspace=source,
        protected_check_workspace=checks,
        execution_role="verifier",
        budget=ResourceBudget(),
    )
    command = DockerSandbox("docker").build_spec_command(spec, name="stage6-check-test")
    joined = "\n".join(command)
    assert "src=" + str(checks.resolve()) + ",dst=/protected_checks,readonly" in joined
