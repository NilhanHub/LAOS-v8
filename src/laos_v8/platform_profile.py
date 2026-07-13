"""Runtime platform diagnostics and conservative SQLite journal selection."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split(".") if part.isdigit())


def sqlite_wal_reset_fix_verified(version: str) -> bool:
    parsed = _version_tuple(version)
    if parsed >= (3, 51, 3):
        return True
    return (3, 50, 7) <= parsed < (3, 51, 0) or (3, 44, 6) <= parsed < (3, 45, 0)


def recommended_sqlite_journal_mode(version: str) -> str:
    return "WAL" if sqlite_wal_reset_fix_verified(version) else "DELETE"


def _git_version() -> str:
    git = shutil.which("git")
    if git is None:
        return "unavailable"
    completed = subprocess.run(  # noqa: S603 - resolved executable and fixed argv
        [git, "--version"], text=True, capture_output=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


@dataclass(frozen=True, slots=True)
class PlatformReport:
    status: str
    python_version: str
    python_implementation: str
    operating_system: str
    machine: str
    git_version: str
    sqlite_version: str
    sqlite_wal_reset_fix_verified: bool
    sqlite_journal_mode: str
    filesystem: str
    connected_privileged_profile_claimed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def doctor(root: Path) -> PlatformReport:
    version = sqlite3.sqlite_version
    supported_python = (3, 11) <= sys.version_info[:2] < (3, 15)
    git_version = _git_version()
    status = "PASS" if supported_python and git_version != "unavailable" else "FAIL"
    return PlatformReport(
        status=status,
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        operating_system=platform.platform(),
        machine=platform.machine(),
        git_version=git_version,
        sqlite_version=version,
        sqlite_wal_reset_fix_verified=sqlite_wal_reset_fix_verified(version),
        sqlite_journal_mode=recommended_sqlite_journal_mode(version),
        filesystem=os.path.splitdrive(str(root.resolve()))[0] or "/",
        connected_privileged_profile_claimed=False,
    )


def write_doctor_report(root: Path, output: Path) -> None:
    output.write_bytes((json.dumps(doctor(root).as_dict(), indent=2) + "\n").encode("utf-8"))
