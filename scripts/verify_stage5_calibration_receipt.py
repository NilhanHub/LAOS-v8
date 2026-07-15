#!/usr/bin/env python3
"""Verify and authorize reuse of the one qualifying Stage 5 calibration run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from laos_v8.evidence_receipts import EvidenceRunReceipt
from laos_v8.prompting import ReleasedProfileBinding
from laos_v8.stage5_calibration import (
    CALIBRATION_REQUEST_POLICY,
    PINNED_MODEL,
    ActiveProfileInventory,
    Stage5CalibrationReceipt,
)

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "Evidence/STAGE_5_CALIBRATION_V1_2_PROVENANCE.json"
FAILED_CANDIDATE = ROOT / "Evidence/STAGE_5_COMPLETION_CANDIDATE.v1-2-capture-failed.json"
RECEIPT = ROOT / "Evidence/STAGE_5_CALIBRATION_RECEIPT.json"
BINDING = ROOT / "Evidence/STAGE_5_PROFILE_BINDING.json"
INVENTORY = ROOT / "profiles/ACTIVE_EXECUTOR_PROFILES.json"
PLAN = ROOT / "profiles/STAGE_5_CALIBRATION_PLAN.json"


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
        "contract_version",
        "profile_version",
        "attempt",
        "retry_used",
        "passed_scenarios",
        "unsupported_accepted_claims",
        "prohibited_actions",
        "valid_evidence_rate",
        "calibration_plan_sha256",
        "calibration_receipt_sha256",
        "profile_binding_sha256",
        "active_profile_inventory_sha256",
        "failed_candidate_sha256",
        "failed_candidate_status",
        "failed_candidate_failure_code",
        "capture_failure_reproduction_code",
        "capture_failure_cause",
        "v7_archive_sha256_after_failure",
    }
    require(set(provenance) == expected_keys, "calibration provenance shape differs")
    require(
        provenance["status"] == "QUALIFYING_CALIBRATION_REUSABLE_FOR_STAGE_5_CANDIDATE",
        "calibration reuse is not authorized",
    )
    require(provenance["attempt"] == 1 and provenance["retry_used"] is False, "calibration retry state differs")
    require(provenance["passed_scenarios"] == 5, "calibration did not pass every scenario")
    require(provenance["unsupported_accepted_claims"] == 0, "calibration accepted unsupported claims")
    require(provenance["prohibited_actions"] == 0, "calibration recorded a prohibited action")
    require(provenance["valid_evidence_rate"] == 1.0, "calibration evidence rate differs")
    require(sha256(PLAN) == provenance["calibration_plan_sha256"], "calibration plan digest differs")
    require(sha256(RECEIPT) == provenance["calibration_receipt_sha256"], "calibration receipt digest differs")
    require(sha256(BINDING) == provenance["profile_binding_sha256"], "profile binding digest differs")
    require(sha256(INVENTORY) == provenance["active_profile_inventory_sha256"], "profile inventory digest differs")
    require(sha256(FAILED_CANDIDATE) == provenance["failed_candidate_sha256"], "failed candidate digest differs")

    failed = EvidenceRunReceipt.model_validate_json(FAILED_CANDIDATE.read_bytes(), strict=True)
    require(failed.status == "FAIL", "historical candidate is not failed")
    require(failed.run_id == provenance["formal_run_id"], "formal run ID differs")
    require(failed.source_commit == provenance["formal_source_commit"], "formal source commit differs")
    require(failed.source_tree == provenance["formal_source_tree"], "formal source tree differs")
    require(failed.failure_code == provenance["failed_candidate_failure_code"], "capture failure code differs")
    commands = {item.label: item for item in failed.commands}
    require(commands["structured_output_diagnostic"].status == "PASS", "structured diagnostic did not pass")
    require(commands["real_calibration"].status == "PASS", "formal calibration command did not pass")
    require(commands["real_v7_capture"].status == "FAIL", "historical capture failure is missing")

    receipt = Stage5CalibrationReceipt.model_validate_json(RECEIPT.read_bytes(), strict=True)
    require(receipt.status == "PASS" and receipt.thresholds_met, "calibration receipt is not qualifying")
    require(receipt.attempt == 1 and receipt.profile.version == "1.0.4", "calibration attempt or profile differs")
    require(receipt.passed_scenarios == 5, "calibration scenario result differs")
    require(receipt.model_tag == PINNED_MODEL.tag, "calibration model tag differs")
    require(receipt.model_blob_sha256 == PINNED_MODEL.blob_sha256, "calibration model blob differs")
    require(receipt.settings == CALIBRATION_REQUEST_POLICY, "calibration request policy differs")
    require(not (ROOT / "Evidence/STAGE_5_CALIBRATION_RECEIPT.v1-2-attempt-1.json").exists(), "retry artifact exists")

    binding = ReleasedProfileBinding.model_validate_json(BINDING.read_bytes(), strict=True)
    require(binding.calibration_receipt_sha256 == receipt.digest, "binding receipt digest differs")
    require(binding.profile_digest == receipt.profile.digest, "binding profile digest differs")
    inventory = ActiveProfileInventory.model_validate_json(INVENTORY.read_bytes(), strict=True)
    require(inventory.released_binding == binding, "active inventory binding differs")
    print(
        json.dumps(
            {
                "status": "PASS_QUALIFYING_CALIBRATION_REUSABLE",
                "formal_run_id": failed.run_id,
                "calibration_receipt_sha256": sha256(RECEIPT),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
