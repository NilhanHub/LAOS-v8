#!/usr/bin/env python3
"""Reproduce fixture-only v7 source observations without executing v7 code."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"
EXPECTED = "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d"


def observe() -> dict[str, object]:
    actual = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if actual != EXPECTED:
        raise RuntimeError("sealed v7 archive digest mismatch")
    with zipfile.ZipFile(ARCHIVE) as zf:
        runtime = zf.read("LAOS_v7/laos_runtime.py").decode("utf-8")
        capture = zf.read("LAOS_v7/tools/capture_runtime.py").decode("utf-8")
        return_validator = zf.read("LAOS_v7/tools/validate_return_pack.py").decode("utf-8")

    observations = [
        ("FX-V7-001", 'f"{e[\'path\']}|{e.get(\'sha256\') or \'NOHASH\'}|{e[\'bytes\']}"' in capture and 'f"{path}|{meta.get(\'bytes\')}|{meta.get(\'sha256\')}"' in runtime, "capture and runtime serialize fingerprint fields in different orders"),
        ("FX-V7-002", "save_task_baseline(root, task_id)" in runtime and "current = project_fingerprint(root)" in runtime, "claim-time baseline logic is source-visible and requires v8 pre-authority sealing"),
        ("FX-V7-003", "jsonschema" not in capture and "jsonschema" not in return_validator, "capture validation does not invoke the shipped Draft 2020-12 schemas through jsonschema"),
        ("FX-V7-004", "baseline = save_task_baseline(root, task_id)" in runtime, "task baseline is captured during claim rather than bound to prior Architect authority"),
        ("FX-V7-005", "path.is_symlink()" in runtime and "continue" in runtime[runtime.index("def project_manifest"):runtime.index("def manifest_digest")], "project manifest explicitly skips symlink entries"),
        ("FX-V7-006", "compress_size" not in runtime[runtime.index("def safe_zip_entries"):runtime.index("def iter_source_files")], "archive inspection has no expansion-ratio or total-size quota"),
        ("FX-V7-007", "shell=True" in runtime[runtime.index("def run_check"):runtime.index("def record_evidence")], "contracted command execution uses shell=True"),
        ("FX-V7-008", "repository_content_fingerprint" in capture and "expected_repository_fingerprint" in runtime and 'f"{e[\'path\']}|{e.get(\'sha256\') or \'NOHASH\'}|{e[\'bytes\']}"' in capture, "capture and continuation/runtime identity use incompatible source-visible contracts"),
    ]
    rows = [{"fixture_id": fid, "observed": bool(passed), "observation": text} for fid, passed, text in observations]
    if not all(row["observed"] for row in rows):
        raise AssertionError("one or more v7 source observations no longer reproduce")
    return {
        "status": "PASS",
        "assurance": "BOOTSTRAP_STATIC_SOURCE_OBSERVATION",
        "archive_sha256": actual,
        "executed_v7_code": False,
        "fixture_count": len(rows),
        "observations": rows,
        "truth_boundary": "These observations bind fixture specifications to v7 source. They do not prove v8 repairs or close any regression.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = observe()
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
