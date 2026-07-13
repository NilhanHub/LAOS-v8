"""Disposable Git candidate workspaces with independent control data."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import RepositoryDrift, SecurityError
from .repository_truth import ManifestSnapshot, build_manifest


def _git(root: Path | None, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise SecurityError("Git is unavailable", code="GIT_UNAVAILABLE")
    command = [executable]
    if root is not None:
        command.extend(("-C", str(root)))
    command.extend(args)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)  # noqa: S603
    if completed.returncode:
        raise RepositoryDrift(completed.stderr.strip() or "Git workspace operation failed", code="GIT_WORKSPACE_FAILED")
    return completed.stdout.strip()


@dataclass(frozen=True, slots=True)
class CandidateWorkspace:
    source: Path
    root: Path
    base_commit: str
    base_seal: str

    @classmethod
    def create(cls, source: Path, destination: Path) -> CandidateWorkspace:
        source = source.resolve(strict=True)
        if destination.exists():
            raise SecurityError("candidate destination already exists", code="CANDIDATE_DESTINATION_EXISTS")
        base = build_manifest(source, seal_kind="base")
        _git(None, "clone", "--no-local", "--no-hardlinks", "--no-tags", str(source), str(destination))
        root = destination.resolve(strict=True)
        common = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve(strict=True)
        expected_git = (root / ".git").resolve(strict=True)
        if common != expected_git or not expected_git.is_dir():
            raise SecurityError("candidate shares or redirects Git control data", code="CANDIDATE_GIT_NOT_ISOLATED")
        _git(root, "checkout", "--detach", base.git_head)
        observed = build_manifest(root, seal_kind="base")
        if observed.seal != base.seal:
            raise RepositoryDrift("candidate clone does not reproduce base seal", code="CANDIDATE_BASE_MISMATCH")
        return cls(source, root, base.git_head, base.seal)

    def commit(self, message: str = "LAOS candidate result") -> tuple[str, ManifestSnapshot]:
        _git(self.root, "add", "--all")
        _git(
            self.root,
            "-c",
            "user.name=LAOS Test Builder",
            "-c",
            "user.email=laos-builder.invalid",
            "commit",
            "--no-gpg-sign",
            "-m",
            message,
        )
        commit = _git(self.root, "rev-parse", "HEAD")
        return commit, build_manifest(self.root, seal_kind="result")

    def reconstruct(self, destination: Path) -> ManifestSnapshot:
        if destination.exists():
            raise SecurityError("verification destination already exists", code="VERIFIER_DESTINATION_EXISTS")
        _git(None, "clone", "--no-local", "--no-hardlinks", "--no-tags", str(self.root), str(destination))
        verifier = destination.resolve(strict=True)
        _git(verifier, "checkout", "--detach", _git(self.root, "rev-parse", "HEAD"))
        return build_manifest(verifier, seal_kind="result")


@dataclass(frozen=True, slots=True)
class PromotionReceipt:
    status: str
    target_ref: str
    expected_base: str
    result_commit: str


def promote_compare_and_swap(
    authoritative: Path,
    candidate: Path,
    *,
    target_ref: str,
    expected_base: str,
    result_commit: str,
) -> PromotionReceipt:
    if not target_ref.startswith("refs/heads/") or ".." in target_ref:
        raise SecurityError("promotion target ref denied", code="PROMOTION_REF_DENIED")
    current = _git(authoritative, "rev-parse", target_ref)
    if current == result_commit:
        return PromotionReceipt("ALREADY_PROMOTED", target_ref, expected_base, result_commit)
    if current != expected_base:
        raise RepositoryDrift(
            "authoritative ref changed before promotion",
            code="PROMOTION_CAS_CONFLICT",
            context={"expected": expected_base, "observed": current},
        )
    _git(authoritative, "fetch", "--no-tags", str(candidate), result_commit)
    fetched = _git(authoritative, "rev-parse", "FETCH_HEAD")
    if fetched != result_commit:
        raise RepositoryDrift("fetched result commit mismatch", code="PROMOTION_FETCH_MISMATCH")
    _git(authoritative, "update-ref", target_ref, result_commit, expected_base)
    return PromotionReceipt("PROMOTED", target_ref, expected_base, result_commit)
