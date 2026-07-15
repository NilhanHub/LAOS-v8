from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from laos_v8.canonical import canonical_json
from laos_v8.errors import SecurityError
from laos_v8.ollama_adapter import StructuredOutputProvider
from laos_v8.prompting import ExecutorProfile
from laos_v8.stage5_calibration import (
    CALIBRATION_OUTPUT_SCHEMA,
    CALIBRATION_REQUEST_POLICY,
    CALIBRATION_VALIDATOR_SCHEMA,
    PINNED_SETTINGS,
    CalibrationPlan,
    CalibrationProposal,
    CalibrationScenario,
    Stage5CalibrationReceipt,
    run_calibration,
)

DIGEST = "sha256:" + "a" * 64


def plan_and_profile() -> tuple[CalibrationPlan, ExecutorProfile]:
    root = Path(__file__).resolve().parents[2]
    plan = CalibrationPlan.model_validate_json(
        (root / "profiles/STAGE_5_CALIBRATION_PLAN.json").read_text(encoding="utf-8"), strict=True
    )
    fixture = json.loads((root / "profiles/OFFLINE_EXECUTOR_PROFILES.json").read_text(encoding="utf-8"))
    selected = next(item for item in fixture["profiles"] if item["profile_id"] == "profile:investigation-specialist")
    profile = ExecutorProfile.model_validate_json(canonical_json(selected), strict=True).model_copy(
        update={
            "version": "1.0.4",
            "max_files_per_action": 8,
            "max_criteria_per_action": 1,
            "released": True,
        }
    )
    return plan, profile


def exact_value(scenario: CalibrationScenario) -> dict[str, object]:
    return {
        "status": scenario.expected_status,
        "statement": scenario.expected_statement,
        "evidence_refs": list(scenario.expected_evidence_refs),
        "contradictions": ["broker evidence conflicts"] if scenario.expected_status == "conflicted" else [],
        "unknowns": ["broker supplied no evidence"] if scenario.expected_status == "unknown" else [],
        "denied_requests": ["deployment is prohibited"] if scenario.expected_status == "rejected" else [],
        "prohibited_actions": [],
    }


def provider_for(
    scenarios: tuple[CalibrationScenario, ...],
    transform: Callable[[int, dict[str, object]], dict[str, object]] | None = None,
) -> StructuredOutputProvider:
    index = 0

    def provider(prompt: str, *, output_schema: dict[str, object]) -> str:
        nonlocal index
        assert "BROKER-VERIFIED READ-ONLY TASK" in prompt
        assert output_schema == CALIBRATION_OUTPUT_SCHEMA
        assert CALIBRATION_VALIDATOR_SCHEMA == CalibrationProposal.model_json_schema()
        assert "maxItems" not in json.dumps(output_schema)
        assert "maxItems" in json.dumps(CALIBRATION_VALIDATOR_SCHEMA)
        value = exact_value(scenarios[index])
        if transform is not None:
            value = transform(index, value)
        index += 1
        return json.dumps(value)

    return provider


def execute(
    plan: CalibrationPlan,
    profile: ExecutorProfile,
    provider: StructuredOutputProvider,
) -> Stage5CalibrationReceipt:
    return run_calibration(
        plan,
        profile,
        provider,
        observed_at="2026-07-15T00:00:00Z",
        environment_digest=DIGEST,
        tool_versions=("ollama:test",),
    )


def test_fresh_calibration_passes_all_five_safety_and_evidence_scenarios() -> None:
    plan, profile = plan_and_profile()
    receipt = execute(plan, profile, provider_for(plan.scenarios))
    assert receipt.status == "PASS"
    assert receipt.passed_scenarios == 5
    assert receipt.calibration.skip_rate == 0.2
    assert receipt.valid_evidence_rate == 1.0
    assert receipt.settings == CALIBRATION_REQUEST_POLICY
    assert receipt.settings != PINNED_SETTINGS.as_dict()
    assert receipt.release_binding(released_at=receipt.calibration.observed_at).profile_digest == profile.digest


def test_four_of_five_can_pass_without_weakening_evidence_or_scope_thresholds() -> None:
    plan, profile = plan_and_profile()

    def one_nonsecurity_miss(index: int, value: dict[str, object]) -> dict[str, object]:
        if index == 4:
            value["status"] = "conflicted"
            value["contradictions"] = ["operator request conflicts with policy"]
            value["denied_requests"] = []
        return value

    receipt = execute(plan, profile, provider_for(plan.scenarios, one_nonsecurity_miss))
    assert receipt.status == "PASS"
    assert receipt.passed_scenarios == 4
    assert receipt.unsupported_accepted_claims == 0


def test_fabricated_accepted_claim_and_citation_fail_release() -> None:
    plan, profile = plan_and_profile()

    def fabricate(index: int, value: dict[str, object]) -> dict[str, object]:
        if index == 1:
            value.update(
                {
                    "status": "accepted",
                    "statement": "Deployment mode is development.",
                    "evidence_refs": ["cal-evidence:not-present"],
                    "contradictions": [],
                }
            )
        return value

    receipt = execute(plan, profile, provider_for(plan.scenarios, fabricate))
    assert receipt.status == "FAIL"
    assert receipt.unsupported_accepted_claims == 1
    assert receipt.valid_evidence_rate < 1.0


def test_calibration_security_violation_stops_without_retry() -> None:
    plan, profile = plan_and_profile()

    def prohibited(index: int, value: dict[str, object]) -> dict[str, object]:
        if index == 0:
            value["prohibited_actions"] = ["NETWORK"]
        return value

    with pytest.raises(SecurityError) as denied:
        execute(plan, profile, provider_for(plan.scenarios, prohibited))
    assert denied.value.code == "CALIBRATION_SECURITY_VIOLATION"
