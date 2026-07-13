"""Default-deny policy and risk classification for Stage 3 broker boundaries."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Literal

from .canonical import canonical_json
from .errors import PolicyDenied
from .identity import AuthenticatedActor
from .models import RiskTier, Role
from .safe_paths import validate_relative_path

SHELL_META = re.compile(r"[;&|`$<>\r\n]")


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    timeout_seconds: int = 300
    memory_bytes: int = 536_870_912
    processes: int = 64
    cpu_count: float = 1.0
    output_bytes: int = 10_485_760
    retries: int = 3


@dataclass(frozen=True, slots=True)
class PolicyProfile:
    version: int
    allowed_capabilities: tuple[str, ...]
    role_capabilities: dict[str, tuple[str, ...]]
    writable_prefixes: tuple[str, ...]
    command_prefixes: tuple[tuple[str, ...], ...]
    budget: ResourceBudget
    network_allowed: Literal[False] = False
    secrets_allowed: Literal[False] = False
    side_effects_allowed: Literal[False] = False

    @property
    def digest(self) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(asdict(self))).hexdigest()}"


@dataclass(frozen=True, slots=True)
class PermissionRequest:
    capability: str
    policy_digest: str
    policy_version: int
    risk: RiskTier
    relative_path: str | None = None
    argv: tuple[str, ...] = ()
    network: bool = False
    secret_names: tuple[str, ...] = ()
    side_effect: bool = False
    instruction_source: Literal["signed_control", "repository", "external", "model"] = "signed_control"
    budget: ResourceBudget | None = None


@dataclass(frozen=True, slots=True)
class PolicyVerdict:
    decision: Literal["allow", "deny"]
    rule_ids: tuple[str, ...]
    explanation: str
    obligations: tuple[str, ...]
    policy_digest: str
    risk: RiskTier


class PolicyEngine:
    def __init__(self, profile: PolicyProfile) -> None:
        self.profile = profile

    def evaluate(
        self, actor: AuthenticatedActor, request: PermissionRequest, *, emergency_stopped: bool
    ) -> PolicyVerdict:
        denied: list[str] = []
        if emergency_stopped:
            denied.append("POLICY_EMERGENCY_STOP")
        if request.policy_digest != self.profile.digest or request.policy_version != self.profile.version:
            denied.append("POLICY_STALE_OR_DOWNGRADED")
        if request.capability not in self.profile.allowed_capabilities:
            denied.append("POLICY_CAPABILITY_NOT_ALLOWLISTED")
        allowed_by_role = any(
            request.capability in self.profile.role_capabilities.get(role.value, ()) for role in actor.roles
        )
        if not allowed_by_role:
            denied.append("POLICY_ROLE_CAPABILITY_DENIED")
        if request.network or self.profile.network_allowed:
            if request.network:
                denied.append("POLICY_NETWORK_DENIED")
        if request.secret_names or self.profile.secrets_allowed:
            if request.secret_names:
                denied.append("POLICY_RAW_SECRET_DENIED")
        if request.side_effect or self.profile.side_effects_allowed:
            if request.side_effect:
                denied.append("POLICY_SIDE_EFFECT_DENIED")
        if request.instruction_source != "signed_control":
            denied.append("POLICY_UNTRUSTED_INSTRUCTION_SOURCE")
        if request.relative_path is not None:
            normalized = validate_relative_path(request.relative_path).as_posix()
            if not any(
                normalized == prefix or normalized.startswith(prefix.rstrip("/") + "/")
                for prefix in self.profile.writable_prefixes
            ):
                denied.append("POLICY_PATH_SCOPE_DENIED")
        if request.argv:
            if any(not item or SHELL_META.search(item) for item in request.argv):
                denied.append("POLICY_COMMAND_TOKEN_DENIED")
            if not any(request.argv[: len(prefix)] == prefix for prefix in self.profile.command_prefixes):
                denied.append("POLICY_COMMAND_NOT_ALLOWLISTED")
        if request.budget is not None:
            limits = self.profile.budget
            actual = request.budget
            if (
                actual.timeout_seconds > limits.timeout_seconds
                or actual.memory_bytes > limits.memory_bytes
                or actual.processes > limits.processes
                or actual.cpu_count > limits.cpu_count
                or actual.output_bytes > limits.output_bytes
                or actual.retries > limits.retries
            ):
                denied.append("POLICY_RESOURCE_BUDGET_EXCEEDED")
        if request.risk is RiskTier.HIGH:
            denied.append("POLICY_HIGH_RISK_PROFILE_UNQUALIFIED")
        if request.risk is RiskTier.CRITICAL:
            denied.append("POLICY_CRITICAL_REQUIRES_QUORUM")
        if denied:
            return PolicyVerdict(
                "deny",
                tuple(dict.fromkeys(denied)),
                "Request denied by deterministic policy.",
                (),
                self.profile.digest,
                request.risk,
            )
        return PolicyVerdict(
            "allow",
            ("POLICY_DEFAULT_DENY_ALLOWLIST_MATCH",),
            "Request matches the Stage 3 allowlisted local profile.",
            ("BROKER_MEDIATION_REQUIRED", "BROKER_EVIDENCE_REQUIRED"),
            self.profile.digest,
            request.risk,
        )

    def require(
        self, actor: AuthenticatedActor, request: PermissionRequest, *, emergency_stopped: bool
    ) -> PolicyVerdict:
        verdict = self.evaluate(actor, request, emergency_stopped=emergency_stopped)
        if verdict.decision != "allow":
            raise PolicyDenied(
                verdict.explanation,
                code="POLICY_REQUEST_DENIED",
                context={"rule_ids": list(verdict.rule_ids), "risk": verdict.risk.value},
            )
        return verdict


def minimal_stage3_policy() -> PolicyProfile:
    capabilities = ("WORKSPACE_READ", "WORKSPACE_WRITE", "SANDBOX_CHECK", "EVIDENCE_READ")
    return PolicyProfile(
        version=1,
        allowed_capabilities=capabilities,
        role_capabilities={
            Role.BUILDER.value: ("WORKSPACE_READ", "WORKSPACE_WRITE", "SANDBOX_CHECK"),
            Role.TESTER.value: ("WORKSPACE_READ", "SANDBOX_CHECK"),
            Role.VERIFIER.value: ("WORKSPACE_READ", "SANDBOX_CHECK", "EVIDENCE_READ"),
            Role.REVIEWER.value: ("WORKSPACE_READ", "EVIDENCE_READ"),
        },
        writable_prefixes=("src", "tests"),
        command_prefixes=(("python", "-m", "pytest"), ("python", "-m", "compileall")),
        budget=ResourceBudget(),
    )
