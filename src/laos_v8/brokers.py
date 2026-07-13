"""Complete-mediation workspace and command brokers for the Stage 3 profile."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import AuthorizationDenied, PolicyDenied
from .evidence import CapturedEvidence, EvidenceBroker
from .identity import AuthenticatedActor
from .models import RiskTier
from .policy import PermissionRequest, PolicyEngine, ResourceBudget
from .repository_truth import require_unchanged
from .safe_paths import SafeRoot
from .sandbox import DockerSandbox, SandboxRequest, SandboxResult
from .state import CanonicalState


@dataclass(frozen=True, slots=True)
class BrokeredCommand:
    result: SandboxResult
    evidence: CapturedEvidence


class ActionClaimBroker:
    """Bind an action claim to host-observed repository truth before recording it."""

    def __init__(self, state: CanonicalState) -> None:
        self.state = state

    def claim(
        self,
        actor: AuthenticatedActor,
        *,
        action_id: str,
        repository: Path,
        expected_base_seal: str,
        lease_expires_at: str,
    ) -> str:
        stopped, _, _ = self.state.control_status()
        if stopped:
            self.state.record_event(
                aggregate_id=action_id,
                actor_id=actor.actor_id,
                event_code="ACTION_CLAIM_DENIED",
                outcome="denied",
                error_code="EMERGENCY_STOP_ACTIVE",
            )
            raise AuthorizationDenied("emergency stop blocks action claims", code="EMERGENCY_STOP_ACTIVE")
        observed = require_unchanged(repository, expected_base_seal, seal_kind="base")
        self.state.claim_action(action_id, actor.actor_id, observed.seal, lease_expires_at)
        return observed.seal


class WorkspaceBroker:
    def __init__(self, root: Path, state: CanonicalState, policy: PolicyEngine) -> None:
        self.root = SafeRoot(root)
        self.state = state
        self.policy = policy

    def write(
        self,
        actor: AuthenticatedActor,
        relative_path: str,
        payload: bytes,
        *,
        policy_version: int,
        policy_digest: str,
        max_bytes: int = 10_485_760,
    ) -> Path:
        stopped, _, _ = self.state.control_status()
        request = PermissionRequest(
            capability="WORKSPACE_WRITE",
            policy_digest=policy_digest,
            policy_version=policy_version,
            risk=RiskTier.MODERATE,
            relative_path=relative_path,
        )
        try:
            verdict = self.policy.require(actor, request, emergency_stopped=stopped)
        except PolicyDenied as exc:
            self.state.record_event(
                aggregate_id=None,
                actor_id=actor.actor_id,
                event_code="WORKSPACE_WRITE_DENIED",
                outcome="denied",
                error_code=exc.code,
                detail={"path": relative_path, "capability": request.capability},
            )
            raise
        target = self.root.write_bytes_atomic(relative_path, payload, max_bytes=max_bytes)
        with self.state.transaction() as connection:
            self.state._event(
                connection,
                aggregate_id=None,
                actor_id=actor.actor_id,
                event_code="WORKSPACE_WRITE",
                outcome="allowed",
                detail={"path": relative_path, "bytes": len(payload), "rules": verdict.rule_ids},
            )
        return target


class CommandBroker:
    def __init__(
        self,
        state: CanonicalState,
        policy: PolicyEngine,
        sandbox: DockerSandbox,
        evidence: EvidenceBroker,
    ) -> None:
        self.state = state
        self.policy = policy
        self.sandbox = sandbox
        self.evidence = evidence

    def run(
        self,
        actor: AuthenticatedActor,
        *,
        argv: tuple[str, ...],
        workspace: Path,
        budget: ResourceBudget,
        policy_version: int,
        policy_digest: str,
        result_seal: str,
        criterion_id: str,
    ) -> BrokeredCommand:
        stopped, _, _ = self.state.control_status()
        request = PermissionRequest(
            capability="SANDBOX_CHECK",
            policy_digest=policy_digest,
            policy_version=policy_version,
            risk=RiskTier.MODERATE,
            argv=argv,
            budget=budget,
        )
        try:
            verdict = self.policy.require(actor, request, emergency_stopped=stopped)
        except PolicyDenied as exc:
            self.state.record_event(
                aggregate_id=criterion_id,
                actor_id=actor.actor_id,
                event_code="SANDBOX_CHECK_DENIED",
                outcome="denied",
                error_code=exc.code,
                detail={"argv": argv, "capability": request.capability},
            )
            raise
        try:
            result = self.sandbox.run(SandboxRequest(argv, workspace, budget))
        except Exception as exc:
            self.state.record_event(
                aggregate_id=criterion_id,
                actor_id=actor.actor_id,
                event_code="SANDBOX_CHECK_FAILED",
                outcome="failed",
                error_code=getattr(exc, "code", "SANDBOX_EXECUTION_FAILED"),
                detail={"argv": argv},
            )
            raise
        report = json.dumps(
            {
                "profile": result.provider,
                "image": result.image,
                "argv": argv,
                "exit_code": result.exit_code,
                "stdout_digest": result.stdout_digest,
                "stderr_digest": result.stderr_digest,
                "network": result.network,
                "root_filesystem": result.root_filesystem,
                "policy_rules": verdict.rule_ids,
            },
            sort_keys=True,
        ).encode("utf-8")
        captured = self.evidence.capture(
            report,
            result_seal=result_seal,
            criterion_id=criterion_id,
            classification="internal",
            collector=result.provider,
            actor_id=actor.actor_id,
        )
        return BrokeredCommand(result, captured)


class EmergencyController:
    def __init__(self, state: CanonicalState, sandbox: DockerSandbox) -> None:
        self.state = state
        self.sandbox = sandbox

    def stop(self, actor_id: str, reason: str) -> dict[str, int]:
        epoch = self.state.set_emergency_stop(actor_id, reason)
        terminated = self.sandbox.emergency_terminate()
        return {"trust_epoch": epoch, "terminated_sandboxes": terminated}
