#!/usr/bin/env python3
"""Generate local, reproducible Stage 2 evidence without claiming privileged runtime support."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError as PydanticValidationError

from laos_v8.canonical import canonical_json
from laos_v8.migration_discovery import discover_v7
from laos_v8.models import ProductObjective
from laos_v8.parser import strict_loads
from laos_v8.platform_profile import doctor

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "Evidence"
V7 = ROOT / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_poc() -> dict[str, object]:
    checks: dict[str, bool] = {}
    try:
        ProductObjective.model_validate(
            {
                "record_type": "product_objective",
                "record_id": "rec-objective-001",
                "project_id": "project-stage2",
                "created_at": "2026-07-13T00:00:00Z",
                "title": "Stage 2",
                "summary": "Strict model proof",
                "success_criteria": (),
                "unexpected": True,
            },
            strict=True,
        )
    except PydanticValidationError:
        checks["pydantic_strict_extra_rejected"] = True
    else:
        checks["pydantic_strict_extra_rejected"] = False

    checks["jsonschema_draft_2020_12_available"] = Draft202012Validator.META_SCHEMA["$id"].endswith(
        "draft/2020-12/schema"
    )
    try:
        strict_loads(b'{"a":1,"a":2}')
    except Exception as exc:
        checks["duplicate_key_rejected"] = getattr(exc, "code", "") == "JSON_DUPLICATE_KEY"
    else:
        checks["duplicate_key_rejected"] = False
    checks["rfc8785_canonical_vector"] = canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'

    packages = {
        name: importlib.metadata.version(name)
        for name in ("pydantic", "jsonschema", "rfc8785", "hypothesis", "pytest", "mypy", "ruff")
    }
    checks["all_checks_pass"] = all(checks.values())
    return {
        "report_version": "1.0.0",
        "status": "PASS" if checks["all_checks_pass"] else "FAIL",
        "checks": checks,
        "resolved_packages": packages,
        "uv_lock_sha256": sha256(ROOT / "uv.lock"),
        "scope": "LOCAL_TYPED_KERNEL_DEPENDENCY_POC",
        "privileged_runtime_support_claimed": False,
    }


def main() -> None:
    write_json(EVIDENCE / "STAGE_2_LOCAL_PLATFORM.json", doctor(ROOT).as_dict())
    write_json(EVIDENCE / "STAGE_2_MIGRATION_DISCOVERY.json", discover_v7(V7))
    write_json(EVIDENCE / "STAGE_2_DEPENDENCY_POC.json", dependency_poc())


if __name__ == "__main__":
    main()
