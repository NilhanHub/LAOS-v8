from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from laos_v8.errors import RepositoryDrift
from laos_v8.repository_truth import build_manifest
from laos_v8.safe_paths import SafeRoot
from laos_v8.workspace import CandidateWorkspace, promote_compare_and_swap


def test_isolated_candidate_clean_reconstruction_and_cas_promotion(
    git_repo: Callable[[str], Path], tmp_path: Path
) -> None:
    source = git_repo()
    candidate = CandidateWorkspace.create(source, tmp_path / "candidate")
    assert (candidate.root / ".git").is_dir()
    SafeRoot(candidate.root).write_bytes_atomic("src/app.py", b"VALUE = 2\n", max_bytes=1024)
    result_commit, result = candidate.commit()
    reconstructed = candidate.reconstruct(tmp_path / "verifier")
    assert reconstructed.seal == result.seal

    git = shutil.which("git")
    assert git is not None
    target_ref = "refs/heads/master"
    receipt = promote_compare_and_swap(
        source,
        candidate.root,
        target_ref=target_ref,
        expected_base=candidate.base_commit,
        result_commit=result_commit,
    )
    assert receipt.status == "PROMOTED"
    promoted = subprocess.check_output([git, "-C", str(source), "rev-parse", target_ref], text=True).strip()  # noqa: S603
    assert promoted == result_commit
    assert (
        promote_compare_and_swap(
            source,
            candidate.root,
            target_ref=target_ref,
            expected_base=candidate.base_commit,
            result_commit=result_commit,
        ).status
        == "ALREADY_PROMOTED"
    )


def test_stale_base_promotion_is_denied(git_repo: Callable[[str], Path], tmp_path: Path) -> None:
    source = git_repo()
    candidate = CandidateWorkspace.create(source, tmp_path / "candidate")
    SafeRoot(candidate.root).write_bytes_atomic("src/app.py", b"VALUE = 2\n", max_bytes=1024)
    result_commit, _ = candidate.commit()
    git = shutil.which("git")
    assert git is not None
    (source / "src" / "other.py").write_bytes(b"OTHER = True\n")
    subprocess.run([git, "-C", str(source), "add", "--all"], check=True)  # noqa: S603
    subprocess.run([git, "-C", str(source), "commit", "-m", "concurrent"], check=True, capture_output=True)  # noqa: S603
    with pytest.raises(RepositoryDrift) as captured:
        promote_compare_and_swap(
            source,
            candidate.root,
            target_ref="refs/heads/master",
            expected_base=candidate.base_commit,
            result_commit=result_commit,
        )
    assert captured.value.code == "PROMOTION_CAS_CONFLICT"


def test_candidate_base_is_exact(git_repo: Callable[[str], Path], tmp_path: Path) -> None:
    source = git_repo()
    base = build_manifest(source, seal_kind="base")
    candidate = CandidateWorkspace.create(source, tmp_path / "candidate")
    assert candidate.base_seal == base.seal
