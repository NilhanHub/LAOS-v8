#!/usr/bin/env python3
"""Reconcile Stage 6 implementation truth without closing release blockers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md"
PLAN_DIGEST = hashlib.sha256(PLAN.read_bytes()).hexdigest()
PLAN_QUALIFIED = f"sha256:{PLAN_DIGEST}"
DATE = "2026-07-15"

CATEGORY_EVIDENCE = {
    "COMMAND_SANDBOX": [
        "src/laos_v8/sandbox.py",
        "src/laos_v8/clean_verifier.py",
        "tests/stage6/test_sandbox_assurance.py",
    ],
    "CRITERIA": [
        "src/laos_v8/criterion_closure.py",
        "tests/stage6/test_criterion_and_review.py",
    ],
    "EVIDENCE": [
        "src/laos_v8/evidence_custody.py",
        "src/laos_v8/custody_service.py",
        "custodian/Dockerfile",
        "tests/stage6/test_evidence_custody.py",
    ],
    "REVIEW": [
        "src/laos_v8/protected_review.py",
        "src/laos_v8/protected_checks.py",
        "tests/stage6/test_protected_checks.py",
        "tests/stage6/test_criterion_and_review.py",
    ],
    "TESTING": [
        "tests/stage6/test_sandbox_assurance.py",
        "tests/stage6/test_evidence_custody.py",
        "tests/stage6/test_protected_checks.py",
        "tests/stage6/test_criterion_and_review.py",
    ],
    "REVISION_1_1": [
        "src/laos_v8/sandbox.py",
        "src/laos_v8/evidence_custody.py",
        "src/laos_v8/protected_review.py",
        "scripts/verify_stage6_controls.py",
    ],
}

BLOCKER_EVIDENCE = {
    "RB-011": ["src/laos_v8/protected_review.py", "tests/stage6/test_criterion_and_review.py"],
    "RB-012": [
        "src/laos_v8/criterion_closure.py",
        "src/laos_v8/protected_checks.py",
        "tests/stage6/test_protected_checks.py",
    ],
    "RB-013": ["src/laos_v8/sandbox.py", "src/laos_v8/clean_verifier.py", "tests/stage6/test_sandbox_assurance.py"],
    "RB-014": ["src/laos_v8/sandbox.py", "src/laos_v8/custody_service.py", "tests/stage6/test_evidence_custody.py"],
}


def _load(name: str) -> dict[str, Any]:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} is not an object")
    return value


def _write(name: str, value: dict[str, Any]) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def _digest(path: str) -> str:
    return "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def reconcile_requirements() -> list[dict[str, Any]]:
    ledger = _load("REQUIREMENTS_LEDGER.json")
    rows = [item for item in ledger["requirements"] if 6 in item.get("implementation_stages", [])]
    if len(rows) != 49:
        raise RuntimeError(f"expected 49 Stage 6 requirements, found {len(rows)}")
    coverage: list[dict[str, Any]] = []
    for item in rows:
        if item["id"] == "REQ-REVISION_1_1-010":
            status = "OPEN_CROSS_SUBSYSTEM_OR_LATER_INTEGRATION_REAL_SECRETS_DENIED"
        elif item["id"] == "REQ-REVISION_1_1-009":
            status = "IMPLEMENTED_FAIL_CLOSED_LOCAL_PROFILE_AWAITING_NILHAN_PROTECTED_REVIEW"
        else:
            status = "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
        evidence = CATEGORY_EVIDENCE[item["category"]]
        item["status"] = status
        item["evidence_status"] = status
        item["independent_reviewer"] = "Nilhan"
        item["stage_6_evidence"] = evidence
        coverage.append(
            {
                "requirement_id": item["id"],
                "category": item["category"],
                "status": status,
                "owner": "Codex",
                "independent_reviewer": "Nilhan",
                "evidence": evidence,
            }
        )
    ledger["reconciled_on"] = DATE
    ledger["stage_6_status"] = "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
    _write("REQUIREMENTS_LEDGER.json", ledger)
    return coverage


def reconcile_ledgers(coverage: list[dict[str, Any]]) -> None:
    program = _load("PROGRAM_STAGE_LEDGER.json")
    stage = next(item for item in program["stages"] if item["stage"] == 6)
    stage["status"] = "IN_PROGRESS_AWAITING_PROTECTED_REVIEW"
    stage["candidate_evidence"] = "Evidence/STAGE_6_COMPLETION_CANDIDATE.json"
    stage["review_challenge"] = "Evidence/STAGE_6_REVIEW_CHALLENGE.json"
    _write("PROGRAM_STAGE_LEDGER.json", program)

    backlog = _load("IMPLEMENTATION_BACKLOG.json")
    stage_backlog = next(item for item in backlog["stages"] if item["stage"] == 6)
    stage_backlog["status"] = "IN_PROGRESS_AWAITING_PROTECTED_REVIEW"
    for task in stage_backlog["tasks"]:
        task["status"] = (
            "AWAITING_NILHAN_PROTECTED_REVIEW" if task["id"] == "S6-REVIEW" else "IMPLEMENTED_AWAITING_REVIEW"
        )
    _write("IMPLEMENTATION_BACKLOG.json", backlog)

    milestones = _load("MILESTONE_LEDGER.json")
    for item in milestones["milestones"]:
        if item["milestone"] in {9, 10, 11}:
            item["stage_6_status"] = "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
            item["open_cross_subsystem_requirements"] = True
            item["stage_6_evidence"] = "STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json"
    _write("MILESTONE_LEDGER.json", milestones)

    scope = _load("SCOPE_LEDGER.json")
    capability = next(
        item for item in scope["capabilities"] if item["capability"] == "action_evidence_review_promotion"
    )
    capability["status"] = "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
    capability["evidence"] = ["STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json"]
    _write("SCOPE_LEDGER.json", scope)

    blockers = _load("RELEASE_BLOCKERS.json")
    blockers["stage_6_candidate"] = "AWAITING_PROTECTED_REVIEW"
    for item in blockers["blockers"]:
        if item["id"] in BLOCKER_EVIDENCE:
            item["status"] = "OPEN"
            item["independent_verifier"] = "NILHAN_PROTECTED_REVIEW_PENDING"
            item["stage_6_mitigation_status"] = "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
            item["stage_6_evidence"] = BLOCKER_EVIDENCE[item["id"]]
            item["evidence_digests"] = [_digest(path) for path in BLOCKER_EVIDENCE[item["id"]]]
    _write("RELEASE_BLOCKERS.json", blockers)

    adrs = _load("ADR_REGISTER.json")
    for item in adrs["adrs"]:
        if item["id"] == "ADR-0006":
            item["status"] = "ACCEPTED_STAGE6_DOCKER_PROVIDER_EXERCISED_AWAITING_PROTECTED_REVIEW"
        elif item["id"] == "ADR-0014":
            item["status"] = "ACCEPTED_STAGE6_ENCRYPTED_CUSTODY_AWAITING_PROTECTED_REVIEW"
        elif item["id"] == "ADR-0005":
            item["status"] = "ACCEPTED_STAGE6_PASSPHRASE_REVIEW_AUTHENTICATION_AWAITING_ENROLLMENT"
    _write("ADR_REGISTER.json", adrs)

    environments = _load("SUPPORTED_ENVIRONMENTS.json")
    environments["claim_status"] = (
        "STAGE_6_WINDOWS_DOCKER_CANDIDATE_AWAITING_PROTECTED_REVIEW_PRODUCTION_UNCLAIMED"
    )
    rows = environments["rows"]
    rows[:] = [item for item in rows if item["id"] != "docker-desktop-linux-amd64-stage6"]
    rows.append(
        {
            "id": "docker-desktop-linux-amd64-stage6",
            "status": "LOCAL_LOW_MODERATE_PROVIDER_EXERCISED_AWAITING_PROTECTED_REVIEW",
            "privileged_connected_mode": True,
            "maximum_risk": "MODERATE",
            "high_critical_status": "DENIED_QUORUM_UNAVAILABLE",
            "real_credentials": "DENIED",
            "evidence": ["STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json", "Evidence/STAGE_6_COMPLETION_CANDIDATE.json"],
        }
    )
    _write("SUPPORTED_ENVIRONMENTS.json", environments)

    threats = _load("THREAT_REGISTER.json")
    threats["stage_6_execution_assurance"] = {
        "status": "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW",
        "covered_release_blockers": ["RB-011", "RB-012", "RB-013", "RB-014"],
        "evidence": ["STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json"],
    }
    keywords = ("sandbox", "evidence", "review", "credential", "secret", "network", "quorum", "shell")
    for item in threats["threats"]:
        text = json.dumps(item).casefold()
        if any(keyword in text for keyword in keywords):
            item["stage_6_status"] = "CONTROL_IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"
    _write("THREAT_REGISTER.json", threats)

    migration = _load("MIGRATION_MATRIX.json")
    migration["stage_6_execution_assurance"] = {
        "historical_criterion_states": "READABLE_NOT_REWRITTEN",
        "ambiguous_migration": "MIGRATION_EVIDENCE_REQUIRED",
        "new_criterion_lifecycle": "CRITERION_V2",
        "evidence_custody": "ENCRYPTED_DOCKER_VOLUME_WITH_SIGNED_PROJECT_INDEX",
        "status": "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW",
    }
    _write("MIGRATION_MATRIX.json", migration)

    coverage_record = {
        "record_version": "1.0.0",
        "authority": "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md Revision 1.1",
        "authority_sha256": PLAN_DIGEST,
        "stage": 6,
        "milestones": [9, 10, 11],
        "status": "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW",
        "requirement_count": len(coverage),
        "requirements": coverage,
        "release_blockers": [
            {"id": blocker_id, "status": "OPEN", "mitigation": "IMPLEMENTED_AWAITING_NILHAN_PROTECTED_REVIEW"}
            for blocker_id in BLOCKER_EVIDENCE
        ],
        "boundaries": {
            "new_model_profile_released": False,
            "qualifying_sandbox_provider": "Docker only",
            "maximum_supported_risk": "MODERATE",
            "high_critical_operations": "DENIED_QUORUM_UNAVAILABLE",
            "real_credentials": "DENIED",
            "release_blockers_closed": False,
        },
    }
    _write("STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json", coverage_record)


def reconcile_status() -> None:
    status = _load("IMPLEMENTATION_STATUS.json")
    status["status"] = "STAGE_6_IN_PROGRESS_AWAITING_PROTECTED_REVIEW_FULL_V8_RUNTIME_NOT_IMPLEMENTED"
    status["milestone"] = 11
    status["milestone_name"] = "Verification depth and independent review"
    status["next_milestone"] = 12
    status["stage_6_status"] = "IN_PROGRESS_AWAITING_PROTECTED_REVIEW"
    status["stage_6_requirements"] = 49
    status["stage_6_release_blockers_mitigated_but_open"] = ["RB-011", "RB-012", "RB-013", "RB-014"]
    status["stage_6_review_assurance"] = "PASSPHRASE_PROTECTED_OPENSSH_ED25519_PENDING_NILHAN_ENROLLMENT"
    status["stage_7_status"] = "PLANNED"
    status["v8_runtime_exists"] = False
    status["v8_release_exists"] = False
    _write("IMPLEMENTATION_STATUS.json", status)


def main() -> int:
    coverage = reconcile_requirements()
    reconcile_ledgers(coverage)
    reconcile_status()
    print(json.dumps({"status": "PASS", "stage": 6, "requirements": len(coverage), "plan": PLAN_QUALIFIED}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
