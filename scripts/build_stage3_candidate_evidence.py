#!/usr/bin/env python3
"""Run Stage 3 gates and write review-candidate evidence from a clean reconstruction."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise RuntimeError(f"required executable is unavailable: {name}")
    return value


def run(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(  # noqa: S603 - executable and argument lists are fixed below
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "argv": argv[1:],
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def git(*args: str) -> str:
    return subprocess.check_output(  # noqa: S603 - resolved executable and fixed evidence arguments
        [executable("git"), "-C", str(ROOT), *args], text=True
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()

    uv = executable("uv")
    scoped_scripts = [
        "scripts/generate_stage3_evidence.py",
        "scripts/reconcile_stage3_records.py",
        "scripts/verify_stage2.py",
        "scripts/verify_stage3.py",
        "scripts/build_stage3_candidate_evidence.py",
    ]
    commands = [
        [uv, "sync", "--frozen"],
        [uv, "run", "--frozen", "ruff", "check", "src", "tests/stage2", "tests/stage3", *scoped_scripts],
        [uv, "run", "--frozen", "mypy"],
        [uv, "run", "--frozen", "pytest", "-q"],
        [uv, "run", "--frozen", "python", "scripts/generate_stage3_evidence.py"],
        [uv, "run", "--frozen", "python", "scripts/verify_stage1.py"],
        [uv, "run", "--frozen", "python", "scripts/verify_stage2.py"],
        [uv, "run", "--frozen", "python", "scripts/verify_stage3.py"],
        [uv, "build"],
    ]
    results = [run(command) for command in commands]
    commit = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    status = git("status", "--short")
    pass_all = all(result["exit_code"] == 0 for result in results)
    pass_all = pass_all and commit == args.expected_commit and not status

    artifact_names = (
        "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md",
        "uv.lock",
        "docs/STAGE_3_ENFORCEMENT_CONTRACT.md",
        "docs/STAGE_3_OPERATOR_PATHS.md",
        "SANDBOX_PROFILE.json",
        "PERMISSION_ENFORCEMENT_MATRIX.json",
        "STAGE_3_THREAT_COVERAGE.json",
        "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json",
        "Evidence/STAGE_3_VERIFICATION.json",
        "baseline/source/LAOS_v7.0_Complete_System(1).zip",
        "dist/laos_v8-8.0.0a3.tar.gz",
        "dist/laos_v8-8.0.0a3-py3-none-any.whl",
    )
    artifacts = []
    for relative in artifact_names:
        path = ROOT / relative
        artifacts.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})

    report = {
        "record_version": "1.0.0",
        "created_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "status": "PASS_AWAITING_NILHAN_REVIEW" if pass_all else "FAIL",
        "assurance": "BOOTSTRAP_NOT_PRODUCTION_SIGNING",
        "stage": 3,
        "stage_name": "Mandatory Security Spine",
        "clean_reconstruction": True,
        "reconstructed_commit": commit,
        "expected_commit": args.expected_commit,
        "reconstructed_tree": tree,
        "reconstruction_worktree_clean_after_gates": not status,
        "commands": results,
        "artifacts": artifacts,
        "release_blockers_closed": [],
        "release_blocker_count_open": 25,
        "independent_reviewer": "Nilhan",
        "security_spine_local_test_profile_implemented": True,
        "real_weaker_agent_executed": False,
        "full_v8_runtime_implemented": False,
        "production_signing_implemented": False,
        "v8_release_published": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "STAGE_3_CANDIDATE_EVIDENCE.json"
    json_path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))

    lines = [
        "# LAOS v8 Stage 3 review-candidate evidence",
        "",
        f"Status: **{report['status']}**",
        "",
        f"- Reconstructed commit: `{commit}`",
        f"- Reconstructed tree: `{tree}`",
        f"- Clean after gates: `{not status}`",
        "- Assurance: `BOOTSTRAP_NOT_PRODUCTION_SIGNING`",
        "- Independent reviewer: Nilhan",
        "- The local Security Spine test profile is implemented.",
        "- All 25 release blockers remain open.",
        "- No real weaker agent, complete v8 runtime, production signing, or v8 release is claimed.",
        "",
        "## Gate results",
        "",
    ]
    lines.extend(
        f"- `{' '.join(result['argv'])}`: **{result['status']}** (exit {result['exit_code']})" for result in results
    )
    lines.extend(["", "## Hashed artifacts", ""])
    lines.extend(f"- `{item['path']}`: `{item['sha256']}`" for item in artifacts)
    (args.output_dir / "STAGE_3_CANDIDATE_EVIDENCE.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print(json.dumps({"status": report["status"], "output": str(json_path)}, indent=2))
    return 0 if pass_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
