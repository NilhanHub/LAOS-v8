from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def alpha_repo(tmp_path: Path) -> Callable[[], Path]:
    git = shutil.which("git")
    assert git is not None

    def create() -> Path:
        root = tmp_path / "authoritative"
        (root / "src").mkdir(parents=True)
        (root / "src" / "calculator.py").write_bytes(
            b'"""Deliberately defective fixture."""\n\n\ndef add(a: int, b: int) -> int:\n    return a - b\n'
        )
        (root / ".gitattributes").write_bytes(b".gitattributes text eol=lf\n*.py text eol=lf\n")
        subprocess.run([git, "init", "-b", "master"], cwd=root, check=True, capture_output=True)  # noqa: S603
        subprocess.run([git, "config", "user.name", "LAOS Alpha"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "config", "user.email", "alpha.invalid"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "config", "core.autocrlf", "false"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "add", "--all"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "commit", "-m", "known defect"], cwd=root, check=True, capture_output=True)  # noqa: S603
        return root

    return create


@pytest.fixture
def actor_factory() -> Callable[..., Any]:
    from laos_v8.identity import AuthenticatedActor
    from laos_v8.models import Role

    def create(
        actor_id: str,
        role: Role,
        *,
        principal: str | None = None,
        session: str | None = None,
        workspace: str | None = None,
    ) -> AuthenticatedActor:
        return AuthenticatedActor(
            actor_id,
            principal or f"local:{actor_id}",
            (role,),
            session or f"session:{actor_id}",
            workspace or f"workspace:{actor_id}",
            0,
        )

    return create
