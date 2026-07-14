from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from laos_v8.action_engine import ActionNode
from laos_v8.canonical import canonical_json
from laos_v8.capture import (
    CAPTURE_RETURN_MEDIA_TYPE,
    AppIntelligenceReturn,
    ArchitectCaptureAcceptance,
    CaptureFact,
    FactDisposition,
    compile_continuation,
    create_capture_request,
    validate_capture_return,
)
from laos_v8.errors import AuthorizationDenied
from laos_v8.signing import ProtectedTestSigner


def _git(root: Path, *args: str) -> None:
    executable = shutil.which("git")
    assert executable is not None
    subprocess.run(  # noqa: S603 - resolved executable and fixture-controlled arguments
        [executable, "-C", str(root), *args], check=True, capture_output=True, text=True
    )


def _repository(root: Path) -> Path:
    root.mkdir()
    (root / "app.txt").write_text("bounded\n", encoding="utf-8")
    _git(root, "init", "--initial-branch=main")
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture.invalid", "commit", "-m", "fixture")
    return root


def _action() -> ActionNode:
    return ActionNode(
        action_id="action:first",
        title="First",
        objective="Continue safely",
        criterion_ids=("criterion:first",),
        allowed_files=("app.txt",),
        permissions=("WORKSPACE_READ",),
        max_attempts=1,
    )


def _return_envelope(
    request: object,
    signer: ProtectedTestSigner,
    *,
    fact_at: str,
    completed_at: str,
    envelope_issued_at: str,
):
    fact = CaptureFact(
        fact_id="fact:one",
        area="repository_identity_environment",
        statement="The bounded fixture exists.",
        evidence_refs=("evidence:fixture",),
        confidence=1.0,
        contradictions=(),
        unknowns=(),
        data_classification="internal",
        captured_at=fact_at,
        freshness_seconds=3600,
    )
    returned = AppIntelligenceReturn(
        capture_id=request.capture_id,  # type: ignore[attr-defined]
        project_id=request.project_id,  # type: ignore[attr-defined]
        repository_seal=request.repository_seal,  # type: ignore[attr-defined]
        capture_tool=request.capture_tool,  # type: ignore[attr-defined]
        capture_tool_version=request.capture_tool_version,  # type: ignore[attr-defined]
        facts=(fact,),
        completed_at=completed_at,
    )
    envelope = signer.sign(
        canonical_json(returned),
        payload_type=CAPTURE_RETURN_MEDIA_TYPE,
        key_purpose="event_anchor",
        issuer="capture:broker",
        audience="architect:stage5",
        issued_at=envelope_issued_at,
        expires_at="2026-07-13T02:00:00Z",
    )
    return returned, envelope


def _request(repo: Path):
    return create_capture_request(
        repo,
        capture_id="capture:clock",
        project_id="project:clock",
        capture_tool="capture",
        capture_tool_version="1",
        issued_at="2026-07-13T00:00:00Z",
        expires_at="2026-07-13T02:00:00Z",
    )[0]


def test_capture_allows_exactly_five_minutes_of_positive_skew(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo")
    request = _request(repo)
    signer = ProtectedTestSigner("event_anchor")
    returned, envelope = _return_envelope(
        request,
        signer,
        fact_at="2026-07-13T01:05:00Z",
        completed_at="2026-07-13T01:05:00Z",
        envelope_issued_at="2026-07-13T01:05:00Z",
    )
    now = datetime(2026, 7, 13, 1, tzinfo=UTC)
    validated = validate_capture_return(
        request,
        envelope,
        repository=repo,
        verifier=signer.trust_root.verifier(),
        expected_issuer="capture:broker",
        expected_audience="architect:stage5",
        now=now,
    )
    acceptance = ArchitectCaptureAcceptance(
        acceptance_id="acceptance:clock",
        capture_digest=validated.capture_digest,
        architect_principal="architect:nilhan-system",
        human_reviewer="Nilhan",
        dispositions=(FactDisposition(fact_id=returned.facts[0].fact_id, status="accepted", rationale="Bounded."),),
        preservation_rules=("preserve fixture",),
        continuation_constraints=("remain read-only",),
        accepted_at="2026-07-13T01:00:00Z",
    )
    result = compile_continuation(repo, validated, acceptance, first_action=_action(), now=now)
    assert result.accepted_fact_ids == ("fact:one",)


@pytest.mark.parametrize(
    ("fact_at", "completed_at", "envelope_issued_at", "code"),
    (
        (
            "2026-07-13T01:05:01Z",
            "2026-07-13T01:00:00Z",
            "2026-07-13T01:00:00Z",
            "CAPTURE_FACT_IN_FUTURE",
        ),
        (
            "2026-07-13T01:01:00Z",
            "2026-07-13T01:00:00Z",
            "2026-07-13T01:00:00Z",
            "CAPTURE_CHRONOLOGY_INVALID",
        ),
        (
            "2026-07-13T01:05:01Z",
            "2026-07-13T01:05:01Z",
            "2026-07-13T01:05:01Z",
            "CAPTURE_RETURN_NOT_YET_VALID",
        ),
    ),
)
def test_capture_rejects_future_and_impossible_chronology(
    tmp_path: Path,
    fact_at: str,
    completed_at: str,
    envelope_issued_at: str,
    code: str,
) -> None:
    repo = _repository(tmp_path / "repo")
    request = _request(repo)
    signer = ProtectedTestSigner("event_anchor")
    _, envelope = _return_envelope(
        request,
        signer,
        fact_at=fact_at,
        completed_at=completed_at,
        envelope_issued_at=envelope_issued_at,
    )
    with pytest.raises(AuthorizationDenied) as denied:
        validate_capture_return(
            request,
            envelope,
            repository=repo,
            verifier=signer.trust_root.verifier(),
            expected_issuer="capture:broker",
            expected_audience="architect:stage5",
            now=datetime(2026, 7, 13, 1, tzinfo=UTC),
        )
    assert denied.value.code == code


def test_capture_rejects_signed_events_before_request_issuance(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo")
    request = _request(repo)
    signer = ProtectedTestSigner("event_anchor")
    _, envelope = _return_envelope(
        request,
        signer,
        fact_at="2026-07-12T23:59:57Z",
        completed_at="2026-07-12T23:59:58Z",
        envelope_issued_at="2026-07-12T23:59:59Z",
    )
    with pytest.raises(AuthorizationDenied) as denied:
        validate_capture_return(
            request,
            envelope,
            repository=repo,
            verifier=signer.trust_root.verifier(),
            expected_issuer="capture:broker",
            expected_audience="architect:stage5",
            now=datetime(2026, 7, 13, 1, tzinfo=UTC),
        )
    assert denied.value.code == "CAPTURE_BEFORE_REQUEST_ISSUED"
