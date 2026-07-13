#!/usr/bin/env python3
"""Fail-closed Stage 3 Mandatory Security Spine verifier."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from laos_v8.brokers import ActionClaimBroker
from laos_v8.errors import PolicyDenied, RepositoryDrift, ValidationError
from laos_v8.identity import AuthenticatedActor
from laos_v8.models import RiskTier, Role
from laos_v8.policy import PermissionRequest, PolicyEngine, minimal_stage3_policy
from laos_v8.repository_truth import build_manifest
from laos_v8.safe_paths import validate_relative_path
from laos_v8.state import CanonicalState

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLAN = "d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729"
EXPECTED_STAGE2 = "28288ba876d0e05a07ba7459ecda9fa6c3e6b716"


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


def git_at(root: Path, *args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed verifier arguments
        [executable, "-C", str(root), *args], text=True
    ).strip()


def verify_governance(checks: list[str]) -> None:
    require(git("rev-parse", "stage2-complete^{}") == EXPECTED_STAGE2, "Stage 2 completion tag changed")
    require(sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md") == EXPECTED_PLAN, "Plan digest changed")
    review = load("Evidence/STAGE_2_REVIEW.json")
    require(review["status"] == "APPROVED" and review["reviewer"] == "Nilhan", "Stage 2 approval missing")
    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_2_status"] == "COMPLETE", "Stage 2 is not complete")
    require(status["stage_3_status"] in {"AWAITING_NILHAN_REVIEW", "COMPLETE"}, "Stage 3 review status is dishonest")
    if status["stage_3_status"] == "COMPLETE":
        review = load("Evidence/STAGE_3_REVIEW.json")
        require(
            review["status"] == "APPROVED"
            and review["reviewer"] == "Nilhan"
            and review["reviewed_candidate_commit"] == "356b9be97ec778068b7acca244310eabc8012472"
            and review["reviewed_candidate_tag"] == "stage3-review-candidate",
            "Stage 3 completion lacks Nilhan approval",
        )
    require(status["security_spine_exists"] is True, "Security Spine status missing")
    if "stage_4_status" in status:
        require(status["real_weaker_agent_executed"] is True, "Stage 4 real-agent execution is not recorded")
    else:
        require(status["real_weaker_agent_executed"] is False, "Stage 3 improperly claims real agent execution")
    require(status["v8_runtime_exists"] is False and status["v8_release_exists"] is False, "Runtime/release overclaim")
    stage3 = next(row for row in load("PROGRAM_STAGE_LEDGER.json")["stages"] if row["stage"] == 3)
    require(stage3["status"] in {"REVIEW_CANDIDATE", "COMPLETED"}, "Stage 3 review state is invalid")
    require(stage3["owner"] == "Codex" and stage3["independent_reviewer"] == "Nilhan", "Stage 3 roles changed")
    checks.append("stage2_approval_and_stage3_truth")


def verify_dependency_amendment(checks: list[str]) -> None:
    amendment = load("Evidence/STAGE_3_DEPENDENCY_AMENDMENT.json")
    require(amendment["status"] == "REVIEWED_AND_LOCKED", "Stage 3 dependency amendment is unreviewed")
    require(amendment["current_uv_lock_sha256"] == sha256(ROOT / "uv.lock"), "Stage 3 lock digest mismatch")
    require(amendment["added_direct_dependency"]["name"] == "cryptography", "Signer dependency is unrecorded")
    require(amendment["added_direct_dependency"]["production_key_custody_claimed"] is False, "Key custody overclaim")
    checks.append("reviewed_ed25519_dependency_amendment")


def verify_contracts(checks: list[str]) -> None:
    for name in (
        "docs/STAGE_3_ENFORCEMENT_CONTRACT.md",
        "SANDBOX_PROFILE.json",
        "PERMISSION_ENFORCEMENT_MATRIX.json",
        "STAGE_3_THREAT_COVERAGE.json",
    ):
        require((ROOT / name).is_file(), f"Missing Stage 3 contract: {name}")
    sandbox = load("SANDBOX_PROFILE.json")
    controls = sandbox["controls"]
    require(
        sandbox["image"].endswith("581c14606911610c6b61e569714e92a726c1ef2437dd034824f644f6d9df6e9d"),
        "Sandbox image is not pinned",
    )
    require(sandbox["maximum_action_risk"] == "moderate", "Sandbox risk scope expanded without evidence")
    require(
        controls["network"] == "none"
        and controls["root_filesystem"] == "read-only"
        and controls["workspace_mount"] == "read-only"
        and controls["capabilities"] == "drop-all"
        and controls["no_new_privileges"] is True
        and controls["host_secrets_mounted"] is False,
        "Sandbox control profile weakened",
    )
    matrix = load("PERMISSION_ENFORCEMENT_MATRIX.json")
    require(len(matrix["rows"]) == 11, "Permission enforcement matrix is incomplete")
    require(all(row["executor_direct_access"] is False for row in matrix["rows"]), "Executor gained direct access")
    unsupported = {"secrets", "production_side_effect"}
    require(
        all(row["status"] == "DENIED_UNIMPLEMENTED" for row in matrix["rows"] if row["capability"] in unsupported),
        "An unsupported capability is not fail-closed",
    )
    checks.append("deployment_sandbox_and_enforcement_contracts")


def verify_local_security_evidence(checks: list[str]) -> None:
    evidence = load("Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json")
    require(evidence["status"] == "PASS", "Local Security Spine profile failed")
    require(evidence["docker"]["status"] == "PASS", "Real Docker sandbox was not exercised")
    probe = evidence["docker"]["probe"]
    require(
        probe["uid"] == 65534
        and int(probe["cap_eff"], 16) == 0
        and probe["no_new_privs"] == "1"
        and len(probe["write_denied"]) == 2
        and probe["network_connect_result"] != 0,
        "Docker adversarial probe did not prove mandatory controls",
    )
    require(
        evidence["state"]["journal_mode"] == "delete"
        and evidence["state"]["foreign_keys"] == 1
        and evidence["state"]["duplicate_claim_denied"] is True
        and evidence["state"]["integrity_check"] == "ok",
        "Transactional state evidence failed",
    )
    require(
        evidence["signing"]["status"] == "PASS" and evidence["signing"]["production_key_custody_claimed"] is False,
        "Protected test signer evidence failed",
    )
    operator = evidence["operator_paths"]
    require(
        operator["status"] == "PASS"
        and operator["backup_restore_digest_match"] is True
        and operator["evidence_export_verified"] is True
        and operator["evidence_purge_tombstoned"] is True
        and operator["denial_explanation_known"] is True
        and operator["production_evidence_custody_claimed"] is False,
        "Minimal pre-Alpha operator path evidence failed",
    )
    require(evidence["uv_lock_sha256"] == sha256(ROOT / "uv.lock"), "Evidence lock binding mismatch")
    require(
        evidence["real_weaker_agent_executed"] is False
        and evidence["external_model_transmission"] is False
        and evidence["production_side_effect_executed"] is False,
        "Stage 3 evidence crossed its authority boundary",
    )
    checks.append("real_local_security_profile_evidence")


def verify_fail_closed_runtime(checks: list[str]) -> None:
    for value in ("../escape", "C:/device", "file:stream", "a\\b"):
        try:
            validate_relative_path(value)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Unsafe path accepted: {value}")
    actor = AuthenticatedActor(
        "actor:builder",
        "local:builder",
        (Role.BUILDER,),
        "session:builder",
        "workspace:builder",
        0,
    )
    profile = minimal_stage3_policy()
    request = PermissionRequest(
        capability="SANDBOX_CHECK",
        policy_digest=profile.digest,
        policy_version=profile.version,
        risk=RiskTier.MODERATE,
        argv=("python", "-m", "pytest"),
        network=True,
    )
    try:
        PolicyEngine(profile).require(actor, request, emergency_stopped=False)
    except PolicyDenied:
        pass
    else:
        raise AssertionError("Network request escaped default-deny policy")
    with tempfile.TemporaryDirectory(prefix="laos-stage3-verifier-") as temporary:
        temporary_root = Path(temporary)
        repository = temporary_root / "repository"
        repository.mkdir()
        git_at(repository, "init", "-b", "main")
        (repository / "app.py").write_bytes(b"VALUE = 1\n")
        git_at(repository, "add", "app.py")
        git_at(
            repository,
            "-c",
            "user.name=LAOS Verifier",
            "-c",
            "user.email=verifier.invalid",
            "commit",
            "-m",
            "base",
        )
        accepted = build_manifest(repository, seal_kind="base")
        (repository / "app.py").write_bytes(b"VALUE = 2\n")
        with CanonicalState(temporary_root / "state.sqlite3") as state:
            broker = ActionClaimBroker(state)
            try:
                broker.claim(
                    actor,
                    action_id="action:drift",
                    repository=repository,
                    expected_base_seal=accepted.seal,
                    lease_expires_at="2099-01-01T00:00:00Z",
                )
            except RepositoryDrift:
                pass
            else:
                raise AssertionError("Pre-claim repository drift was accepted")
            current = build_manifest(repository, seal_kind="base")
            broker.claim(
                actor,
                action_id="action:one",
                repository=repository,
                expected_base_seal=current.seal,
                lease_expires_at="2099-01-01T00:00:00Z",
            )
            try:
                broker.claim(
                    actor,
                    action_id="action:one",
                    repository=repository,
                    expected_base_seal=current.seal,
                    lease_expires_at="2099-01-01T00:00:00Z",
                )
            except Exception as exc:
                require(getattr(exc, "code", "") == "ACTION_ALREADY_CLAIMED", "Wrong double-claim error")
            else:
                raise AssertionError("Two workers claimed one action")
    checks.append("fail_closed_path_policy_and_claim_runtime")


def verify_ledgers(checks: list[str]) -> None:
    blockers = load("RELEASE_BLOCKERS.json")
    require(
        blockers["count"] == 25 and all(row["status"] == "OPEN" for row in blockers["blockers"]),
        "A release blocker closed early",
    )
    coverage = load("STAGE_3_THREAT_COVERAGE.json")
    require(
        coverage["threat_count"] == 50
        and coverage["control_exercised_count"] == 26
        and coverage["release_threats_closed"] == 0,
        "Threat coverage ledger mismatch",
    )
    requirements = load("REQUIREMENTS_LEDGER.json")["requirements"]
    stage3 = [row for row in requirements if 3 in row["implementation_stages"]]
    require(len(stage3) == 82, "Stage 3 requirement mapping changed")
    require(
        all(row["owner"] == "Codex" and row["independent_reviewer"] == "Nilhan" for row in stage3),
        "Stage 3 requirement ownership missing",
    )
    require(all(row["status"] != "ACCEPTED" for row in stage3), "Requirement accepted before independent review")
    support = load("SUPPORTED_ENVIRONMENTS.json")
    require("PRODUCTION_UNCLAIMED" in support["claim_status"], "Support matrix overclaims production")
    checks.append("requirements_threats_support_and_blockers")


def verify_repository_hygiene(checks: list[str]) -> None:
    tracked = git("ls-files").splitlines()
    forbidden_suffixes = (".sqlite", ".sqlite3", "-wal", "-shm")
    require(not any(name.lower().endswith(forbidden_suffixes) for name in tracked), "Mutable database state is tracked")
    private_markers = ("BEGIN " + "PRIVATE KEY", "OPENSSH " + "PRIVATE KEY")
    for name in tracked:
        path = ROOT / name
        if path.is_file() and path.stat().st_size <= 2_000_000:
            try:
                value = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            require(not any(marker in value for marker in private_markers), f"Private-key material found: {name}")
    checks.append("no_tracked_runtime_state_or_private_keys")


def verify_operator_paths(checks: list[str]) -> None:
    require((ROOT / "docs/STAGE_3_OPERATOR_PATHS.md").is_file(), "Stage 3 operator guide is missing")
    cli = (ROOT / "src/laos_v8/cli.py").read_text(encoding="utf-8")
    for command in (
        "explain-denial",
        "backup",
        "restore",
        "trust-status",
        "trust-recover",
        "evidence-export",
        "evidence-purge",
        "evidence-reconcile-purges",
    ):
        require(f'"{command}"' in cli, f"Minimal operator command is missing: {command}")
    checks.append("minimal_pre_alpha_operator_paths")


def verify() -> dict[str, object]:
    checks: list[str] = []
    verify_governance(checks)
    verify_dependency_amendment(checks)
    verify_contracts(checks)
    verify_local_security_evidence(checks)
    verify_fail_closed_runtime(checks)
    verify_ledgers(checks)
    verify_repository_hygiene(checks)
    verify_operator_paths(checks)
    return {"status": "PASS", "stage": 3, "check_count": len(checks), "checks": checks}


def main() -> int:
    try:
        result = verify()
    except Exception as exc:
        result = {"status": "FAIL", "stage": 3, "error": str(exc)}
        exit_code = 1
    else:
        exit_code = 0
    output = json.dumps(result, indent=2) + "\n"
    (ROOT / "Evidence" / "STAGE_3_VERIFICATION.json").write_bytes(output.encode("utf-8"))
    print(output, end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
