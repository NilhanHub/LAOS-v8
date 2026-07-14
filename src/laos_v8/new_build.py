"""Governed, content-addressed new-build genesis compiler."""

from __future__ import annotations

import base64
import hashlib
import os
import shutil
import subprocess
import unicodedata
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .action_engine import ActionNode
from .canonical import canonical_json
from .errors import AuthorizationDenied, SecurityError, StateConflict, ValidationError
from .repository_truth import build_manifest, require_unchanged
from .safe_paths import SafeRoot, validate_relative_path

_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _validated_template_path(value: str) -> PurePosixPath:
    parsed = validate_relative_path(value)
    normalized_parts: list[str] = []
    for part in parsed.parts:
        normalized = unicodedata.normalize("NFC", part)
        if normalized != part:
            raise ValueError("TEMPLATE_PATH_NONCANONICAL")
        if part.endswith((" ", ".")):
            raise ValueError("TEMPLATE_PATH_AMBIGUOUS")
        device_name = part.split(".", maxsplit=1)[0].upper()
        if device_name in _WINDOWS_RESERVED_NAMES:
            raise ValueError("TEMPLATE_PATH_AMBIGUOUS")
        normalized_parts.append(normalized)
    result = PurePosixPath(*normalized_parts)
    if result.parts[0].casefold() in {".git", ".laos"}:
        raise ValueError("TEMPLATE_CONTROL_PATH_DENIED")
    return result


def _template_collision_key(value: str) -> str:
    return _validated_template_path(value).as_posix().casefold()


class ProductObjective(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    goals: tuple[str, ...] = Field(min_length=1, max_length=256)
    users: tuple[str, ...] = Field(min_length=1, max_length=256)
    constraints: tuple[str, ...] = Field(min_length=1, max_length=256)
    non_goals: tuple[str, ...] = Field(min_length=1, max_length=256)
    data_classes: tuple[Literal["public", "internal", "restricted"], ...] = Field(min_length=1, max_length=3)
    risk_posture: Literal["low", "medium", "high"]
    target_support_environment: str = Field(min_length=1, max_length=1024)
    unresolved_decisions: tuple[str, ...] = Field(max_length=256)


class RequirementNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    requirement_id: str = Field(pattern=r"^requirement:[A-Za-z0-9._-]{1,120}$")
    statement: str = Field(min_length=1, max_length=8192)
    depends_on: tuple[str, ...] = Field(max_length=256)
    mandatory: bool = True


class CriterionNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    criterion_id: str = Field(pattern=r"^criterion:[A-Za-z0-9._-]{1,120}$")
    requirement_id: str
    statement: str = Field(min_length=1, max_length=8192)


class Blueprint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    blueprint_id: str = Field(pattern=r"^blueprint:[A-Za-z0-9._-]{1,120}$")
    version: int = Field(ge=1)
    supersedes_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    objective: ProductObjective
    requirements: tuple[RequirementNode, ...] = Field(min_length=1, max_length=10_000)
    criteria: tuple[CriterionNode, ...] = Field(min_length=1, max_length=10_000)
    security_boundaries: tuple[str, ...] = Field(min_length=1, max_length=256)
    budget: tuple[str, ...] = Field(min_length=1, max_length=256)
    initial_scope: tuple[str, ...] = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def graph_is_complete_and_acyclic(self) -> Blueprint:
        if self.objective.unresolved_decisions:
            raise ValueError("BLUEPRINT_MANDATORY_DECISIONS_UNRESOLVED")
        if (self.version == 1 and self.supersedes_digest is not None) or (
            self.version > 1 and self.supersedes_digest is None
        ):
            raise ValueError("BLUEPRINT_SUPERSESSION_INVALID")
        requirement_ids = [item.requirement_id for item in self.requirements]
        criterion_ids = [item.criterion_id for item in self.criteria]
        if len(requirement_ids) != len(set(requirement_ids)) or len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("BLUEPRINT_DUPLICATE_NODE")
        known = set(requirement_ids)
        for requirement in self.requirements:
            if requirement.requirement_id in requirement.depends_on or not set(requirement.depends_on) <= known:
                raise ValueError("BLUEPRINT_DEPENDENCY_INVALID")
        pending = set(known)
        resolved: set[str] = set()
        while pending:
            ready = {
                item
                for item in pending
                if set(next(r for r in self.requirements if r.requirement_id == item).depends_on) <= resolved
            }
            if not ready:
                raise ValueError("BLUEPRINT_REQUIREMENT_CYCLE")
            resolved.update(ready)
            pending.difference_update(ready)
        criterion_requirements = {item.requirement_id for item in self.criteria}
        if not criterion_requirements <= known:
            raise ValueError("BLUEPRINT_ORPHAN_CRITERION")
        mandatory = {item.requirement_id for item in self.requirements if item.mandatory}
        if not mandatory <= criterion_requirements:
            raise ValueError("BLUEPRINT_SILENT_REQUIREMENT_LOSS")
        return self

    @property
    def digest(self) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(self.model_dump(mode='json'))).hexdigest()}"


class NewBuildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    request_id: str = Field(pattern=r"^new-build:[A-Za-z0-9._-]{1,120}$")
    project_id: str = Field(pattern=r"^project:[A-Za-z0-9._-]{1,120}$")
    blueprint_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    template_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    initial_action: ActionNode


class BlueprintAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    acceptance_id: str = Field(pattern=r"^acceptance:[A-Za-z0-9._-]{1,120}$")
    blueprint_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    architect_proposal_envelope_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    human_reviewer: Literal["Nilhan"]
    accepted_at: str
    expires_at: str


class TemplateFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    path: str
    content_b64: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    executable: bool = False

    @model_validator(mode="after")
    def safe_and_exact(self) -> TemplateFile:
        _validated_template_path(self.path)
        try:
            payload = base64.b64decode(self.content_b64, validate=True)
        except ValueError as exc:
            raise ValueError("TEMPLATE_BASE64_INVALID") from exc
        if hashlib.sha256(payload).hexdigest() != self.sha256:
            raise ValueError("TEMPLATE_FILE_DIGEST_MISMATCH")
        return self

    def payload(self) -> bytes:
        return base64.b64decode(self.content_b64, validate=True)


class ReviewedTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    template_id: str = Field(pattern=r"^template:[A-Za-z0-9._-]{1,120}$")
    toolchain: tuple[str, ...] = Field(min_length=1, max_length=256)
    dependencies: tuple[str, ...] = Field(max_length=10_000)
    licenses: tuple[str, ...] = Field(min_length=1, max_length=256)
    provenance: tuple[str, ...] = Field(min_length=1, max_length=256)
    compatible_environments: tuple[str, ...] = Field(min_length=1, max_length=256)
    files: tuple[TemplateFile, ...] = Field(min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def unique_paths(self) -> ReviewedTemplate:
        paths = [_template_collision_key(item.path) for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("TEMPLATE_DUPLICATE_PATH")
        return self

    @property
    def digest(self) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(self.model_dump(mode='json'))).hexdigest()}"


class TemplateRegistry:
    def __init__(self, templates: tuple[ReviewedTemplate, ...]) -> None:
        self._templates = {item.digest: item for item in templates}
        if len(self._templates) != len(templates):
            raise ValidationError("duplicate template digest", code="TEMPLATE_DUPLICATE_DIGEST")

    def require(self, digest: str, *, environment: str) -> ReviewedTemplate:
        try:
            template = self._templates[digest]
        except KeyError as exc:
            raise AuthorizationDenied("template is not reviewed", code="TEMPLATE_UNTRUSTED") from exc
        if environment not in template.compatible_environments:
            raise AuthorizationDenied("template is incompatible", code="TEMPLATE_INCOMPATIBLE")
        return template


class GenesisReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    project_id: str
    intent_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    blueprint_digest: str
    template_digest: str
    genesis_commit: str = Field(pattern=r"^[0-9a-f]{40,64}$")
    source_seal: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    base_seal: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    first_action: ActionNode
    trace_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


def _git(root: Path | None, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise SecurityError("Git is unavailable", code="GIT_UNAVAILABLE")
    command = [executable]
    if root is not None:
        command.extend(("-C", str(root)))
    command.extend(args)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    completed = subprocess.run(command, text=True, capture_output=True, check=False, env=environment)  # noqa: S603
    if completed.returncode:
        raise StateConflict(completed.stderr.strip() or "genesis Git operation failed", code="GENESIS_GIT_FAILED")
    return completed.stdout.strip()


class GenesisCompiler:
    def __init__(self, registry: TemplateRegistry, control_root: Path) -> None:
        self.registry = registry
        self.control_root = control_root.resolve()
        self.control_root.mkdir(parents=True, exist_ok=True)

    def compile(
        self,
        request: NewBuildRequest,
        blueprint: Blueprint,
        acceptance: BlueprintAcceptance,
        *,
        destination: Path,
        now: str,
    ) -> GenesisReceipt:
        if request.blueprint_digest != blueprint.digest or acceptance.blueprint_digest != blueprint.digest:
            raise AuthorizationDenied("blueprint binding mismatch", code="GENESIS_BLUEPRINT_BINDING_MISMATCH")
        accepted = datetime.fromisoformat(acceptance.accepted_at.replace("Z", "+00:00")).astimezone(UTC)
        current = datetime.fromisoformat(now.replace("Z", "+00:00")).astimezone(UTC)
        expiry = datetime.fromisoformat(acceptance.expires_at.replace("Z", "+00:00")).astimezone(UTC)
        if current < accepted:
            raise AuthorizationDenied("blueprint acceptance is not yet valid", code="GENESIS_ACCEPTANCE_NOT_YET_VALID")
        if current >= expiry:
            raise AuthorizationDenied("blueprint acceptance is stale", code="GENESIS_ACCEPTANCE_EXPIRED")
        if not set(request.initial_action.allowed_files) <= set(blueprint.initial_scope):
            raise AuthorizationDenied("first action exceeds accepted scope", code="GENESIS_FIRST_ACTION_SCOPE_DENIED")
        blueprint_criteria = {item.criterion_id for item in blueprint.criteria}
        if not set(request.initial_action.criterion_ids) <= blueprint_criteria:
            raise AuthorizationDenied(
                "first action criterion is not accepted",
                code="GENESIS_FIRST_ACTION_CRITERION_DENIED",
            )
        template = self.registry.require(
            request.template_digest,
            environment=blueprint.objective.target_support_environment,
        )
        intent = canonical_json(
            {
                "request": request.model_dump(mode="json"),
                "blueprint_digest": blueprint.digest,
                "acceptance": acceptance.model_dump(mode="json"),
                "destination": str(destination.resolve()),
            }
        )
        intent_digest = f"sha256:{hashlib.sha256(intent).hexdigest()}"
        receipt_path = self.control_root / f"{request.project_id.removeprefix('project:')}.receipt.json"
        if receipt_path.exists():
            receipt = GenesisReceipt.model_validate_json(receipt_path.read_bytes(), strict=True)
            if receipt.intent_digest != intent_digest or receipt.project_id != request.project_id:
                raise StateConflict("project genesis intent differs", code="GENESIS_INTENT_CONFLICT")
            require_unchanged(destination, receipt.source_seal, seal_kind="source")
            return receipt
        if destination.exists():
            partial_intent_path = destination / ".laos" / "genesis-intent.json"
            if not partial_intent_path.is_file() or partial_intent_path.read_bytes() != intent:
                raise StateConflict("destination belongs to another project or intent", code="GENESIS_PATH_COLLISION")
            quarantine_name = (
                f"quarantine-{request.project_id.removeprefix('project:')}-{intent_digest[7:19]}"
            )
            quarantine = self.control_root / quarantine_name
            if quarantine.exists():
                raise StateConflict("genesis quarantine collision", code="GENESIS_QUARANTINE_COLLISION")
            destination.replace(quarantine)
        destination.mkdir(parents=True)
        try:
            safe_destination = SafeRoot(destination)
            for item in template.files:
                relative = _validated_template_path(item.path)
                parents: list[str] = []
                for part in relative.parent.parts:
                    parents.append(part)
                    safe_destination.for_write("/".join(parents)).mkdir(exist_ok=True)
                target = safe_destination.write_bytes_atomic(
                    relative.as_posix(),
                    item.payload(),
                    max_bytes=104_857_600,
                )
                if item.executable:
                    target.chmod(0o755)
            control = safe_destination.for_write(".laos")
            control.mkdir()
            safe_destination.write_bytes_atomic(
                ".laos/blueprint.json",
                canonical_json(blueprint.model_dump(mode="json")),
                max_bytes=2_000_000,
            )
            safe_destination.write_bytes_atomic(
                ".laos/genesis-intent.json",
                intent,
                max_bytes=2_000_000,
            )
            _git(None, "init", "--initial-branch=main", str(destination))
            _git(destination, "config", "core.hooksPath", os.devnull)
            _git(destination, "config", "commit.gpgSign", "false")
            _git(destination, "add", "--all")
            _git(
                destination,
                "-c",
                "user.name=LAOS Genesis Controller",
                "-c",
                "user.email=laos-genesis.invalid",
                "commit",
                "--no-gpg-sign",
                "-m",
                "LAOS governed genesis",
            )
            commit = _git(destination, "rev-parse", "HEAD")
            source = build_manifest(destination, seal_kind="source")
            base = build_manifest(destination, seal_kind="base")
            trace = canonical_json(
                {
                    "blueprint_digest": blueprint.digest,
                    "template_digest": template.digest,
                    "genesis_commit": commit,
                    "source_seal": source.seal,
                    "base_seal": base.seal,
                    "first_action": request.initial_action.model_dump(mode="json"),
                }
            )
            receipt = GenesisReceipt(
                project_id=request.project_id,
                intent_digest=intent_digest,
                blueprint_digest=blueprint.digest,
                template_digest=template.digest,
                genesis_commit=commit,
                source_seal=source.seal,
                base_seal=base.seal,
                first_action=request.initial_action,
                trace_digest=f"sha256:{hashlib.sha256(trace).hexdigest()}",
            )
            receipt_path.write_bytes(canonical_json(receipt.model_dump(mode="json")))
            return receipt
        except Exception:
            failed = self.control_root / f"failed-{request.project_id.removeprefix('project:')}-{intent_digest[7:19]}"
            if destination.exists() and not failed.exists():
                destination.replace(failed)
            raise
