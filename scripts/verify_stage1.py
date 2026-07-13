#!/usr/bin/env python3
"""Fail-closed Stage 1 governance and fixture verifier."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_V7 = "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d"
EXPECTED_STAGE0 = "9a98570803b78e29dada15ae7ee9f84feaf05284"
EXPECTED_PLAN = "d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> object:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def verify() -> dict[str, object]:
    checks: list[str] = []
    require(git("rev-parse", "stage0-complete^{}") == EXPECTED_STAGE0, "Stage 0 tag target changed")
    checks.append("stage0_tag_target")
    require(sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md") == EXPECTED_PLAN, "Revision 1.1 plan digest changed")
    checks.append("authoritative_plan_digest")
    require("does not replace" in (ROOT / "LAOS_v8_TEN_STAGE_IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8"), "Ten-stage plan lacks subordination rule")
    checks.append("ten_stage_plan_subordinate")

    baseline_v7 = ROOT / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"
    require(sha256(baseline_v7) == EXPECTED_V7, "Embedded v7 archive changed")
    checks.append("embedded_v7_digest")

    requirements = load("REQUIREMENTS_LEDGER.json")
    require(requirements["requirement_count"] == len(requirements["requirements"]) == 241, "Requirement count mismatch")
    require(len({r["id"] for r in requirements["requirements"]}) == 241, "Duplicate requirement ID")
    require(requirements["stage0_historical_requirement_count"] == 210 and requirements["revision_1_1_added_requirement_count"] == 31, "Revision 1.1 requirement reconciliation mismatch")
    require(all(r["source_plan_revision"] == "1.1" and r["implementation_stages"] for r in requirements["requirements"]), "Unreconciled requirement")
    checks.append("requirements_241_reconciled")

    stages = load("PROGRAM_STAGE_LEDGER.json")["stages"]
    require([row["stage"] for row in stages] == list(range(1, 11)), "Ten-stage ledger mismatch")
    checks.append("ten_stage_ledger")
    milestones = load("MILESTONE_LEDGER.json")["milestones"]
    require([row["milestone"] for row in milestones] == list(range(17)), "Milestone ledger mismatch")
    checks.append("milestones_0_to_16")

    blockers = load("RELEASE_BLOCKERS.json")
    require(blockers["count"] == 25, "Release blocker count mismatch")
    require([b["id"] for b in blockers["blockers"]] == [f"RB-{n:03d}" for n in range(1, 26)], "Release blocker IDs mismatch")
    require(all(b["status"] == "OPEN" and not b["builder_write_authority"] for b in blockers["blockers"]), "A blocker was prematurely closed or builder-writable")
    checks.append("release_blockers_open")

    threats = load("THREAT_REGISTER.json")
    require(threats["count"] == len(threats["threats"]) == 50, "Threat register mismatch")
    require(len({t["id"] for t in threats["threats"]}) == 50, "Duplicate threat ID")
    checks.append("threats_50_open")

    fixtures = sorted((ROOT / "tests" / "fixtures" / "v7_regressions").glob("*.json"))
    require(len(fixtures) == 8, "Expected eight v7 regression fixtures")
    for path in fixtures:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        require(fixture["status"] == "FIXTURE_SPECIFIED_IMPLEMENTATION_OPEN", f"Fixture status overclaims closure: {path.name}")
        require(fixture["source_archive_sha256"] == EXPECTED_V7, f"Fixture v7 binding mismatch: {path.name}")
        require(fixture["source_regressions"] and fixture["oracle"] and fixture["owner_stage"], f"Incomplete fixture: {path.name}")
    checks.append("eight_fixture_specs")
    reproduction = load("Evidence/V7_FIXTURE_REPRODUCTION.json")
    require(reproduction["status"] == "PASS" and reproduction["fixture_count"] == 8, "v7 fixture source observations did not reproduce")
    require(reproduction["executed_v7_code"] is False, "fixture reproduction unexpectedly executed v7 code")
    checks.append("v7_fixture_source_observations")

    status = load("IMPLEMENTATION_STATUS.json")
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "False v8 implementation/release claim")
    require(status["stage_1_status"] in {"AWAITING_NILHAN_REVIEW", "COMPLETE"}, "Invalid Stage 1 status")
    if status["stage_1_status"] == "COMPLETE":
        review = load("Evidence/STAGE_1_REVIEW.json")
        require(review["status"] == "APPROVED" and review["reviewer"] == "Nilhan", "Stage 1 completion lacks Nilhan approval")
    checks.append("honest_implementation_status")

    decision = (ROOT / "decisions" / "V7_MAINTENANCE_DECISION.md").read_text(encoding="utf-8")
    require("do not build or claim a v7.0.1" in decision and "BOOTSTRAP" in decision, "Fixture-only decision missing")
    checks.append("fixture_only_decision")

    for name in ("SCOPE_LEDGER.json", "SUPPORTED_ENVIRONMENTS.json", "PERFORMANCE_LEDGER.json", "MIGRATION_MATRIX.json", "ADR_REGISTER.json", "IMPLEMENTATION_BACKLOG.json"):
        load(name)
    checks.append("auxiliary_ledgers_parse")
    return {"status": "PASS", "checks": checks, "check_count": len(checks)}


def main() -> int:
    try:
        result = verify()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
