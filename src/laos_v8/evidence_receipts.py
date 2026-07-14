"""Versioned, run-bound evidence receipts for bootstrap assurance gates."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
GitObjectId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40,64}$")]

STAGE5_SCOPED_PATHS = (
    "src",
    "tests/stage2",
    "tests/stage3",
    "tests/stage4",
    "tests/stage5",
    "scripts/generate_stage3_evidence.py",
    "scripts/verify_stage3.py",
    "scripts/verify_stage5_checkpoint.py",
    "scripts/build_stage3_candidate_evidence.py",
    "scripts/build_stage5_candidate_evidence.py",
)
STAGE5_SECURITY_TESTS = (
    "tests/stage2/test_canonical_and_transitions.py",
    "tests/stage3/test_capsule_and_signing.py",
    "tests/stage5/test_action_engine.py",
    "tests/stage5/test_packs_and_trust.py",
    "tests/stage5/test_core_workflows.py",
    "tests/stage5/test_capture_security.py",
    "tests/stage5/test_evidence_integrity.py",
)


def stage5_candidate_command_policy(run_id: str, source_commit: str) -> dict[str, tuple[str, ...]]:
    """Return the exact, run-bound command policy accepted for a Stage 5 candidate."""

    stage3_root = Path(tempfile.gettempdir()) / f"laos-stage5-{run_id.removeprefix('run:')}"
    stage3_evidence = str(stage3_root / "STAGE_3_LOCAL_SECURITY_PROFILE.json")
    stage3_verification = str(stage3_root / "STAGE_3_VERIFICATION.json")
    return {
        "uv_sync": ("uv", "sync", "--frozen", "--all-groups"),
        "ruff_scoped": ("uv", "run", "--frozen", "ruff", "check", *STAGE5_SCOPED_PATHS),
        "mypy": ("uv", "run", "--frozen", "mypy"),
        "pytest_full": ("uv", "run", "--frozen", "pytest", "-q"),
        "docker_integration": (
            "uv",
            "run",
            "--frozen",
            "pytest",
            "-q",
            "tests/stage3/test_brokers_sandbox_evidence.py::test_real_docker_sandbox_when_engine_available",
        ),
        "verify_stage1": ("uv", "run", "--frozen", "python", "scripts/verify_stage1.py"),
        "verify_stage2": ("uv", "run", "--frozen", "python", "scripts/verify_stage2.py"),
        "verify_stage3": (
            "uv",
            "run",
            "--frozen",
            "python",
            "scripts/verify_stage3.py",
            "--evidence",
            stage3_evidence,
            "--expected-run-id",
            run_id,
            "--expected-source-commit",
            source_commit,
            "--output",
            stage3_verification,
        ),
        "verify_stage4": ("uv", "run", "--frozen", "python", "scripts/verify_stage4.py"),
        "verify_stage5": (
            "uv",
            "run",
            "--frozen",
            "python",
            "scripts/verify_stage5_checkpoint.py",
        ),
        "package_build": ("uv", "build"),
        "security_regressions": (
            "uv",
            "run",
            "--frozen",
            "pytest",
            "-q",
            *STAGE5_SECURITY_TESTS,
        ),
    }


class CommandReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    label: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{2,63}$")]
    argv: tuple[Annotated[str, StringConstraints(min_length=1, max_length=4096)], ...] = Field(
        min_length=1, max_length=128
    )
    exit_code: int
    status: Literal["PASS", "FAIL"]
    stdout_sha256: Sha256Hex
    stderr_sha256: Sha256Hex
    stdout_bytes: int = Field(ge=0)
    stderr_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def exit_status_agrees(self) -> CommandReceipt:
        if (self.exit_code == 0) != (self.status == "PASS"):
            raise ValueError("EVIDENCE_COMMAND_STATUS_MISMATCH")
        return self


class ArtifactReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: Annotated[str, StringConstraints(min_length=1, max_length=1024)]
    bytes: int = Field(ge=0)
    sha256: Sha256Hex

    @model_validator(mode="after")
    def path_is_repository_relative(self) -> ArtifactReceipt:
        parsed = PurePosixPath(self.path)
        if parsed.is_absolute() or "\\" in self.path or any(part in {"", ".", ".."} for part in parsed.parts):
            raise ValueError("EVIDENCE_ARTIFACT_PATH_UNSAFE")
        return self


class EvidenceRunReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.1.0"] = "1.1.0"
    run_id: Annotated[str, StringConstraints(pattern=r"^run:[a-f0-9]{32}$")]
    stage: int = Field(ge=1, le=10)
    status: Literal["IN_PROGRESS", "FAIL", "PASS_AWAITING_NILHAN_REVIEW"]
    assurance: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    producer_authentication: Literal["NONE_STAGE6_OPEN"] = "NONE_STAGE6_OPEN"
    generator_version: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    source_commit: GitObjectId | None = None
    source_tree: GitObjectId | None = None
    started_at_utc: str
    completed_at_utc: str | None = None
    commands: tuple[CommandReceipt, ...] = Field(default=(), max_length=128)
    artifacts: tuple[ArtifactReceipt, ...] = Field(default=(), max_length=4096)
    failure_code: str | None = None

    @model_validator(mode="after")
    def state_is_complete(self) -> EvidenceRunReceipt:
        def timestamp(value: str) -> datetime:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("EVIDENCE_TIMESTAMP_INVALID") from exc
            if parsed.tzinfo is None or not value.endswith("Z"):
                raise ValueError("EVIDENCE_TIMESTAMP_INVALID")
            return parsed.astimezone(UTC)

        labels = [command.label for command in self.commands]
        paths = [artifact.path for artifact in self.artifacts]
        started = timestamp(self.started_at_utc)
        completed = timestamp(self.completed_at_utc) if self.completed_at_utc is not None else None
        if len(labels) != len(set(labels)) or len(paths) != len(set(paths)):
            raise ValueError("EVIDENCE_RECEIPT_DUPLICATE_IDENTITY")
        if self.status == "IN_PROGRESS" and self.completed_at_utc is not None:
            raise ValueError("EVIDENCE_IN_PROGRESS_HAS_COMPLETION")
        if completed is not None and completed < started:
            raise ValueError("EVIDENCE_TIMESTAMP_ORDER_INVALID")
        if self.status == "FAIL" and (self.completed_at_utc is None or not self.failure_code):
            raise ValueError("EVIDENCE_FAILURE_INCOMPLETE")
        if self.status == "PASS_AWAITING_NILHAN_REVIEW":
            if self.completed_at_utc is None or self.source_commit is None or self.source_tree is None:
                raise ValueError("EVIDENCE_PASS_PROVENANCE_INCOMPLETE")
            if not self.commands or any(command.status != "PASS" for command in self.commands):
                raise ValueError("EVIDENCE_PASS_COMMANDS_INCOMPLETE")
            if not self.artifacts or self.failure_code is not None:
                raise ValueError("EVIDENCE_PASS_ARTIFACTS_INCOMPLETE")
        return self


class EvidenceReviewReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["APPROVED"] = "APPROVED"
    reviewer: Literal["Nilhan"] = "Nilhan"
    reviewed_run_id: Annotated[str, StringConstraints(pattern=r"^run:[a-f0-9]{32}$")]
    reviewed_candidate_commit: GitObjectId
    reviewed_candidate_tag: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    evidence_receipt_sha256: Sha256Hex
    approved_at_utc: str
    approval_statement: Annotated[str, StringConstraints(min_length=1, max_length=4096)]


def new_run_id() -> str:
    return f"run:{uuid.uuid4().hex}"


def atomic_write_json(path: Path, value: BaseModel | dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
