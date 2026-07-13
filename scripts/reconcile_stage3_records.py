#!/usr/bin/env python3
"""Reconcile machine-readable records with the Stage 3 Security Spine review candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write(name: str, value: object) -> None:
    (ROOT / name).write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def update_status() -> None:
    status = load("IMPLEMENTATION_STATUS.json")
    status.update(
        {
            "milestone": 4,
            "milestone_name": "Mandatory Security Spine through policy and risk classification",
            "next_milestone": 5,
            "stage_3_status": "AWAITING_NILHAN_REVIEW",
            "status": "STAGE_3_REVIEW_CANDIDATE_LOCAL_SECURITY_SPINE_IMPLEMENTED_FULL_V8_RUNTIME_NOT_IMPLEMENTED",
            "security_spine_exists": True,
            "security_spine_assurance": "LOCAL_TEST_PROFILE_AWAITING_INDEPENDENT_REVIEW",
            "real_weaker_agent_executed": False,
            "v8_runtime_exists": False,
            "v8_release_exists": False,
        }
    )
    write("IMPLEMENTATION_STATUS.json", status)


def update_program() -> None:
    ledger = load("PROGRAM_STAGE_LEDGER.json")
    stage3 = next(row for row in ledger["stages"] if row["stage"] == 3)
    stage3.update(
        {
            "status": "REVIEW_CANDIDATE",
            "owner": "Codex",
            "independent_reviewer": "Nilhan",
            "evidence_policy": "BOOTSTRAP_NOT_PRODUCTION_SIGNING",
        }
    )
    write("PROGRAM_STAGE_LEDGER.json", ledger)

    backlog = load("IMPLEMENTATION_BACKLOG.json")
    stage3_backlog = next(row for row in backlog["stages"] if row["stage"] == 3)
    stage3_backlog["status"] = "REVIEW_CANDIDATE"
    for task in stage3_backlog["tasks"]:
        if task["id"] in {"S3-CONTRACT", "S3-EVIDENCE"}:
            task["status"] = "COMPLETED"
        elif task["id"] == "S3-REVIEW":
            task["status"] = "AWAITING_NILHAN_REVIEW"
    write("IMPLEMENTATION_BACKLOG.json", backlog)

    milestones = load("MILESTONE_LEDGER.json")
    for number in (3, 4):
        row = next(item for item in milestones["milestones"] if item["milestone"] == number)
        row.update(
            {
                "owner": "Codex",
                "independent_reviewer": "Nilhan",
                "estimate_range": "Implemented for the local Stage 3 test profile; awaiting independent review.",
                "required_evidence": (
                    "Bootstrap adversarial tests, Docker profile, transactional state, clean reconstruction, "
                    "and Nilhan review."
                ),
                "open_cross_subsystem_requirements": True,
            }
        )
    write("MILESTONE_LEDGER.json", milestones)


def update_requirements() -> None:
    implemented = {
        "REQ-TRUST_ZONES-005",
        "REQ-TRUST_ZONES-006",
        "REQ-TRUST_ZONES-007",
        "REQ-TRUST_ZONES-008",
        *(f"REQ-REPOSITORY_TRUTH-{number:03d}" for number in (1, 2, 3, 5, 6, 7, 8)),
        *(f"REQ-PATHS_ARCHIVES-{number:03d}" for number in (1, 2, 3, 4, 5, 7, 8)),
        *(f"REQ-STATE_CONCURRENCY-{number:03d}" for number in (1, 4, 6, 7, 8, 9)),
        *(f"REQ-IDENTITY_PROVENANCE-{number:03d}" for number in (1, 2, 3, 4, 5, 6, 8)),
        *(f"REQ-COMMAND_SANDBOX-{number:03d}" for number in (1, 3, 4, 5, 6, 7, 8, 9)),
        "REQ-REVISION_1_1-003",
        "REQ-REVISION_1_1-007",
        "REQ-REVISION_1_1-012",
        "REQ-REVISION_1_1-019",
    }
    evidence = [
        "docs/STAGE_3_ENFORCEMENT_CONTRACT.md",
        "PERMISSION_ENFORCEMENT_MATRIX.json",
        "SANDBOX_PROFILE.json",
        "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json",
        "Evidence/STAGE_3_VERIFICATION.json",
        "docs/STAGE_3_OPERATOR_PATHS.md",
        "tests/stage3",
    ]
    ledger = load("REQUIREMENTS_LEDGER.json")
    for requirement in ledger["requirements"]:
        if requirement["id"] == "REQ-REVISION_1_1-031" and 3 not in requirement["implementation_stages"]:
            requirement["implementation_stages"] = sorted([*requirement["implementation_stages"], 3])
        if 3 not in requirement["implementation_stages"]:
            continue
        requirement["owner"] = "Codex"
        requirement["independent_reviewer"] = "Nilhan"
        if requirement["id"] in implemented:
            requirement["status"] = "IMPLEMENTED_AWAITING_REVIEW"
            requirement["evidence_status"] = "BOOTSTRAP_EVIDENCE_CAPTURED"
            requirement["evidence"] = evidence
        else:
            requirement["status"] = "OPEN_CROSS_SUBSYSTEM_OR_LATER_INTEGRATION"
            requirement["evidence_status"] = "PARTIAL_STAGE_3_FOUNDATION_ONLY"
            if requirement["id"] == "REQ-REVISION_1_1-031":
                requirement["evidence_status"] = "PARTIAL_STAGE_3_PRE_ALPHA_OPERATOR_PATHS"
                requirement["evidence"] = evidence
    write("REQUIREMENTS_LEDGER.json", ledger)


def update_adrs() -> None:
    ledger = load("ADR_REGISTER.json")
    statuses = {
        "ADR-0002": "ACCEPTED_STAGE_3_LOCAL_PROFILE",
        "ADR-0003": "PARTIAL_LOCAL_STATE_MIGRATION_LIFECYCLE_OPEN",
        "ADR-0005": "PARTIAL_TEST_SIGNER_PRODUCTION_CUSTODY_OPEN",
        "ADR-0006": "ACCEPTED_DOCKER_PROFILE_EXERCISED",
        "ADR-0008": "ACCEPTED_STAGE_3_LOCAL_PROFILE",
        "ADR-0009": "PARTIAL_GIT_CAS_FOUNDATION_ALPHA_INTEGRATION_OPEN",
        "ADR-0010": "ACCEPTED_TEST_ROOT_PRODUCTION_LIFECYCLE_OPEN",
        "ADR-0012": "ACCEPTED_V8_0",
    }
    for row in ledger["adrs"]:
        if row["id"] in statuses:
            row["status"] = statuses[row["id"]]
    write("ADR_REGISTER.json", ledger)


def update_support() -> None:
    matrix = load("SUPPORTED_ENVIRONMENTS.json")
    matrix["matrix_version"] = "1.1.0"
    matrix["claim_status"] = "STAGE_3_LOCAL_SECURITY_SPINE_REVIEW_CANDIDATE_PRODUCTION_UNCLAIMED"
    matrix["security_spine_profile"] = {
        "host_os": "Windows 11",
        "filesystem": "local NTFS",
        "git": "2.53.0.windows.2",
        "python": "3.14.3 local evidence; 3.11-3.14 contract",
        "sqlite": "3.50.4 rollback-journal DELETE",
        "sandbox": "Docker Desktop 29.5.3 Linux x86_64",
        "image": "python 3.14.3 alpine3.23 linux/amd64 digest 581c1460...",
        "model_path": "local deterministic adapter only",
        "production_side_effects": "unsupported",
    }
    for row in matrix["rows"]:
        if row["id"] == "connected-windows-local-git":
            row["status"] = "LOCAL_STAGE_3_TEST_PROFILE_VERIFIED_AWAITING_REVIEW"
            row["evidence"] = [
                "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json",
                "SANDBOX_PROFILE.json",
                "docs/STAGE_3_ENFORCEMENT_CONTRACT.md",
            ]
        elif row["id"] == "connected-linux-local-git":
            row["status"] = "CI_CONFIGURED_NOT_EXECUTED_REMOTELY"
        elif row["id"] == "offline-verification-read-only":
            row["status"] = "LOCAL_CONTRACT_TESTED_PACK_INTEGRATION_OPEN"
    matrix["rows"] = [row for row in matrix["rows"] if row["id"] != "docker-desktop-linux-amd64-stage3"]
    matrix["rows"].append(
        {
            "id": "docker-desktop-linux-amd64-stage3",
            "status": "LOCAL_PROVIDER_EXERCISED_AWAITING_REVIEW",
            "privileged_connected_mode": True,
            "evidence": ["SANDBOX_PROFILE.json", "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json"],
        }
    )
    write("SUPPORTED_ENVIRONMENTS.json", matrix)


def update_threats() -> None:
    exercised = {
        "TM-002",
        "TM-004",
        "TM-005",
        "TM-006",
        "TM-007",
        "TM-008",
        "TM-009",
        "TM-010",
        "TM-011",
        "TM-012",
        "TM-014",
        "TM-015",
        "TM-016",
        "TM-017",
        "TM-018",
        "TM-019",
        "TM-020",
        "TM-022",
        "TM-028",
        "TM-036",
        "TM-039",
        "TM-041",
        "TM-042",
        "TM-043",
        "TM-046",
        "TM-047",
    }
    register = load("THREAT_REGISTER.json")
    coverage: list[dict[str, object]] = []
    for threat in register["threats"]:
        is_exercised = threat["id"] in exercised
        threat["stage_3_status"] = (
            "CONTROL_EXERCISED_AWAITING_INDEPENDENT_REVIEW" if is_exercised else "OPEN_LATER_STAGE"
        )
        threat["status"] = "OPEN"
        if is_exercised:
            threat["stage_3_evidence"] = ["tests/stage3", "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json"]
        coverage.append(
            {
                "id": threat["id"],
                "status": threat["stage_3_status"],
                "release_status": "OPEN",
            }
        )
    write("THREAT_REGISTER.json", register)
    write(
        "STAGE_3_THREAT_COVERAGE.json",
        {
            "coverage_version": "1.0.0",
            "control_exercised_count": len(exercised),
            "threat_count": len(coverage),
            "release_threats_closed": 0,
            "rows": coverage,
        },
    )


def update_blockers() -> None:
    blockers = load("RELEASE_BLOCKERS.json")
    for blocker in blockers["blockers"]:
        blocker["status"] = "OPEN"
        if blocker["owner_stage"] == 3:
            blocker["stage_3_note"] = (
                "Local Security Spine controls are exercised, but this blocker remains open pending independent "
                "review and later integrated release gates."
            )
            blocker["independent_verifier"] = "Nilhan"
    write("RELEASE_BLOCKERS.json", blockers)


def main() -> None:
    update_status()
    update_program()
    update_requirements()
    update_adrs()
    update_support()
    update_threats()
    update_blockers()


if __name__ == "__main__":
    main()
