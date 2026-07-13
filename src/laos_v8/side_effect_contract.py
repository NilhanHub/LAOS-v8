"""Milestone 2 in-memory authorization contract for future side effects."""

from __future__ import annotations

from collections.abc import Callable

from .errors import AuthorizationDenied
from .models import ActorIdentity, AuditEntry, Role, SideEffectRecord
from .result import ResultEnvelope


def attempt_verification(
    record: SideEffectRecord,
    actor: ActorIdentity,
    occurred_at: str,
    external_operation: Callable[[], None],
) -> tuple[SideEffectRecord, ResultEnvelope[None]]:
    if Role.VERIFIER not in actor.roles:
        error = AuthorizationDenied(
            "actor lacks side-effect verification authority",
            code="SIDE_EFFECT_VERIFY_ROLE_DENIED",
            context={"actor_id": actor.record_id, "required_role": Role.VERIFIER.value},
        )
        event = AuditEntry(
            event_code="SIDE_EFFECT_VERIFY_DENIED",
            actor_id=actor.record_id,
            occurred_at=occurred_at,
            outcome="denied",
            error_code=error.code,
        )
        updated = record.model_copy(update={"audit": (*record.audit, event)})
        return updated, ResultEnvelope.denied(error, (event.model_dump(mode="json"),))
    external_operation()
    return record, ResultEnvelope(status="ok", value=None)
