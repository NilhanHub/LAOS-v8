from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from laos_v8.canonical import canonical_json
from laos_v8.evidence_receipts import atomic_write_json
from laos_v8.ollama_adapter import PinnedOllamaAdapter
from laos_v8.platform_profile import doctor
from laos_v8.prompting import ExecutorProfile
from laos_v8.stage5_calibration import PINNED_MODEL, PINNED_SETTINGS, load_calibration_plan, run_calibration


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_profile(root: Path) -> ExecutorProfile:
    payload = json.loads((root / "profiles" / "OFFLINE_EXECUTOR_PROFILES.json").read_text(encoding="utf-8"))
    selected = next(item for item in payload["profiles"] if item["profile_id"] == "profile:investigation-specialist")
    return ExecutorProfile.model_validate_json(canonical_json(selected), strict=True).model_copy(
        update={
            "version": "1.0.4",
            "max_files_per_action": 8,
            "max_criteria_per_action": 1,
            "released": True,
        }
    )


def ollama_version() -> str:
    executable = shutil.which("ollama")
    if not executable:
        return "ollama:unavailable"
    completed = subprocess.run(  # noqa: S603 - resolved executable and fixed argv
        [executable, "--version"], text=True, capture_output=True, check=False, timeout=15
    )
    value = completed.stdout.strip() if completed.returncode == 0 else "unavailable"
    return f"ollama:{value}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the preregistered Stage 5 Qwen calibration")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binding-output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    plan = load_calibration_plan(root / "profiles" / "STAGE_5_CALIBRATION_PLAN.json")
    profile = load_profile(root)
    environment = doctor(root).as_dict()
    environment_digest = f"sha256:{hashlib.sha256(canonical_json(environment)).hexdigest()}"
    provider = PinnedOllamaAdapter(PINNED_MODEL, settings=PINNED_SETTINGS)
    provider.verify_pin()
    observed_at = utc_now()
    receipt = run_calibration(
        plan,
        profile,
        provider,
        observed_at=observed_at,
        environment_digest=environment_digest,
        tool_versions=(
            ollama_version(),
            f"python:{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ),
    )
    atomic_write_json(args.output, receipt)
    if receipt.status == "FAIL":
        first_path = args.output.with_name(f"{args.output.stem}.v1-2-attempt-1{args.output.suffix}")
        atomic_write_json(first_path, receipt)
        reduced = profile.model_copy(
            update={
                "version": "1.0.5",
                "max_files_per_action": 4,
                "max_criteria_per_action": 1,
            }
        )
        receipt = run_calibration(
            plan,
            reduced,
            provider,
            observed_at=utc_now(),
            environment_digest=environment_digest,
            tool_versions=(
                ollama_version(),
                f"python:{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            ),
            attempt=2,
        )
        atomic_write_json(args.output, receipt)
    if receipt.status != "PASS":
        return 1
    if args.binding_output:
        atomic_write_json(args.binding_output, receipt.release_binding(released_at=receipt.calibration.observed_at))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
