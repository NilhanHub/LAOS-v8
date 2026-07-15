"""Clean, non-repairing verification in a distinct disposable workspace."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .canonical import canonical_json
from .errors import SecurityError, ValidationError
from .policy import ResourceBudget
from .safe_paths import REPARSE_POINT
from .sandbox import CommandSpec, SandboxProvider


class VerificationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: str = Field(default="1.0.0", pattern=r"^1\.0\.0$")
    receipt_id: str = Field(pattern=r"^verification:[a-f0-9]{32}$")
    status: str = Field(pattern=r"^PASS$")
    criterion_ids: tuple[str, ...]
    source_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_tree: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    post_verification_source_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    verifier_workspace_id: str = Field(pattern=r"^workspace:clean:[a-f0-9]{32}$")
    provider_id: str
    image: str
    argv_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    exit_code: int
    stdout_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    stderr_digest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    repair_permitted: bool = False


def _tree_digest(root: Path) -> str:
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & REPARSE_POINT:
            raise SecurityError(
                "clean verifier source contains a link or reparse point",
                code="CLEAN_SOURCE_LINK_DENIED",
            )
        if path.is_dir():
            continue
        if not stat.S_ISREG(info.st_mode):
            raise SecurityError("clean verifier source contains a special file", code="CLEAN_SOURCE_SPECIAL_FILE")
        payload = path.read_bytes()
        entries.append({"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    return f"sha256:{hashlib.sha256(canonical_json(entries)).hexdigest()}"


class CleanVerifier:
    def __init__(self, sandbox: SandboxProvider) -> None:
        self.sandbox = sandbox

    def verify(
        self,
        candidate: Path,
        *,
        argv: tuple[str, ...],
        budget: ResourceBudget,
        criterion_ids: tuple[str, ...],
        source_commit: str,
        source_tree: str,
        protected_check_workspace: Path | None = None,
    ) -> VerificationReceipt:
        source = candidate.resolve(strict=True)
        if not source.is_dir() or not criterion_ids or len(criterion_ids) != len(set(criterion_ids)):
            raise ValidationError("clean verification input is invalid", code="CLEAN_VERIFICATION_INPUT_INVALID")
        source_digest = _tree_digest(source)
        workspace_id = f"workspace:clean:{uuid.uuid4().hex}"
        with tempfile.TemporaryDirectory(prefix="laos-clean-verifier-") as temporary:
            verifier_root = Path(temporary) / "source"
            shutil.copytree(source, verifier_root, ignore=shutil.ignore_patterns(".git"))
            if protected_check_workspace is not None:
                mountpoint = verifier_root / ".laos-protected-checks"
                if mountpoint.exists():
                    raise SecurityError(
                        "candidate occupies the protected-check control path",
                        code="PROTECTED_CHECK_MOUNTPOINT_OCCUPIED",
                    )
                mountpoint.mkdir(mode=0o500)
            for path in verifier_root.rglob("*"):
                if path.is_file():
                    os.chmod(path, stat.S_IREAD)
            result = self.sandbox.run_spec(
                CommandSpec(
                    argv=argv,
                    workspace=verifier_root,
                    budget=budget,
                    protected_check_workspace=protected_check_workspace,
                    execution_role="verifier",
                )
            )
        post_digest = _tree_digest(source)
        if post_digest != source_digest:
            raise SecurityError("authoritative source changed during clean verification", code="CLEAN_SOURCE_DRIFT")
        if result.exit_code != 0:
            raise SecurityError(
                "clean verification failed",
                code="CLEAN_VERIFICATION_FAILED",
                context={
                    "exit_code": result.exit_code,
                    "stdout_digest": result.stdout_digest,
                    "stderr_digest": result.stderr_digest,
                },
            )
        return VerificationReceipt(
            receipt_id=f"verification:{uuid.uuid4().hex}",
            status="PASS",
            criterion_ids=criterion_ids,
            source_commit=source_commit,
            source_tree=source_tree,
            source_digest=source_digest,
            post_verification_source_digest=post_digest,
            verifier_workspace_id=workspace_id,
            provider_id=result.provider,
            image=result.image,
            argv_digest=f"sha256:{hashlib.sha256(canonical_json(list(argv))).hexdigest()}",
            exit_code=result.exit_code,
            stdout_digest=result.stdout_digest,
            stderr_digest=result.stderr_digest,
        )
