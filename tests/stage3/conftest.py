from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def git_repo(tmp_path: Path) -> Callable[[str], Path]:
    git = shutil.which("git")
    assert git is not None

    def create(name: str = "repo") -> Path:
        root = tmp_path / name
        root.mkdir()
        subprocess.run([git, "init", "-b", "master"], cwd=root, check=True, capture_output=True)  # noqa: S603
        subprocess.run([git, "config", "user.name", "LAOS Test"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "config", "user.email", "laos-test.invalid"], cwd=root, check=True)  # noqa: S603
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / ".gitattributes").write_bytes(b".gitattributes text eol=lf\n*.py text eol=lf\n")
        (root / "src" / "app.py").write_bytes(b"VALUE = 1\n")
        (root / "tests" / "test_app.py").write_bytes(b"def test_value():\n    assert 1 == 1\n")
        subprocess.run([git, "add", "--all"], cwd=root, check=True)  # noqa: S603
        subprocess.run([git, "commit", "-m", "base"], cwd=root, check=True, capture_output=True)  # noqa: S603
        return root

    return create


@pytest.fixture
def now_values() -> dict[str, str]:
    return {
        "past": "2026-07-12T00:00:00Z",
        "now": "2026-07-13T00:00:00Z",
        "future": "2026-07-14T00:00:00Z",
        "far_future": "2099-01-01T00:00:00Z",
    }


@pytest.fixture
def digest() -> str:
    return "sha256:" + "0" * 64


@pytest.fixture
def actor_factory() -> Callable[..., Any]:
    from laos_v8.identity import AuthenticatedActor
    from laos_v8.models import Role

    def create(
        actor_id: str = "actor:builder",
        principal: str = "local:builder",
        roles: tuple[Role, ...] = (Role.BUILDER,),
        session: str = "session-builder",
        workspace: str = "workspace-builder",
        epoch: int = 0,
    ) -> AuthenticatedActor:
        return AuthenticatedActor(actor_id, principal, roles, session, workspace, epoch)

    return create
