#!/usr/bin/env python3
"""Fail-closed verifier for Nilhan-approved Stage 5 completion."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from laos_v8.evidence_receipts import EvidenceRunReceipt

ROOT = Path(__file__).resolve().parents[1]
PLAN_SHA256 = "d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729"
CANDIDATE_PATH = "Evidence/STAGE_5_COMPLETION_CANDIDATE.json"
REVIEW_PATH = "Evidence/STAGE_5_REVIEW.json"
EXPECTED_GATES = {
    "PROTECTED_SIGNING_CUSTODY",
    "RELEASED_PROFILE_REAL_CALIBRATION",
    "REAL_WEAKER_INVESTIGATOR_CAPTURE_ROUND_TRIP",
}
EXPECTED_REVIEW_KEYS = {
    "record_version",
    "stage",
    "status",
    "reviewer",
    "reviewer_role",
    "reviewed_candidate_run_id",
    "reviewed_candidate_source_commit",
    "reviewed_candidate_evidence_commit",
    "reviewed_candidate_tag",
    "candidate_receipt_sha256",
    "decision_recorded_at_utc",
    "approval_statement",
    "scope",
    "cleared_stage_5_gates",
    "does_not_approve",
    "assurance",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved Git and fixed verifier arguments
        [executable, "-C", str(ROOT), *args], text=True
    ).strip()


def git_bytes(*args: str) -> bytes:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved Git and fixed verifier arguments
        [executable, "-C", str(ROOT), *args]
    )


def verify(completion_tag: str | None = None) -> list[str]:
    checks: list[str] = []
    require(sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md") == PLAN_SHA256, "active plan differs")

    candidate_path = ROOT / CANDIDATE_PATH
    candidate = EvidenceRunReceipt.model_validate_json(candidate_path.read_bytes(), strict=True)
    require(candidate.status == "PASS_AWAITING_NILHAN_REVIEW", "immutable candidate status differs")
    require(candidate.run_id == "run:ea3248f8ede94973ae669ded5fa3c30f", "candidate run differs")
    require(candidate.source_commit == "7497d149281e9e6924bf79cc22c2c89ea51f8dfe", "candidate source differs")
    require(
        len(candidate.commands) == 20 and all(item.status == "PASS" for item in candidate.commands),
        "candidate gates differ",
    )
    for artifact in candidate.artifacts:
        path = ROOT / artifact.path
        require(path.is_file(), f"candidate artifact missing: {artifact.path}")
        require(path.stat().st_size == artifact.bytes, f"candidate artifact size differs: {artifact.path}")
        require(sha256(path) == artifact.sha256, f"candidate artifact digest differs: {artifact.path}")
    checks.append("immutable_passing_candidate")

    review = load(REVIEW_PATH)
    require(isinstance(review, dict) and set(review) == EXPECTED_REVIEW_KEYS, "Stage 5 review shape differs")
    require(review["stage"] == 5 and review["status"] == "APPROVED_COMPLETE", "Stage 5 review decision differs")
    require(review["reviewer"] == "Nilhan", "Stage 5 reviewer differs")
    require(
        review["reviewer_role"] == "SOLE_HUMAN_REVIEWER_INDEPENDENT_FROM_CODEX_IMPLEMENTER",
        "reviewer role differs",
    )
    require(review["reviewed_candidate_run_id"] == candidate.run_id, "reviewed run differs")
    require(review["reviewed_candidate_source_commit"] == candidate.source_commit, "reviewed source differs")
    require(review["candidate_receipt_sha256"] == sha256(candidate_path), "reviewed receipt digest differs")
    require(set(review["cleared_stage_5_gates"]) == EXPECTED_GATES, "cleared Stage 5 gates differ")
    require(review["scope"] == "STAGE_5_COMPLETION_ONLY", "review scope differs")
    require("LAOS_V8_RELEASE" in review["does_not_approve"], "release exclusion is missing")
    require(
        review["assurance"] == "BOOTSTRAP_HUMAN_REVIEW_PROVENANCE_STAGE6_PROTECTED_AUTHENTICATION_OPEN",
        "review assurance differs",
    )
    tagged_candidate = git("rev-parse", f"{review['reviewed_candidate_tag']}^{{commit}}")
    require(tagged_candidate == review["reviewed_candidate_evidence_commit"], "candidate tag target differs")
    require(git("rev-parse", f"{tagged_candidate}^") == candidate.source_commit, "candidate tag parent differs")
    tagged_receipt = git_bytes("show", f"{tagged_candidate}:{CANDIDATE_PATH}")
    require(hashlib.sha256(tagged_receipt).hexdigest() == sha256(candidate_path), "tagged candidate receipt differs")
    checks.append("nilhan_review_candidate_binding")

    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_5_status"] == "COMPLETE", "Stage 5 is not complete")
    require(status["stage_6_status"] == "PLANNED", "Stage 6 status differs")
    require(status["stage_5_checkpoint"] == "COMPLETE_NILHAN_APPROVED", "Stage 5 checkpoint differs")
    require(status["stage_5_open_gates"] == [], "Stage 5 gates remain open")
    require(set(status["stage_5_gate_evidence_status"]) == EXPECTED_GATES, "Stage 5 gate identities differ")
    require(
        all(
            value == "PASS_NILHAN_APPROVED_COMPLETE"
            for value in status["stage_5_gate_evidence_status"].values()
        ),
        "Stage 5 gate status differs",
    )
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "v8 completion overclaim")
    checks.append("program_truth_stage5_complete_v8_unreleased")

    stage_ledger = load("PROGRAM_STAGE_LEDGER.json")
    stage5 = next(item for item in stage_ledger["stages"] if item["stage"] == 5)
    stage6 = next(item for item in stage_ledger["stages"] if item["stage"] == 6)
    require(stage5["status"] == "COMPLETED" and stage6["status"] == "PLANNED", "stage ledger transition differs")
    require(stage5["owner"] == "Codex" and stage5["independent_reviewer"] == "Nilhan", "Stage 5 roles differ")

    coverage = load("STAGE_5_CORE_WORKFLOW_COVERAGE.json")
    rows = {item["id"]: item for item in coverage["coverage"]}
    require(coverage["assurance"] == "STAGE_5_COMPLETE_NILHAN_APPROVED", "coverage assurance differs")
    for identifier in ("S5-05", "S5-11", "S5-14"):
        require(rows[identifier]["status"] == "PASS_NILHAN_APPROVED", f"{identifier} review status differs")

    blockers = load("RELEASE_BLOCKERS.json")
    require(len(blockers["blockers"]) == 25, "release blocker count differs")
    require(all(item["status"] == "OPEN" for item in blockers["blockers"]), "a release blocker was closed early")
    require(
        blockers["stage_5_completion_candidate"]["cleared_release_blockers"] == [],
        "Stage 5 cleared a release blocker",
    )
    for relative in (
        "ADR_REGISTER.json",
        "KNOWN_DEFECTS.md",
        "MIGRATION_MATRIX.json",
        "RELEASE_BLOCKERS.json",
        "THREAT_REGISTER.json",
    ):
        require(
            "AWAITING_NILHAN_REVIEW" not in (ROOT / relative).read_text(encoding="utf-8"),
            f"current Stage 5 ledger still awaits Nilhan review: {relative}",
        )
    checks.append("coverage_and_later_gates_preserved")

    if completion_tag is not None:
        completion_commit = git("rev-parse", f"{completion_tag}^{{commit}}")
        require(git("rev-parse", f"{completion_commit}^") == tagged_candidate, "completion tag parent differs")
        tagged_review = git_bytes("show", f"{completion_commit}:{REVIEW_PATH}")
        require(hashlib.sha256(tagged_review).hexdigest() == sha256(ROOT / REVIEW_PATH), "tagged review differs")
        tagged_status = git_bytes("show", f"{completion_commit}:IMPLEMENTATION_STATUS.json")
        require(
            hashlib.sha256(tagged_status).hexdigest() == sha256(ROOT / "IMPLEMENTATION_STATUS.json"),
            "tagged status differs",
        )
        checks.append("stage5_complete_tag_binding")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--completion-tag")
    args = parser.parse_args()
    try:
        checks = verify(args.completion_tag)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "PASS_STAGE_5_COMPLETE_NILHAN_APPROVED", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
