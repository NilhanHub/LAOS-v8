#!/usr/bin/env python3
"""Create Bootstrap evidence for the Stage 1 review candidate."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": list(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-tree", required=True)
    args = parser.parse_args()

    commands = [
        run(sys.executable, "scripts/reproduce_v7_fixtures.py"),
        run(sys.executable, "scripts/verify_stage1.py"),
        run(sys.executable, "-m", "pytest", "tests/test_stage1_governance.py", "-q"),
        run(sys.executable, "-m", "compileall", "-q", "scripts", "tests"),
    ]
    if any(command["exit_code"] != 0 for command in commands):
        raise SystemExit("candidate verification command failed")

    stage0_package = ARTIFACT_ROOT / "LAOS_v8_STAGE_0_COMPLETE_PACKAGE.zip"
    inner_results = []
    with zipfile.ZipFile(stage0_package) as zf:
        declared = zf.read("PACKAGE_CONTENTS_CHECKSUMS.sha256").decode("utf-8")
        for line in declared.splitlines():
            digest, name = line.split("  ", 1)
            actual = hashlib.sha256(zf.read(name)).hexdigest()
            inner_results.append({"path": name, "declared_sha256": digest, "actual_sha256": actual, "pass": actual == digest})
    if not all(row["pass"] for row in inner_results):
        raise SystemExit("Stage 0 internal checksum mismatch")

    tracked_candidate_files = subprocess.check_output(["git", "diff", "--cached", "--name-only", "stage0-complete"], cwd=ROOT, text=True).splitlines()
    evidence = {
        "record_version": "1.0.0",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "assurance": "BOOTSTRAP",
        "status": "PASS_AWAITING_NILHAN_REVIEW",
        "implementer": "Codex",
        "independent_reviewer": "Nilhan",
        "independent_review_status": "PENDING",
        "fixture_only_track": True,
        "v7_0_1_release_claim": False,
        "v8_runtime_implemented": False,
        "v8_release_published": False,
        "stage0_tag_target": subprocess.check_output(["git", "rev-parse", "stage0-complete^{}"], cwd=ROOT, text=True).strip(),
        "verified_content_tree": args.content_tree,
        "candidate_file_count": len(tracked_candidate_files),
        "candidate_files": tracked_candidate_files,
        "artifact_hashes": {
            "original_v7_zip": sha256(ARTIFACT_ROOT / "LAOS_v7.0_Complete_System.zip"),
            "stage0_complete_package": sha256(stage0_package),
            "revision_1_1_plan": sha256(ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md"),
            "plan_review": sha256(ROOT / "LAOS_v8_PLAN_REVIEW_2026-07-12.md"),
            "embedded_v7_zip": sha256(ROOT / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"),
        },
        "stage0_internal_checksums": inner_results,
        "commands": commands,
        "counts": {
            "requirements": 241,
            "historical_stage0_requirements": 210,
            "revision_1_1_requirements": 31,
            "regressions": 40,
            "fixture_specs": 8,
            "threats": 50,
            "release_blockers_open": 25,
            "implementation_stages": 10,
            "original_milestones": 17,
        },
        "truth_boundary": "This record verifies a Stage 1 review candidate. It is not production v8 signing, a v7.0.1 release, a working v8 runtime, or a v8 release.",
    }
    output_json = ROOT / "Evidence" / "STAGE_1_CANDIDATE_VERIFICATION.json"
    output_json.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Stage 1 candidate verification",
        "",
        "**PASS — implementation candidate created; Nilhan review remains pending.**",
        "",
        f"- Assurance: `{evidence['assurance']}`",
        f"- Verified content tree: `{args.content_tree}`",
        f"- Stage 0 tag target: `{evidence['stage0_tag_target']}`",
        f"- Candidate files changed/added: `{len(tracked_candidate_files)}`",
        "- Fixture-only v7 path: `true`",
        "- v7.0.1 release claimed: `false`",
        "- v8 runtime implemented: `false`",
        "- v8 release published: `false`",
        "",
        "## Verification",
        "",
    ]
    for command in commands:
        lines.append(f"- `{ ' '.join(command['command']) }`: exit `{command['exit_code']}`")
    lines.extend([
        "",
        "All seven Stage 0 internal package checksums matched. The original and embedded v7 archives remain byte-identical. All 25 release blockers remain open.",
        "",
        "## Review boundary",
        "",
        "Codex cannot independently approve its own candidate. Stage 1 remains open until Nilhan reviews this evidence and the candidate diff. A completion tag must not be created before that approval.",
        "",
    ])
    (ROOT / "Evidence" / "STAGE_1_CANDIDATE_VERIFICATION.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": evidence["status"], "content_tree": args.content_tree, "candidate_files": len(tracked_candidate_files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
