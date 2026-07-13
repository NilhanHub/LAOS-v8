from __future__ import annotations

from laos_v8.models import ActorIdentity, Role, SideEffectRecord
from laos_v8.side_effect_contract import attempt_verification

NOW = "2026-07-13T00:00:00Z"
DIGEST = "sha256:" + "0" * 64


def test_unauthorized_builder_is_denied_before_external_operation() -> None:
    record = SideEffectRecord(
        record_id="side-effect:effect-1",
        project_id="project:demo",
        created_at=NOW,
        operation="PUBLISH_RELEASE",
        payload_digest=DIGEST,
        state="dispatched",
    )
    actor = ActorIdentity(
        record_id="actor:builder-1",
        project_id="project:demo",
        created_at=NOW,
        principal="local:test-builder",
        roles=(Role.BUILDER,),
        identity_issuer="local:test-issuer",
    )
    external_calls = 0

    def external_operation() -> None:
        nonlocal external_calls
        external_calls += 1

    updated, result = attempt_verification(record, actor, NOW, external_operation)

    assert external_calls == 0
    assert result.status == "denied"
    assert result.error is not None
    assert result.error["code"] == "SIDE_EFFECT_VERIFY_ROLE_DENIED"
    assert updated.model_copy(update={"audit": record.audit}) == record
    assert len(updated.audit) == 1
    assert updated.audit[0].outcome == "denied"
    assert updated.audit[0].error_code == "SIDE_EFFECT_VERIFY_ROLE_DENIED"
