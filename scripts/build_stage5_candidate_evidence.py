#!/usr/bin/env python3
"""Build a run-bound Stage 5 security-remediation review candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from laos_v8.evidence_receipts import (
    STAGE5_SCOPED_PATHS,
    STAGE5_SECURITY_TESTS,
    ArtifactReceipt,
    CommandReceipt,
    EvidenceRunReceipt,
    atomic_write_json,
    new_run_id,
    stage5_candidate_command_policy,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = (
    "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md",
    "STAGE_5_CORE_WORKFLOW_COVERAGE.json",
    "IMPLEMENTATION_STATUS.json",
    "Evidence/DOCKER_AUTOSTART_VERIFICATION.json",
    "schemas/golden/protected-envelope-v2.json",
    "uv.lock",
)
ASSURANCE = "BOOTSTRAP_BUILDER_ASSERTED_NOT_AUTHENTICATED_NOT_PRODUCTION_SIGNING"
GENERATOR_VERSION = "laos-stage5-candidate/1.1.0"
EXPECTED_REPOSITORY_OUTPUT = "Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json"

# Keep the public imports available to focused policy tests without duplicating command policy.
SCOPED_PATHS = STAGE5_SCOPED_PATHS
SECURITY_TESTS = STAGE5_SECURITY_TESTS


def executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise RuntimeError(f"required-executable-unavailable:{name}")
    return resolved


def git(*args: str) -> str:
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed evidence arguments
        [executable("git"), "-C", str(ROOT), *args], text=True
    ).strip()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(label: str, recorded_argv: tuple[str, ...], *, uv: str) -> CommandReceipt:
    actual_argv = [uv if index == 0 and value == "uv" else value for index, value in enumerate(recorded_argv)]
    completed = subprocess.run(  # noqa: S603 - resolved executable and fixed command arrays
        actual_argv,
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    skipped = label == "docker_integration" and b"skipped" in completed.stdout.lower()
    passed = completed.returncode == 0 and not skipped
    return CommandReceipt(
        label=label,
        argv=recorded_argv,
        exit_code=completed.returncode if not skipped else 125,
        status="PASS" if passed else "FAIL",
        stdout_sha256=digest(completed.stdout),
        stderr_sha256=digest(completed.stderr),
        stdout_bytes=len(completed.stdout),
        stderr_bytes=len(completed.stderr),
    )


def artifact_receipts() -> tuple[ArtifactReceipt, ...]:
    receipts: list[ArtifactReceipt] = []
    for relative in ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"candidate-artifact-missing:{relative}")
        payload = path.read_bytes()
        receipts.append(ArtifactReceipt(path=relative, bytes=len(payload), sha256=digest(payload)))
    return tuple(receipts)


def git_status_paths() -> set[str]:
    completed = subprocess.run(  # noqa: S603 - resolved Git and fixed status arguments
        [
            executable("git"),
            "-C",
            str(ROOT),
            "-c",
            "core.quotepath=false",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        capture_output=True,
        check=True,
    )
    fields = completed.stdout.decode("utf-8", errors="strict").split("\0")
    paths: set[str] = set()
    index = 0
    while index < len(fields) and fields[index]:
        entry = fields[index]
        if len(entry) < 4 or entry[2] != " ":
            raise RuntimeError("git-status-record-invalid")
        status = entry[:2]
        paths.add(entry[3:].replace("\\", "/"))
        index += 1
        if "R" in status or "C" in status:
            if index >= len(fields) or not fields[index]:
                raise RuntimeError("git-status-rename-record-invalid")
            paths.add(fields[index].replace("\\", "/"))
            index += 1
    return paths


def validate_output_path(output: Path) -> str | None:
    if output.exists() and output.is_symlink():
        raise RuntimeError("candidate-output-symlink-denied")
    if not output.is_relative_to(ROOT):
        return None
    relative = output.relative_to(ROOT).as_posix()
    if relative != EXPECTED_REPOSITORY_OUTPUT:
        raise RuntimeError("candidate-repository-output-path-denied")
    tracked = subprocess.run(  # noqa: S603 - resolved Git and exact repository-relative path
        [executable("git"), "-C", str(ROOT), "ls-files", "--error-unmatch", "--", relative],
        capture_output=True,
        check=False,
    )
    if tracked.returncode == 0:
        raise RuntimeError("candidate-output-must-be-untracked")
    return relative


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    allowed_output = validate_output_path(output)
    run_id = new_run_id()
    started = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    initial_status = git_status_paths()
    if source_commit != args.expected_commit or initial_status:
        raise SystemExit("candidate builder requires the expected clean source commit")
    in_progress = EvidenceRunReceipt(
        run_id=run_id,
        stage=5,
        status="IN_PROGRESS",
        assurance=ASSURANCE,
        producer_authentication="NONE_STAGE6_OPEN",
        generator_version=GENERATOR_VERSION,
        source_commit=source_commit,
        source_tree=source_tree,
        started_at_utc=started,
    )
    atomic_write_json(output, in_progress)
    uv = executable("uv")
    commands: list[CommandReceipt] = []
    command_policy = stage5_candidate_command_policy(run_id, source_commit)
    stage3_root = Path(command_policy["verify_stage3"][6]).parent

    try:
        for label, argv in command_policy.items():
            if label == "verify_stage3":
                if stage3_root.exists():
                    raise RuntimeError("stage3-run-directory-already-exists")
                stage3_root.mkdir(parents=True)
            commands.append(run(label, argv, uv=uv))
        failure = next((command.label for command in commands if command.status != "PASS"), None)
        final_status = git_status_paths()
        unexpected = final_status if allowed_output is None else final_status - {allowed_output}
        if failure is not None:
            raise RuntimeError(f"candidate-command-failed:{failure}")
        if unexpected:
            raise RuntimeError("worktree-dirty-after-candidate-gates")
        receipt = EvidenceRunReceipt(
            run_id=run_id,
            stage=5,
            status="PASS_AWAITING_NILHAN_REVIEW",
            assurance=ASSURANCE,
            producer_authentication="NONE_STAGE6_OPEN",
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            source_tree=source_tree,
            started_at_utc=started,
            completed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            commands=tuple(commands),
            artifacts=artifact_receipts(),
        )
    except Exception as exc:
        receipt = EvidenceRunReceipt(
            run_id=run_id,
            stage=5,
            status="FAIL",
            assurance=ASSURANCE,
            producer_authentication="NONE_STAGE6_OPEN",
            generator_version=GENERATOR_VERSION,
            source_commit=source_commit,
            source_tree=source_tree,
            started_at_utc=started,
            completed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            commands=tuple(commands),
            failure_code=str(exc),
        )
    finally:
        if stage3_root.resolve().parent == Path(tempfile.gettempdir()).resolve():
            shutil.rmtree(stage3_root, ignore_errors=True)
    atomic_write_json(output, receipt)
    print(json.dumps({"status": receipt.status, "run_id": receipt.run_id, "output": str(output)}, indent=2))
    return 0 if receipt.status == "PASS_AWAITING_NILHAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
