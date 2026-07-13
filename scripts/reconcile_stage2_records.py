#!/usr/bin/env python3
"""Reconcile machine-readable program records with the Stage 2 review candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_SHA256 = "d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729"


def load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write(name: str, value: object) -> None:
    (ROOT / name).write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def reconcile_status() -> None:
    status = load("IMPLEMENTATION_STATUS.json")
    status.update(
        {
            "milestone": 2,
            "milestone_name": "Typed v8 kernel and strict validation",
            "next_milestone": 3,
            "stage_2_status": "AWAITING_NILHAN_REVIEW",
            "status": "STAGE_2_REVIEW_CANDIDATE_TYPED_KERNEL_IMPLEMENTED_V8_RUNTIME_NOT_IMPLEMENTED",
            "typed_kernel_exists": True,
            "v8_runtime_exists": False,
            "v8_release_exists": False,
        }
    )
    write("IMPLEMENTATION_STATUS.json", status)


def reconcile_program_ledgers() -> None:
    stages = load("PROGRAM_STAGE_LEDGER.json")
    stage2 = next(row for row in stages["stages"] if row["stage"] == 2)
    stage2.update(
        {
            "status": "REVIEW_CANDIDATE",
            "owner": "Codex",
            "independent_reviewer": "Nilhan",
            "evidence_policy": "BOOTSTRAP_NOT_PRODUCTION_SIGNING",
        }
    )
    write("PROGRAM_STAGE_LEDGER.json", stages)

    backlog = load("IMPLEMENTATION_BACKLOG.json")
    row = next(item for item in backlog["stages"] if item["stage"] == 2)
    row["status"] = "REVIEW_CANDIDATE"
    for task in row["tasks"]:
        if task["id"] in {"S2-CONTRACT", "S2-EVIDENCE"}:
            task["status"] = "COMPLETED"
        elif task["id"] == "S2-REVIEW":
            task["status"] = "AWAITING_NILHAN_REVIEW"
    write("IMPLEMENTATION_BACKLOG.json", backlog)

    milestones = load("MILESTONE_LEDGER.json")
    milestone2 = next(row for row in milestones["milestones"] if row["milestone"] == 2)
    milestone2.update(
        {
            "owner": "Codex",
            "independent_reviewer": "Nilhan",
            "external_dependencies": [
                "CPython >=3.11,<3.15",
                "Pydantic 2.13.4",
                "jsonschema 4.26.0",
                "rfc8785 0.1.4",
            ],
            "estimate_range": "Implemented; awaiting independent Stage 2 review.",
            "required_evidence": (
                "Bootstrap Stage 2 test, schema, dependency, platform, migration, and reconstruction evidence."
            ),
            "open_cross_subsystem_requirements": True,
        }
    )
    write("MILESTONE_LEDGER.json", milestones)


def reconcile_requirements() -> None:
    requirements = load("REQUIREMENTS_LEDGER.json")
    implemented = {
        "REQ-SCHEMAS-001",
        "REQ-SCHEMAS-002",
        "REQ-SCHEMAS-003",
        "REQ-SCHEMAS-005",
        "REQ-REVISION_1_1-002",
        "REQ-REVISION_1_1-014",
    }
    evidence = [
        "schemas/SCHEMA_REGISTRY.json",
        "schemas/ERROR_CODES.json",
        "schemas/TRANSITION_TABLES.json",
        "tests/stage2",
        "Evidence/STAGE_2_VERIFICATION.json",
    ]
    for requirement in requirements["requirements"]:
        if 2 not in requirement["implementation_stages"]:
            continue
        requirement["owner"] = "Codex"
        requirement["independent_reviewer"] = "Nilhan"
        if requirement["id"] in implemented:
            requirement["status"] = "IMPLEMENTED_AWAITING_REVIEW"
            requirement["evidence_status"] = "BOOTSTRAP_EVIDENCE_CAPTURED"
            requirement["evidence"] = evidence
        else:
            requirement["status"] = "OPEN_CROSS_SUBSYSTEM_OR_LATER_INTEGRATION"
            requirement["evidence_status"] = "PARTIAL_STAGE_2_FOUNDATION_ONLY"
    write("REQUIREMENTS_LEDGER.json", requirements)


def reconcile_support() -> None:
    write(
        "SUPPORTED_ENVIRONMENTS.json",
        {
            "matrix_version": "1.0.0",
            "claim_status": "TYPED_KERNEL_LOCAL_VERIFIED_PRIVILEGED_RUNTIME_UNCLAIMED",
            "supported_python": ">=3.11,<3.15",
            "kernel_ci_matrix": [
                {"os": "windows-2025", "python": version, "status": "CONFIGURED_NOT_EXECUTED_REMOTELY"}
                for version in ("3.11", "3.12", "3.13", "3.14")
            ]
            + [
                {"os": "ubuntu-24.04", "python": version, "status": "CONFIGURED_NOT_EXECUTED_REMOTELY"}
                for version in ("3.11", "3.12", "3.13", "3.14")
            ],
            "rows": [
                {
                    "id": "typed-kernel-windows-local-git",
                    "status": "LOCAL_CONTRACT_VERIFIED",
                    "privileged_connected_mode": False,
                    "filesystem": "local NTFS workspace",
                    "evidence": ["Evidence/STAGE_2_LOCAL_PLATFORM.json"],
                },
                {
                    "id": "typed-kernel-linux-local-git",
                    "status": "CI_CONFIGURED_NOT_EXECUTED_REMOTELY",
                    "privileged_connected_mode": False,
                    "filesystem": "local filesystem required",
                    "evidence": [".github/workflows/ci.yml"],
                },
                {
                    "id": "connected-windows-local-git",
                    "status": "PRIVILEGED_RUNTIME_NOT_IMPLEMENTED",
                    "privileged_connected_mode": True,
                    "evidence": [],
                },
                {
                    "id": "connected-linux-local-git",
                    "status": "PRIVILEGED_RUNTIME_NOT_IMPLEMENTED",
                    "privileged_connected_mode": True,
                    "evidence": [],
                },
                {
                    "id": "offline-verification-read-only",
                    "status": "PLANNED",
                    "privileged_connected_mode": False,
                    "evidence": [],
                },
                {
                    "id": "offline-privileged-authority",
                    "status": "UNSUPPORTED_V8_0",
                    "privileged_connected_mode": False,
                    "evidence": [],
                },
                {
                    "id": "direct-host-unmediated",
                    "status": "UNSUPPORTED",
                    "privileged_connected_mode": False,
                    "evidence": [],
                },
                {
                    "id": "non-git-authoritative-mutation",
                    "status": "UNSUPPORTED_V8_0",
                    "privileged_connected_mode": False,
                    "evidence": [],
                },
                {
                    "id": "network-filesystem-sqlite",
                    "status": "UNSUPPORTED",
                    "privileged_connected_mode": False,
                    "evidence": ["PLATFORM_GOLDEN_VECTORS.json"],
                },
                {
                    "id": "distributed-canonical-state",
                    "status": "DEFER_V8_X",
                    "privileged_connected_mode": False,
                    "evidence": [],
                },
            ],
        },
    )


def reconcile_performance() -> None:
    budgets: dict[str, dict[str, object]] = {
        "manifest_time_memory": {
            "max_entries": 100000,
            "max_input_bytes": 1073741824,
            "max_seconds": 60,
            "max_peak_bytes": 2147483648,
        },
        "pack_size_latency": {"max_output_bytes": 104857600, "max_seconds": 60},
        "state_contention": {"p95_target_ms": 250, "busy_timeout_seconds": 30},
        "sandbox_startup": {"max_seconds": 60},
        "evidence_growth": {"max_bytes_per_action": 1073741824},
        "full_suite_duration": {"max_seconds": 1800},
        "flake_rate": {"max_percent": 0},
        "tokens": {"max_per_action": 200000},
        "cost": {"max_usd_per_action": 25},
        "retries": {"max_per_action": 3},
        "human_minutes": {"max_per_action": 120},
    }
    ledger = load("PERFORMANCE_LEDGER.json")
    ledger["ledger_version"] = "1.0.0"
    ledger["status"] = "PROVISIONAL_CIRCUIT_BREAKERS_DEFINED_ALPHA_MEASUREMENT_REQUIRED"
    ledger["authority_sha256"] = PLAN_SHA256
    ledger["policy"] = "PERFORMANCE_BUDGETS.md"
    for metric in ledger["metrics"]:
        metric["budget"] = budgets[metric["id"]]
        metric["measurement"] = "NOT_MEASURED_PRE_ALPHA"
        metric["status"] = "PROVISIONAL_NOT_A_PRODUCTION_CLAIM"
    write("PERFORMANCE_LEDGER.json", ledger)


def reconcile_blockers() -> None:
    blockers = load("RELEASE_BLOCKERS.json")
    rb006 = next(row for row in blockers["blockers"] if row["id"] == "RB-006")
    rb006["status"] = "OPEN"
    rb006["independent_verifier"] = "Nilhan"
    rb006["stage_2_note"] = (
        "Typed parsing and validation are implemented, but the blocker remains open until protected canonical-state "
        "integration and independent verification exist."
    )
    write("RELEASE_BLOCKERS.json", blockers)


def main() -> None:
    reconcile_status()
    reconcile_program_ledgers()
    reconcile_requirements()
    reconcile_support()
    reconcile_performance()
    reconcile_blockers()


if __name__ == "__main__":
    main()
