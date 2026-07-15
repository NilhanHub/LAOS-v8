#!/usr/bin/env python3
"""Verify the unapproved Stage 6 candidate without creating approval."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from laos_v8.canonical import canonical_json
from laos_v8.evidence_custody import DockerEvidenceCustodian, verify_evidence_index
from laos_v8.protected_checks import ProtectedCheckStore
from laos_v8.protected_review import ReviewChallenge
from laos_v8.signing import PublicTrustRoot
from laos_v8.stage6_candidate import Stage6CandidateReceipt

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LABELS = {
    "uv_sync", "ruff_changed", "ruff_baseline", "mypy", "pytest_full", "package_build", "verify_stage1",
    "verify_stage2",
    "generate_stage3", "verify_stage3", "verify_stage4", "verify_stage5", "verify_stage6_controls",
    "sandbox_conformance",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git(*args: str) -> str:
    executable = shutil.which("git")
    require(executable is not None, "Git is unavailable")
    completed = subprocess.run(  # noqa: S603 - resolved Git and fixed verifier arguments
        [executable, "-C", str(ROOT), *args], text=True, capture_output=True, check=False, timeout=30
    )
    require(completed.returncode == 0, completed.stderr.strip() or "Git verification failed")
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=ROOT / "Evidence/STAGE_6_COMPLETION_CANDIDATE.json")
    parser.add_argument("--challenge", type=Path, default=ROOT / "Evidence/STAGE_6_REVIEW_CHALLENGE.json")
    args = parser.parse_args()
    receipt = Stage6CandidateReceipt.model_validate_json(args.candidate.read_bytes(), strict=True)
    challenge = ReviewChallenge.model_validate_json(args.challenge.read_bytes(), strict=True)
    require(canonical_json(challenge) == canonical_json(receipt.review_challenge), "review challenge differs")
    require(set(item.label for item in receipt.commands) == EXPECTED_LABELS, "candidate command policy differs")
    require(git("rev-parse", receipt.source_commit) == receipt.source_commit, "candidate source commit is missing")
    require(
        git("rev-parse", f"{receipt.source_commit}^{{tree}}") == receipt.source_tree,
        "candidate source tree differs",
    )
    plan = "sha256:" + hashlib.sha256((ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md").read_bytes()).hexdigest()
    require(receipt.plan_digest == plan, "candidate plan digest differs")
    trust = PublicTrustRoot(
        receipt.event_anchor_key_id,
        receipt.event_anchor_public_key_b64,
        "event_anchor",
        "STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR",
    )
    verify_evidence_index(
        receipt.evidence_index,
        trust=trust,
        expected_issuer="control:stage6",
        expected_audience="reviewer:nilhan",
    )
    payload = DockerEvidenceCustodian(ROOT).fetch(receipt.custody_object.object_id)
    require(
        "sha256:" + hashlib.sha256(payload).hexdigest() == receipt.custody_object.plaintext_digest,
        "custodied replay digest differs",
    )
    check_store = Path.home() / ".laos" / "protected_checks" / "stage6" / receipt.run_id.removeprefix("run:")
    ProtectedCheckStore(check_store).verify(
        receipt.protected_check_bundle.bundle_id,
        trust=trust,
        expected_issuer="control:stage6",
        expected_audience="verifier:clean",
    )
    require(receipt.status == "PASS_AWAITING_NILHAN_PROTECTED_REVIEW", "candidate status is overstated")
    print(
        json.dumps(
            {
                "status": "PASS_AWAITING_NILHAN_PROTECTED_REVIEW",
                "run_id": receipt.run_id,
                "source_commit": receipt.source_commit,
                "release_blockers_open": list(receipt.release_blockers_open),
            },
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
