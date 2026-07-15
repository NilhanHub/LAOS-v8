"""Strict Stage 6 clean-reconstruction candidate receipt."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .clean_verifier import VerificationReceipt
from .evidence_custody import CustodiedEvidenceObject, SignedEvidenceIndex
from .evidence_receipts import CommandReceipt
from .protected_checks import ProtectedCheckBundle
from .protected_review import ReviewChallenge


class Stage6CandidateReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    run_id: str = Field(pattern=r"^run:[a-f0-9]{32}$")
    status: Literal["PASS_AWAITING_NILHAN_PROTECTED_REVIEW"]
    assurance: Literal["STAGE_6_WINDOWS_DOCKER_LOW_MODERATE_CANDIDATE"]
    generator_version: Literal["laos-stage6-candidate/1.0.0"]
    source_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_tree: str = Field(pattern=r"^[a-f0-9]{40}$")
    plan_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    started_at_utc: str
    completed_at_utc: str
    commands: tuple[CommandReceipt, ...] = Field(min_length=10, max_length=32)
    stage4_model_proposal_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    stage4_original_result_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    replay_verification: VerificationReceipt
    protected_check_bundle: ProtectedCheckBundle
    custody_object: CustodiedEvidenceObject
    evidence_index: SignedEvidenceIndex
    event_anchor_key_id: str
    event_anchor_public_key_b64: str
    review_challenge: ReviewChallenge
    requirement_count: Literal[49] = 49
    release_blockers_open: tuple[Literal["RB-011", "RB-012", "RB-013", "RB-014"], ...]
    new_model_profile_released: Literal[False] = False
    maximum_supported_risk: Literal["MODERATE"] = "MODERATE"
    high_critical_status: Literal["DENIED_QUORUM_UNAVAILABLE"] = "DENIED_QUORUM_UNAVAILABLE"
    real_credentials: Literal["DENIED"] = "DENIED"
    v8_runtime_complete: Literal[False] = False
    v8_release_exists: Literal[False] = False

    @model_validator(mode="after")
    def candidate_is_complete_but_unapproved(self) -> Stage6CandidateReceipt:
        labels = [item.label for item in self.commands]
        if len(labels) != len(set(labels)) or any(item.status != "PASS" for item in self.commands):
            raise ValueError("STAGE6_CANDIDATE_COMMANDS_INVALID")
        if set(self.release_blockers_open) != {"RB-011", "RB-012", "RB-013", "RB-014"}:
            raise ValueError("STAGE6_CANDIDATE_BLOCKERS_INVALID")
        if self.review_challenge.capsule.candidate_commit != self.source_commit:
            raise ValueError("STAGE6_CANDIDATE_REVIEW_SOURCE_MISMATCH")
        if self.review_challenge.capsule.evidence_index_digest != self.evidence_index.event_anchor_envelope_digest:
            raise ValueError("STAGE6_CANDIDATE_REVIEW_EVIDENCE_MISMATCH")
        return self
