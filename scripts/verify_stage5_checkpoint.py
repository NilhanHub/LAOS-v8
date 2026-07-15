#!/usr/bin/env python3
"""Fail-closed verifier for the Stage 5 completion candidate checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from laos_v8.canonical import canonical_json
from laos_v8.evidence_receipts import (
    EvidenceReviewReceipt,
    EvidenceRunReceipt,
    stage5_candidate_command_policy,
)
from laos_v8.prompting import ExecutorProfile
from laos_v8.sandbox import DockerSandbox
from laos_v8.stage5_calibration import ActiveProfileInventory

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COVERAGE = {
    "S5-01": (5, "PASS_BOOTSTRAP_SIGNER"),
    "S5-02": (5, "PASS_BOOTSTRAP_SIGNER"),
    "S5-03": (5, "PASS"),
    "S5-04": (5, "PASS_PROTECTED_ENVELOPE_V2_BOOTSTRAP_TRUST_PROFILE"),
    "S5-05": (5, "PASS_AWAITING_NILHAN_REVIEW"),
    "S5-06": (6, "PASS"),
    "S5-07": (6, "PASS"),
    "S5-08": (6, "PASS"),
    "S5-09": (7, "PASS_OFFLINE_FIXTURES_NOT_RELEASED"),
    "S5-10": (7, "PASS"),
    "S5-11": (7, "PASS_AWAITING_NILHAN_REVIEW"),
    "S5-12": (8, "PASS_CAPTURE_FIXTURE_WITH_TIME_BINDING"),
    "S5-13": (8, "PASS_TEMPLATE_FIXTURE_WITH_WINDOWS_ALIAS_DEFENSE"),
    "S5-14": (8, "PASS_AWAITING_NILHAN_REVIEW"),
}
REQUIRED_CANDIDATE_ARTIFACTS = {
    "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md",
    "STAGE_5_CORE_WORKFLOW_COVERAGE.json",
    "IMPLEMENTATION_STATUS.json",
    "Evidence/DOCKER_AUTOSTART_VERIFICATION.json",
    "schemas/golden/protected-envelope-v2.json",
    "uv.lock",
}
EXPECTED_CANDIDATE_ASSURANCE = "BOOTSTRAP_BUILDER_ASSERTED_NOT_AUTHENTICATED_NOT_PRODUCTION_SIGNING"
EXPECTED_CANDIDATE_GENERATOR = "laos-stage5-candidate/1.1.0"
EXPECTED_CANDIDATE_PATH = "Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json"
EXPECTED_CANDIDATE_TAG = "stage5-security-remediation-candidate"


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed verifier arguments
        [executable, "-C", str(ROOT), *args], text=True
    ).strip()


def git_bytes(*args: str) -> bytes:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed verifier arguments
        [executable, "-C", str(ROOT), *args]
    )


def verify_candidate_evidence(path: Path, *, expected_source_commit: str) -> EvidenceRunReceipt:
    receipt = EvidenceRunReceipt.model_validate_json(path.read_bytes(), strict=True)
    require(receipt.stage == 5, "Candidate evidence belongs to another stage")
    require(receipt.status == "PASS_AWAITING_NILHAN_REVIEW", "Candidate evidence is not a passing review candidate")
    require(receipt.assurance == EXPECTED_CANDIDATE_ASSURANCE, "Candidate assurance boundary changed")
    require(receipt.producer_authentication == "NONE_STAGE6_OPEN", "Candidate producer assurance changed")
    require(receipt.generator_version == EXPECTED_CANDIDATE_GENERATOR, "Candidate generator version changed")
    require(receipt.source_commit == expected_source_commit, "Candidate source commit differs")
    command_policy = stage5_candidate_command_policy(receipt.run_id, expected_source_commit)
    require(
        tuple(command.label for command in receipt.commands) == tuple(command_policy),
        "Candidate command order or identities differ",
    )
    require(
        all(command.argv == command_policy[command.label] for command in receipt.commands),
        "Candidate command arguments differ",
    )
    require(
        {artifact.path for artifact in receipt.artifacts} == REQUIRED_CANDIDATE_ARTIFACTS,
        "Candidate artifacts differ",
    )
    require(receipt.source_commit is not None and receipt.source_tree is not None, "Candidate source is unbound")
    require(git("rev-parse", f"{receipt.source_commit}^{{tree}}") == receipt.source_tree, "Candidate tree mismatch")
    for artifact in receipt.artifacts:
        target = ROOT / artifact.path
        require(target.is_file(), f"Candidate artifact is missing: {artifact.path}")
        require(target.stat().st_size == artifact.bytes, f"Candidate artifact size changed: {artifact.path}")
        require(sha256(target) == artifact.sha256, f"Candidate artifact hash changed: {artifact.path}")
    return receipt


def verify_review_receipt(path: Path, candidate: EvidenceRunReceipt, candidate_path: Path) -> None:
    review = EvidenceReviewReceipt.model_validate_json(path.read_bytes(), strict=True)
    require(review.reviewed_run_id == candidate.run_id, "Review targets another evidence run")
    require(review.evidence_receipt_sha256 == sha256(candidate_path), "Review evidence digest mismatch")
    require(review.reviewed_candidate_tag == EXPECTED_CANDIDATE_TAG, "Review tag changed")
    tagged_commit = git("rev-parse", f"{review.reviewed_candidate_tag}^{{commit}}")
    require(
        tagged_commit == review.reviewed_candidate_commit,
        "Review candidate tag does not resolve to its recorded commit",
    )
    parent_row = git("rev-list", "--parents", "-n", "1", tagged_commit).split()
    require(len(parent_row) == 2, "Review candidate commit must have exactly one parent")
    require(parent_row[1] == candidate.source_commit, "Review candidate parent is not the source commit")
    try:
        relative_candidate = candidate_path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise AssertionError("Review candidate receipt must be repository-bound") from exc
    require(relative_candidate == EXPECTED_CANDIDATE_PATH, "Review candidate receipt path changed")
    tagged_receipt = git_bytes("show", f"{tagged_commit}:{relative_candidate}")
    require(hashlib.sha256(tagged_receipt).hexdigest() == sha256(candidate_path), "Tagged candidate receipt differs")
    raise AssertionError("PROTECTED_NILHAN_REVIEW_AUTHENTICATION_NOT_IMPLEMENTED")


def verify() -> list[str]:
    checks: list[str] = []
    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_4_status"] == "COMPLETE", "Stage 4 is not complete")
    require(status["stage_5_status"] in {"IN_PROGRESS", "COMPLETE"}, "Stage 5 checkpoint status changed")
    stage5_complete = status["stage_5_status"] == "COMPLETE"
    expected_program_states = {
        (
            "STAGE_5_COMPLETION_CANDIDATE_RERUN_REQUIRED_FULL_V8_RUNTIME_NOT_IMPLEMENTED",
            "COMPLETION_CANDIDATE_RERUN_REQUIRED",
        ),
        (
            "STAGE_5_COMPLETION_CANDIDATE_PASS_AWAITING_NILHAN_REVIEW_FULL_V8_RUNTIME_NOT_IMPLEMENTED",
            "COMPLETION_CANDIDATE_PASS_AWAITING_NILHAN_REVIEW",
        ),
    }
    if stage5_complete:
        require(
            status["stage_5_checkpoint"] == "COMPLETE_NILHAN_APPROVED"
            and status["stage_6_status"]
            in {
                "PLANNED",
                "IN_PROGRESS_AWAITING_PROTECTED_REVIEW",
                "PASS_AWAITING_NILHAN_PROTECTED_REVIEW",
                "COMPLETE",
            },
            "completed Stage 5 program status differs",
        )
        require(status["stage_5_open_gates"] == [], "completed Stage 5 retains an open gate")
        review = load("Evidence/STAGE_5_REVIEW.json")
        require(
            review["status"] == "APPROVED_COMPLETE" and review["reviewer"] == "Nilhan",
            "Stage 5 completion lacks Nilhan approval",
        )
        require(
            review["candidate_receipt_sha256"] == sha256(ROOT / "Evidence/STAGE_5_COMPLETION_CANDIDATE.json"),
            "Stage 5 completion review targets another candidate",
        )
    else:
        require(
            (status["status"], status["stage_5_checkpoint"]) in expected_program_states,
            "program status overclaims or omits the Stage 5 candidate state",
        )
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "v8 overclaim")
    required_open = {
        "PROTECTED_SIGNING_CUSTODY",
        "RELEASED_PROFILE_REAL_CALIBRATION",
        "REAL_WEAKER_INVESTIGATOR_CAPTURE_ROUND_TRIP",
    }
    if not stage5_complete:
        require(set(status["stage_5_open_gates"]) == required_open, "Stage 5 open gates changed")
    checks.append("program_truth")

    stage = next(item for item in load("PROGRAM_STAGE_LEDGER.json")["stages"] if item["stage"] == 5)
    require(
        stage["status"]
        in {
            "IN_PROGRESS_COMPLETION_CANDIDATE_RERUN_REQUIRED",
            "IN_PROGRESS_COMPLETION_CANDIDATE_AWAITING_NILHAN_REVIEW",
            "COMPLETED",
        },
        "Stage 5 ledger status is not a permitted in-progress candidate state",
    )
    require(stage["owner"] == "Codex" and stage["independent_reviewer"] == "Nilhan", "roles changed")
    checks.append("governance")

    coverage = load("STAGE_5_CORE_WORKFLOW_COVERAGE.json")
    rows = coverage["coverage"]
    identifiers = [row["id"] for row in rows]
    require(len(identifiers) == len(set(identifiers)), "Stage 5 coverage contains duplicate criteria")
    require(set(identifiers) == set(EXPECTED_COVERAGE), "Stage 5 coverage criterion identities changed")
    expected_coverage = dict(EXPECTED_COVERAGE)
    if stage5_complete:
        for identifier in ("S5-05", "S5-11", "S5-14"):
            expected_coverage[identifier] = (expected_coverage[identifier][0], "PASS_NILHAN_APPROVED")
    require(
        all((row["milestone"], row["status"]) == expected_coverage[row["id"]] for row in rows),
        "Stage 5 milestone ownership or status changed",
    )
    plan_digest = sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md")
    require(coverage.get("authority_sha256") == plan_digest, "Stage 5 coverage is not bound to the active plan")
    checks.append("milestone_coverage")

    fixture = load("profiles/OFFLINE_EXECUTOR_PROFILES.json")
    profiles = tuple(
        ExecutorProfile.model_validate_json(canonical_json(item), strict=True) for item in fixture["profiles"]
    )
    require(len(profiles) == 7 and len({item.executor_class for item in profiles}) == 7, "profile classes incomplete")
    require(all(not item.released for item in profiles), "an uncalibrated profile was released")
    require(
        fixture["assurance"] == "OFFLINE_FIXTURES_NOT_RELEASED_NOT_CALIBRATED",
        "profile assurance overclaim",
    )
    active = ActiveProfileInventory.model_validate_json(
        (ROOT / "profiles/ACTIVE_EXECUTOR_PROFILES.json").read_bytes(), strict=True
    )
    require(sum(item.released for item in active.profiles) == 1, "active profile release count differs")
    checks.append("offline_profiles_and_one_calibrated_active_profile")

    expected_modules = {
        "src/laos_v8/action_engine.py",
        "src/laos_v8/capture.py",
        "src/laos_v8/new_build.py",
        "src/laos_v8/packs.py",
        "src/laos_v8/prompting.py",
        "src/laos_v8/trust.py",
    }
    require(all((ROOT / path).is_file() for path in expected_modules), "Stage 5 module missing")
    require((ROOT / "Evidence/STAGE_5_IMPLEMENTATION_CHECKPOINT.md").is_file(), "checkpoint evidence missing")
    checks.append("implementation_presence")

    readiness = DockerSandbox().ensure_available()
    require(readiness.available and bool(readiness.server_version), "Docker engine is not currently ready")
    checks.append("automatic_docker_dependency_live")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-evidence", type=Path)
    parser.add_argument("--expected-source-commit")
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--require-review", action="store_true")
    args = parser.parse_args()
    try:
        checks = verify()
        program = load("IMPLEMENTATION_STATUS.json")
        if program["stage_5_checkpoint"] == "COMPLETE_NILHAN_APPROVED":
            status = "PASS_STAGE_5_COMPLETE_NILHAN_APPROVED"
        else:
            status = (
                "PASS_STAGE_5_COMPLETION_CANDIDATE_AWAITING_NILHAN_REVIEW"
                if program["stage_5_checkpoint"] == "COMPLETION_CANDIDATE_PASS_AWAITING_NILHAN_REVIEW"
                else "PASS_STAGE_5_COMPLETION_CANDIDATE_RERUN_REQUIRED"
            )
        candidate = None
        if args.candidate_evidence is not None:
            require(args.expected_source_commit is not None, "Candidate evidence requires an expected source commit")
            candidate_path = args.candidate_evidence.resolve()
            candidate = verify_candidate_evidence(
                candidate_path,
                expected_source_commit=args.expected_source_commit,
            )
            checks.append("candidate_evidence_revision_and_hash_binding")
            status = "PASS_AWAITING_NILHAN_REVIEW"
        if args.require_review:
            require(candidate is not None and args.candidate_evidence is not None, "Review requires candidate evidence")
            require(args.review_receipt is not None, "Nilhan review receipt is required")
            verify_review_receipt(args.review_receipt.resolve(), candidate, args.candidate_evidence.resolve())
        elif args.review_receipt is not None:
            raise AssertionError("Review receipt requires --require-review")
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
