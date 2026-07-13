"""Read-only existing-application capture and drift-safe continuation contracts."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .action_engine import ActionNode
from .canonical import canonical_json
from .errors import AuthorizationDenied, ValidationError
from .models import TypedEnvelope
from .repository_truth import ManifestSnapshot, build_manifest, require_unchanged
from .signing import EnvelopeVerifier

CAPTURE_RETURN_MEDIA_TYPE = "application/vnd.nilhan.laos.app-intelligence-return.v1+json"
CAPTURE_AREAS = (
    "repository_identity_environment",
    "architecture_components_data",
    "features_ui_apis_authentication_authorization",
    "integrations_external_systems",
    "commands_tests_build_deployment_operations",
    "defects_debt_protected_areas_conflicts_unknowns",
)
CAPTURE_DENIED = (
    "PRODUCT_CODE_WRITE",
    "REPAIR",
    "DEPLOY",
    "CLOUD_MUTATION",
    "EXTERNAL_SIDE_EFFECT",
    "REPOSITORY_CODE_EXECUTION",
    "NETWORK",
    "RAW_SECRETS",
)


class CaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    capture_id: str = Field(pattern=r"^capture:[A-Za-z0-9._-]{1,120}$")
    project_id: str = Field(pattern=r"^project:[A-Za-z0-9._-]{1,120}$")
    repository_seal: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    repository_head: str = Field(pattern=r"^[0-9a-f]{40,64}$")
    areas: tuple[str, ...] = CAPTURE_AREAS
    allowed_capabilities: tuple[Literal["WORKSPACE_READ", "EVIDENCE_WRITE"], ...] = (
        "WORKSPACE_READ",
        "EVIDENCE_WRITE",
    )
    denied_capabilities: tuple[str, ...] = CAPTURE_DENIED
    capture_tool: str = Field(min_length=1, max_length=256)
    capture_tool_version: str = Field(min_length=1, max_length=128)
    issued_at: str
    expires_at: str

    @model_validator(mode="after")
    def complete_read_only_contract(self) -> CaptureRequest:
        if self.areas != CAPTURE_AREAS:
            raise ValueError("CAPTURE_AREAS_INCOMPLETE")
        if not set(CAPTURE_DENIED) <= set(self.denied_capabilities):
            raise ValueError("CAPTURE_DENIALS_INCOMPLETE")
        return self


class CaptureFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    fact_id: str = Field(pattern=r"^fact:[A-Za-z0-9._-]{1,120}$")
    area: str
    statement: str = Field(min_length=1, max_length=8192)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=256)
    confidence: float = Field(ge=0, le=1)
    contradictions: tuple[str, ...] = Field(max_length=256)
    unknowns: tuple[str, ...] = Field(max_length=256)
    data_classification: Literal["public", "internal", "restricted"]
    captured_at: str
    freshness_seconds: int = Field(ge=1, le=31_536_000)


class AppIntelligenceReturn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    capture_id: str
    project_id: str
    repository_seal: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    capture_tool: str
    capture_tool_version: str
    facts: tuple[CaptureFact, ...] = Field(min_length=1, max_length=10_000)
    completed_at: str

    @model_validator(mode="after")
    def unique_facts(self) -> AppIntelligenceReturn:
        identifiers = [fact.fact_id for fact in self.facts]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("CAPTURE_DUPLICATE_FACT")
        if any(fact.area not in CAPTURE_AREAS for fact in self.facts):
            raise ValueError("CAPTURE_AREA_UNKNOWN")
        return self


class FactDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    fact_id: str
    status: Literal["accepted", "rejected", "conflicted", "unknown"]
    rationale: str = Field(min_length=1, max_length=4096)


class ArchitectCaptureAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    acceptance_id: str = Field(pattern=r"^acceptance:[A-Za-z0-9._-]{1,120}$")
    capture_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    architect_principal: str = Field(min_length=1, max_length=512)
    human_reviewer: Literal["Nilhan"]
    dispositions: tuple[FactDisposition, ...] = Field(min_length=1, max_length=10_000)
    preservation_rules: tuple[str, ...] = Field(min_length=1, max_length=256)
    continuation_constraints: tuple[str, ...] = Field(min_length=1, max_length=256)
    accepted_at: str


class ValidatedCapture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    capture: AppIntelligenceReturn
    capture_digest: str
    envelope_digest: str


class ContinuationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    project_id: str
    base_seal: str
    capture_digest: str
    accepted_fact_ids: tuple[str, ...]
    rejected_fact_ids: tuple[str, ...]
    conflicted_fact_ids: tuple[str, ...]
    unknown_fact_ids: tuple[str, ...]
    preservation_rules: tuple[str, ...]
    continuation_constraints: tuple[str, ...]
    first_action: ActionNode


def create_capture_request(
    repository: Path,
    *,
    capture_id: str,
    project_id: str,
    capture_tool: str,
    capture_tool_version: str,
    issued_at: str,
    expires_at: str,
) -> tuple[CaptureRequest, ManifestSnapshot]:
    snapshot = build_manifest(repository, seal_kind="source")
    request = CaptureRequest(
        capture_id=capture_id,
        project_id=project_id,
        repository_seal=snapshot.seal,
        repository_head=snapshot.git_head,
        capture_tool=capture_tool,
        capture_tool_version=capture_tool_version,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    return request, snapshot


def validate_capture_return(
    request: CaptureRequest,
    envelope: TypedEnvelope,
    *,
    repository: Path,
    verifier: EnvelopeVerifier,
    expected_issuer: str,
    expected_audience: str,
    now: datetime,
) -> ValidatedCapture:
    current = now.astimezone(UTC)
    expires = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00")).astimezone(UTC)
    if current >= expires:
        raise AuthorizationDenied("capture request is stale", code="CAPTURE_REQUEST_EXPIRED")
    envelope_issued = datetime.fromisoformat(envelope.issued_at.replace("Z", "+00:00")).astimezone(UTC)
    if current < envelope_issued:
        raise AuthorizationDenied("capture return is not yet valid", code="CAPTURE_RETURN_NOT_YET_VALID")
    if envelope.expires_at is None:
        raise AuthorizationDenied("capture return lacks expiry", code="CAPTURE_RETURN_EXPIRY_REQUIRED")
    envelope_expires = datetime.fromisoformat(envelope.expires_at.replace("Z", "+00:00")).astimezone(UTC)
    if current >= envelope_expires:
        raise AuthorizationDenied("capture return is expired", code="CAPTURE_RETURN_EXPIRED")
    payload = verifier.verify(
        envelope,
        expected_purpose="event_anchor",
        expected_payload_type=CAPTURE_RETURN_MEDIA_TYPE,
        expected_issuer=expected_issuer,
        expected_audience=expected_audience,
    )
    returned = AppIntelligenceReturn.model_validate_json(payload, strict=True)
    if (
        returned.capture_id != request.capture_id
        or returned.project_id != request.project_id
        or returned.repository_seal != request.repository_seal
        or returned.capture_tool != request.capture_tool
        or returned.capture_tool_version != request.capture_tool_version
    ):
        raise AuthorizationDenied("capture return binding mismatch", code="CAPTURE_RETURN_BINDING_MISMATCH")
    require_unchanged(repository, request.repository_seal, seal_kind="source")
    for fact in returned.facts:
        captured = datetime.fromisoformat(fact.captured_at.replace("Z", "+00:00")).astimezone(UTC)
        if current >= captured + timedelta(seconds=fact.freshness_seconds):
            raise AuthorizationDenied("capture fact is stale", code="CAPTURE_FACT_STALE")
    digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    envelope_digest = f"sha256:{hashlib.sha256(canonical_json(envelope.model_dump(mode='json'))).hexdigest()}"
    return ValidatedCapture(capture=returned, capture_digest=digest, envelope_digest=envelope_digest)


def compile_continuation(
    repository: Path,
    validated: ValidatedCapture,
    acceptance: ArchitectCaptureAcceptance,
    *,
    first_action: ActionNode,
    now: datetime,
) -> ContinuationResult:
    capture = validated.capture
    require_unchanged(repository, capture.repository_seal, seal_kind="source")
    if acceptance.capture_digest != validated.capture_digest:
        raise AuthorizationDenied("acceptance targets another capture", code="CAPTURE_ACCEPTANCE_BINDING_MISMATCH")
    current = now.astimezone(UTC)
    for fact in capture.facts:
        captured = datetime.fromisoformat(fact.captured_at.replace("Z", "+00:00")).astimezone(UTC)
        if current >= captured + timedelta(seconds=fact.freshness_seconds):
            raise AuthorizationDenied("capture fact is stale", code="CAPTURE_FACT_STALE")
    known = {fact.fact_id for fact in capture.facts}
    dispositions = {item.fact_id: item.status for item in acceptance.dispositions}
    if len(dispositions) != len(acceptance.dispositions) or set(dispositions) != known:
        raise ValidationError("every fact requires exactly one disposition", code="CAPTURE_DISPOSITIONS_INCOMPLETE")
    grouped = {
        status: tuple(sorted(key for key, value in dispositions.items() if value == status))
        for status in ("accepted", "rejected", "conflicted", "unknown")
    }
    return ContinuationResult(
        project_id=capture.project_id,
        base_seal=capture.repository_seal,
        capture_digest=validated.capture_digest,
        accepted_fact_ids=grouped["accepted"],
        rejected_fact_ids=grouped["rejected"],
        conflicted_fact_ids=grouped["conflicted"],
        unknown_fact_ids=grouped["unknown"],
        preservation_rules=acceptance.preservation_rules,
        continuation_constraints=acceptance.continuation_constraints,
        first_action=first_action,
    )
