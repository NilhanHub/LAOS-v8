from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from laos_v8.alpha import (
    AlphaVerdict,
    EditProposal,
    apply_and_submit,
    parse_bounded_proposal,
    promote_reviewed,
    reconcile_promotion,
    review_result,
)
from laos_v8.brokers import WorkspaceBroker
from laos_v8.errors import (
    AuthorizationDenied,
    EvidenceError,
    PolicyDenied,
    RepositoryDrift,
    ReviewError,
    SecurityError,
    ValidationError,
)
from laos_v8.evidence import EvidenceBroker
from laos_v8.models import RiskTier, Role
from laos_v8.policy import PermissionRequest, PolicyEngine, minimal_stage4_alpha_policy
from laos_v8.repository_truth import build_manifest
from laos_v8.state import CanonicalState
from laos_v8.workspace import CandidateWorkspace


def test_strict_proposal_contract() -> None:
    output = json.dumps({"relative_path": "src/calculator.py", "replacement": "def add(a, b):\n    return a + b\n"})
    assert parse_bounded_proposal(output, allowed_path="src/calculator.py").replacement.endswith("\n")
    with pytest.raises(SecurityError, match="outside the signed action"):
        parse_bounded_proposal(
            json.dumps({"relative_path": "tests/test_acceptance.py", "replacement": "pass\n"}),
            allowed_path="src/calculator.py",
        )
    with pytest.raises(ValidationError):
        parse_bounded_proposal("not-json", allowed_path="src/calculator.py")


def test_alpha_policy_denies_out_of_scope_network_secrets_future_actions_and_commands(
    actor_factory: Callable[..., Any],
) -> None:
    actor = actor_factory("builder:alpha", Role.BUILDER)
    profile = minimal_stage4_alpha_policy()
    policy = PolicyEngine(profile)
    base = dict(
        capability="WORKSPACE_WRITE",
        policy_digest=profile.digest,
        policy_version=profile.version,
        risk=RiskTier.MODERATE,
    )
    allowed = policy.evaluate(
        actor,
        PermissionRequest(**base, relative_path="src/calculator.py"),
        emergency_stopped=False,
    )
    assert allowed.decision == "allow"
    denied = (
        PermissionRequest(**base, relative_path="tests/test.py"),
        PermissionRequest(**base, relative_path="../escape.py"),
        PermissionRequest(**base, relative_path="src/calculator.py", network=True),
        PermissionRequest(**base, relative_path="src/calculator.py", secret_names=("TOKEN",)),
        PermissionRequest(**base, relative_path="src/calculator.py", side_effect=True),
        PermissionRequest(**base, relative_path="src/calculator.py", instruction_source="model"),
        PermissionRequest(**base, relative_path="src/calculator.py", argv=("powershell", "-Command", "whoami")),
    )
    for request in denied:
        with pytest.raises((PolicyDenied, SecurityError, ValidationError)):
            policy.require(actor, request, emergency_stopped=False)


def test_submit_independent_review_promotion_and_reconciliation(
    alpha_repo: Callable[[], Path], tmp_path: Path, actor_factory: Callable[..., Any]
) -> None:
    source = alpha_repo()
    candidate = CandidateWorkspace.create(source, tmp_path / "candidate")
    profile = minimal_stage4_alpha_policy()
    policy = PolicyEngine(profile)
    builder = actor_factory("builder:alpha", Role.BUILDER)
    reviewer = actor_factory("reviewer:alpha", Role.REVIEWER)
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        submission = apply_and_submit(
            candidate,
            WorkspaceBroker(candidate.root, state, policy),
            builder,
            EditProposal(
                relative_path="src/calculator.py",
                replacement="def add(a: int, b: int) -> int:\n    return a + b\n",
            ),
            policy_version=profile.version,
            policy_digest=profile.digest,
        )
        evidence_broker = EvidenceBroker(tmp_path / "evidence", state)
        evidence = evidence_broker.capture(
            b'{"exit_code": 0}',
            result_seal=submission.result.seal,
            criterion_id="criterion:alpha-addition",
            classification="internal",
            collector="test-verifier",
            actor_id="verifier:alpha",
        )
        verdict = review_result(
            builder=builder,
            reviewer=reviewer,
            evidence_broker=evidence_broker,
            evidence=evidence,
            result_seal=submission.result.seal,
            check_exit_code=0,
        )
        assert reconcile_promotion(source, submission, target_ref="refs/heads/master") == "retry_safe"
        assert promote_reviewed(source, submission, verdict, target_ref="refs/heads/master").status == "PROMOTED"
        assert reconcile_promotion(source, submission, target_ref="refs/heads/master") == "already_promoted"


def test_self_review_stale_base_and_evidence_mutation_are_denied(
    alpha_repo: Callable[[], Path], tmp_path: Path, actor_factory: Callable[..., Any]
) -> None:
    source = alpha_repo()
    candidate = CandidateWorkspace.create(source, tmp_path / "candidate")
    profile = minimal_stage4_alpha_policy()
    builder = actor_factory("builder:alpha", Role.BUILDER)
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        submission = apply_and_submit(
            candidate,
            WorkspaceBroker(candidate.root, state, PolicyEngine(profile)),
            builder,
            EditProposal(relative_path="src/calculator.py", replacement="def add(a, b):\n    return a + b\n"),
            policy_version=profile.version,
            policy_digest=profile.digest,
        )
        evidence_broker = EvidenceBroker(tmp_path / "evidence", state)
        evidence = evidence_broker.capture(
            b"proof",
            result_seal=submission.result.seal,
            criterion_id="criterion:alpha-addition",
            classification="internal",
            collector="test-verifier",
            actor_id="verifier:alpha",
        )
        with pytest.raises(ReviewError):
            review_result(
                builder=builder,
                reviewer=builder,
                evidence_broker=evidence_broker,
                evidence=evidence,
                result_seal=submission.result.seal,
                check_exit_code=0,
            )
        (evidence_broker.root.root / evidence.relative_path).write_bytes(b"mutated")
        with pytest.raises(EvidenceError):
            evidence_broker.verify(evidence)

        other = source / "src" / "concurrent.py"
        other.write_text("VALUE = 1\n", encoding="utf-8")
        git = shutil.which("git")
        assert git
        subprocess.run([git, "-C", str(source), "add", "--all"], check=True)  # noqa: S603
        subprocess.run(  # noqa: S603
            [git, "-C", str(source), "commit", "-m", "concurrent"],
            check=True,
            capture_output=True,
        )
        verdict = AlphaVerdict("pass", "reviewer:alpha", evidence.digest, submission.result.seal)
        with pytest.raises(RepositoryDrift):
            promote_reviewed(source, submission, verdict, target_ref="refs/heads/master")
        assert reconcile_promotion(source, submission, target_ref="refs/heads/master") == "conflict"


def test_result_seal_reconstructs_from_candidate(alpha_repo: Callable[[], Path], tmp_path: Path) -> None:
    candidate = CandidateWorkspace.create(alpha_repo(), tmp_path / "candidate")
    (candidate.root / "src" / "calculator.py").write_bytes(b"def add(a, b):\n    return a + b\n")
    _, result = candidate.commit()
    reconstructed = candidate.reconstruct(tmp_path / "reconstructed")
    assert reconstructed.seal == result.seal
    assert build_manifest(tmp_path / "reconstructed", seal_kind="result").seal == result.seal


def test_redemption_and_verification_crash_boundaries_reconcile_after_reopen(tmp_path: Path) -> None:
    state_path = tmp_path / "state.sqlite3"
    digest = "sha256:" + "7" * 64
    with CanonicalState(state_path) as state:
        state.redeem_capsule("capsule:crash", "builder:alpha", 1, "token-hash")
    with CanonicalState(state_path) as reopened:
        with pytest.raises(AuthorizationDenied) as replay:
            reopened.redeem_capsule("capsule:crash", "builder:alpha", 1, "token-hash")
        assert replay.value.code == "CAPSULE_REPLAY_DENIED"
        broker = EvidenceBroker(tmp_path / "evidence", reopened)
        first = broker.capture(
            b"deterministic verifier report",
            result_seal=digest,
            criterion_id="criterion:alpha-addition",
            classification="internal",
            collector="verifier:alpha",
            actor_id="verifier:alpha",
        )
    with CanonicalState(state_path) as reopened_again:
        broker = EvidenceBroker(tmp_path / "evidence", reopened_again)
        repeated = broker.capture(
            b"deterministic verifier report",
            result_seal=digest,
            criterion_id="criterion:alpha-addition",
            classification="internal",
            collector="verifier:alpha",
            actor_id="verifier:alpha",
        )
        assert repeated.digest == first.digest
        assert broker.verify(repeated) == b"deterministic verifier report"
