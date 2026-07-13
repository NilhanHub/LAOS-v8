"""Canonical Git-first repository manifests and typed seals."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .canonical import canonical_json
from .errors import RepositoryDrift, ResourceLimitError, SecurityError
from .safe_paths import REPARSE_POINT, SafeRoot, validate_relative_path

MANIFEST_ALGORITHM = "laos-git-manifest-v1"
IGNORE_POLICY = "laos-ignore-v1"
MAX_ENTRIES = 100_000
MAX_BYTES = 1_073_741_824


def _git(root: Path, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise SecurityError("Git is unavailable", code="GIT_UNAVAILABLE")
    completed = subprocess.run(  # noqa: S603 - resolved executable and fixed call sites
        [executable, "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise RepositoryDrift(completed.stderr.strip() or "Git operation failed", code="GIT_TRUTH_FAILED")
    return completed.stdout.strip()


@dataclass(frozen=True, slots=True)
class ManifestItem:
    path: str
    kind: str
    size: int
    sha256: str
    mode: int
    link_target: str | None


@dataclass(frozen=True, slots=True)
class ManifestSnapshot:
    algorithm: str
    ignore_policy: str
    git_head: str
    entries: tuple[ManifestItem, ...]
    seal: str

    def as_dict(self) -> dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "ignore_policy": self.ignore_policy,
            "git_head": self.git_head,
            "entries": [asdict(entry) for entry in self.entries],
            "seal": self.seal,
        }


def _listed_paths(root: Path) -> list[str]:
    output = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted((item for item in output.split("\x00") if item), key=lambda value: value.encode("utf-8"))


def build_manifest(root: Path, *, seal_kind: str = "workspace") -> ManifestSnapshot:
    root = root.resolve(strict=True)
    safe = SafeRoot(root)
    paths = _listed_paths(root)
    if len(paths) > MAX_ENTRIES:
        raise ResourceLimitError("repository manifest entry limit exceeded", code="MANIFEST_ENTRY_LIMIT")
    casefolded: set[str] = set()
    total = 0
    entries: list[ManifestItem] = []
    for relative in paths:
        normalized = validate_relative_path(relative).as_posix()
        collision_key = normalized.casefold()
        if collision_key in casefolded:
            raise RepositoryDrift("repository contains a case collision", code="REPOSITORY_CASE_COLLISION")
        casefolded.add(collision_key)
        path = safe.manifest_entry(normalized)
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if path.is_symlink():
            target = os.readlink(path)
            payload = target.encode("utf-8", errors="strict")
            entries.append(
                ManifestItem(normalized, "symlink", len(payload), hashlib.sha256(payload).hexdigest(), mode, target)
            )
            continue
        if getattr(info, "st_file_attributes", 0) & REPARSE_POINT:
            raise SecurityError("unexpected repository reparse point", code="REPOSITORY_REPARSE_DENIED")
        if not stat.S_ISREG(info.st_mode):
            raise SecurityError("repository entry is not a regular file", code="REPOSITORY_SPECIAL_FILE")
        total += info.st_size
        if total > MAX_BYTES:
            raise ResourceLimitError("repository manifest byte limit exceeded", code="MANIFEST_BYTE_LIMIT")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(ManifestItem(normalized, "file", info.st_size, digest, mode, None))
    head = _git(root, "rev-parse", "HEAD")
    unsigned = {
        "algorithm": MANIFEST_ALGORITHM,
        "ignore_policy": IGNORE_POLICY,
        "seal_kind": seal_kind,
        "git_head": head,
        "entries": [asdict(entry) for entry in entries],
    }
    seal = f"sha256:{hashlib.sha256(canonical_json(unsigned)).hexdigest()}"
    return ManifestSnapshot(MANIFEST_ALGORITHM, IGNORE_POLICY, head, tuple(entries), seal)


def require_unchanged(root: Path, expected_seal: str, *, seal_kind: str = "workspace") -> ManifestSnapshot:
    observed = build_manifest(root, seal_kind=seal_kind)
    if observed.seal != expected_seal:
        raise RepositoryDrift(
            "repository differs from its accepted seal",
            code="REPOSITORY_SEAL_MISMATCH",
            context={"expected": expected_seal, "observed": observed.seal},
        )
    return observed
