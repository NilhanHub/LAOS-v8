#!/usr/bin/env python3
"""Verify the Stage 5 completion candidate without granting Nilhan approval."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from laos_v8.evidence_receipts import EvidenceRunReceipt
from laos_v8.prompting import ReleasedProfileBinding
from laos_v8.stage5_calibration import (
    CALIBRATION_OUTPUT_SCHEMA_DIGEST,
    CALIBRATION_REQUEST_POLICY,
    CALIBRATION_VALIDATOR_SCHEMA_DIGEST,
    PINNED_MODEL,
    SETTINGS_DIGEST,
    ActiveProfileInventory,
    Stage5CalibrationReceipt,
)
from laos_v8.stage5_real_capture import (
    CAPTURE_OUTPUT_SCHEMA_DIGEST,
    CAPTURE_VALIDATOR_SCHEMA_DIGEST,
    V7_ARCHIVE_SHA256,
    RealCaptureReceipt,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = "Evidence/STAGE_5_COMPLETION_CANDIDATE.json"
EXPECTED_ASSURANCE = "LOCAL_PROTECTED_SIGNER_AND_PINNED_MODEL_AWAITING_NILHAN_REVIEW"
EXPECTED_GENERATOR = "laos-stage5-completion-candidate/1.5.0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(relative: str) -> object:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_signer_identity(value: object) -> tuple[str, str, str, tuple[tuple[str, int, str, str], ...]]:
    require(isinstance(value, dict), "protected signer status is invalid")
    assurance = value.get("assurance")
    instance = value.get("signer_instance_id")
    volume = value.get("volume")
    raw_keys = value.get("keys")
    require(isinstance(assurance, str), "protected signer assurance is invalid")
    require(isinstance(instance, str), "protected signer instance is invalid")
    require(isinstance(volume, str), "protected signer volume is invalid")
    require(isinstance(raw_keys, list), "protected signer keys are invalid")
    keys: list[tuple[str, int, str, str]] = []
    for raw in raw_keys:
        require(isinstance(raw, dict), "protected signer key is invalid")
        purpose = raw.get("purpose")
        generation = raw.get("generation")
        key_id = raw.get("key_id")
        status = raw.get("status")
        require(isinstance(purpose, str), "protected signer key purpose is invalid")
        require(isinstance(generation, int), "protected signer key generation is invalid")
        require(isinstance(key_id, str), "protected signer key ID is invalid")
        require(isinstance(status, str), "protected signer key status is invalid")
        keys.append((purpose, generation, key_id, status))
    return assurance, instance, volume, tuple(sorted(keys))


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved Git and fixed verifier arguments
        [executable, "-C", str(ROOT), *args], text=True
    ).strip()


def verify(expected_source_commit: str, candidate_tag: str | None) -> list[str]:
    checks: list[str] = []
    candidate_path = ROOT / CANDIDATE_PATH
    candidate = EvidenceRunReceipt.model_validate_json(candidate_path.read_bytes(), strict=True)
    require(candidate.status == "PASS_AWAITING_NILHAN_REVIEW", "candidate is not awaiting Nilhan review")
    require(candidate.assurance == EXPECTED_ASSURANCE, "candidate assurance changed")
    require(candidate.generator_version == EXPECTED_GENERATOR, "candidate generator changed")
    require(candidate.producer_authentication == "NONE_STAGE6_OPEN", "Stage 6 producer boundary changed")
    require(candidate.source_commit == expected_source_commit, "candidate source commit differs")
    require(git("rev-parse", f"{expected_source_commit}^{{tree}}") == candidate.source_tree, "source tree differs")
    for artifact in candidate.artifacts:
        path = ROOT / artifact.path
        require(path.is_file(), f"candidate artifact missing: {artifact.path}")
        require(path.stat().st_size == artifact.bytes, f"candidate artifact size differs: {artifact.path}")
        require(sha256(path) == artifact.sha256, f"candidate artifact hash differs: {artifact.path}")
    require(all(command.status == "PASS" for command in candidate.commands), "candidate command failed")
    required_labels = {
        "formal_calibration_receipt",
        "structured_output_diagnostic",
        "formal_capture_receipt",
        "protected_signer_build",
        "protected_signer_bootstrap",
        "protected_signer_doctor",
        "pytest_full",
        "docker_integration",
        "mypy",
        "ruff_scoped",
        "ruff_repository_baseline",
        "ruff_stage5_recovery",
        "package_build",
        "verify_stage1",
        "verify_stage2",
        "verify_stage3",
        "verify_stage4",
        "verify_stage5",
        "security_regressions",
    }
    require(required_labels <= {item.label for item in candidate.commands}, "candidate gate command is missing")
    checks.append("run_bound_candidate")

    calibration_path = ROOT / "Evidence/STAGE_5_CALIBRATION_RECEIPT.json"
    calibration = Stage5CalibrationReceipt.model_validate_json(calibration_path.read_bytes(), strict=True)
    require(calibration.status == "PASS" and calibration.thresholds_met, "calibration did not qualify")
    require(calibration.model_tag == PINNED_MODEL.tag, "calibration model tag drifted")
    require(calibration.model_blob_sha256 == PINNED_MODEL.blob_sha256, "calibration model blob drifted")
    require(calibration.calibration.settings_digest == SETTINGS_DIGEST, "calibration settings drifted")
    require(calibration.profile.version in {"1.0.4", "1.0.5"}, "released profile version is unexpected")
    require(calibration.settings == CALIBRATION_REQUEST_POLICY, "calibration request policy drifted")
    require(
        calibration.settings.get("output_schema_sha256") == CALIBRATION_OUTPUT_SCHEMA_DIGEST,
        "calibration schema binding drifted",
    )
    require(
        calibration.settings.get("validator_schema_sha256") == CALIBRATION_VALIDATOR_SCHEMA_DIGEST,
        "calibration validator binding drifted",
    )
    require(calibration.unsupported_accepted_claims == 0, "calibration accepted unsupported claims")
    require(calibration.prohibited_actions == 0, "calibration performed a prohibited action")
    checks.append("qualifying_calibration")

    binding = ReleasedProfileBinding.model_validate_json(
        (ROOT / "Evidence/STAGE_5_PROFILE_BINDING.json").read_bytes(), strict=True
    )
    require(binding.profile_digest == calibration.profile.digest, "profile binding digest differs")
    require(binding.model_tag == PINNED_MODEL.tag, "binding model tag differs")
    require(binding.model_blob_sha256 == PINNED_MODEL.blob_sha256, "binding model blob differs")
    require(binding.settings_digest == SETTINGS_DIGEST, "binding settings differ")
    require(binding.calibration_receipt_sha256 == calibration.digest, "binding calibration receipt differs")
    inventory = ActiveProfileInventory.model_validate_json(
        (ROOT / "profiles/ACTIVE_EXECUTOR_PROFILES.json").read_bytes(), strict=True
    )
    require(inventory.released_binding == binding, "active profile inventory binding differs")
    require(sum(item.released for item in inventory.profiles) == 1, "active profile release count differs")
    checks.append("exact_profile_binding")

    capture = RealCaptureReceipt.model_validate_json(
        (ROOT / "Evidence/STAGE_5_REAL_CAPTURE_RECEIPT.json").read_bytes(), strict=True
    )
    require(capture.status == "PASS_AWAITING_NILHAN_REVIEW", "capture review status differs")
    require(capture.archive_sha256_before == V7_ARCHIVE_SHA256, "v7 archive digest differs")
    require(capture.archive_sha256_after == V7_ARCHIVE_SHA256, "v7 archive changed")
    require(capture.profile_digest == binding.profile_digest, "capture profile binding differs")
    require(capture.settings_digest == binding.settings_digest, "capture settings binding differs")
    require(capture.output_schema_sha256 == CAPTURE_OUTPUT_SCHEMA_DIGEST, "capture output schema differs")
    require(capture.validator_schema_sha256 == CAPTURE_VALIDATOR_SCHEMA_DIGEST, "capture validator schema differs")
    require(capture.source_seal_before == capture.source_seal_after, "captured source changed")
    require(capture.human_reviewer is None, "capture falsely claims Nilhan review")
    require(not capture.repository_code_executed, "capture executed repository code")
    require(not capture.provider_direct_repository_access, "provider received repository access")
    require(len(capture.facts) == 6, "capture areas are incomplete")
    checks.append("sealed_v7_round_trip")

    signer = load("Evidence/STAGE_5_PROTECTED_SIGNER_STATUS.json")
    capture_signer = load("Evidence/STAGE_5_REAL_CAPTURE_SIGNER_STATUS.json")
    require(isinstance(signer, dict) and signer.get("status") == "PASS", "protected signer doctor failed")
    require(
        signer.get("assurance") == "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
        "protected signer assurance differs",
    )
    live_identity = protected_signer_identity(signer)
    capture_identity = protected_signer_identity(capture_signer)
    require(live_identity == capture_identity, "protected signer identity continuity differs")
    live_keys = {(purpose, generation): (key_id, status) for purpose, generation, key_id, status in live_identity[3]}
    require(
        live_keys.get(("capsule", 1), (None, None))[0] == capture.capsule_key_id,
        "current capsule signer key differs from capture",
    )
    require(
        live_keys.get(("event_anchor", 1), (None, None))[0] == capture.event_anchor_key_id,
        "current event-anchor signer key differs from capture",
    )
    checks.append("protected_signing_custody")

    status = load("IMPLEMENTATION_STATUS.json")
    require(isinstance(status, dict) and status.get("stage_5_status") == "IN_PROGRESS", "Stage 5 overclaim")
    require(
        status.get("stage_5_checkpoint") == "COMPLETION_CANDIDATE_PASS_AWAITING_NILHAN_REVIEW",
        "completion checkpoint differs",
    )
    require(status.get("v8_runtime_exists") is False and status.get("v8_release_exists") is False, "v8 overclaim")
    coverage = load("STAGE_5_CORE_WORKFLOW_COVERAGE.json")
    require(isinstance(coverage, dict), "Stage 5 coverage is invalid")
    rows = {item["id"]: item for item in coverage["coverage"]}
    for identifier in ("S5-05", "S5-11", "S5-14"):
        require(rows[identifier]["status"] == "PASS_AWAITING_NILHAN_REVIEW", f"{identifier} status differs")
    require(
        coverage["authority_sha256"] == sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md"),
        "coverage plan binding differs",
    )
    checks.append("program_truth_awaiting_review")

    if candidate_tag is not None:
        tagged = git("rev-parse", f"{candidate_tag}^{{commit}}")
        parent = git("rev-parse", f"{tagged}^")
        require(parent == expected_source_commit, "candidate tag parent is not the source commit")
        tagged_candidate = subprocess.check_output(  # noqa: S603 - resolved Git and fixed tagged path
            [shutil.which("git") or "git", "-C", str(ROOT), "show", f"{tagged}:{CANDIDATE_PATH}"]
        )
        require(hashlib.sha256(tagged_candidate).hexdigest() == sha256(candidate_path), "tagged receipt differs")
        checks.append("candidate_tag_binding")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--candidate-tag")
    args = parser.parse_args()
    try:
        checks = verify(args.expected_source_commit, args.candidate_tag)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "PASS_AWAITING_NILHAN_REVIEW", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
