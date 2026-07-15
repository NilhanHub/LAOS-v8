#!/usr/bin/env python3
"""Build the Stage 6 candidate from a clean reconstruction and protected providers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from laos_v8.canonical import canonical_json, content_digest
from laos_v8.clean_verifier import CleanVerifier
from laos_v8.evidence_custody import (
    CustodyStoreRequest,
    DockerEvidenceCustodian,
    EvidenceLevel,
    sign_evidence_index,
)
from laos_v8.evidence_receipts import CommandReceipt
from laos_v8.policy import ResourceBudget
from laos_v8.protected_checks import ProtectedCheckStore
from laos_v8.protected_review import ReviewCapsule, ReviewChallenge
from laos_v8.protected_signer import DockerProtectedSigner
from laos_v8.sandbox import DockerSandbox
from laos_v8.stage6_candidate import Stage6CandidateReceipt

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d"
EXPECTED_LABELS = (
    "uv_sync",
    "ruff_changed",
    "ruff_baseline",
    "mypy",
    "pytest_full",
    "package_build",
    "verify_stage1",
    "verify_stage2",
    "generate_stage3",
    "verify_stage3",
    "verify_stage4",
    "verify_stage5",
    "verify_stage6_controls",
    "sandbox_conformance",
)


def executable(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise RuntimeError(f"required executable is unavailable: {name}")
    return value


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(  # noqa: S603 - resolved Git and fixed builder call sites
        [executable("git"), "-C", str(root), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
        timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "Git command failed")
    return completed.stdout.strip()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(clone: Path, label: str, argv: tuple[str, ...], environment: dict[str, str]) -> CommandReceipt:
    actual = list(argv)
    if actual[0] == "uv":
        actual[0] = executable("uv")
    completed = subprocess.run(  # noqa: S603 - fixed structured candidate commands; no shell
        actual,
        cwd=clone,
        env=environment,
        capture_output=True,
        check=False,
        timeout=1800,
    )
    receipt = CommandReceipt(
        label=label,
        argv=argv,
        exit_code=completed.returncode,
        status="PASS" if completed.returncode == 0 else "FAIL",
        stdout_sha256=digest(completed.stdout),
        stderr_sha256=digest(completed.stderr),
        stdout_bytes=len(completed.stdout),
        stderr_bytes=len(completed.stderr),
    )
    if receipt.status != "PASS":
        safe_tail = completed.stderr.decode("utf-8", "replace")[-2000:]
        raise RuntimeError(f"candidate command failed: {label}: {safe_tail}")
    return receipt


def command_policy(run_id: str, source_commit: str) -> dict[str, tuple[str, ...]]:
    generated = f"Evidence/generated/stage6/{run_id.removeprefix('run:')}"
    return {
        "uv_sync": ("uv", "sync", "--frozen", "--all-groups"),
        "ruff_changed": (
            "uv", "run", "--frozen", "ruff", "check", "src/laos_v8", "tests/stage6",
            "scripts/build_stage6_candidate.py", "scripts/verify_stage6_candidate.py",
            "scripts/reconcile_stage6.py", "scripts/verify_stage6_controls.py",
        ),
        "ruff_baseline": ("uv", "run", "--frozen", "python", "scripts/verify_ruff_baseline.py"),
        "mypy": ("uv", "run", "--frozen", "mypy"),
        "pytest_full": ("uv", "run", "--frozen", "pytest", "-q"),
        "package_build": ("uv", "build"),
        "verify_stage1": ("uv", "run", "--frozen", "python", "scripts/verify_stage1.py"),
        "verify_stage2": ("uv", "run", "--frozen", "python", "scripts/verify_stage2.py"),
        "generate_stage3": (
            "uv", "run", "--frozen", "python", "scripts/generate_stage3_evidence.py", "--output",
            f"{generated}/stage3.json", "--run-id", run_id,
        ),
        "verify_stage3": (
            "uv", "run", "--frozen", "python", "scripts/verify_stage3.py", "--evidence",
            f"{generated}/stage3.json", "--expected-run-id", run_id, "--expected-source-commit", source_commit,
            "--output", f"{generated}/stage3-verification.json",
        ),
        "verify_stage4": ("uv", "run", "--frozen", "python", "scripts/verify_stage4.py"),
        "verify_stage5": ("uv", "run", "--frozen", "python", "scripts/verify_stage5_complete.py"),
        "verify_stage6_controls": ("uv", "run", "--frozen", "python", "scripts/verify_stage6_controls.py"),
        "sandbox_conformance": ("uv", "run", "--frozen", "laos", "sandbox-conformance"),
    }


def replay_stage4(
    clone: Path,
    run_id: str,
    signer: DockerProtectedSigner,
    custodian: DockerEvidenceCustodian,
) -> tuple[object, ...]:
    runtime = json.loads((clone / "Evidence/STAGE_4_ALPHA_RUNTIME/run.json").read_text(encoding="utf-8"))
    proposal_path = clone / "Evidence/STAGE_4_ALPHA_RUNTIME/model-proposal.json"
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    expected_proposal = {
        "relative_path": "src/calculator.py",
        "replacement": "def add(a: int, b: int) -> int:\n    return a + b\n",
    }
    if proposal != expected_proposal:
        raise RuntimeError("Stage 4 model proposal differs")
    with tempfile.TemporaryDirectory(prefix="laos-stage6-replay-") as temporary:
        candidate = Path(temporary) / "candidate"
        shutil.copytree(clone / "tests/fixtures/stage4_alpha/source", candidate)
        (candidate / proposal["relative_path"]).write_text(proposal["replacement"], encoding="utf-8", newline="\n")
        store_root = Path.home() / ".laos" / "protected_checks" / "stage6" / run_id.removeprefix("run:")
        check_store = ProtectedCheckStore(store_root)
        issued_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        bundle = check_store.provision(
            (clone / "tests/fixtures/stage4_alpha/protected/acceptance.py",),
            argv=("python", "/workspace/.laos-protected-checks/acceptance.py"),
            signer=signer,
            issuer="control:stage6",
            audience="verifier:clean",
            issued_at=issued_at,
        )
        result_tree = git(clone, "rev-parse", f"{runtime['result_commit']}^{{tree}}")
        verification = CleanVerifier(DockerSandbox()).verify(
            candidate,
            argv=bundle.argv,
            budget=ResourceBudget(
                timeout_seconds=60,
                memory_bytes=268_435_456,
                processes=32,
                output_bytes=1_048_576,
                retries=1,
            ),
            criterion_ids=(runtime["criterion_id"],),
            source_commit=runtime["result_commit"],
            source_tree=result_tree,
            protected_check_workspace=store_root / bundle.bundle_id.removeprefix("check-bundle:") / "checks",
        )
    replay_payload = canonical_json(
        {
            "record_version": "1.0.0",
            "run_id": run_id,
            "stage4_result_commit": runtime["result_commit"],
            "model_proposal_digest": "sha256:" + digest(proposal_path.read_bytes()),
            "verification": verification.model_dump(mode="json"),
            "protected_check_bundle_digest": bundle.bundle_digest,
        }
    )
    custody_object = custodian.capture(
        CustodyStoreRequest(
            payload=replay_payload,
            criterion_id=runtime["criterion_id"],
            classification="restricted",
            collector="collector:stage6-candidate",
            collector_version="1.0.0",
            source_seal=verification.source_digest,
            result_seal=verification.post_verification_source_digest,
            policy_digest=content_digest(DockerSandbox.assurance_profile),
            redaction_method="structured-minimization-v1",
            evidence_level=EvidenceLevel.L3,
            created_at=datetime.now(UTC),
        )
    )
    index = sign_evidence_index(
        (custody_object,),
        source_commit=git(clone, "rev-parse", "HEAD"),
        signer=signer,
        issuer="control:stage6",
        audience="reviewer:nilhan",
        issued_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    return verification, bundle, custody_object, index, runtime, proposal_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    archive = args.archive.resolve(strict=True)
    if archive.name != "LAOS_v7.0_Complete_System.zip" or digest(archive.read_bytes()) != ARCHIVE_SHA256:
        raise SystemExit("sealed v7 archive differs")
    dirty = git(ROOT, "status", "--porcelain", "--untracked-files=all")
    if git(ROOT, "rev-parse", "HEAD") != args.expected_commit or dirty:
        raise SystemExit("Stage 6 candidate requires the expected clean source commit")
    run_id = f"run:{uuid.uuid4().hex}"
    started = datetime.now(UTC)
    with tempfile.TemporaryDirectory(prefix="laos-stage6-candidate-") as temporary:
        clone = Path(temporary) / "source"
        subprocess.run(  # noqa: S603 - resolved Git and exact source repository
            [executable("git"), "clone", "--no-local", "--quiet", str(ROOT), str(clone)], check=True, timeout=120
        )
        git(clone, "checkout", "--detach", "--quiet", args.expected_commit)
        source_commit = git(clone, "rev-parse", "HEAD")
        source_tree = git(clone, "rev-parse", "HEAD^{tree}")
        environment = os.environ.copy()
        environment["LAOS_V7_ARCHIVE"] = str(archive)
        policy = command_policy(run_id, source_commit)
        if tuple(policy) != EXPECTED_LABELS:
            raise RuntimeError("Stage 6 command policy order differs")
        commands = tuple(run(clone, label, argv, environment) for label, argv in policy.items())
        DockerProtectedSigner.build_image(clone)
        signer = DockerProtectedSigner(clone, "event_anchor")
        signer.bootstrap()
        DockerEvidenceCustodian.build_image(clone)
        custodian = DockerEvidenceCustodian(clone)
        custodian.bootstrap()
        verification, bundle, custody_object, index, runtime, proposal_path = replay_stage4(
            clone, run_id, signer, custodian
        )
        coverage = json.loads((clone / "STAGE_6_EXECUTION_ASSURANCE_COVERAGE.json").read_text(encoding="utf-8"))
        plan_digest = "sha256:" + digest((clone / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md").read_bytes())
        review_capsule = ReviewCapsule(
            candidate_commit=source_commit,
            source_tree=source_tree,
            plan_digest=plan_digest,
            policy_digest=content_digest(DockerSandbox.assurance_profile),
            criteria_digest=content_digest(coverage["requirements"]),
            evidence_index_digest=index.event_anchor_envelope_digest,
            check_bundle_digest=bundle.bundle_digest,
            verification_digest=content_digest(verification),
            criterion_ids=(runtime["criterion_id"],),
        )
        challenge = ReviewChallenge.issue(review_capsule, now=datetime.now(UTC), lifetime=timedelta(hours=1))
        trust = signer.trust_root
        receipt = Stage6CandidateReceipt(
            run_id=run_id,
            status="PASS_AWAITING_NILHAN_PROTECTED_REVIEW",
            assurance="STAGE_6_WINDOWS_DOCKER_LOW_MODERATE_CANDIDATE",
            generator_version="laos-stage6-candidate/1.0.0",
            source_commit=source_commit,
            source_tree=source_tree,
            plan_digest=plan_digest,
            started_at_utc=started.isoformat().replace("+00:00", "Z"),
            completed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            commands=commands,
            stage4_model_proposal_digest="sha256:" + digest(proposal_path.read_bytes()),
            stage4_original_result_commit=runtime["result_commit"],
            replay_verification=verification,
            protected_check_bundle=bundle,
            custody_object=custody_object,
            evidence_index=index,
            event_anchor_key_id=trust.key_id,
            event_anchor_public_key_b64=trust.public_key_b64,
            review_challenge=challenge,
            release_blockers_open=("RB-011", "RB-012", "RB-013", "RB-014"),
        )
    output_root = args.output_root.resolve()
    evidence = output_root / "Evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    candidate_path = evidence / "STAGE_6_COMPLETION_CANDIDATE.json"
    challenge_path = evidence / "STAGE_6_REVIEW_CHALLENGE.json"
    if candidate_path.exists() or challenge_path.exists():
        raise SystemExit("Stage 6 candidate output already exists")
    candidate_path.write_bytes(canonical_json(receipt) + b"\n")
    challenge_path.write_bytes(canonical_json(receipt.review_challenge) + b"\n")
    print(json.dumps({"status": receipt.status, "run_id": run_id, "source_commit": source_commit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
