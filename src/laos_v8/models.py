"""Canonical strict domain models for LAOS v8 trusted records."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .value_types import MediaType, ProjectId, RecordId, SafeRelativePath, Sha256Digest, StableCode, UtcTimestamp


class Role(StrEnum):
    ARCHITECT = "architect"
    BUILDER = "builder"
    INVESTIGATOR = "investigator"
    TESTER = "tester"
    VERIFIER = "verifier"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    SIGNER = "signer"
    RELEASE_VERIFIER = "release_verifier"


class RiskTier(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RecordBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, str_max_length=65536)

    record_type: str
    record_version: Literal["1.0.0"] = "1.0.0"
    record_id: RecordId
    project_id: ProjectId
    created_at: UtcTimestamp


class NamedRecord(RecordBase):
    title: Annotated[str, StringConstraints(min_length=1, max_length=512)]


class ProductObjective(NamedRecord):
    record_type: Literal["product_objective"] = "product_objective"
    summary: Annotated[str, StringConstraints(min_length=1, max_length=16384)]
    success_criteria: tuple[Annotated[str, StringConstraints(min_length=1, max_length=4096)], ...] = Field(
        max_length=256
    )


class Engagement(NamedRecord):
    record_type: Literal["engagement"] = "engagement"
    objective_id: RecordId
    state: Literal["draft", "active", "blocked", "accepted", "cancelled"]


class NewBuildRequest(NamedRecord):
    record_type: Literal["new_build_request"] = "new_build_request"
    objective_id: RecordId
    requested_capabilities: tuple[StableCode, ...] = Field(max_length=256)


class BlueprintAcceptanceRecord(RecordBase):
    record_type: Literal["blueprint_acceptance"] = "blueprint_acceptance"
    blueprint_id: RecordId
    accepted_by: RecordId
    blueprint_digest: Sha256Digest


class GenesisRepositoryRecord(RecordBase):
    record_type: Literal["genesis_repository"] = "genesis_repository"
    blueprint_acceptance_id: RecordId
    source_seal: Sha256Digest
    repository_kind: Literal["git"] = "git"


class ProjectBlueprint(NamedRecord):
    record_type: Literal["project_blueprint"] = "project_blueprint"
    objective_id: RecordId
    requirement_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=4096)


class Requirement(NamedRecord):
    record_type: Literal["requirement"] = "requirement"
    description: Annotated[str, StringConstraints(min_length=1, max_length=16384)]
    priority: Literal["P0", "P1", "P2"]
    scope: Literal["MUST_V8_0", "SHOULD_V8_0", "DEFER_V8_X"]
    criterion_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=1024)


class AcceptanceCriterion(NamedRecord):
    record_type: Literal["acceptance_criterion"] = "acceptance_criterion"
    requirement_id: RecordId
    statement: Annotated[str, StringConstraints(min_length=1, max_length=8192)]
    evidence_level: Literal["L0", "L1", "L2", "L3", "L4"]
    state: Literal["open", "proven", "reviewed", "accepted", "rejected"]


class Task(NamedRecord):
    record_type: Literal["task"] = "task"
    criterion_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=1024)
    depends_on: tuple[RecordId, ...] = Field(default=(), max_length=1024)
    state: Literal["planned", "ready", "active", "blocked", "review", "accepted", "cancelled"]


class ActionDefinition(NamedRecord):
    record_type: Literal["action_definition"] = "action_definition"
    task_id: RecordId
    phase: Literal["understand", "plan", "implement", "verify", "review", "promote"]
    criterion_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=1024)
    permissions: tuple[StableCode, ...] = Field(max_length=1024)


class ActionCapsule(RecordBase):
    record_type: Literal["action_capsule"] = "action_capsule"
    capsule_id: RecordId
    issuer_id: RecordId
    actor_id: RecordId
    role: Role
    audience: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    action_definition_digest: Sha256Digest
    base_seal: Sha256Digest
    policy_digest: Sha256Digest
    profile_digest: Sha256Digest
    skill_digest: Sha256Digest
    state_version: Annotated[int, Field(ge=0)]
    attempt_sequence: Annotated[int, Field(ge=1)]
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp
    revocation_epoch: Annotated[int, Field(ge=0)]


class ActionAttempt(RecordBase):
    record_type: Literal["action_attempt"] = "action_attempt"
    action_definition_id: RecordId
    capsule_id: RecordId
    sequence: Annotated[int, Field(ge=1)]
    state: Literal["created", "active", "submitted", "verified", "rejected", "aborted"]
    result_seal: Sha256Digest | None


class PromotionIntent(RecordBase):
    record_type: Literal["promotion_intent"] = "promotion_intent"
    base_seal: Sha256Digest
    result_seal: Sha256Digest
    target_ref: Annotated[str, StringConstraints(pattern=r"^refs/heads/[A-Za-z0-9._/-]{1,240}$")]
    state: Literal["prepared", "locked", "promoted", "conflict", "reconciled", "aborted"]


class WorkspaceSeal(RecordBase):
    record_type: Literal["workspace_seal"] = "workspace_seal"
    seal_kind: Literal["source", "base", "result", "workspace", "evidence"]
    manifest_digest: Sha256Digest
    parent_seal: Sha256Digest | None


class ManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: SafeRelativePath
    kind: Literal["file", "symlink"]
    size: Annotated[int, Field(ge=0)]
    digest: Sha256Digest
    mode: Annotated[int, Field(ge=0, le=0o7777)]
    link_target: str | None


class RepositoryManifest(RecordBase):
    record_type: Literal["repository_manifest"] = "repository_manifest"
    algorithm: Literal["laos-manifest-v1"] = "laos-manifest-v1"
    entries: tuple[ManifestEntry, ...] = Field(max_length=100000)

    @model_validator(mode="after")
    def unique_paths(self) -> RepositoryManifest:
        paths = [entry.path for entry in self.entries]
        if len(paths) != len(set(paths)):
            raise ValueError("manifest paths must be unique")
        return self


class ActorIdentity(RecordBase):
    record_type: Literal["actor_identity"] = "actor_identity"
    principal: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    roles: tuple[Role, ...] = Field(min_length=1, max_length=16)
    identity_issuer: Annotated[str, StringConstraints(min_length=1, max_length=512)]


class CapabilityGrant(RecordBase):
    record_type: Literal["capability_grant"] = "capability_grant"
    actor_id: RecordId
    role: Role
    capabilities: tuple[StableCode, ...] = Field(min_length=1, max_length=1024)
    policy_digest: Sha256Digest
    expires_at: UtcTimestamp
    revocation_epoch: Annotated[int, Field(ge=0)]


class ModelProfile(NamedRecord):
    record_type: Literal["model_profile"] = "model_profile"
    provider: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    model: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    model_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    built_in_tools_allowed: Literal[False] = False
    max_tokens: Annotated[int, Field(gt=0, le=200000)]


class PromptContract(RecordBase):
    record_type: Literal["prompt_contract"] = "prompt_contract"
    action_definition_id: RecordId
    profile_digest: Sha256Digest
    context_labels: tuple[Literal["signed_instruction", "trusted_truth", "evidence", "untrusted_content"], ...] = Field(
        max_length=4096
    )


class CheckDefinition(NamedRecord):
    record_type: Literal["check_definition"] = "check_definition"
    argv: tuple[Annotated[str, StringConstraints(min_length=1, max_length=4096)], ...] = Field(
        min_length=1, max_length=128
    )
    working_directory: SafeRelativePath
    timeout_seconds: Annotated[int, Field(gt=0, le=3600)]
    network: Literal["deny", "allowlisted"] = "deny"


class CheckRun(RecordBase):
    record_type: Literal["check_run"] = "check_run"
    check_definition_id: RecordId
    source_seal: Sha256Digest
    result_seal: Sha256Digest
    exit_code: int
    stdout_digest: Sha256Digest
    stderr_digest: Sha256Digest


class EvidenceObject(RecordBase):
    record_type: Literal["evidence_object"] = "evidence_object"
    digest: Sha256Digest
    media_type: MediaType
    classification: DataClassification
    collector_id: RecordId
    result_seal: Sha256Digest


class EvidenceBinding(RecordBase):
    record_type: Literal["evidence_binding"] = "evidence_binding"
    criterion_id: RecordId
    evidence_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=1024)
    result_seal: Sha256Digest


class ReviewRecord(RecordBase):
    record_type: Literal["review_record"] = "review_record"
    criterion_id: RecordId
    reviewer_id: RecordId
    builder_id: RecordId
    verdict: Literal["pass", "fail", "repair_required"]
    evidence_binding_id: RecordId

    @model_validator(mode="after")
    def reviewer_is_not_builder(self) -> ReviewRecord:
        if self.reviewer_id == self.builder_id:
            raise ValueError("reviewer and builder identities must differ")
        return self


class AuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    event_code: StableCode
    actor_id: RecordId
    occurred_at: UtcTimestamp
    outcome: Literal["allowed", "denied", "failed"]
    error_code: StableCode | None


class SideEffectRecord(RecordBase):
    record_type: Literal["side_effect_record"] = "side_effect_record"
    operation: StableCode
    payload_digest: Sha256Digest
    state: Literal["proposed", "approved", "dispatched", "verified", "failed", "outcome_unknown", "reconciled"]
    audit: tuple[AuditEntry, ...] = Field(default=(), max_length=4096)


class ApprovalRecord(RecordBase):
    record_type: Literal["approval_record"] = "approval_record"
    side_effect_id: RecordId
    approver_id: RecordId
    displayed_transaction_digest: Sha256Digest
    expires_at: UtcTimestamp


class CheckpointRecord(RecordBase):
    record_type: Literal["checkpoint_record"] = "checkpoint_record"
    workspace_seal: Sha256Digest
    archive_digest: Sha256Digest


class IncidentRecord(NamedRecord):
    record_type: Literal["incident_record"] = "incident_record"
    severity: RiskTier
    state: Literal["open", "contained", "recovering", "revalidated", "closed"]
    affected_trust_epoch: Annotated[int, Field(ge=0)]


class AmendmentRecord(NamedRecord):
    record_type: Literal["amendment_record"] = "amendment_record"
    supersedes_digest: Sha256Digest
    replacement_digest: Sha256Digest
    reason: Annotated[str, StringConstraints(min_length=1, max_length=8192)]


class CaptureRequest(RecordBase):
    record_type: Literal["capture_request"] = "capture_request"
    source_seal: Sha256Digest
    allowed_paths: tuple[SafeRelativePath, ...] = Field(max_length=4096)


class AppIntelligenceReturn(RecordBase):
    record_type: Literal["app_intelligence_return"] = "app_intelligence_return"
    capture_request_id: RecordId
    source_seal: Sha256Digest
    claim_digests: tuple[Sha256Digest, ...] = Field(max_length=10000)


class CaptureAcceptanceRecord(RecordBase):
    record_type: Literal["capture_acceptance"] = "capture_acceptance"
    app_intelligence_return_id: RecordId
    accepted_source_seal: Sha256Digest
    accepted_by: RecordId


class ContinuationPlan(NamedRecord):
    record_type: Literal["continuation_plan"] = "continuation_plan"
    capture_acceptance_id: RecordId
    base_seal: Sha256Digest
    task_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=4096)


class ArtifactRecord(RecordBase):
    record_type: Literal["artifact_record"] = "artifact_record"
    digest: Sha256Digest
    media_type: MediaType
    size: Annotated[int, Field(ge=0)]
    source_revision_digest: Sha256Digest


class ReleaseRecord(RecordBase):
    record_type: Literal["release_record"] = "release_record"
    version: Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+(?:[a-z0-9.-]+)?$")]
    artifact_ids: tuple[RecordId, ...] = Field(min_length=1, max_length=1024)
    release_gate_matrix_digest: Sha256Digest
    state: Literal["planned", "built", "hashed", "extracted", "retested", "attested", "frozen", "published"]


class AttestationRecord(RecordBase):
    record_type: Literal["attestation_record"] = "attestation_record"
    subject_digest: Sha256Digest
    predicate_type: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    envelope_digest: Sha256Digest


class EvaluationRun(RecordBase):
    record_type: Literal["evaluation_run"] = "evaluation_run"
    protocol_digest: Sha256Digest
    candidate_digest: Sha256Digest
    partition: Literal["development", "validation", "holdout"]
    state: Literal["planned", "sealed", "running", "complete", "invalidated"]


class PolicyDecision(RecordBase):
    record_type: Literal["policy_decision"] = "policy_decision"
    policy_digest: Sha256Digest
    actor_id: RecordId
    action_definition_digest: Sha256Digest
    decision: Literal["allow", "deny"]
    rule_ids: tuple[StableCode, ...] = Field(min_length=1, max_length=1024)


class OutboxEntry(RecordBase):
    record_type: Literal["outbox_entry"] = "outbox_entry"
    aggregate_id: RecordId
    operation: StableCode
    idempotency_key: Annotated[str, StringConstraints(min_length=16, max_length=256)]
    payload_digest: Sha256Digest
    state: Literal["pending", "dispatched", "confirmed", "outcome_unknown", "reconciled"]


class SupportClaim(RecordBase):
    record_type: Literal["support_claim"] = "support_claim"
    environment_id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{2,127}$")]
    capability: StableCode
    status: Literal["planned", "supported", "unsupported", "deferred"]
    evidence_digests: tuple[Sha256Digest, ...] = Field(max_length=1024)


class TypedEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    envelope_version: Literal["1.0.0"] = "1.0.0"
    payload_type: Annotated[str, StringConstraints(pattern=r"^application/vnd\.nilhan\.laos\.[a-z0-9.-]+\+json$")]
    payload: Annotated[str, StringConstraints(min_length=1, max_length=2_000_000)]
    algorithm: Literal["Ed25519"]
    key_id: RecordId
    key_purpose: Literal["capsule", "event_anchor", "release"]
    issuer: RecordId
    audience: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    subject_digest: Sha256Digest
    issued_at: UtcTimestamp
    expires_at: UtcTimestamp | None
    signature: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{86}$")]


RecordModel = (
    Engagement
    | ProductObjective
    | NewBuildRequest
    | BlueprintAcceptanceRecord
    | GenesisRepositoryRecord
    | ProjectBlueprint
    | Requirement
    | AcceptanceCriterion
    | Task
    | ActionDefinition
    | ActionCapsule
    | ActionAttempt
    | PromotionIntent
    | WorkspaceSeal
    | RepositoryManifest
    | ActorIdentity
    | CapabilityGrant
    | ModelProfile
    | PromptContract
    | CheckDefinition
    | CheckRun
    | EvidenceObject
    | EvidenceBinding
    | ReviewRecord
    | SideEffectRecord
    | ApprovalRecord
    | CheckpointRecord
    | IncidentRecord
    | AmendmentRecord
    | CaptureRequest
    | AppIntelligenceReturn
    | CaptureAcceptanceRecord
    | ContinuationPlan
    | ArtifactRecord
    | ReleaseRecord
    | AttestationRecord
    | EvaluationRun
    | PolicyDecision
    | OutboxEntry
    | SupportClaim
)

RECORD_MODELS: tuple[type[RecordBase], ...] = (
    Engagement,
    ProductObjective,
    NewBuildRequest,
    BlueprintAcceptanceRecord,
    GenesisRepositoryRecord,
    ProjectBlueprint,
    Requirement,
    AcceptanceCriterion,
    Task,
    ActionDefinition,
    ActionCapsule,
    ActionAttempt,
    PromotionIntent,
    WorkspaceSeal,
    RepositoryManifest,
    ActorIdentity,
    CapabilityGrant,
    ModelProfile,
    PromptContract,
    CheckDefinition,
    CheckRun,
    EvidenceObject,
    EvidenceBinding,
    ReviewRecord,
    SideEffectRecord,
    ApprovalRecord,
    CheckpointRecord,
    IncidentRecord,
    AmendmentRecord,
    CaptureRequest,
    AppIntelligenceReturn,
    CaptureAcceptanceRecord,
    ContinuationPlan,
    ArtifactRecord,
    ReleaseRecord,
    AttestationRecord,
    EvaluationRun,
    PolicyDecision,
    OutboxEntry,
    SupportClaim,
)


def model_for_record_type(record_type: str) -> type[RecordBase] | None:
    return next((model for model in RECORD_MODELS if model.model_fields["record_type"].default == record_type), None)
