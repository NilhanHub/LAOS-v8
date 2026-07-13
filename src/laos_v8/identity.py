"""Authenticated actor identities, hashed bearer tokens, grants, and independence checks."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass

from .errors import AuthorizationDenied, ReviewError
from .models import Role
from .state import CanonicalState


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    actor_id: str
    principal: str
    roles: tuple[Role, ...]
    session_fingerprint: str
    workspace_id: str
    revocation_epoch: int


class IdentityService:
    def __init__(self, state: CanonicalState) -> None:
        self.state = state

    def register(
        self,
        *,
        actor_id: str,
        principal: str,
        roles: tuple[Role, ...],
        session_fingerprint: str,
        workspace_id: str,
        expires_at: str,
        revocation_epoch: int,
    ) -> str:
        token = secrets.token_urlsafe(32)
        digest = token_hash(token)
        with self.state.transaction() as connection:
            connection.execute(
                "INSERT INTO actors(actor_id, principal, roles_json, token_hash, session_fingerprint, workspace_id, "
                "expires_at, revocation_epoch) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    actor_id,
                    principal,
                    json.dumps([role.value for role in roles]),
                    digest,
                    session_fingerprint,
                    workspace_id,
                    expires_at,
                    revocation_epoch,
                ),
            )
            self.state._event(
                connection,
                aggregate_id=actor_id,
                actor_id="system:identity",
                event_code="ACTOR_REGISTERED",
                outcome="allowed",
                detail={"principal": principal, "roles": [role.value for role in roles]},
            )
        return token

    def grant(
        self,
        *,
        actor_id: str,
        project_id: str,
        base_seal: str,
        audience: str,
        capabilities: tuple[str, ...],
        policy_digest: str,
        expires_at: str,
        revocation_epoch: int,
    ) -> str:
        grant_id = f"grant:{uuid.uuid4().hex}"
        with self.state.transaction() as connection:
            connection.execute(
                "INSERT INTO capability_grants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    grant_id,
                    actor_id,
                    project_id,
                    base_seal,
                    audience,
                    json.dumps(capabilities),
                    policy_digest,
                    expires_at,
                    revocation_epoch,
                ),
            )
            self.state._event(
                connection,
                aggregate_id=grant_id,
                actor_id="system:identity",
                event_code="CAPABILITY_GRANTED",
                outcome="allowed",
                detail={
                    "actor_id": actor_id,
                    "project_id": project_id,
                    "base_seal": base_seal,
                    "audience": audience,
                    "capabilities": capabilities,
                },
            )
        return grant_id

    def authenticate(self, token: str, *, required_epoch: int) -> AuthenticatedActor:
        candidate = token_hash(token)
        rows = self.state.connection.execute(
            "SELECT * FROM actors WHERE disabled = 0 AND expires_at > strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
        ).fetchall()
        row = next((item for item in rows if hmac.compare_digest(str(item["token_hash"]), candidate)), None)
        if row is None:
            self.state.record_event(
                aggregate_id=None,
                actor_id="system:unauthenticated",
                event_code="IDENTITY_AUTHENTICATION_DENIED",
                outcome="denied",
                error_code="IDENTITY_AUTHENTICATION_DENIED",
            )
            raise AuthorizationDenied("actor token is invalid or expired", code="IDENTITY_AUTHENTICATION_DENIED")
        if int(row["revocation_epoch"]) != required_epoch:
            self.state.record_event(
                aggregate_id=str(row["actor_id"]),
                actor_id=str(row["actor_id"]),
                event_code="IDENTITY_EPOCH_REVOKED",
                outcome="denied",
                error_code="IDENTITY_EPOCH_REVOKED",
            )
            raise AuthorizationDenied("actor token belongs to a revoked epoch", code="IDENTITY_EPOCH_REVOKED")
        return AuthenticatedActor(
            str(row["actor_id"]),
            str(row["principal"]),
            tuple(Role(value) for value in json.loads(str(row["roles_json"]))),
            str(row["session_fingerprint"]),
            str(row["workspace_id"]),
            int(row["revocation_epoch"]),
        )

    def require_capability(
        self,
        actor: AuthenticatedActor,
        capability: str,
        *,
        project_id: str,
        base_seal: str,
        audience: str,
        policy_digest: str,
        required_epoch: int,
    ) -> None:
        rows = self.state.connection.execute(
            "SELECT * FROM capability_grants WHERE actor_id = ? AND expires_at > strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
            (actor.actor_id,),
        ).fetchall()
        for row in rows:
            capabilities = json.loads(str(row["capabilities_json"]))
            if (
                capability in capabilities
                and str(row["project_id"]) == project_id
                and str(row["base_seal"]) == base_seal
                and str(row["audience"]) == audience
                and str(row["policy_digest"]) == policy_digest
                and int(row["revocation_epoch"]) == required_epoch
            ):
                return
        self.state.record_event(
            aggregate_id=actor.actor_id,
            actor_id=actor.actor_id,
            event_code="CAPABILITY_DENIED",
            outcome="denied",
            error_code="CAPABILITY_DENIED",
            detail={
                "capability": capability,
                "project_id": project_id,
                "base_seal": base_seal,
                "audience": audience,
            },
        )
        raise AuthorizationDenied("capability grant is missing or stale", code="CAPABILITY_DENIED")


def require_independent(builder: AuthenticatedActor, reviewer: AuthenticatedActor) -> None:
    shared = {
        "actor": builder.actor_id == reviewer.actor_id,
        "principal": builder.principal == reviewer.principal,
        "session": builder.session_fingerprint == reviewer.session_fingerprint,
        "workspace": builder.workspace_id == reviewer.workspace_id,
    }
    if any(shared.values()):
        raise ReviewError(
            "reviewer is not independent of builder",
            code="REVIEW_INDEPENDENCE_FAILED",
            context={key: value for key, value in shared.items() if value},
        )
    if Role.REVIEWER not in reviewer.roles and Role.VERIFIER not in reviewer.roles:
        raise ReviewError("reviewer lacks a review role", code="REVIEW_ROLE_REQUIRED")
