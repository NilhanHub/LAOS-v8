#!/usr/bin/env python3
"""Fail-closed Stage 2 typed-kernel and platform-contract verifier."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from laos_v8.errors import AuthorizationDenied, DuplicateKeyError, UnknownRecordType, UnsupportedRecordVersion
from laos_v8.migrations import MigrationRegistry
from laos_v8.models import RECORD_MODELS, ActorIdentity, Role, SideEffectRecord
from laos_v8.parser import strict_loads
from laos_v8.platform_profile import recommended_sqlite_journal_mode
from laos_v8.schema_registry import SCHEMA_DIALECT, validate_record_bytes
from laos_v8.side_effect_contract import attempt_verification

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLAN = "d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729"
EXPECTED_V7 = "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d"


def load(name: str) -> Any:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed verifier arguments
        [executable, "-C", str(ROOT), *args], text=True
    ).strip()


def valid_requirement_bytes(**updates: object) -> bytes:
    value: dict[str, object] = {
        "record_type": "requirement",
        "record_version": "1.0.0",
        "record_id": "requirement:stage2-verifier",
        "project_id": "project:stage2",
        "created_at": "2026-07-13T00:00:00Z",
        "title": "Verifier record",
        "description": "Strict Stage 2 verifier input",
        "priority": "P0",
        "scope": "MUST_V8_0",
        "criterion_ids": ["criterion:stage2-verifier"],
    }
    value.update(updates)
    return json.dumps(value).encode()


def verify_schemas(checks: list[str]) -> None:
    registry = load("schemas/SCHEMA_REGISTRY.json")
    require(registry["dialect"] == SCHEMA_DIALECT, "Schema registry dialect changed")
    require(len(registry["schemas"]) == len(RECORD_MODELS) == 40, "Expected 40 canonical schemas")
    paths: set[str] = set()
    for entry in registry["schemas"]:
        require(set(entry) == {"path", "sha256"}, "Schema registry entry lacks a digest")
        path = ROOT / entry["path"]
        require(path.is_file(), f"Missing schema: {entry['path']}")
        require(sha256(path) == entry["sha256"], f"Schema digest mismatch: {entry['path']}")
        schema = json.loads(path.read_text(encoding="utf-8"))
        require(schema["$schema"] == SCHEMA_DIALECT, f"Wrong schema dialect: {entry['path']}")
        require(schema.get("additionalProperties") is False, f"Schema is not closed: {entry['path']}")
        paths.add(entry["path"])
    require(len(paths) == 40, "Duplicate schema registry path")
    checks.append("forty_hashed_draft_2020_12_schemas")


def verify_fail_closed_parsing(checks: list[str]) -> None:
    require(validate_record_bytes(valid_requirement_bytes()).record_type == "requirement", "Valid record rejected")
    try:
        strict_loads(b'{"a":1,"a":2}')
    except DuplicateKeyError:
        pass
    else:
        raise AssertionError("Duplicate JSON key accepted")
    try:
        validate_record_bytes(valid_requirement_bytes(record_type="invented"))
    except UnknownRecordType:
        pass
    else:
        raise AssertionError("Unknown record type accepted")
    try:
        validate_record_bytes(valid_requirement_bytes(record_version="2.0.0"))
    except UnsupportedRecordVersion:
        pass
    else:
        raise AssertionError("Unknown record version accepted")
    try:
        MigrationRegistry().migrate({"record_type": "requirement", "record_version": "0.9.0"}, "1.0.0")
    except UnsupportedRecordVersion:
        pass
    else:
        raise AssertionError("Unregistered record migration was guessed")
    checks.append("fail_closed_parser_schema_and_migration")


def verify_authorization_contract(checks: list[str]) -> None:
    require(issubclass(AuthorizationDenied, Exception), "AuthorizationDenied hierarchy missing")
    record = SideEffectRecord(
        record_id="side-effect:stage2-verifier",
        project_id="project:stage2",
        created_at="2026-07-13T00:00:00Z",
        operation="VERIFY_EXTERNAL_EFFECT",
        payload_digest="sha256:" + "0" * 64,
        state="dispatched",
    )
    actor = ActorIdentity(
        record_id="actor:stage2-builder",
        project_id="project:stage2",
        created_at="2026-07-13T00:00:00Z",
        principal="local:stage2-builder",
        roles=(Role.BUILDER,),
        identity_issuer="local:stage2-verifier",
    )
    calls = 0

    def external_operation() -> None:
        nonlocal calls
        calls += 1

    updated, result = attempt_verification(record, actor, "2026-07-13T00:00:00Z", external_operation)
    require(calls == 0, "Unauthorized builder reached external operation")
    require(result.status == "denied" and result.error is not None, "Missing structured denial")
    require(result.error["code"] == "SIDE_EFFECT_VERIFY_ROLE_DENIED", "Unstable denial code")
    require(updated.model_copy(update={"audit": record.audit}) == record, "Denial changed aggregate state")
    require(len(updated.audit) == 1 and updated.audit[0].outcome == "denied", "Denial audit missing")
    checks.append("unauthorized_side_effect_fails_before_external_operation")


def verify_platform(checks: list[str]) -> None:
    vectors = load("PLATFORM_GOLDEN_VECTORS.json")
    for vector in vectors["sqlite_journal_vectors"]:
        require(
            recommended_sqlite_journal_mode(vector["sqlite"]) == vector["expected"],
            f"SQLite journal vector failed: {vector['sqlite']}",
        )
    local = load("Evidence/STAGE_2_LOCAL_PLATFORM.json")
    require(local["status"] == "PASS", "Local Stage 2 platform doctor failed")
    if not local["sqlite_wal_reset_fix_verified"]:
        require(local["sqlite_journal_mode"] == "DELETE", "Unverified SQLite selected WAL")
    support = load("SUPPORTED_ENVIRONMENTS.json")
    require("PRIVILEGED_RUNTIME_UNCLAIMED" in support["claim_status"], "Support matrix overclaims runtime")
    require(len(support["kernel_ci_matrix"]) == 8, "Expected eight configured CI combinations")
    checks.append("platform_matrix_and_safe_sqlite_fallback")


def verify_governance(checks: list[str]) -> None:
    require(git("rev-parse", "stage1-complete^{}") == "07680b067079c3b6e261b133629fe2123b1807b8", "Stage 1 tag changed")
    require(sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md") == EXPECTED_PLAN, "Plan digest changed")
    blockers = load("RELEASE_BLOCKERS.json")
    require(
        blockers["count"] == 25 and all(row["status"] == "OPEN" for row in blockers["blockers"]),
        "A release blocker was prematurely closed",
    )
    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_2_status"] == "AWAITING_NILHAN_REVIEW", "Stage 2 review state is dishonest")
    require(status["typed_kernel_exists"] is True, "Typed kernel status missing")
    require(
        status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "Runtime or release overclaim"
    )
    stage2 = next(row for row in load("PROGRAM_STAGE_LEDGER.json")["stages"] if row["stage"] == 2)
    require(
        stage2["status"] == "REVIEW_CANDIDATE" and stage2["independent_reviewer"] == "Nilhan",
        "Stage 2 review assignment mismatch",
    )
    checks.append("plan_stage_and_open_blocker_truth")


def verify_generated_evidence(checks: list[str]) -> None:
    dependency = load("Evidence/STAGE_2_DEPENDENCY_POC.json")
    require(dependency["status"] == "PASS", "Dependency proof of concept failed")
    require(dependency["uv_lock_sha256"] == sha256(ROOT / "uv.lock"), "Dependency lock changed after evidence")
    migration = load("Evidence/STAGE_2_MIGRATION_DISCOVERY.json")
    require(migration["mode"] == "READ_ONLY_NO_EXTRACTION", "Migration discovery extracted the v7 archive")
    require(migration["source_sha256"] == EXPECTED_V7, "Migration source digest mismatch")
    require(migration["migration_status"] == "DISCOVERY_ONLY_NOT_MIGRATED", "Migration evidence overclaims completion")
    checks.append("dependency_and_read_only_migration_evidence")


def verify() -> dict[str, object]:
    checks: list[str] = []
    verify_governance(checks)
    verify_schemas(checks)
    verify_fail_closed_parsing(checks)
    verify_authorization_contract(checks)
    verify_platform(checks)
    verify_generated_evidence(checks)
    require(load("schemas/ERROR_CODES.json")["registry_version"] == "1.0.0", "Error registry missing")
    require(len(load("schemas/TRANSITION_TABLES.json")["aggregates"]) == 7, "Transition table set changed")
    require(load("schemas/golden/canonicalization-v1.json")["profile"] == "RFC8785-JCS", "Canonical vector missing")
    checks.append("stable_errors_transitions_and_canonical_vector")
    performance = load("PERFORMANCE_LEDGER.json")
    require(all(metric["budget"] for metric in performance["metrics"]), "A provisional budget is undefined")
    require(
        all(metric["measurement"] == "NOT_MEASURED_PRE_ALPHA" for metric in performance["metrics"]),
        "Stage 2 claims Alpha measurements",
    )
    checks.append("provisional_pre_alpha_budgets")
    return {"status": "PASS", "stage": 2, "check_count": len(checks), "checks": checks}


def main() -> int:
    try:
        result = verify()
    except Exception as exc:
        result = {"status": "FAIL", "stage": 2, "error": str(exc)}
        exit_code = 1
    else:
        exit_code = 0
    output = json.dumps(result, indent=2) + "\n"
    (ROOT / "Evidence" / "STAGE_2_VERIFICATION.json").write_bytes(output.encode("utf-8"))
    print(output, end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
