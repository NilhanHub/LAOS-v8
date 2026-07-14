from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from laos_v8.errors import AuthorizationDenied, PolicyDenied, ReviewError, StateConflict, ValidationError
from laos_v8.identity import IdentityService, require_independent
from laos_v8.models import RiskTier, Role
from laos_v8.policy import PermissionRequest, PolicyEngine, ResourceBudget, minimal_stage3_policy
from laos_v8.state import CanonicalState


def test_transactional_state_audit_cas_claim_and_backup(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    with CanonicalState(database) as state:
        assert state.connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        created = state.create_aggregate("task:one", "task", "planned", {"value": 1}, "actor:architect")
        transitioned = state.transition(
            created.aggregate_id,
            expected_version=0,
            target_state="ready",
            payload={"value": 2},
            actor_id="actor:architect",
        )
        assert transitioned.version == 1
        assert state.connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 2
        with pytest.raises(StateConflict) as captured:
            state.transition(
                created.aggregate_id,
                expected_version=0,
                target_state="active",
                payload={"value": 3},
                actor_id="actor:architect",
            )
        assert captured.value.code == "STATE_VERSION_CONFLICT"
        state.claim_action("action:one", "actor:builder-a", "sha256:" + "0" * 64, "2099-01-01T00:00:00Z")
        with pytest.raises(StateConflict) as captured:
            state.claim_action("action:one", "actor:builder-b", "sha256:" + "0" * 64, "2099-01-01T00:00:00Z")
        assert captured.value.code == "ACTION_ALREADY_CLAIMED"
        state.integrity_check()
        backup = tmp_path / "backup.sqlite3"
        assert state.backup(backup).startswith("sha256:")
        assert backup.is_file()
        epoch = state.set_emergency_stop("actor:architect", "contain test")
        with pytest.raises(StateConflict):
            state.recover_trust("actor:architect", "wrong epoch", expected_epoch=epoch - 1)
        assert state.recover_trust("actor:architect", "reviewed recovery", expected_epoch=epoch) == epoch + 1
    restored = tmp_path / "restored.sqlite3"
    assert CanonicalState.restore(backup, restored).startswith("sha256:")
    with CanonicalState(restored) as state:
        assert state.get_aggregate("task:one").state == "ready"
        assert state.control_status() == (False, 0, "")
    backup.unlink()
    assert not backup.exists()


def test_existing_state_version_is_never_guessed_or_silently_upgraded(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(legacy) as connection:
        connection.execute("CREATE TABLE control_state(singleton INTEGER PRIMARY KEY)")
        connection.execute("PRAGMA user_version = 1")
    with pytest.raises(ValidationError) as captured:
        CanonicalState(legacy)
    assert captured.value.code == "STATE_SCHEMA_VERSION_UNSUPPORTED"


def test_identity_uses_hashed_tokens_epoch_grants_and_real_independence(tmp_path: Path, digest: str) -> None:
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        service = IdentityService(state)
        token = service.register(
            actor_id="actor:builder",
            principal="local:builder",
            roles=(Role.BUILDER,),
            session_fingerprint="session-a",
            workspace_id="workspace-a",
            expires_at="2099-01-01T00:00:00Z",
            revocation_epoch=0,
        )
        assert token not in state.path.read_bytes().decode("latin1")
        actor = service.authenticate(token, required_epoch=0)
        service.grant(
            actor_id=actor.actor_id,
            project_id="project:stage3",
            base_seal=digest,
            audience="broker:stage3",
            capabilities=("WORKSPACE_WRITE",),
            policy_digest=digest,
            expires_at="2099-01-01T00:00:00Z",
            revocation_epoch=0,
        )
        service.require_capability(
            actor,
            "WORKSPACE_WRITE",
            project_id="project:stage3",
            base_seal=digest,
            audience="broker:stage3",
            policy_digest=digest,
            required_epoch=0,
        )
        with pytest.raises(AuthorizationDenied):
            service.require_capability(
                actor,
                "WORKSPACE_WRITE",
                project_id="project:other",
                base_seal=digest,
                audience="broker:stage3",
                policy_digest=digest,
                required_epoch=0,
            )
        with pytest.raises(AuthorizationDenied):
            service.authenticate(token, required_epoch=1)

        reviewer_token = service.register(
            actor_id="actor:reviewer",
            principal="local:reviewer",
            roles=(Role.REVIEWER,),
            session_fingerprint="session-b",
            workspace_id="workspace-b",
            expires_at="2099-01-01T00:00:00Z",
            revocation_epoch=0,
        )
        reviewer = service.authenticate(reviewer_token, required_epoch=0)
        require_independent(actor, reviewer)
        with pytest.raises(ReviewError):
            require_independent(
                actor, reviewer.__class__(reviewer.actor_id, actor.principal, reviewer.roles, "x", "y", 0)
            )


def test_policy_is_default_deny_and_fails_closed(actor_factory: Callable[..., object]) -> None:
    actor = actor_factory()
    profile = minimal_stage3_policy()
    engine = PolicyEngine(profile)
    allowed = PermissionRequest(
        capability="WORKSPACE_WRITE",
        policy_digest=profile.digest,
        policy_version=profile.version,
        risk=RiskTier.MODERATE,
        relative_path="src/app.py",
    )
    assert engine.require(actor, allowed, emergency_stopped=False).decision == "allow"

    variants = [
        {"network": True},
        {"secret_names": ("TOKEN",)},
        {"side_effect": True},
        {"relative_path": "docs/private.md"},
        {"instruction_source": "repository"},
        {"risk": RiskTier.HIGH},
        {"risk": RiskTier.CRITICAL},
        {"policy_version": 0},
        {"budget": ResourceBudget(memory_bytes=999_999_999)},
    ]
    for changes in variants:
        request = replace(allowed, **changes)
        with pytest.raises(PolicyDenied):
            engine.require(actor, request, emergency_stopped=False)
    with pytest.raises(PolicyDenied):
        engine.require(actor, allowed, emergency_stopped=True)
