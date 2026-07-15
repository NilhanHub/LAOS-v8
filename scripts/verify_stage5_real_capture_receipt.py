#!/usr/bin/env python3
"""Verify and authorize reuse of the qualifying sealed-v7 capture receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from laos_v8.evidence_receipts import EvidenceRunReceipt
from laos_v8.prompting import ReleasedProfileBinding
from laos_v8.stage5_real_capture import V7_ARCHIVE_SHA256, RealCaptureReceipt

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "Evidence/STAGE_5_REAL_CAPTURE_PROVENANCE.json"
FAILED_CANDIDATE = ROOT / "Evidence/STAGE_5_COMPLETION_CANDIDATE.capture-pass-test-path-failed.json"
CAPTURE = ROOT / "Evidence/STAGE_5_REAL_CAPTURE_RECEIPT.json"
SIGNER = ROOT / "Evidence/STAGE_5_PROTECTED_SIGNER_STATUS.json"
BINDING = ROOT / "Evidence/STAGE_5_PROFILE_BINDING.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    expected_keys = {
        "record_version",
        "status",
        "policy",
        "formal_run_id",
        "formal_source_commit",
        "formal_source_tree",
        "capture_id",
        "capture_receipt_sha256",
        "protected_signer_status_sha256",
        "failed_candidate_sha256",
        "failed_candidate_status",
        "failed_candidate_failure_code",
        "downstream_failure_reproduction",
        "v7_archive_sha256_before",
        "v7_archive_sha256_after",
        "source_seal_before",
        "source_seal_after",
        "repository_code_executed",
        "first_capsule_redeemed",
        "review_status",
    }
    require(set(provenance) == expected_keys, "capture provenance shape differs")
    require(
        provenance["status"] == "QUALIFYING_REAL_CAPTURE_REUSABLE_FOR_STAGE_5_CANDIDATE",
        "capture reuse is not authorized",
    )
    require(sha256(CAPTURE) == provenance["capture_receipt_sha256"], "capture receipt digest differs")
    require(sha256(SIGNER) == provenance["protected_signer_status_sha256"], "signer status digest differs")
    require(sha256(FAILED_CANDIDATE) == provenance["failed_candidate_sha256"], "failed candidate digest differs")
    require(
        provenance["v7_archive_sha256_before"] == V7_ARCHIVE_SHA256
        and provenance["v7_archive_sha256_after"] == V7_ARCHIVE_SHA256,
        "capture provenance archive digest differs",
    )
    require(provenance["source_seal_before"] == provenance["source_seal_after"], "capture source seal differs")
    require(provenance["repository_code_executed"] is False, "capture executed repository code")
    require(provenance["first_capsule_redeemed"] is False, "capture redeemed its first capsule")
    require(provenance["review_status"] == "PASS_AWAITING_NILHAN_REVIEW", "capture review status differs")

    failed = EvidenceRunReceipt.model_validate_json(FAILED_CANDIDATE.read_bytes(), strict=True)
    require(failed.status == "FAIL", "historical capture candidate is not failed")
    require(failed.run_id == provenance["formal_run_id"], "capture run ID differs")
    require(failed.source_commit == provenance["formal_source_commit"], "capture source commit differs")
    require(failed.source_tree == provenance["formal_source_tree"], "capture source tree differs")
    require(failed.failure_code == provenance["failed_candidate_failure_code"], "downstream failure code differs")
    commands = {item.label: item for item in failed.commands}
    for label in (
        "structured_output_diagnostic",
        "formal_calibration_receipt",
        "protected_signer_build",
        "protected_signer_bootstrap",
        "real_v7_capture",
        "protected_signer_doctor",
        "uv_sync",
        "ruff_scoped",
        "mypy",
    ):
        require(commands[label].status == "PASS", f"historical command did not pass: {label}")
    require(commands["pytest_full"].status == "FAIL", "historical downstream pytest failure is missing")

    capture = RealCaptureReceipt.model_validate_json(CAPTURE.read_bytes(), strict=True)
    binding = ReleasedProfileBinding.model_validate_json(BINDING.read_bytes(), strict=True)
    require(capture.capture_id == provenance["capture_id"], "capture ID differs")
    require(capture.status == "PASS_AWAITING_NILHAN_REVIEW", "capture receipt status differs")
    require(capture.archive_sha256_before == V7_ARCHIVE_SHA256, "capture archive before digest differs")
    require(capture.archive_sha256_after == V7_ARCHIVE_SHA256, "capture archive after digest differs")
    require(capture.source_seal_before == capture.source_seal_after, "capture source changed")
    require(capture.profile_digest == binding.profile_digest, "capture profile binding differs")
    require(capture.settings_digest == binding.settings_digest, "capture settings binding differs")
    require(capture.human_reviewer is None, "capture falsely names Nilhan as reviewer")
    require(not capture.repository_code_executed, "capture executed repository code")
    require(not capture.provider_direct_repository_access, "provider received repository access")
    require(not capture.first_capsule_redeemed, "capture redeemed the first capsule")
    require(len(capture.facts) == 6, "capture areas are incomplete")
    signer = json.loads(SIGNER.read_text(encoding="utf-8"))
    require(signer.get("status") == "PASS", "protected signer status is not PASS")
    require(
        signer.get("assurance") == "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
        "protected signer assurance differs",
    )
    print(
        json.dumps(
            {
                "status": "PASS_QUALIFYING_REAL_CAPTURE_REUSABLE",
                "formal_run_id": failed.run_id,
                "capture_receipt_sha256": sha256(CAPTURE),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
