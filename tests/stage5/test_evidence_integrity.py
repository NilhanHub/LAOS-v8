from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError as PydanticValidationError

from laos_v8.evidence_receipts import ArtifactReceipt, EvidenceRunReceipt, stage5_candidate_command_policy

ROOT = Path(__file__).resolve().parents[2]


def _script(name: str) -> ModuleType:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"laos_test_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("collector", ("docker_details", "state_details"))
def test_stage3_failed_run_replaces_prior_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    collector: str,
) -> None:
    module = _script("generate_stage3_evidence.py")
    output = tmp_path / "stage3.json"
    output.write_text('{"status":"PASS","stale":true}\n', encoding="utf-8")

    def fail() -> dict[str, object]:
        raise RuntimeError("injected-collector-failure")

    if collector == "state_details":
        monkeypatch.setattr(module, "docker_details", lambda: {"status": "PASS"})
    monkeypatch.setattr(
        module,
        "git",
        lambda *args: "" if args[0] == "status" else "1" * 40,
    )
    monkeypatch.setattr(module, collector, fail)
    report = module.generate(output, run_id="run:" + "a" * 32)
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"
    assert persisted["status"] == "FAIL"
    assert persisted["run_id"] == "run:" + "a" * 32
    assert persisted["failure_code"] == "RuntimeError"
    assert "stale" not in persisted


def test_stage3_current_verification_rejects_wrong_run_before_values(tmp_path: Path) -> None:
    module = _script("verify_stage3.py")
    evidence = tmp_path / "stage3.json"
    evidence.write_text(
        json.dumps(
                {
                    "record_version": "2.0.0",
                    "generator_version": "laos-stage3-evidence/2.1.0",
                    "status": "PASS",
                "run_id": "run:" + "a" * 32,
                "source_commit": "0" * 40,
                "source_tree": "0" * 40,
                "started_at_utc": "2026-07-14T00:00:00Z",
                "completed_at_utc": "2026-07-14T00:01:00Z",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="run ID mismatch"):
        module.verify_local_security_evidence(
            [],
            evidence_path=evidence,
            expected_run_id="run:" + "b" * 32,
            expected_source_commit="0" * 40,
            historical=False,
        )


def test_stage3_current_verification_rejects_reversed_timestamps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage3.py")
    evidence = tmp_path / "stage3.json"
    evidence.write_text(
        json.dumps(
            {
                "record_version": "2.0.0",
                "generator_version": "laos-stage3-evidence/2.1.0",
                "status": "PASS",
                "run_id": "run:" + "a" * 32,
                "source_commit": "0" * 40,
                "source_tree": "0" * 40,
                "started_at_utc": "2026-07-14T00:01:00Z",
                "completed_at_utc": "2026-07-14T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "git", lambda *args: "0" * 40)
    with pytest.raises(AssertionError, match="timing order"):
        module.verify_local_security_evidence(
            [],
            evidence_path=evidence,
            expected_run_id="run:" + "a" * 32,
            expected_source_commit="0" * 40,
            historical=False,
        )


def test_stage3_current_verification_rejects_stale_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage3.py")
    evidence = tmp_path / "stage3.json"
    evidence.write_text(
        json.dumps(
            {
                "record_version": "2.0.0",
                "generator_version": "laos-stage3-evidence/2.1.0",
                "status": "PASS",
                "run_id": "run:" + "a" * 32,
                "source_commit": "0" * 40,
                "source_tree": "0" * 40,
                "started_at_utc": "2026-07-14T00:00:00Z",
                "completed_at_utc": "2026-07-14T00:01:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "git", lambda *args: "0" * 40)
    monkeypatch.setattr(module, "utc_now", lambda: datetime(2026, 7, 14, 1, tzinfo=UTC))
    with pytest.raises(AssertionError, match="stale"):
        module.verify_local_security_evidence(
            [],
            evidence_path=evidence,
            expected_run_id="run:" + "a" * 32,
            expected_source_commit="0" * 40,
            historical=False,
        )


def test_stage3_full_current_verifier_regenerates_before_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage3.py")
    evidence = tmp_path / "stage3.json"
    evidence.write_text('{"status":"PASS","forged":true}\n', encoding="utf-8")

    def regenerate(path: Path, *, expected_run_id: str, expected_source_commit: str) -> None:
        assert expected_run_id == "run:" + "a" * 32
        assert expected_source_commit == "1" * 40
        path.write_text('{"status":"PASS","regenerated":true}\n', encoding="utf-8")

    def verify_evidence(checks: list[str], **kwargs: object) -> None:
        assert json.loads(evidence.read_text(encoding="utf-8"))["regenerated"] is True
        checks.append("regenerated_current_evidence")

    monkeypatch.setattr(module, "regenerate_current_evidence", regenerate)
    monkeypatch.setattr(module, "verify_local_security_evidence", verify_evidence)
    for name in (
        "verify_governance",
        "verify_dependency_amendment",
        "verify_contracts",
        "verify_fail_closed_runtime",
        "verify_ledgers",
        "verify_repository_hygiene",
        "verify_operator_paths",
    ):
        monkeypatch.setattr(module, name, lambda checks: None)
    result = module.verify(
        evidence_path=evidence,
        expected_run_id="run:" + "a" * 32,
        expected_source_commit="1" * 40,
        historical=False,
    )
    assert result["status"] == "PASS_BOOTSTRAP_CURRENT_EVIDENCE_NOT_AUTHENTICATED"
    assert "forged" not in json.loads(evidence.read_text(encoding="utf-8"))


def test_stage3_generator_rejects_dirty_source_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("generate_stage3_evidence.py")
    monkeypatch.setattr(module, "git", lambda *args: " M src/changed.py" if args[0] == "status" else "1" * 40)
    output = tmp_path / "stage3.json"
    report = module.generate(output, run_id="run:" + "a" * 32)
    assert report["status"] == "FAIL"
    assert report["failure_code"] == "RuntimeError"
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "FAIL"


def _without_real_docker(module: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    class ReadySandbox:
        def ensure_available(self) -> SimpleNamespace:
            return SimpleNamespace(available=True, server_version="test")

    monkeypatch.setattr(module, "DockerSandbox", ReadySandbox)


def test_stage5_checkpoint_rejects_duplicate_or_omitted_criteria(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _script("verify_stage5_checkpoint.py")
    original_load = module.load

    def load(relative: str):
        value = original_load(relative)
        if relative == "STAGE_5_CORE_WORKFLOW_COVERAGE.json":
            value = copy.deepcopy(value)
            value["coverage"][0] = copy.deepcopy(value["coverage"][1])
        return value

    monkeypatch.setattr(module, "load", load)
    _without_real_docker(module, monkeypatch)
    with pytest.raises(AssertionError, match="duplicate criteria"):
        module.verify()


def test_stage5_checkpoint_rejects_wrong_plan_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _script("verify_stage5_checkpoint.py")
    original_load = module.load

    def load(relative: str):
        value = original_load(relative)
        if relative == "STAGE_5_CORE_WORKFLOW_COVERAGE.json":
            value = copy.deepcopy(value)
            value["authority_sha256"] = "0" * 64
        return value

    monkeypatch.setattr(module, "load", load)
    _without_real_docker(module, monkeypatch)
    with pytest.raises(AssertionError, match="active plan"):
        module.verify()


def test_stage5_checkpoint_does_not_trust_mutable_docker_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _script("verify_stage5_checkpoint.py")
    original_load = module.load
    loaded: list[str] = []

    def load(relative: str):
        loaded.append(relative)
        return original_load(relative)

    monkeypatch.setattr(module, "load", load)
    _without_real_docker(module, monkeypatch)
    checks = module.verify()
    assert "automatic_docker_dependency_live" in checks
    assert "Evidence/DOCKER_AUTOSTART_VERIFICATION.json" not in loaded


def test_stage5_candidate_rejects_self_asserted_pass_without_commands(tmp_path: Path) -> None:
    module = _script("verify_stage5_checkpoint.py")
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(
            {
                "record_version": "1.1.0",
                "run_id": "run:" + "a" * 32,
                "stage": 5,
                "status": "PASS_AWAITING_NILHAN_REVIEW",
                "assurance": "BOOTSTRAP_BUILDER_ASSERTED_NOT_AUTHENTICATED_NOT_PRODUCTION_SIGNING",
                "producer_authentication": "NONE_STAGE6_OPEN",
                "generator_version": "test",
                "source_commit": "0" * 40,
                "source_tree": "0" * 40,
                "started_at_utc": "2026-07-14T00:00:00Z",
                "completed_at_utc": "2026-07-14T00:01:00Z",
                "commands": [],
                "artifacts": [],
                "failure_code": None,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PydanticValidationError):
        module.verify_candidate_evidence(candidate, expected_source_commit="0" * 40)


def _candidate_receipt(module: ModuleType, artifact: Path, *, artifact_sha256: str) -> dict[str, object]:
    empty_hash = hashlib.sha256(b"").hexdigest()
    run_id = "run:" + "a" * 32
    source_commit = "1" * 40
    commands = [
        {
            "label": label,
            "argv": list(argv),
            "exit_code": 0,
            "status": "PASS",
            "stdout_sha256": empty_hash,
            "stderr_sha256": empty_hash,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
        }
        for label, argv in stage5_candidate_command_policy(run_id, source_commit).items()
    ]
    return {
        "record_version": "1.1.0",
        "run_id": run_id,
        "stage": 5,
        "status": "PASS_AWAITING_NILHAN_REVIEW",
        "assurance": "BOOTSTRAP_BUILDER_ASSERTED_NOT_AUTHENTICATED_NOT_PRODUCTION_SIGNING",
        "producer_authentication": "NONE_STAGE6_OPEN",
        "generator_version": "laos-stage5-candidate/1.1.0",
        "source_commit": source_commit,
        "source_tree": "2" * 40,
        "started_at_utc": "2026-07-14T00:00:00Z",
        "completed_at_utc": "2026-07-14T00:01:00Z",
        "commands": commands,
        "artifacts": [
            {
                "path": artifact.name,
                "bytes": artifact.stat().st_size,
                "sha256": artifact_sha256,
            }
        ],
        "failure_code": None,
    }


def test_stage5_candidate_rejects_artifact_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _script("verify_stage5_checkpoint.py")
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"current")
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(_candidate_receipt(module, artifact, artifact_sha256=hashlib.sha256(b"old").hexdigest())),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "REQUIRED_CANDIDATE_ARTIFACTS", {artifact.name})
    monkeypatch.setattr(module, "git", lambda *args: "2" * 40)
    with pytest.raises(AssertionError, match="artifact hash changed"):
        module.verify_candidate_evidence(candidate, expected_source_commit="1" * 40)


def test_stage5_candidate_rejects_wrong_command_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage5_checkpoint.py")
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"current")
    receipt = _candidate_receipt(module, artifact, artifact_sha256=hashlib.sha256(b"current").hexdigest())
    receipt["commands"][0]["argv"] = ["uv", "self-asserted-pass"]  # type: ignore[index]
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "REQUIRED_CANDIDATE_ARTIFACTS", {artifact.name})
    monkeypatch.setattr(module, "git", lambda *args: "2" * 40)
    with pytest.raises(AssertionError, match="arguments differ"):
        module.verify_candidate_evidence(candidate, expected_source_commit="1" * 40)


def test_stage5_candidate_does_not_claim_ephemeral_build_packages() -> None:
    module = _script("verify_stage5_checkpoint.py")
    assert not any(path.startswith("dist/") for path in module.REQUIRED_CANDIDATE_ARTIFACTS)
    assert stage5_candidate_command_policy("run:" + "a" * 32, "1" * 40)["package_build"] == (
        "uv",
        "build",
    )


def _git(root: Path, *args: str) -> None:
    executable = shutil.which("git")
    assert executable is not None
    subprocess.run(  # noqa: S603 - resolved executable and fixture-controlled arguments
        [executable, "-C", str(root), *args],
        check=True,
        capture_output=True,
    )


def test_stage5_builder_uses_exact_status_path_exemption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("build_stage5_candidate_evidence.py")
    _git(tmp_path, "init", "--initial-branch=main")
    (tmp_path / "src").mkdir()
    source = tmp_path / "src/file.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "src/file.py")
    _git(tmp_path, "-c", "user.name=Fixture", "-c", "user.email=fixture.invalid", "commit", "-m", "base")
    source.write_text("VALUE = 2\n", encoding="utf-8")
    (tmp_path / "s").write_text("candidate\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "EXPECTED_REPOSITORY_OUTPUT", "s")
    assert module.validate_output_path(tmp_path / "s") == "s"
    assert module.git_status_paths() - {"s"} == {"src/file.py"}


def test_stage5_builder_rejects_tracked_output_artifact_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("build_stage5_candidate_evidence.py")
    _git(tmp_path, "init", "--initial-branch=main")
    package = tmp_path / "dist/package.whl"
    package.parent.mkdir()
    package.write_bytes(b"package")
    _git(tmp_path, "add", "dist/package.whl")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "EXPECTED_REPOSITORY_OUTPUT", "dist/package.whl")
    with pytest.raises(RuntimeError, match="must-be-untracked"):
        module.validate_output_path(package)


def _review_fixture(
    module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    tagged_parent: str,
) -> tuple[Path, EvidenceRunReceipt]:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"artifact")
    candidate_path = tmp_path / "Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json"
    candidate_path.parent.mkdir()
    candidate_path.write_text(
        json.dumps(_candidate_receipt(module, artifact, artifact_sha256=hashlib.sha256(b"artifact").hexdigest())),
        encoding="utf-8",
    )
    candidate = EvidenceRunReceipt.model_validate_json(candidate_path.read_bytes(), strict=True)
    tagged_commit = "3" * 40
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "record_version": "1.0.0",
                "status": "APPROVED",
                "reviewer": "Nilhan",
                "reviewed_run_id": candidate.run_id,
                "reviewed_candidate_commit": tagged_commit,
                "reviewed_candidate_tag": "stage5-security-remediation-candidate",
                "evidence_receipt_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
                "approved_at_utc": "2026-07-14T00:00:00Z",
                "approval_statement": "I reviewed this candidate.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "git",
        lambda *args: tagged_commit if args[0] == "rev-parse" else f"{tagged_commit} {tagged_parent}",
    )
    monkeypatch.setattr(module, "git_bytes", lambda *args: candidate_path.read_bytes())
    return review_path, candidate


def test_stage5_review_rejects_unrelated_candidate_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage5_checkpoint.py")
    review_path, candidate = _review_fixture(module, tmp_path, monkeypatch, tagged_parent="4" * 40)
    candidate_path = tmp_path / "Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json"
    with pytest.raises(AssertionError, match="parent is not the source commit"):
        module.verify_review_receipt(review_path, candidate, candidate_path)


def test_stage5_review_fails_closed_without_nilhan_authentication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _script("verify_stage5_checkpoint.py")
    review_path, candidate = _review_fixture(module, tmp_path, monkeypatch, tagged_parent="1" * 40)
    candidate_path = tmp_path / "Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json"
    with pytest.raises(AssertionError, match="PROTECTED_NILHAN_REVIEW_AUTHENTICATION_NOT_IMPLEMENTED"):
        module.verify_review_receipt(review_path, candidate, candidate_path)


def test_evidence_receipt_rejects_unsafe_artifact_path() -> None:
    with pytest.raises(PydanticValidationError, match="EVIDENCE_ARTIFACT_PATH_UNSAFE"):
        ArtifactReceipt(path="../outside", bytes=0, sha256="0" * 64)
