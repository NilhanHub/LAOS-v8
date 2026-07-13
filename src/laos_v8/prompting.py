"""Versioned executor profiles and deterministic Stage 5 prompt/context compilation."""

from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json
from .errors import AuthorizationDenied, ValidationError
from .safe_paths import validate_relative_path

ContextClass = Literal[
    "signed_instruction",
    "trusted_project_truth",
    "evidence",
    "untrusted_repository",
    "untrusted_external",
]
UncertaintyStatus = Literal["unresolved", "resolved"]


class ExecutorProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    profile_id: str = Field(pattern=r"^profile:[A-Za-z0-9._-]{1,120}$")
    version: str = Field(pattern=r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$")
    executor_class: Literal[
        "fragile_local_desktop",
        "weak_general_desktop",
        "standard_coding",
        "strong_coding",
        "investigation_specialist",
        "test_verifier",
        "independent_reviewer",
    ]
    max_files_per_action: int = Field(ge=1, le=256)
    max_criteria_per_action: int = Field(ge=1, le=256)
    max_prompt_bytes: int = Field(ge=512, le=1_000_000)
    max_instructions: int = Field(ge=1, le=512)
    repetition: int = Field(ge=0, le=5)
    max_examples: int = Field(ge=0, le=32)
    allowed_tools: tuple[str, ...] = Field(max_length=128)
    retry_budget: int = Field(ge=1, le=10)
    require_fresh_session: bool
    network_policy: Literal["deny", "broker_only"]
    review_depth: Literal["criterion", "action", "full_delta"]
    safety_ceiling: Literal["low", "medium", "high"]
    released: bool = False

    @model_validator(mode="after")
    def unique_tools(self) -> ExecutorProfile:
        if len(self.allowed_tools) != len(set(self.allowed_tools)):
            raise ValueError("PROFILE_DUPLICATE_TOOL")
        return self

    @property
    def digest(self) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(self.model_dump(mode='json'))).hexdigest()}"


class ProfilePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    max_files_per_action: int = Field(ge=1, le=256)
    max_criteria_per_action: int = Field(ge=1, le=256)
    max_prompt_bytes: int = Field(ge=512, le=1_000_000)
    max_retry_budget: int = Field(ge=1, le=10)
    allowed_tools: tuple[str, ...]
    allow_network_broker: bool = False
    maximum_safety_ceiling: Literal["low", "medium", "high"] = "medium"


class CalibrationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    calibration_id: str = Field(pattern=r"^calibration:[A-Za-z0-9._-]{1,120}$")
    profile_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provider: str = Field(min_length=1, max_length=256)
    model_snapshot: str = Field(min_length=1, max_length=512)
    tool_versions: tuple[str, ...]
    settings_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    prompt_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    observed_at: str
    environment_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    partition: Literal["development", "calibration"]
    compliance_rate: float = Field(ge=0, le=1)
    skip_rate: float = Field(ge=0, le=1)
    scope_adherence_rate: float = Field(ge=0, le=1)
    evidence_quality_rate: float = Field(ge=0, le=1)
    broker_evidence_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    qualifying_security_spine: bool

    @model_validator(mode="after")
    def stable_snapshot(self) -> CalibrationRecord:
        aliases = {"latest", "default", "auto", "stable"}
        if self.model_snapshot.strip().lower() in aliases:
            raise ValueError("CALIBRATION_DRIFT_PRONE_ALIAS")
        if not self.qualifying_security_spine:
            raise ValueError("CALIBRATION_SECURITY_SPINE_REQUIRED")
        return self


class ContextItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    context_id: str = Field(pattern=r"^context:[A-Za-z0-9._-]{1,120}$")
    classification: ContextClass
    source_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    content: str = Field(min_length=1, max_length=100_000)


class ContextManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str = Field(pattern=r"^action:[A-Za-z0-9._-]{1,120}$")
    role: str = Field(min_length=1, max_length=256)
    items: tuple[ContextItem, ...] = Field(max_length=512)

    @model_validator(mode="after")
    def unique_context(self) -> ContextManifest:
        identifiers = [item.context_id for item in self.items]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("CONTEXT_DUPLICATE_ID")
        return self


class UncertaintyItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    uncertainty_id: str = Field(pattern=r"^uncertainty:[A-Za-z0-9._-]{1,120}$")
    statement: str = Field(min_length=1, max_length=4096)
    status: UncertaintyStatus = "unresolved"
    resolution_evidence: str | None = None

    @model_validator(mode="after")
    def resolution_is_evidenced(self) -> UncertaintyItem:
        if self.status == "resolved" and not self.resolution_evidence:
            raise ValueError("UNCERTAINTY_RESOLUTION_EVIDENCE_REQUIRED")
        if self.status == "unresolved" and self.resolution_evidence is not None:
            raise ValueError("UNCERTAINTY_UNRESOLVED_HAS_EVIDENCE")
        return self


class HandoffState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str
    decisions: tuple[str, ...]
    blockers: tuple[str, ...]
    conflicts: tuple[str, ...]
    uncertainties: tuple[UncertaintyItem, ...]
    next_legal_action: str = Field(min_length=1, max_length=4096)
    exploration_notes: tuple[str, ...] = ()

    def compact(self) -> HandoffState:
        """Discard exploration noise while preserving all authority-relevant state."""
        return self.model_copy(update={"exploration_notes": ()})


class PromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str = Field(pattern=r"^action:[A-Za-z0-9._-]{1,120}$")
    role: str = Field(min_length=1, max_length=1024)
    repository: str = Field(min_length=1, max_length=4096)
    goal: str = Field(min_length=1, max_length=8192)
    finish_line: tuple[str, ...] = Field(min_length=1, max_length=256)
    allowed_scope: tuple[str, ...] = Field(min_length=1, max_length=256)
    forbidden_scope: tuple[str, ...] = Field(min_length=1, max_length=256)
    checks: tuple[str, ...] = Field(min_length=1, max_length=256)
    evidence: tuple[str, ...] = Field(min_length=1, max_length=256)
    stop_conditions: tuple[str, ...] = Field(min_length=1, max_length=256)
    unavailable_tools: str = Field(min_length=1, max_length=4096)
    final_response_format: str = Field(min_length=1, max_length=4096)
    requested_tools: tuple[str, ...] = Field(max_length=128)
    requested_permissions: tuple[str, ...] = Field(max_length=128)
    examples: tuple[str, ...] = Field(max_length=32)


class CompiledPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    action_id: str
    profile_digest: str
    context_digest: str
    prompt_digest: str
    text: str


_PLACEHOLDER = re.compile(r"(?i)(?:\bTODO\b|\bTBD\b|\bFIXME\b|\{\{[^}]+\}\}|<PLACEHOLDER>)")
_PRIVATE = re.compile(r"(?i)(?:MASTER_FRAMEWORK_PRIVATE|LAOS_HIDDEN_CHECK|FUTURE_ACTION|ARCHITECT_ONLY)")
_SAFETY_ORDER = {"low": 0, "medium": 1, "high": 2}


class PromptCompiler:
    def __init__(self, policy: ProfilePolicy) -> None:
        self.policy = policy

    def validate_profile(self, profile: ExecutorProfile) -> None:
        if profile.max_files_per_action > self.policy.max_files_per_action:
            raise AuthorizationDenied("profile file authority exceeds policy", code="PROFILE_AUTHORITY_EXCEEDED")
        if profile.max_criteria_per_action > self.policy.max_criteria_per_action:
            raise AuthorizationDenied("profile criterion authority exceeds policy", code="PROFILE_AUTHORITY_EXCEEDED")
        if (
            profile.max_prompt_bytes > self.policy.max_prompt_bytes
            or profile.retry_budget > self.policy.max_retry_budget
        ):
            raise AuthorizationDenied("profile budget exceeds policy", code="PROFILE_AUTHORITY_EXCEEDED")
        if not set(profile.allowed_tools) <= set(self.policy.allowed_tools):
            raise AuthorizationDenied("profile tools exceed policy", code="PROFILE_AUTHORITY_EXCEEDED")
        if profile.network_policy == "broker_only" and not self.policy.allow_network_broker:
            raise AuthorizationDenied("profile network exceeds policy", code="PROFILE_AUTHORITY_EXCEEDED")
        if _SAFETY_ORDER[profile.safety_ceiling] > _SAFETY_ORDER[self.policy.maximum_safety_ceiling]:
            raise AuthorizationDenied("profile safety ceiling exceeds policy", code="PROFILE_AUTHORITY_EXCEEDED")

    def require_release_calibration(
        self,
        profile: ExecutorProfile,
        records: tuple[CalibrationRecord, ...],
    ) -> None:
        if profile.released and not any(record.profile_digest == profile.digest for record in records):
            raise ValidationError("released profile lacks calibration evidence", code="PROFILE_CALIBRATION_REQUIRED")

    def decompose(
        self,
        *,
        files: tuple[str, ...],
        criteria: tuple[str, ...],
        profile: ExecutorProfile,
    ) -> tuple[dict[str, tuple[str, ...]], ...]:
        self.validate_profile(profile)
        safe_files = tuple(validate_relative_path(path).as_posix() for path in files)
        chunks: list[dict[str, tuple[str, ...]]] = []
        file_groups = [
            safe_files[index : index + profile.max_files_per_action]
            for index in range(0, len(safe_files), profile.max_files_per_action)
        ] or [()]
        criterion_groups = [
            criteria[index : index + profile.max_criteria_per_action]
            for index in range(0, len(criteria), profile.max_criteria_per_action)
        ] or [()]
        count = max(len(file_groups), len(criterion_groups))
        for index in range(count):
            chunks.append({
                "files": file_groups[index] if index < len(file_groups) else (),
                "criteria": criterion_groups[index] if index < len(criterion_groups) else (),
            })
        return tuple(chunks)

    def compile(self, spec: PromptSpec, context: ContextManifest, profile: ExecutorProfile) -> CompiledPrompt:
        self.validate_profile(profile)
        if spec.action_id != context.action_id:
            raise ValidationError("prompt context action differs", code="PROMPT_CONTEXT_BINDING_MISMATCH")
        allowed = tuple(validate_relative_path(path).as_posix() for path in spec.allowed_scope)
        forbidden = tuple(validate_relative_path(path).as_posix() for path in spec.forbidden_scope)
        if set(allowed) & set(forbidden):
            raise ValidationError("prompt scope contradicts itself", code="PROMPT_STRUCTURAL_CONTRADICTION")
        if len(allowed) > profile.max_files_per_action or len(spec.finish_line) > profile.max_criteria_per_action:
            raise ValidationError("work exceeds executor profile", code="PROMPT_REQUIRES_DECOMPOSITION")
        if len(spec.examples) > profile.max_examples:
            raise ValidationError("prompt has too many examples", code="PROMPT_EXAMPLE_LIMIT")
        instruction_count = sum(
            len(values)
            for values in (
                spec.finish_line,
                spec.allowed_scope,
                spec.forbidden_scope,
                spec.checks,
                spec.evidence,
                spec.stop_conditions,
                spec.requested_tools,
                spec.requested_permissions,
                spec.examples,
            )
        )
        if instruction_count > profile.max_instructions:
            raise ValidationError("prompt has too many instructions", code="PROMPT_INSTRUCTION_LIMIT")
        if not set(spec.requested_tools) <= set(profile.allowed_tools):
            raise AuthorizationDenied("prompt requests unavailable tool", code="PROMPT_TOOL_DENIED")
        forbidden_permissions = set(spec.requested_permissions) - {"WORKSPACE_READ", "MEDIATED_WRITE"}
        if forbidden_permissions:
            raise AuthorizationDenied("prompt requests forbidden permission", code="PROMPT_PERMISSION_DENIED")
        payload = canonical_json({"spec": spec.model_dump(mode="json"), "context": context.model_dump(mode="json")})
        if _PLACEHOLDER.search(payload.decode("utf-8")):
            raise ValidationError("prompt contains unresolved placeholder", code="PROMPT_PLACEHOLDER")
        if _PRIVATE.search(payload.decode("utf-8")):
            raise AuthorizationDenied("prompt leaks Architect-only information", code="PROMPT_PRIVATE_LEAK")
        stop_body = "\n".join(spec.stop_conditions)
        if profile.repetition:
            stop_body += "\n" + "\n".join(
                f"REMINDER {index + 1}: {item}"
                for index in range(profile.repetition)
                for item in spec.stop_conditions
            )
        profile_controls = canonical_json(
            {
                "allowed_tools": profile.allowed_tools,
                "network_policy": profile.network_policy,
                "retry_budget": profile.retry_budget,
                "require_fresh_session": profile.require_fresh_session,
                "review_depth": profile.review_depth,
                "safety_ceiling": profile.safety_ceiling,
            }
        ).decode("utf-8")
        sections: list[tuple[str, str]] = [
            ("CURRENT ACTION", spec.action_id),
            ("STOP CONDITIONS", stop_body),
            ("ROLE", spec.role),
            ("REPOSITORY", spec.repository),
            ("GOAL", spec.goal),
            ("FINISH LINE", "\n".join(spec.finish_line)),
            ("ALLOWED SCOPE", "\n".join(allowed)),
            ("FORBIDDEN SCOPE", "\n".join(forbidden)),
            ("CHECKS", "\n".join(spec.checks)),
            ("EVIDENCE", "\n".join(spec.evidence)),
            ("UNAVAILABLE TOOLS", spec.unavailable_tools),
            ("EXECUTION PROFILE", profile_controls),
            ("FINAL RESPONSE FORMAT", spec.final_response_format),
            ("CONTEXT MANIFEST", canonical_json(context.model_dump(mode="json")).decode("utf-8")),
        ]
        if spec.examples:
            sections.insert(-1, ("EXAMPLES", "\n".join(spec.examples)))
        text = "\n\n".join(f"## {title}\n{body}" for title, body in sections)
        encoded = text.encode("utf-8")
        if len(encoded) > min(profile.max_prompt_bytes, self.policy.max_prompt_bytes):
            raise ValidationError("compiled prompt exceeds size limit", code="PROMPT_SIZE_EXCEEDED")
        context_bytes = canonical_json(context.model_dump(mode="json"))
        return CompiledPrompt(
            action_id=spec.action_id,
            profile_digest=profile.digest,
            context_digest=f"sha256:{hashlib.sha256(context_bytes).hexdigest()}",
            prompt_digest=f"sha256:{hashlib.sha256(encoded).hexdigest()}",
            text=text,
        )
