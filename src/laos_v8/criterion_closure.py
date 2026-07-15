"""Criterion-level closure, staleness, migration, and Git CAS promotion."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .canonical import canonical_json, content_digest
from .errors import SecurityError, StateConflict, ValidationError
from .evidence_custody import EvidenceLevel
from .state import AggregateState, CanonicalState


class CriterionState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IMPLEMENTED = "IMPLEMENTED"
    EVIDENCE_READY = "EVIDENCE_READY"
    VERIFIED = "VERIFIED"
    INDEPENDENTLY_REVIEWED = "INDEPENDENTLY_REVIEWED"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    ACCEPTED = "ACCEPTED"
    STALE = "STALE"


TRANSITIONS: dict[CriterionState, frozenset[CriterionState]] = {
    CriterionState.NOT_STARTED: frozenset({CriterionState.IMPLEMENTED}),
    CriterionState.IMPLEMENTED: frozenset({CriterionState.EVIDENCE_READY, CriterionState.STALE}),
    CriterionState.EVIDENCE_READY: frozenset({CriterionState.VERIFIED, CriterionState.STALE}),
    CriterionState.VERIFIED: frozenset({CriterionState.INDEPENDENTLY_REVIEWED, CriterionState.STALE}),
    CriterionState.INDEPENDENTLY_REVIEWED: frozenset({CriterionState.PROMOTION_PENDING, CriterionState.STALE}),
    CriterionState.PROMOTION_PENDING: frozenset({CriterionState.ACCEPTED, CriterionState.STALE}),
    CriterionState.ACCEPTED: frozenset({CriterionState.STALE}),
    CriterionState.STALE: frozenset({CriterionState.IMPLEMENTED}),
}


class CriterionEvidenceMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    criterion_id: str = Field(pattern=r"^criterion:[A-Za-z0-9._:-]+$")
    risk: Literal["low", "moderate", "high", "critical"]
    required_level: EvidenceLevel
    source_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    policy_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    check_bundle_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    profile_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    environment_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    positive_evidence: tuple[str, ...]
    negative_evidence: tuple[str, ...]

    @model_validator(mode="after")
    def closure_evidence_is_specific_and_sufficient(self) -> CriterionEvidenceMatrix:
        if self.risk in {"high", "critical"}:
            raise ValueError("CRITERION_RISK_UNSUPPORTED")
        minimum = EvidenceLevel.L2 if self.risk == "low" else EvidenceLevel.L3
        order = list(EvidenceLevel)
        if order.index(self.required_level) < order.index(minimum):
            raise ValueError("CRITERION_EVIDENCE_LEVEL_INSUFFICIENT")
        if not self.positive_evidence:
            raise ValidationError(
                "criterion positive evidence is required",
                code="CRITERION_POSITIVE_EVIDENCE_REQUIRED",
            )
        if not self.negative_evidence:
            raise ValidationError(
                "criterion negative evidence is required",
                code="CRITERION_NEGATIVE_EVIDENCE_REQUIRED",
            )
        all_evidence = (*self.positive_evidence, *self.negative_evidence)
        if any(value in {"PASS", "FAIL"} for value in all_evidence):
            raise ValidationError("generic PASS cannot close a criterion", code="CRITERION_GENERIC_PASS_DENIED")
        if any(re.fullmatch(r"sha256:[a-f0-9]{64}", value) is None for value in all_evidence):
            raise ValidationError("criterion evidence digest is invalid", code="CRITERION_EVIDENCE_DIGEST_INVALID")
        if len(all_evidence) != len(set(all_evidence)):
            raise ValidationError("criterion evidence contains duplicate bindings", code="CRITERION_EVIDENCE_DUPLICATE")
        return self


class PromotionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    ref: str
    expected_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    target_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    observed_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    promoted: bool
    reconciled: bool
    receipt_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class CriterionController:
    """Stage 6 controller using a new aggregate kind; historical v1 rows remain untouched."""

    def __init__(self, state: CanonicalState) -> None:
        self.state = state

    def create(self, matrix: CriterionEvidenceMatrix, *, actor_id: str) -> AggregateState:
        payload = {
            "record_version": "2.0.0",
            "matrix": matrix.model_dump(mode="json"),
            "matrix_digest": content_digest(matrix),
            "verification_digest": None,
            "review_digest": None,
            "promotion_digest": None,
        }
        return self.state.create_aggregate(
            matrix.criterion_id,
            "criterion_v2",
            CriterionState.NOT_STARTED.value,
            payload,
            actor_id,
        )

    def _transition(
        self,
        current: AggregateState,
        target: CriterionState,
        *,
        actor_id: str,
        payload: dict[str, object],
    ) -> AggregateState:
        source = CriterionState(current.state)
        if target not in TRANSITIONS[source]:
            raise StateConflict(
                f"illegal criterion transition: {source.value} -> {target.value}",
                code="ILLEGAL_STATE_TRANSITION",
            )
        serialized = canonical_json(payload).decode("utf-8")
        digest = "sha256:" + hashlib.sha256(canonical_json({"value": payload})).hexdigest()
        with self.state.transaction() as connection:
            updated = connection.execute(
                "UPDATE aggregates SET state = ?, version = version + 1, payload_json = ?, payload_digest = ? "
                "WHERE aggregate_id = ? AND aggregate_kind = 'criterion_v2' AND version = ? AND state = ?",
                (target.value, serialized, digest, current.aggregate_id, current.version, current.state),
            )
            if updated.rowcount != 1:
                raise StateConflict("criterion compare-and-swap failed", code="STATE_VERSION_CONFLICT")
            self.state._event(
                connection,
                aggregate_id=current.aggregate_id,
                actor_id=actor_id,
                event_code="CRITERION_V2_TRANSITION",
                outcome="allowed",
                detail={"from": source.value, "to": target.value, "version": current.version + 1},
            )
        return AggregateState(
            current.aggregate_id,
            current.aggregate_kind,
            target.value,
            current.version + 1,
            payload,
            digest,
        )

    def advance(
        self,
        current: AggregateState,
        target: CriterionState,
        *,
        actor_id: str,
        verification_digest: str | None = None,
        review_digest: str | None = None,
        promotion_digest: str | None = None,
    ) -> AggregateState:
        payload: dict[str, object] = dict(current.payload)
        source = CriterionState(current.state)
        if target not in TRANSITIONS[source]:
            raise StateConflict(
                f"illegal criterion transition: {source.value} -> {target.value}",
                code="ILLEGAL_STATE_TRANSITION",
            )
        if target is CriterionState.VERIFIED:
            if verification_digest is None:
                raise ValidationError("verification receipt is required", code="CRITERION_VERIFICATION_REQUIRED")
            payload["verification_digest"] = verification_digest
        elif target is CriterionState.INDEPENDENTLY_REVIEWED:
            if review_digest is None or payload.get("verification_digest") is None:
                raise ValidationError("protected review is required", code="CRITERION_REVIEW_REQUIRED")
            payload["review_digest"] = review_digest
        elif target is CriterionState.PROMOTION_PENDING:
            if payload.get("review_digest") is None:
                raise ValidationError("accepted review is required", code="CRITERION_REVIEW_REQUIRED")
        elif target is CriterionState.ACCEPTED:
            if promotion_digest is None:
                raise ValidationError("promotion receipt is required", code="CRITERION_PROMOTION_REQUIRED")
            payload["promotion_digest"] = promotion_digest
        return self._transition(current, target, actor_id=actor_id, payload=payload)

    def invalidate_if_drifted(
        self,
        current: AggregateState,
        matrix: CriterionEvidenceMatrix,
        *,
        actor_id: str,
    ) -> AggregateState:
        digest = content_digest(matrix)
        if digest == current.payload.get("matrix_digest"):
            return current
        payload: dict[str, object] = dict(current.payload)
        payload.update(
            {
                "matrix": matrix.model_dump(mode="json"),
                "matrix_digest": digest,
                "verification_digest": None,
                "review_digest": None,
                "promotion_digest": None,
            }
        )
        return self._transition(current, CriterionState.STALE, actor_id=actor_id, payload=payload)


def migrate_historical_criterion(
    old_state: str,
    *,
    evidence_bound: bool = False,
    reviewed: bool = False,
    promoted: bool = False,
) -> CriterionState:
    if old_state == "open":
        return CriterionState.NOT_STARTED
    if old_state == "proven" and evidence_bound:
        return CriterionState.VERIFIED
    if old_state == "reviewed" and evidence_bound and reviewed:
        return CriterionState.INDEPENDENTLY_REVIEWED
    if old_state == "accepted" and evidence_bound and reviewed and promoted:
        return CriterionState.ACCEPTED
    raise ValidationError(
        "historical criterion migration requires qualifying evidence",
        code="MIGRATION_EVIDENCE_REQUIRED",
        context={"old_state": old_state},
    )


class GitPromoter:
    def __init__(self, repository: Path) -> None:
        self.repository = repository.resolve(strict=True)
        git = shutil.which("git")
        if git is None:
            raise SecurityError("Git is unavailable", code="GIT_UNAVAILABLE")
        self.git: str = git

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        return subprocess.run(  # noqa: S603 - trusted Git executable and validated structured arguments
            [self.git, "-C", str(self.repository), "-c", "core.hooksPath=" + os.devnull, *args],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
            timeout=30,
            env=environment,
        )

    def promote(self, ref: str, *, expected_commit: str, target_commit: str) -> PromotionReceipt:
        if re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", ref) is None or ".." in ref:
            raise ValidationError("promotion ref is invalid", code="PROMOTION_REF_INVALID")
        if any(re.fullmatch(r"[a-f0-9]{40}", value) is None for value in (expected_commit, target_commit)):
            raise ValidationError("promotion commit is invalid", code="PROMOTION_COMMIT_INVALID")
        if self._run("cat-file", "-e", f"{target_commit}^{{commit}}").returncode:
            raise ValidationError("promotion target commit is missing", code="PROMOTION_TARGET_MISSING")
        updated = self._run("update-ref", ref, target_commit, expected_commit)
        if updated.returncode:
            raise StateConflict("promotion compare-and-swap failed", code="PROMOTION_COMPARE_AND_SWAP_CONFLICT")
        observed_process = self._run("rev-parse", "--verify", ref)
        observed = observed_process.stdout.strip()
        reconciled = observed_process.returncode == 0 and observed == target_commit
        if not reconciled:
            raise StateConflict("promotion outcome could not be reconciled", code="PROMOTION_RECONCILIATION_FAILED")
        unsigned: dict[str, object] = {
            "record_version": "1.0.0", "ref": ref, "expected_commit": expected_commit,
            "target_commit": target_commit, "observed_commit": observed, "promoted": True, "reconciled": True,
        }
        return PromotionReceipt(
            ref=ref,
            expected_commit=expected_commit,
            target_commit=target_commit,
            observed_commit=observed,
            promoted=True,
            reconciled=True,
            receipt_digest=content_digest(unsigned),
        )
