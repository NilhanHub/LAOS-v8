#!/usr/bin/env python3
"""Generate the real Stage 5 completion candidate from one clean source commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from laos_v8.canonical import canonical_json
from laos_v8.evidence_receipts import (
    ArtifactReceipt,
    CommandReceipt,
    EvidenceRunReceipt,
    atomic_write_json,
    new_run_id,
    stage5_candidate_command_policy,
)
from laos_v8.prompting import ExecutorProfile, ReleasedProfileBinding
from laos_v8.stage5_calibration import (
    Stage5CalibrationReceipt,
    build_active_profile_inventory,
)
from laos_v8.stage5_real_capture import V7_ARCHIVE_SHA256, RealCaptureReceipt

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "laos-stage5-completion-candidate/1.5.0"
ASSURANCE = "LOCAL_PROTECTED_SIGNER_AND_PINNED_MODEL_AWAITING_NILHAN_REVIEW"
GENERATED = {
    "calibration": "Evidence/STAGE_5_CALIBRATION_RECEIPT.json",
    "binding": "Evidence/STAGE_5_PROFILE_BINDING.json",
    "capture": "Evidence/STAGE_5_REAL_CAPTURE_RECEIPT.json",
    "signer": "Evidence/STAGE_5_PROTECTED_SIGNER_STATUS.json",
    "profiles": "profiles/ACTIVE_EXECUTOR_PROFILES.json",
    "candidate": "Evidence/STAGE_5_COMPLETION_CANDIDATE.json",
}
STATIC_ARTIFACTS = (
    "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md",
    "Evidence/STAGE_5_CALIBRATION_V1_FAILURES.json",
    "Evidence/STAGE_5_CALIBRATION_V1_1_FAILURES.json",
    "Evidence/STAGE_5_CALIBRATION_RECEIPT.v1-1-attempt-1.json",
    "Evidence/STAGE_5_CALIBRATION_RECEIPT.v1-1-attempt-2.json",
    "Evidence/STAGE_5_CALIBRATION_V1_2_PROVENANCE.json",
    "Evidence/STAGE_5_COMPLETION_CANDIDATE.v1-1-failed.json",
    "Evidence/STAGE_5_COMPLETION_CANDIDATE.v1-2-capture-failed.json",
    "Evidence/STAGE_5_COMPLETION_CANDIDATE.capture-pass-test-path-failed.json",
    "Evidence/STAGE_5_REAL_CAPTURE_PROVENANCE.json",
    "Evidence/STAGE_5_REAL_CAPTURE_SIGNER_STATUS.json",
    "Evidence/STAGE_5_COMPLETION_CANDIDATE.pre-reconciliation-pass.json",
    "Evidence/STAGE_5_PRE_RECONCILIATION_CANDIDATE_PROVENANCE.json",
    "Evidence/STAGE_5_COMPLETION_CANDIDATE.signer-status-alias-failed.json",
    "Evidence/STAGE_5_SIGNER_STATUS_ALIAS_FAILURE_PROVENANCE.json",
    "profiles/STAGE_5_CALIBRATION_PLAN.json",
    "profiles/STAGE_5_CALIBRATION_PLAN_V1_1_RETIRED.json",
)


def executable(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise RuntimeError(f"required-executable-unavailable:{name}")
    return resolved


def git(*args: str) -> str:
    return subprocess.check_output(  # noqa: S603 - resolved Git and fixed evidence arguments
        [executable("git"), "-C", str(ROOT), *args], text=True
    ).strip()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def run(label: str, argv: tuple[str, ...]) -> tuple[CommandReceipt, bytes]:
    actual = [executable("uv") if index == 0 and value == "uv" else value for index, value in enumerate(argv)]
    completed = subprocess.run(  # noqa: S603 - resolved executables and structured fixed arguments
        actual,
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    skipped = label == "docker_integration" and b"skipped" in completed.stdout.lower()
    passed = completed.returncode == 0 and not skipped
    receipt = CommandReceipt(
        label=label,
        argv=argv,
        exit_code=completed.returncode if not skipped else 125,
        status="PASS" if passed else "FAIL",
        stdout_sha256=digest(completed.stdout),
        stderr_sha256=digest(completed.stderr),
        stdout_bytes=len(completed.stdout),
        stderr_bytes=len(completed.stderr),
    )
    return receipt, completed.stdout


def load_offline_profiles() -> tuple[ExecutorProfile, ...]:
    payload = json.loads((ROOT / "profiles/OFFLINE_EXECUTOR_PROFILES.json").read_text(encoding="utf-8"))
    return tuple(
        ExecutorProfile.model_validate_json(canonical_json(item), strict=True) for item in payload["profiles"]
    )


def artifact_receipts(output_root: Path) -> tuple[ArtifactReceipt, ...]:
    values: list[ArtifactReceipt] = []
    for relative in (*STATIC_ARTIFACTS, *(value for key, value in GENERATED.items() if key != "candidate")):
        generated = output_root / relative
        source = generated if generated.is_file() else ROOT / relative
        if not source.is_file():
            raise RuntimeError(f"candidate-artifact-missing:{relative}")
        payload = source.read_bytes()
        values.append(ArtifactReceipt(path=relative, bytes=len(payload), sha256=digest(payload)))
    return tuple(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    if output_root == ROOT or output_root.is_relative_to(ROOT):
        raise SystemExit("completion candidate output must be outside the clean source reconstruction")
    output_root.mkdir(parents=True, exist_ok=True)
    archive = args.archive.resolve(strict=True)
    if archive.name != "LAOS_v7.0_Complete_System.zip" or file_digest(archive) != V7_ARCHIVE_SHA256:
        raise SystemExit("sealed v7 archive digest differs")
    os.environ["LAOS_V7_ARCHIVE"] = str(archive)
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    if source_commit != args.expected_commit or git("status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("completion candidate builder requires the expected clean source commit")
    run_id = new_run_id()
    started = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    candidate_path = output_root / GENERATED["candidate"]
    atomic_write_json(
        candidate_path,
        EvidenceRunReceipt(
            run_id=run_id,
            stage=5,
            status="IN_PROGRESS",
            assurance=ASSURANCE,
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            source_tree=source_tree,
            started_at_utc=started,
        ),
    )
    commands: list[CommandReceipt] = []
    stage3_root: Path | None = None
    try:
        command, _ = run(
            "structured_output_diagnostic",
            ("uv", "run", "--frozen", "python", "scripts/diagnose_stage5_structured_output.py"),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:structured_output_diagnostic")

        command, _ = run(
            "formal_calibration_receipt",
            ("uv", "run", "--frozen", "python", "scripts/verify_stage5_calibration_receipt.py"),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:formal_calibration_receipt")
        calibration_receipt = Stage5CalibrationReceipt.model_validate_json(
            (ROOT / GENERATED["calibration"]).read_bytes(), strict=True
        )
        binding_record = ReleasedProfileBinding.model_validate_json(
            (ROOT / GENERATED["binding"]).read_bytes(), strict=True
        )
        calibration = output_root / GENERATED["calibration"]
        binding = output_root / GENERATED["binding"]
        atomic_write_json(calibration, calibration_receipt)
        atomic_write_json(binding, binding_record)
        inventory = build_active_profile_inventory(load_offline_profiles(), calibration_receipt)
        atomic_write_json(output_root / GENERATED["profiles"], inventory)

        for label, signer_command in (
            ("protected_signer_build", "signer-build"),
            ("protected_signer_bootstrap", "signer-bootstrap"),
        ):
            command, _ = run(label, ("uv", "run", "--frozen", "laos", signer_command))
            commands.append(command)
            if command.status != "PASS":
                raise RuntimeError(f"candidate-command-failed:{label}")

        command, _ = run(
            "formal_capture_receipt",
            ("uv", "run", "--frozen", "python", "scripts/verify_stage5_real_capture_receipt.py"),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:formal_capture_receipt")
        capture_receipt = RealCaptureReceipt.model_validate_json(
            (ROOT / GENERATED["capture"]).read_bytes(), strict=True
        )
        atomic_write_json(output_root / GENERATED["capture"], capture_receipt)

        command, signer_output = run(
            "protected_signer_doctor",
            ("uv", "run", "--frozen", "laos", "signer-doctor", "--purpose", "capsule"),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:protected_signer_doctor")
        signer_status = json.loads(signer_output)
        atomic_write_json(output_root / GENERATED["signer"], signer_status)

        policy = stage5_candidate_command_policy(run_id, source_commit)
        stage3_root = Path(policy["verify_stage3"][6]).parent
        for label, argv in policy.items():
            if label == "verify_stage3":
                stage3_root.mkdir(parents=True, exist_ok=False)
            command, _ = run(label, argv)
            commands.append(command)
            if command.status != "PASS":
                raise RuntimeError(f"candidate-command-failed:{label}")
        command, _ = run(
            "ruff_stage5_recovery",
            (
                "uv",
                "run",
                "--frozen",
                "ruff",
                "check",
                "scripts/build_stage5_completion_candidate.py",
                "scripts/diagnose_stage5_structured_output.py",
                "scripts/run_stage5_calibration.py",
                "scripts/run_stage5_real_capture.py",
                "scripts/verify_stage5_calibration_receipt.py",
                "scripts/verify_stage5_real_capture_receipt.py",
                "scripts/verify_stage5_completion_candidate.py",
                "scripts/verify_ruff_baseline.py",
            ),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:ruff_stage5_recovery")
        command, _ = run(
            "ruff_repository_baseline",
            ("uv", "run", "--frozen", "python", "scripts/verify_ruff_baseline.py"),
        )
        commands.append(command)
        if command.status != "PASS":
            raise RuntimeError("candidate-command-failed:ruff_repository_baseline")
        if git("status", "--porcelain", "--untracked-files=all"):
            raise RuntimeError("clean reconstruction changed during candidate generation")
        receipt = EvidenceRunReceipt(
            run_id=run_id,
            stage=5,
            status="PASS_AWAITING_NILHAN_REVIEW",
            assurance=ASSURANCE,
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            source_tree=source_tree,
            started_at_utc=started,
            completed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            commands=tuple(commands),
            artifacts=artifact_receipts(output_root),
        )
    except Exception as exc:
        receipt = EvidenceRunReceipt(
            run_id=run_id,
            stage=5,
            status="FAIL",
            assurance=ASSURANCE,
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            source_tree=source_tree,
            started_at_utc=started,
            completed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            commands=tuple(commands),
            failure_code=str(exc),
        )
    finally:
        if stage3_root is not None and stage3_root.parent.resolve() == Path(tempfile.gettempdir()).resolve():
            shutil.rmtree(stage3_root, ignore_errors=True)
    atomic_write_json(candidate_path, receipt)
    print(json.dumps({"status": receipt.status, "run_id": run_id, "output": str(candidate_path)}, indent=2))
    return 0 if receipt.status == "PASS_AWAITING_NILHAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
