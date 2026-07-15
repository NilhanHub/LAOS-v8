#!/usr/bin/env python3
"""Exercise schema enforcement only on permanently retired Stage 5 scenarios."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from laos_v8.canonical import canonical_json
from laos_v8.ollama_adapter import PinnedOllamaAdapter
from laos_v8.stage5_calibration import (
    CALIBRATION_OUTPUT_SCHEMA,
    PINNED_MODEL,
    PINNED_SETTINGS,
    CalibrationProposal,
    CalibrationScenario,
    calibration_prompt,
)

ROOT = Path(__file__).resolve().parents[1]
RETIRED_PLAN = ROOT / "profiles/STAGE_5_CALIBRATION_PLAN_V1_1_RETIRED.json"
EXPECTED_RETIRED_SHA256 = "ef82b4039285590297cb368bcafb9e6688eba79a7a15680d0b5a6db353ed0300"


def main() -> int:
    payload = RETIRED_PLAN.read_bytes()
    if hashlib.sha256(payload).hexdigest() != EXPECTED_RETIRED_SHA256:
        raise SystemExit("retired calibration plan digest differs")
    decoded = json.loads(payload)
    if decoded.get("record_version") != "1.1.0":
        raise SystemExit("diagnostic input is not the retired v1.1 plan")
    scenarios = tuple(
        CalibrationScenario.model_validate_json(canonical_json(item), strict=True) for item in decoded["scenarios"]
    )
    provider = PinnedOllamaAdapter(PINNED_MODEL, settings=PINNED_SETTINGS)
    provider.verify_pin()
    output_hashes: list[str] = []
    for scenario in scenarios:
        raw = provider(calibration_prompt(scenario), output_schema=CALIBRATION_OUTPUT_SCHEMA)
        output_hashes.append(hashlib.sha256(raw.encode("utf-8")).hexdigest())
        proposal = CalibrationProposal.model_validate_json(raw, strict=True)
        exact = (
            proposal.status == scenario.expected_status
            and proposal.statement == scenario.expected_statement
            and proposal.evidence_refs == scenario.expected_evidence_refs
            and not proposal.prohibited_actions
        )
        if not exact:
            raise SystemExit(f"retired scenario semantic mismatch: {scenario.scenario_id}")
    print(
        json.dumps(
            {
                "status": "PASS_DIAGNOSTIC_ONLY_NONQUALIFYING",
                "retired_plan_sha256": EXPECTED_RETIRED_SHA256,
                "scenario_count": len(scenarios),
                "output_set_sha256": hashlib.sha256(json.dumps(output_hashes).encode("utf-8")).hexdigest(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
