from __future__ import annotations

# ruff: noqa: S603
import base64
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from laos_v8.criterion_closure import (
    CriterionController,
    CriterionEvidenceMatrix,
    CriterionState,
    GitPromoter,
    migrate_historical_criterion,
)
from laos_v8.errors import ReviewError, StateConflict, ValidationError
from laos_v8.evidence_custody import EvidenceLevel
from laos_v8.protected_review import (
    ProtectedReviewVerifier,
    QuorumParticipant,
    ReviewCapsule,
    ReviewChallenge,
    require_quorum,
)
from laos_v8.state import CanonicalState


def _digest(letter: str) -> str:
    return "sha256:" + letter * 64


def _matrix(**updates: object) -> CriterionEvidenceMatrix:
    values: dict[str, object] = {
        "criterion_id": "criterion:stage6-closure",
        "risk": "moderate",
        "required_level": EvidenceLevel.L3,
        "source_digest": _digest("a"),
        "policy_digest": _digest("b"),
        "check_bundle_digest": _digest("c"),
        "profile_digest": _digest("d"),
        "environment_digest": _digest("e"),
        "positive_evidence": (_digest("f"),),
        "negative_evidence": (_digest("1"),),
    }
    values.update(updates)
    return CriterionEvidenceMatrix(**values)


def test_full_criterion_lifecycle_and_staleness(tmp_path: Path) -> None:
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        controller = CriterionController(state)
        current = controller.create(_matrix(), actor_id="architect:nilhan")
        assert current.state == CriterionState.NOT_STARTED
        current = controller.advance(current, CriterionState.IMPLEMENTED, actor_id="builder:codex")
        current = controller.advance(current, CriterionState.EVIDENCE_READY, actor_id="broker:evidence")
        current = controller.advance(
            current,
            CriterionState.VERIFIED,
            actor_id="verifier:clean",
            verification_digest=_digest("2"),
        )
        current = controller.advance(
            current,
            CriterionState.INDEPENDENTLY_REVIEWED,
            actor_id="reviewer:nilhan",
            review_digest=_digest("3"),
        )
        current = controller.advance(current, CriterionState.PROMOTION_PENDING, actor_id="broker:promotion")
        current = controller.advance(
            current,
            CriterionState.ACCEPTED,
            actor_id="broker:promotion",
            promotion_digest=_digest("4"),
        )
        stale = controller.invalidate_if_drifted(current, _matrix(policy_digest=_digest("9")), actor_id="system:drift")
        assert stale.state == CriterionState.STALE


def test_closure_rejects_generic_or_incomplete_evidence(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="negative") as missing:
        _matrix(negative_evidence=())
    assert missing.value.code == "CRITERION_NEGATIVE_EVIDENCE_REQUIRED"
    with pytest.raises(ValidationError, match="generic") as generic:
        _matrix(positive_evidence=("PASS",))
    assert generic.value.code == "CRITERION_GENERIC_PASS_DENIED"

    with CanonicalState(tmp_path / "state.sqlite3") as state:
        controller = CriterionController(state)
        current = controller.create(_matrix(), actor_id="architect:nilhan")
        current = controller.advance(current, CriterionState.IMPLEMENTED, actor_id="builder:codex")
        with pytest.raises(StateConflict) as skipped:
            controller.advance(current, CriterionState.VERIFIED, actor_id="verifier:clean")
        assert skipped.value.code == "ILLEGAL_STATE_TRANSITION"


def test_historical_migration_never_guesses() -> None:
    assert migrate_historical_criterion("open") == CriterionState.NOT_STARTED
    with pytest.raises(ValidationError, match="evidence") as ambiguous:
        migrate_historical_criterion("accepted")
    assert ambiguous.value.code == "MIGRATION_EVIDENCE_REQUIRED"
    assert (
        migrate_historical_criterion("accepted", evidence_bound=True, reviewed=True, promoted=True)
        == CriterionState.ACCEPTED
    )


def test_git_promotion_uses_compare_and_swap(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run([git, "init", "-q", "-b", "master"], cwd=repository, check=True)
    subprocess.run([git, "config", "user.email", "stage6@example.invalid"], cwd=repository, check=True)
    subprocess.run([git, "config", "user.name", "Stage 6"], cwd=repository, check=True)
    (repository / "proof.txt").write_text("one\n", encoding="utf-8")
    subprocess.run([git, "add", "proof.txt"], cwd=repository, check=True)
    subprocess.run([git, "commit", "-qm", "one"], cwd=repository, check=True)
    base = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    subprocess.run([git, "checkout", "-qb", "candidate"], cwd=repository, check=True)
    (repository / "proof.txt").write_text("two\n", encoding="utf-8")
    subprocess.run([git, "commit", "-qam", "two"], cwd=repository, check=True)
    target = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    receipt = GitPromoter(repository).promote("refs/heads/master", expected_commit=base, target_commit=target)
    assert receipt.promoted and receipt.reconciled
    with pytest.raises(StateConflict) as conflict:
        GitPromoter(repository).promote("refs/heads/master", expected_commit=base, target_commit=target)
    assert conflict.value.code == "PROMOTION_COMPARE_AND_SWAP_CONFLICT"


def _challenge(now: datetime) -> ReviewChallenge:
    capsule = ReviewCapsule(
        candidate_commit="a" * 40,
        source_tree="b" * 40,
        plan_digest=_digest("a"),
        policy_digest=_digest("b"),
        criteria_digest=_digest("c"),
        evidence_index_digest=_digest("d"),
        check_bundle_digest=_digest("e"),
        verification_digest=_digest("f"),
    )
    return ReviewChallenge.issue(capsule, now=now, lifetime=timedelta(minutes=15))


def test_ssh_review_signature_is_bound_expiring_and_single_use(tmp_path: Path) -> None:
    ssh_keygen = shutil.which("ssh-keygen")
    assert ssh_keygen is not None
    private = tmp_path / "id_ed25519"
    subprocess.run([ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(private)], check=True)
    now = datetime.now(UTC).replace(microsecond=0)
    challenge = _challenge(now)
    payload = challenge.canonical_bytes()
    payload_file = tmp_path / "challenge.json"
    payload_file.write_bytes(payload)
    subprocess.run(
        [ssh_keygen, "-Y", "sign", "-f", str(private), "-n", "laos-v8-review", str(payload_file)],
        check=True,
    )
    signature = base64.b64encode((tmp_path / "challenge.json.sig").read_bytes()).decode("ascii")
    verifier = ProtectedReviewVerifier("nilhan", (tmp_path / "id_ed25519.pub").read_text(encoding="utf-8"))
    record = verifier.verify_and_record(challenge, signature, verdicts={"criterion:stage6-closure": "ACCEPT"}, now=now)
    assert record.reviewer_id == "nilhan"
    with pytest.raises(ReviewError) as replay:
        verifier.verify_and_record(challenge, signature, verdicts={"criterion:stage6-closure": "ACCEPT"}, now=now)
    assert replay.value.code == "REVIEW_CHALLENGE_REPLAY"

    expired = _challenge(now - timedelta(hours=1))
    with pytest.raises(ReviewError) as expiry:
        ProtectedReviewVerifier("nilhan", (tmp_path / "id_ed25519.pub").read_text()).verify_and_record(
            expired, signature, verdicts={"criterion:stage6-closure": "ACCEPT"}, now=now
        )
    assert expiry.value.code == "REVIEW_CHALLENGE_EXPIRED"


def test_critical_quorum_rejects_shared_control_and_unavailable_profile() -> None:
    nilhan = QuorumParticipant(
        principal_id="nilhan", role="human", key_id="key:nilhan", session_id="s1", workspace_id="w1",
        controller_id="controller:nilhan"
    )
    verifier = QuorumParticipant(
        principal_id="verifier:a", role="verifier", key_id="key:a", session_id="s2", workspace_id="w2",
        controller_id="controller:codex"
    )
    with pytest.raises(ReviewError) as unavailable:
        require_quorum((nilhan, verifier), risk="critical")
    assert unavailable.value.code == "QUORUM_UNAVAILABLE"
    duplicate = QuorumParticipant(
        principal_id="verifier:b", role="verifier", key_id="key:b", session_id="s3", workspace_id="w3",
        controller_id="controller:codex"
    )
    with pytest.raises(ReviewError) as shared:
        require_quorum((nilhan, verifier, duplicate), risk="critical")
    assert shared.value.code == "FALSE_INDEPENDENCE"
