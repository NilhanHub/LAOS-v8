#!/usr/bin/env python3
"""Verify Stage 6 program truth using only the Python standard library."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BLOCKERS = {"RB-011", "RB-012", "RB-013", "RB-014"}
EXPECTED_COUNTS = {"COMMAND_SANDBOX": 9, "CRITERIA": 8, "EVIDENCE": 10, "REVIEW": 9, "TESTING": 8, "REVISION_1_1": 5}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load(name: str) -> dict[str, Any]:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{name} is not an object")
    return value


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    completed = subprocess.run(  # noqa: S603 - resolved Git and fixed verifier call sites
        [executable, "-C", str(ROOT), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
        timeout=30,
    )
    require(completed.returncode == 0, completed.stderr.strip() or "Git verification failed")
    return completed.stdout.strip()


def main() -> int:
    plan_digest = hashlib.sha256((ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md").read_bytes()).hexdigest()
    coverage = load("STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json")
    requirements = load("REQUIREMENTS_LEDGER.json")
    blockers = load("RELEASE_BLOCKERS.json")
    program = load("PROGRAM_STAGE_LEDGER.json")
    status = load("IMPLEMENTATION_STATUS.json")
    environments = load("SUPPORTED_ENVIRONMENTS.json")
    profiles = load("profiles/ACTIVE_EXECUTOR_PROFILES.json")

    require(coverage["authority_sha256"] == plan_digest, "Stage 6 coverage plan hash differs")
    expected = {item["id"] for item in requirements["requirements"] if 6 in item.get("implementation_stages", [])}
    observed = [item["requirement_id"] for item in coverage["requirements"]]
    require(
        len(expected) == 49 and len(observed) == 49 and set(observed) == expected,
        "Stage 6 requirement map differs",
    )
    require(len(observed) == len(set(observed)), "Stage 6 coverage duplicates a requirement")
    counts: dict[str, int] = {}
    for item in coverage["requirements"]:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
        require(item["owner"] == "Codex" and item["independent_reviewer"] == "Nilhan", "Stage 6 roles differ")
        require(item["evidence"], f"{item['requirement_id']} lacks evidence")
        for path in item["evidence"]:
            require((ROOT / path).is_file(), f"Stage 6 evidence path is missing: {path}")
    require(counts == EXPECTED_COUNTS, "Stage 6 category counts differ")

    active_blockers = {item["id"]: item for item in blockers["blockers"] if item["id"] in EXPECTED_BLOCKERS}
    require(set(active_blockers) == EXPECTED_BLOCKERS, "Stage 6 blocker set differs")
    for item in active_blockers.values():
        require(item["status"] == "OPEN", f"{item['id']} was closed before Stage 10")
        require(item["builder_write_authority"] is False, f"{item['id']} builder authority changed")
        require(item["stage_6_evidence"] and item["evidence_digests"], f"{item['id']} lacks mitigation evidence")

    stage = next(item for item in program["stages"] if item["stage"] == 6)
    require(stage["status"] == "IN_PROGRESS_AWAITING_PROTECTED_REVIEW", "Stage 6 status is overstated")
    require(status["stage_6_status"] == "IN_PROGRESS_AWAITING_PROTECTED_REVIEW", "implementation status differs")
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "v8 completion overstated")
    require(status["stage_7_status"] == "PLANNED", "Stage 7 status differs")

    stage6_row = next(item for item in environments["rows"] if item["id"] == "docker-desktop-linux-amd64-stage6")
    require(stage6_row["maximum_risk"] == "MODERATE", "Stage 6 support row overstates risk")
    require(stage6_row["high_critical_status"] == "DENIED_QUORUM_UNAVAILABLE", "critical quorum is overstated")
    released = [item for item in profiles["profiles"] if item.get("released") is True]
    require(
        len(released) == 1 and released[0]["profile_id"] == "profile:investigation-specialist",
        "new model profile released",
    )

    required_files = (
        "src/laos_v8/clean_verifier.py", "src/laos_v8/evidence_custody.py", "src/laos_v8/custody_service.py",
        "src/laos_v8/criterion_closure.py", "src/laos_v8/protected_checks.py", "src/laos_v8/protected_review.py",
        "custodian/Dockerfile", "tests/stage6/test_sandbox_assurance.py", "tests/stage6/test_evidence_custody.py",
        "tests/stage6/test_protected_checks.py", "tests/stage6/test_criterion_and_review.py",
    )
    require(all((ROOT / path).is_file() for path in required_files), "Stage 6 implementation file is missing")

    historical_changes = [
        path for path in git("diff", "--name-only", "stage5-complete", "--", "Evidence").splitlines()
        if path and not path.startswith("Evidence/STAGE_6_")
    ]
    require(not historical_changes, f"historical evidence changed: {historical_changes}")
    print(
        json.dumps(
            {"status": "PASS", "stage": 6, "requirements": 49, "blockers_open": sorted(EXPECTED_BLOCKERS)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
