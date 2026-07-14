#!/usr/bin/env python3
"""Fail-closed verifier for the non-completion Stage 5 implementation checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from laos_v8.canonical import canonical_json
from laos_v8.prompting import ExecutorProfile

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify() -> list[str]:
    checks: list[str] = []
    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_4_status"] == "COMPLETE", "Stage 4 is not complete")
    require(status["stage_5_status"] == "IN_PROGRESS", "Stage 5 checkpoint status changed")
    require(
        status["status"] == "STAGE_5_IN_PROGRESS_SIGNING_CUSTODY_DECISION_REQUIRED_FULL_V8_RUNTIME_NOT_IMPLEMENTED",
        "program status overclaims or omits the custody decision",
    )
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "v8 overclaim")
    required_open = {
        "PROTECTED_SIGNING_CUSTODY",
        "RELEASED_PROFILE_REAL_CALIBRATION",
        "REAL_WEAKER_INVESTIGATOR_CAPTURE_ROUND_TRIP",
    }
    require(set(status["stage_5_open_gates"]) == required_open, "Stage 5 open gates changed")
    checks.append("program_truth")

    stage = next(item for item in load("PROGRAM_STAGE_LEDGER.json")["stages"] if item["stage"] == 5)
    require(stage["status"] == "IN_PROGRESS", "Stage 5 ledger status is not in progress")
    require(stage["owner"] == "Codex" and stage["independent_reviewer"] == "Nilhan", "roles changed")
    checks.append("governance")

    coverage = load("STAGE_5_CORE_WORKFLOW_COVERAGE.json")
    rows = coverage["coverage"]
    require(len(rows) == 14, "Stage 5 coverage rows are incomplete")
    require({row["milestone"] for row in rows} == {5, 6, 7, 8}, "Milestone coverage changed")
    open_rows = {row["id"] for row in rows if row["status"].startswith("OPEN_")}
    require(open_rows == {"S5-05", "S5-11", "S5-14"}, "Stage 5 open claims changed")
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
    checks.append("offline_profiles")

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

    docker = load("Evidence/DOCKER_AUTOSTART_VERIFICATION.json")
    require(docker["status"] == "PASS", "Docker automatic-start evidence failed")
    require(docker["cold_start"]["manual_operator_action_required"] is False, "manual Docker startup remains")
    require(docker["cold_start"]["final_desktop_status"] == "running", "Docker was not left running")
    require(docker["verification"]["laos_tests"] == "PASS_119_NO_DOCKER_SKIP", "Docker test was skipped")
    require(docker["verification"]["sanitized_log_contains_command_arguments"] is False, "Docker log leaked argv")
    checks.append("automatic_docker_dependency")
    return checks


def main() -> int:
    checks = verify()
    print(json.dumps({"status": "PASS_STAGE_5_CHECKPOINT_NOT_COMPLETE", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
