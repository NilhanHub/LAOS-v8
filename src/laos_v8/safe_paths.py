"""Fail-closed path containment and bounded ZIP extraction."""

from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import ResourceLimitError, SecurityError, ValidationError

REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def validate_relative_path(value: str) -> PurePosixPath:
    if not value or "\x00" in value or "\\" in value:
        raise ValidationError("path must be a non-empty POSIX relative path", code="UNSAFE_PATH")
    if value.startswith(("/", "//")) or ":" in value:
        raise ValidationError("absolute, device, UNC, drive, and ADS paths are forbidden", code="UNSAFE_PATH")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValidationError("path traversal is forbidden", code="UNSAFE_PATH")
    return path


def _is_reparse(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


class SafeRoot:
    """Broker-exclusive root with no-follow checks at every path component."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValidationError("safe root must be a directory", code="SAFE_ROOT_NOT_DIRECTORY")
        root_info = self.root.lstat()
        if self.root.is_symlink() or _is_reparse(root_info):
            raise SecurityError("safe root cannot be a link or reparse point", code="SAFE_ROOT_REPARSE")

    def _join(self, relative: str, *, allow_missing_leaf: bool, allow_link_leaf: bool = False) -> Path:
        parsed = validate_relative_path(relative)
        current = self.root
        for index, part in enumerate(parsed.parts):
            current = current / part
            is_leaf = index == len(parsed.parts) - 1
            try:
                info = current.lstat()
            except FileNotFoundError:
                if allow_missing_leaf and is_leaf:
                    break
                raise ValidationError("path component does not exist", code="PATH_COMPONENT_MISSING") from None
            is_link = current.is_symlink() or _is_reparse(info)
            if is_link and not (allow_link_leaf and is_leaf):
                raise SecurityError("link or reparse traversal denied", code="PATH_REPARSE_DENIED")
            if not is_leaf and not stat.S_ISDIR(info.st_mode):
                raise ValidationError("non-directory path component", code="PATH_COMPONENT_NOT_DIRECTORY")
        containment_target = current.parent if allow_link_leaf and current.is_symlink() else current
        try:
            containment_target.resolve(strict=False).relative_to(self.root)
        except ValueError:
            raise SecurityError("path escaped safe root", code="PATH_ESCAPE_DENIED") from None
        return current

    def existing(self, relative: str) -> Path:
        path = self._join(relative, allow_missing_leaf=False)
        info = path.lstat()
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise SecurityError("unexpected hard link denied", code="PATH_HARDLINK_DENIED")
        return path

    def manifest_entry(self, relative: str) -> Path:
        """Return an lstat-safe final entry while still denying linked parent traversal."""
        return self._join(relative, allow_missing_leaf=False, allow_link_leaf=True)

    def for_write(self, relative: str) -> Path:
        path = self._join(relative, allow_missing_leaf=True)
        parent_relative = path.parent.relative_to(self.root).as_posix()
        if parent_relative != ".":
            parent = self._join(parent_relative, allow_missing_leaf=False)
            if not parent.is_dir():
                raise ValidationError("write parent is not a directory", code="WRITE_PARENT_NOT_DIRECTORY")
        return path

    def read_bytes(self, relative: str, *, max_bytes: int) -> bytes:
        path = self.existing(relative)
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise ValidationError("only regular files may be read", code="READ_NOT_REGULAR_FILE")
        if info.st_size > max_bytes:
            raise ResourceLimitError("file exceeds read budget", code="READ_SIZE_LIMIT")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            return stream.read(max_bytes + 1)

    def write_bytes_atomic(self, relative: str, payload: bytes, *, max_bytes: int) -> Path:
        if len(payload) > max_bytes:
            raise ResourceLimitError("write exceeds byte budget", code="WRITE_SIZE_LIMIT")
        target = self.for_write(relative)
        if target.exists():
            info = target.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink > 1:
                raise SecurityError("write target is not a unique regular file", code="WRITE_TARGET_DENIED")
        descriptor, temporary = tempfile.mkstemp(prefix=".laos-write-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self.for_write(relative)
            os.replace(temporary, target)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise
        return target


@dataclass(frozen=True, slots=True)
class ArchiveLimits:
    max_entries: int = 10_000
    max_total_bytes: int = 1_073_741_824
    max_entry_bytes: int = 104_857_600
    max_ratio: int = 100
    max_depth: int = 32


def safe_extract_zip(archive: Path, destination: Path, limits: ArchiveLimits | None = None) -> list[str]:
    active = limits or ArchiveLimits()
    destination.mkdir(parents=True, exist_ok=True)
    root = SafeRoot(destination)
    extracted: list[str] = []
    total = 0
    seen: set[str] = set()
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        if len(members) > active.max_entries:
            raise ResourceLimitError("archive entry limit exceeded", code="ARCHIVE_ENTRY_LIMIT")
        for member in members:
            raw_name = member.filename.rstrip("/")
            if not raw_name:
                continue
            parsed = validate_relative_path(raw_name)
            normalized = parsed.as_posix()
            collision_key = normalized.casefold()
            if collision_key in seen:
                raise SecurityError("archive duplicate or case collision", code="ARCHIVE_NAME_COLLISION")
            seen.add(collision_key)
            if len(parsed.parts) > active.max_depth:
                raise ResourceLimitError("archive nesting limit exceeded", code="ARCHIVE_DEPTH_LIMIT")
            mode = member.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type == stat.S_IFLNK or file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise SecurityError("archive links and special files are forbidden", code="ARCHIVE_LINK_DENIED")
            if member.is_dir():
                directory = root.for_write(normalized)
                directory.mkdir(exist_ok=True)
                continue
            total += member.file_size
            if member.file_size > active.max_entry_bytes or total > active.max_total_bytes:
                raise ResourceLimitError("archive expanded-size limit exceeded", code="ARCHIVE_SIZE_LIMIT")
            compressed = max(member.compress_size, 1)
            if member.file_size / compressed > active.max_ratio:
                raise ResourceLimitError("archive compression ratio limit exceeded", code="ARCHIVE_RATIO_LIMIT")
            parts: list[str] = []
            for part in parsed.parent.parts:
                parts.append(part)
                directory = root.for_write("/".join(parts))
                directory.mkdir(exist_ok=True)
            root.for_write(normalized)
            payload = source.read(member)
            if len(payload) != member.file_size:
                raise SecurityError("archive size changed during extraction", code="ARCHIVE_SIZE_MISMATCH")
            root.write_bytes_atomic(normalized, payload, max_bytes=active.max_entry_bytes)
            extracted.append(normalized)
    return extracted
