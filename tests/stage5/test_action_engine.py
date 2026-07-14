from __future__ import annotations

from datetime import UTC, datetime

import pytest

from laos_v8.action_engine import (
    AMENDMENT_MEDIA_TYPE,
    ActionAmendment,
    ActionEngine,
    ActionNode,
    CriterionPlan,
    PlanSubmission,
    UnderstandSubmission,
)
from laos_v8.canonical import canonical_json
from laos_v8.errors import AuthorizationDenied, SecurityError, StateConflict, ValidationError
from laos_v8.models import TypedEnvelope
from laos_v8.signing import ProtectedTestSigner


def action(
    number: int,
    *,
    depends_on: tuple[str, ...] = (),
    max_attempts: int = 3,
    fresh: bool = False,
) -> ActionNode:
    return ActionNode(
        action_id=f"action:{number}",
        title=f"Action {number}",
        objective=f"Objective {number} SECRET_FUTURE_{number}",
        criterion_ids=(f"criterion:{number}:a", f"criterion:{number}:b"),
        depends_on=depends_on,
        allowed_files=(f"src/action_{number}.py", f"tests/test_action_{number}.py"),
        permissions=("WORKSPACE_READ", "MEDIATED_WRITE"),
        max_attempts=max_attempts,
        require_fresh_session=fresh,
    )


def engine(*, fresh: bool = False, max_attempts: int = 3) -> ActionEngine:
    return ActionEngine(
        "chain:stage5",
        (
            action(1, fresh=fresh, max_attempts=max_attempts),
            action(2, depends_on=("action:1",)),
        ),
    )


def understand(node: ActionNode) -> UnderstandSubmission:
    return UnderstandSubmission(
        action_id=node.action_id,
        objective=node.objective,
        criterion_ids=node.criterion_ids,
        invariants=("preserve signed authority",),
        non_goals=("do not reveal future work",),
        preservation_rules=("retain history",),
        allowed_scope=node.allowed_files,
        forbidden_scope=("secrets/",),
        unknowns=(),
        source_references=(node.allowed_files[0],),
        verification_strategy=("run criterion checks",),
    )


def plan(node: ActionNode) -> PlanSubmission:
    return PlanSubmission(
        action_id=node.action_id,
        mappings=tuple(
            CriterionPlan(
                criterion_id=criterion_id,
                files=(node.allowed_files[index],),
                intended_changes=("bounded implementation",),
                checks=("focused test",),
                failure_paths=("fail closed",),
                preservation_checks=("scope unchanged",),
                evidence=("test transcript",),
                recovery=("return to PLAN",),
            )
            for index, criterion_id in enumerate(node.criterion_ids)
        ),
    )


def advance_to_awaiting(subject: ActionEngine, *, session: str = "session:existing") -> ActionNode:
    node = subject.current.action
    subject.submit_understand(understand(node))
    subject.submit_plan(plan(node))
    return subject.issue_implementation(session_fingerprint=session)


def signed_amendment(
    subject: ActionEngine,
    signer: ProtectedTestSigner,
    replacement: ActionNode,
    *,
    amendment_id: str = "amendment:one",
    chain_id: str = "chain:stage5",
    issued_at: str = "2026-07-13T00:00:00Z",
    expires_at: str = "2026-07-14T00:00:00Z",
) -> TypedEnvelope:
    amendment = ActionAmendment(
        amendment_id=amendment_id,
        chain_id=chain_id,
        supersedes_action_id=subject.current.action.action_id,
        replacement=replacement,
        reason="signed correction",
    )
    payload = canonical_json(amendment.model_dump(mode="json"))
    return signer.sign(
        payload,
        payload_type=AMENDMENT_MEDIA_TYPE,
        key_purpose="event_anchor",
        issuer="authority:stage5",
        audience="engine:stage5",
        issued_at=issued_at,
        expires_at=expires_at,
    )


def test_only_current_action_is_public_and_phase_skips_are_denied() -> None:
    subject = engine()
    public = subject.current.model_dump_json()
    assert "action:1" in public
    assert "SECRET_FUTURE_2" not in public
    assert "action:2" not in public
    with pytest.raises(StateConflict) as denied:
        subject.submit_plan(plan(subject.current.action))
    assert denied.value.code == "ACTION_PHASE_SKIP_DENIED"
    with pytest.raises(StateConflict):
        subject.issue_implementation(session_fingerprint="session:existing")


def test_understand_requires_exact_binding_criteria_scope_and_safe_sources() -> None:
    for mutation, expected in (
        ({"objective": "substituted"}, "UNDERSTAND_BINDING_MISMATCH"),
        ({"criterion_ids": ("criterion:1:a",)}, "UNDERSTAND_CRITERIA_INCOMPLETE"),
        ({"allowed_scope": ("src/other.py",)}, "UNDERSTAND_SCOPE_INVALID"),
    ):
        subject = engine()
        invalid = understand(subject.current.action).model_copy(update=mutation)
        with pytest.raises(ValidationError) as denied:
            subject.submit_understand(invalid)
        assert denied.value.code == expected
    subject = engine()
    unsafe = understand(subject.current.action).model_copy(update={"source_references": ("../escape",)})
    with pytest.raises(ValidationError):
        subject.submit_understand(unsafe)


def test_plan_requires_every_criterion_once_and_stays_in_scope() -> None:
    subject = engine()
    node = subject.current.action
    subject.submit_understand(understand(node))
    incomplete = plan(node).model_copy(update={"mappings": plan(node).mappings[:1]})
    with pytest.raises(ValidationError) as denied:
        subject.submit_plan(incomplete)
    assert denied.value.code == "PLAN_CRITERIA_INCOMPLETE"

    subject = engine()
    node = subject.current.action
    subject.submit_understand(understand(node))
    mappings = list(plan(node).mappings)
    mappings[0] = mappings[0].model_copy(update={"files": ("src/outside.py",)})
    with pytest.raises(ValidationError) as outside:
        subject.submit_plan(PlanSubmission(action_id=node.action_id, mappings=tuple(mappings)))
    assert outside.value.code == "PLAN_SCOPE_INVALID"


def test_fresh_session_and_criterion_acceptance_gate_future_reveal() -> None:
    subject = engine(fresh=True)
    node = subject.current.action
    subject.submit_understand(understand(node))
    subject.submit_plan(plan(node))
    with pytest.raises(AuthorizationDenied) as denied:
        subject.issue_implementation(session_fingerprint="session:old")
    assert denied.value.code == "ACTION_FRESH_SESSION_REQUIRED"
    issued = subject.issue_implementation(session_fingerprint="fresh:new")
    assert issued.action_id == "action:1"
    with pytest.raises(ValidationError) as open_criteria:
        subject.accept_current(accepted_criteria=("criterion:1:a",))
    assert open_criteria.value.code == "ACTION_CRITERIA_OPEN"
    subject.accept_current(accepted_criteria=node.criterion_ids)
    assert subject.current.action.action_id == "action:2"
    assert subject.current.phase == "UNDERSTAND"


def test_terminal_acceptance_completes_chain() -> None:
    subject = engine()
    first = advance_to_awaiting(subject)
    subject.accept_current(accepted_criteria=first.criterion_ids)
    second = advance_to_awaiting(subject)
    subject.accept_current(accepted_criteria=second.criterion_ids)
    assert subject.current.phase == "COMPLETE"
    with pytest.raises(StateConflict):
        subject.submit_understand(understand(second))


def test_failed_attempts_repair_then_escalate_on_repeat_or_budget() -> None:
    repeated = engine()
    advance_to_awaiting(repeated)
    assert repeated.record_failed_attempt(approach="one", failure="same") == "repair"
    repeated.submit_plan(plan(repeated.current.action))
    repeated.issue_implementation(session_fingerprint="session:existing")
    assert repeated.record_failed_attempt(approach="one", failure="same") == "escalate"
    assert repeated.current.phase == "BLOCKED"

    budget = engine(max_attempts=2)
    advance_to_awaiting(budget)
    assert budget.record_failed_attempt(approach="one", failure="first") == "repair"
    budget.submit_plan(plan(budget.current.action))
    budget.issue_implementation(session_fingerprint="session:existing")
    assert budget.record_failed_attempt(approach="two", failure="second") == "escalate"
    assert budget.current.phase == "BLOCKED"


def test_signed_amendment_is_bound_time_limited_replay_safe_and_historical() -> None:
    subject = engine()
    signer = ProtectedTestSigner("event_anchor")
    replacement = subject.current.action.model_copy(update={"objective": "Amended objective"})
    envelope = signed_amendment(subject, signer, replacement)
    verifier = signer.trust_root.verifier()
    subject.apply_amendment(
        envelope,
        verifier=verifier,
        expected_issuer="authority:stage5",
        expected_audience="engine:stage5",
        now=datetime(2026, 7, 13, 1, tzinfo=UTC),
    )
    assert subject.current.action.objective == "Amended objective"
    assert subject.current.amendment_count == 1
    with pytest.raises(AuthorizationDenied) as replay:
        subject.apply_amendment(
            envelope,
            verifier=verifier,
            expected_issuer="authority:stage5",
            expected_audience="engine:stage5",
            now=datetime(2026, 7, 13, 1, tzinfo=UTC),
        )
    assert replay.value.code == "AMENDMENT_REPLAY_DENIED"


@pytest.mark.parametrize(
    ("issued_at", "expires_at", "now", "code"),
    (
        ("2026-07-14T00:00:00Z", "2026-07-15T00:00:00Z", datetime(2026, 7, 13, tzinfo=UTC), "AMENDMENT_NOT_YET_VALID"),
        ("2026-07-12T00:00:00Z", "2026-07-13T00:00:00Z", datetime(2026, 7, 13, tzinfo=UTC), "AMENDMENT_EXPIRED"),
    ),
)
def test_amendment_time_window_is_enforced(
    issued_at: str,
    expires_at: str,
    now: datetime,
    code: str,
) -> None:
    subject = engine()
    signer = ProtectedTestSigner("event_anchor")
    envelope = signed_amendment(
        subject,
        signer,
        subject.current.action,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    with pytest.raises(AuthorizationDenied) as denied:
        subject.apply_amendment(
            envelope,
            verifier=signer.trust_root.verifier(),
            expected_issuer="authority:stage5",
            expected_audience="engine:stage5",
            now=now,
        )
    assert denied.value.code == code


def test_expired_amendment_cannot_be_extended_without_resigning() -> None:
    subject = engine()
    signer = ProtectedTestSigner("event_anchor")
    original = signed_amendment(
        subject,
        signer,
        subject.current.action.model_copy(update={"objective": "signed replacement"}),
        expires_at="2026-07-13T00:00:00Z",
    )
    substituted = original.model_copy(update={"expires_at": "2030-07-13T00:00:00Z"})
    with pytest.raises(SecurityError) as denied:
        subject.apply_amendment(
            substituted,
            verifier=signer.trust_root.verifier(),
            expected_issuer="authority:stage5",
            expected_audience="engine:stage5",
            now=datetime(2026, 7, 14, tzinfo=UTC),
        )
    assert denied.value.code == "SIGNATURE_INVALID"


def test_amendment_cannot_rewire_graph_or_change_active_attempt() -> None:
    subject = engine()
    signer = ProtectedTestSigner("event_anchor")
    rewired = subject.current.action.model_copy(update={"depends_on": ("action:2",)})
    envelope = signed_amendment(subject, signer, rewired)
    with pytest.raises(ValidationError) as denied:
        subject.apply_amendment(
            envelope,
            verifier=signer.trust_root.verifier(),
            expected_issuer="authority:stage5",
            expected_audience="engine:stage5",
            now=datetime(2026, 7, 13, 1, tzinfo=UTC),
        )
    assert denied.value.code == "AMENDMENT_DEPENDENCIES_CHANGED"

    active = engine()
    advance_to_awaiting(active)
    envelope = signed_amendment(active, signer, active.current.action)
    with pytest.raises(StateConflict) as phase_denied:
        active.apply_amendment(
            envelope,
            verifier=signer.trust_root.verifier(),
            expected_issuer="authority:stage5",
            expected_audience="engine:stage5",
            now=datetime(2026, 7, 13, 1, tzinfo=UTC),
        )
    assert phase_denied.value.code == "AMENDMENT_PHASE_DENIED"
