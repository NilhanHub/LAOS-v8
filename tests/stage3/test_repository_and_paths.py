from __future__ import annotations

import stat
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from laos_v8.brokers import ActionClaimBroker
from laos_v8.errors import RepositoryDrift, ResourceLimitError, SecurityError, ValidationError
from laos_v8.repository_truth import build_manifest, require_unchanged
from laos_v8.safe_paths import ArchiveLimits, SafeRoot, safe_extract_zip, validate_relative_path
from laos_v8.state import CanonicalState


def test_one_byte_repository_drift_changes_seal(git_repo: Callable[[str], Path]) -> None:
    root = git_repo()
    before = build_manifest(root, seal_kind="base")
    (root / "src" / "app.py").write_bytes(b"VALUE = 2\n")
    after = build_manifest(root, seal_kind="base")
    assert before.seal != after.seal
    with pytest.raises(RepositoryDrift, match="differs"):
        require_unchanged(root, before.seal, seal_kind="base")


def test_action_claim_broker_rejects_preclaim_repository_drift(
    git_repo: Callable[[str], Path], tmp_path: Path, actor_factory: Callable[..., Any]
) -> None:
    root = git_repo()
    accepted = build_manifest(root, seal_kind="base")
    (root / "src" / "app.py").write_bytes(b"VALUE = 2\n")
    with CanonicalState(tmp_path / "state.sqlite3") as state:
        broker = ActionClaimBroker(state)
        with pytest.raises(RepositoryDrift):
            broker.claim(
                actor_factory(),
                action_id="action:drift",
                repository=root,
                expected_base_seal=accepted.seal,
                lease_expires_at="2099-01-01T00:00:00Z",
            )
        assert state.connection.execute("SELECT count(*) FROM action_claims").fetchone()[0] == 0
        current = build_manifest(root, seal_kind="base")
        assert (
            broker.claim(
                actor_factory(),
                action_id="action:current",
                repository=root,
                expected_base_seal=current.seal,
                lease_expires_at="2099-01-01T00:00:00Z",
            )
            == current.seal
        )


def test_manifest_records_final_symlink_without_following_it(git_repo: Callable[[str], Path], tmp_path: Path) -> None:
    root = git_repo()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    link = root / "outside-link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("filesystem does not permit symlink creation")
    manifest = build_manifest(root, seal_kind="base")
    entry = next(item for item in manifest.entries if item.path == "outside-link.txt")
    assert entry.kind == "symlink"
    assert entry.link_target is not None and entry.link_target.endswith(str(outside))


@pytest.mark.parametrize("value", ["../escape", "/absolute", "C:/device", "file:stream", "a\\b", "//server/x"])
def test_unsafe_paths_fail_closed(value: str) -> None:
    with pytest.raises(ValidationError) as captured:
        validate_relative_path(value)
    assert captured.value.code == "UNSAFE_PATH"


def test_safe_root_atomic_write_and_hardlink_denial(tmp_path: Path) -> None:
    root = tmp_path / "root"
    (root / "src").mkdir(parents=True)
    safe = SafeRoot(root)
    safe.write_bytes_atomic("src/file.txt", b"safe", max_bytes=8)
    assert safe.read_bytes("src/file.txt", max_bytes=8) == b"safe"
    linked = root / "src" / "linked.txt"
    try:
        linked.hardlink_to(root / "src" / "file.txt")
    except OSError:
        pytest.skip("filesystem does not support hardlink test")
    with pytest.raises(SecurityError) as captured:
        safe.read_bytes("src/file.txt", max_bytes=8)
    assert captured.value.code == "PATH_HARDLINK_DENIED"


def test_safe_zip_rejects_traversal_case_collision_links_and_bombs(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.txt", b"bad")
    with pytest.raises(ValidationError):
        safe_extract_zip(traversal, tmp_path / "traversal-out")

    collision = tmp_path / "collision.zip"
    with zipfile.ZipFile(collision, "w") as archive:
        archive.writestr("A.txt", b"a")
        archive.writestr("a.txt", b"b")
    with pytest.raises(SecurityError) as captured:
        safe_extract_zip(collision, tmp_path / "collision-out")
    assert captured.value.code == "ARCHIVE_NAME_COLLISION"

    link = tmp_path / "link.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(link, "w") as archive:
        archive.writestr(info, "outside")
    with pytest.raises(SecurityError) as captured:
        safe_extract_zip(link, tmp_path / "link-out")
    assert captured.value.code == "ARCHIVE_LINK_DENIED"

    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("large.txt", b"0" * 10_000)
    with pytest.raises(ResourceLimitError):
        safe_extract_zip(bomb, tmp_path / "bomb-out", ArchiveLimits(max_ratio=2))


def test_safe_zip_extracts_regular_files(tmp_path: Path) -> None:
    source = tmp_path / "safe.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("src/app.py", b"print('safe')\n")
    output = tmp_path / "out"
    assert safe_extract_zip(source, output) == ["src/app.py"]
    assert (output / "src" / "app.py").read_bytes() == b"print('safe')\n"
