"""Deterministic Stage 5 Anti-Skip Action Engine."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json
from .errors import AuthorizationDenied, StateConflict, ValidationError
from .models import TypedEnvelope
from .safe_paths import validate_relative_path
from .signing import EnvelopeVerifier

AMENDMENT_MEDIA_TYPE = "application/vnd.nilhan.laos.action-amendment.v1+json"


class ActionNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str = Field(pattern=r"^action:[A-Za-z0-9._-]{1,120}$")
    title: str = Field(min_length=1, max_length=512)
    objective: str = Field(min_length=1, max_length=8192)
    criterion_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    depends_on: tuple[str, ...] = Field(default=(), max_length=256)
    allowed_files: tuple[str, ...] = Field(min_length=1, max_length=256)
    permissions: tuple[str, ...] = Field(max_length=128)
    max_attempts: int = Field(ge=1, le=10)
    require_fresh_session: bool = False

    @model_validator(mode="after")
    def validate_unique_and_safe(self) -> ActionNode:
        for values, code in (
            (self.criterion_ids, "ACTION_DUPLICATE_CRITERION"),
            (self.depends_on, "ACTION_DUPLICATE_DEPENDENCY"),
            (self.allowed_files, "ACTION_DUPLICATE_FILE"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(code)
        for path in self.allowed_files:
            validate_relative_path(path)
        if self.action_id in self.depends_on:
            raise ValueError("action cannot depend on itself")
        return self


class UnderstandSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str
    objective: str = Field(min_length=1, max_length=8192)
    criterion_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    invariants: tuple[str, ...] = Field(min_length=1, max_length=256)
    non_goals: tuple[str, ...] = Field(min_length=1, max_length=256)
    preservation_rules: tuple[str, ...] = Field(min_length=1, max_length=256)
    allowed_scope: tuple[str, ...] = Field(min_length=1, max_length=256)
    forbidden_scope: tuple[str, ...] = Field(min_length=1, max_length=256)
    unknowns: tuple[str, ...] = Field(max_length=256)
    source_references: tuple[str, ...] = Field(min_length=1, max_length=256)
    verification_strategy: tuple[str, ...] = Field(min_length=1, max_length=256)


class CriterionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    criterion_id: str
    files: tuple[str, ...] = Field(min_length=1, max_length=256)
    intended_changes: tuple[str, ...] = Field(min_length=1, max_length=256)
    checks: tuple[str, ...] = Field(min_length=1, max_length=256)
    failure_paths: tuple[str, ...] = Field(min_length=1, max_length=256)
    preservation_checks: tuple[str, ...] = Field(min_length=1, max_length=256)
    evidence: tuple[str, ...] = Field(min_length=1, max_length=256)
    recovery: tuple[str, ...] = Field(min_length=1, max_length=256)


class PlanSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str
    mappings: tuple[CriterionPlan, ...] = Field(min_length=1, max_length=256)


class ActionAmendment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    amendment_id: str = Field(pattern=r"^amendment:[A-Za-z0-9._-]{1,120}$")
    chain_id: str = Field(pattern=r"^chain:[A-Za-z0-9._-]{1,120}$")
    supersedes_action_id: str
    replacement: ActionNode
    reason: str = Field(min_length=1, max_length=4096)


class PublicAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action: ActionNode
    phase: Literal["UNDERSTAND", "PLAN", "IMPLEMENT", "AWAIT_ACCEPTANCE", "BLOCKED", "COMPLETE"]
    attempt_count: int
    amendment_count: int


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("amendment time is invalid", code="AMENDMENT_TIME_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValidationError("amendment time lacks an offset", code="AMENDMENT_TIME_INVALID")
    return parsed.astimezone(UTC)


class ActionEngine:
    """Expose exactly one action and refuse phase skipping at every method boundary."""

    def __init__(self, chain_id: str, actions: tuple[ActionNode, ...]) -> None:
        if not chain_id.startswith("chain:") or len(chain_id) > 128:
            raise ValidationError("chain ID is invalid", code="ACTION_CHAIN_ID_INVALID")
        if not actions:
            raise ValidationError("action graph is empty", code="ACTION_GRAPH_EMPTY")
        self.chain_id = chain_id
        self._actions = {action.action_id: action for action in actions}
        if len(self._actions) != len(actions):
            raise ValidationError("duplicate action ID", code="ACTION_DUPLICATE_ID")
        self._order = self._topological_order()
        roots = [item for item in self._order if not self._actions[item].depends_on]
        if len(roots) != 1:
            raise ValidationError("action graph must expose exactly one root", code="ACTION_MULTIPLE_READY")
        self._accepted: set[str] = set()
        self._current = roots[0]
        self._phase: Literal["UNDERSTAND", "PLAN", "IMPLEMENT", "AWAIT_ACCEPTANCE", "BLOCKED", "COMPLETE"] = (
            "UNDERSTAND"
        )
        self._attempt_fingerprints: list[str] = []
        self._amendment_history: list[str] = []

    def _topological_order(self) -> tuple[str, ...]:
        known = set(self._actions)
        for action in self._actions.values():
            missing = set(action.depends_on) - known
            if missing:
                raise ValidationError(
                    "action dependency is missing",
                    code="ACTION_DEPENDENCY_MISSING",
                    context={"action_id": action.action_id, "missing": sorted(missing)},
                )
        pending = set(known)
        resolved: list[str] = []
        while pending:
            ready = sorted(item for item in pending if set(self._actions[item].depends_on) <= set(resolved))
            if not ready:
                raise ValidationError("action graph contains a cycle", code="ACTION_GRAPH_CYCLE")
            resolved.extend(ready)
            pending.difference_update(ready)
        return tuple(resolved)

    @property
    def current(self) -> PublicAction:
        return PublicAction(
            action=self._actions[self._current],
            phase=self._phase,
            attempt_count=len(self._attempt_fingerprints),
            amendment_count=len(self._amendment_history),
        )

    def submit_understand(self, submission: UnderstandSubmission) -> None:
        if self._phase != "UNDERSTAND":
            raise StateConflict("UNDERSTAND is not current", code="ACTION_PHASE_SKIP_DENIED")
        action = self._actions[self._current]
        if submission.action_id != action.action_id or submission.objective != action.objective:
            raise ValidationError("UNDERSTAND action binding mismatch", code="UNDERSTAND_BINDING_MISMATCH")
        if set(submission.criterion_ids) != set(action.criterion_ids):
            raise ValidationError("UNDERSTAND criteria are incomplete", code="UNDERSTAND_CRITERIA_INCOMPLETE")
        if set(submission.allowed_scope) != set(action.allowed_files):
            raise ValidationError("UNDERSTAND scope differs from authority", code="UNDERSTAND_SCOPE_INVALID")
        for path in (*submission.allowed_scope, *submission.source_references):
            validate_relative_path(path)
        self._phase = "PLAN"

    def submit_plan(self, submission: PlanSubmission) -> None:
        if self._phase != "PLAN":
            raise StateConflict("PLAN is not current", code="ACTION_PHASE_SKIP_DENIED")
        action = self._actions[self._current]
        if submission.action_id != action.action_id:
            raise ValidationError("PLAN action binding mismatch", code="PLAN_BINDING_MISMATCH")
        identifiers = [mapping.criterion_id for mapping in submission.mappings]
        if len(identifiers) != len(set(identifiers)) or set(identifiers) != set(action.criterion_ids):
            raise ValidationError("PLAN criteria are incomplete or duplicated", code="PLAN_CRITERIA_INCOMPLETE")
        for mapping in submission.mappings:
            for path in mapping.files:
                normalized = validate_relative_path(path).as_posix()
                if normalized not in action.allowed_files:
                    raise ValidationError("PLAN file is outside action scope", code="PLAN_SCOPE_INVALID")
        self._phase = "IMPLEMENT"

    def issue_implementation(self, *, session_fingerprint: str) -> ActionNode:
        if self._phase != "IMPLEMENT":
            raise StateConflict("IMPLEMENT authority is unavailable", code="ACTION_PHASE_SKIP_DENIED")
        action = self._actions[self._current]
        if action.require_fresh_session and not session_fingerprint.startswith("fresh:"):
            raise AuthorizationDenied("fresh session required", code="ACTION_FRESH_SESSION_REQUIRED")
        self._phase = "AWAIT_ACCEPTANCE"
        return action

    def record_failed_attempt(self, *, approach: str, failure: str) -> Literal["repair", "escalate"]:
        if self._phase != "AWAIT_ACCEPTANCE":
            raise StateConflict("no implementation attempt is active", code="ACTION_ATTEMPT_NOT_ACTIVE")
        fingerprint = hashlib.sha256(canonical_json({"approach": approach, "failure": failure})).hexdigest()
        repeated = fingerprint in self._attempt_fingerprints
        self._attempt_fingerprints.append(fingerprint)
        action = self._actions[self._current]
        if repeated or len(self._attempt_fingerprints) >= action.max_attempts:
            self._phase = "BLOCKED"
            return "escalate"
        self._phase = "PLAN"
        return "repair"

    def accept_current(self, *, accepted_criteria: tuple[str, ...]) -> None:
        if self._phase != "AWAIT_ACCEPTANCE":
            raise StateConflict("action is not awaiting acceptance", code="ACTION_CLOSE_DENIED")
        action = self._actions[self._current]
        if set(accepted_criteria) != set(action.criterion_ids):
            raise ValidationError("not every criterion is accepted", code="ACTION_CRITERIA_OPEN")
        self._accepted.add(action.action_id)
        candidates = [
            action_id
            for action_id in self._order
            if action_id not in self._accepted and set(self._actions[action_id].depends_on) <= self._accepted
        ]
        if not candidates:
            self._phase = "COMPLETE"
            return
        self._current = candidates[0]
        self._phase = "UNDERSTAND"
        self._attempt_fingerprints.clear()

    def apply_amendment(
        self,
        envelope: TypedEnvelope,
        *,
        verifier: EnvelopeVerifier,
        expected_issuer: str,
        expected_audience: str,
        now: datetime,
    ) -> None:
        if self._phase in {"AWAIT_ACCEPTANCE", "BLOCKED", "COMPLETE"}:
            raise StateConflict("current action cannot be amended in this phase", code="AMENDMENT_PHASE_DENIED")
        payload = verifier.verify(
            envelope,
            expected_purpose="event_anchor",
            expected_payload_type=AMENDMENT_MEDIA_TYPE,
            expected_issuer=expected_issuer,
            expected_audience=expected_audience,
        )
        current_time = now.astimezone(UTC)
        if current_time < _utc(envelope.issued_at):
            raise AuthorizationDenied("amendment is not yet valid", code="AMENDMENT_NOT_YET_VALID")
        if envelope.expires_at is None or current_time >= _utc(envelope.expires_at):
            raise AuthorizationDenied("amendment is expired", code="AMENDMENT_EXPIRED")
        amendment = ActionAmendment.model_validate_json(payload, strict=True)
        if amendment.chain_id != self.chain_id or amendment.supersedes_action_id != self._current:
            raise AuthorizationDenied("amendment binding mismatch", code="AMENDMENT_BINDING_MISMATCH")
        if amendment.replacement.action_id != self._current:
            raise ValidationError("replacement action ID changed", code="AMENDMENT_ACTION_ID_CHANGED")
        current_action = self._actions[self._current]
        if amendment.replacement.depends_on != current_action.depends_on:
            raise ValidationError("replacement dependencies changed", code="AMENDMENT_DEPENDENCIES_CHANGED")
        digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if digest in self._amendment_history:
            raise AuthorizationDenied("amendment replay denied", code="AMENDMENT_REPLAY_DENIED")
        self._actions[self._current] = amendment.replacement
        self._amendment_history.append(digest)
        self._phase = "UNDERSTAND"
