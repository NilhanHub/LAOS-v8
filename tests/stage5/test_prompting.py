from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from laos_v8.canonical import canonical_json
from laos_v8.errors import AuthorizationDenied, ValidationError
from laos_v8.prompting import (
    CalibrationRecord,
    ContextItem,
    ContextManifest,
    ExecutorProfile,
    HandoffState,
    ProfilePolicy,
    PromptCompiler,
    PromptSpec,
    UncertaintyItem,
)

DIGEST = "sha256:" + "a" * 64


def profile(**updates: object) -> ExecutorProfile:
    base: dict[str, object] = {
        "profile_id": "profile:weak-desktop",
        "version": "1.0.0",
        "executor_class": "weak_general_desktop",
        "max_files_per_action": 2,
        "max_criteria_per_action": 2,
        "max_prompt_bytes": 8192,
        "max_instructions": 64,
        "repetition": 1,
        "max_examples": 1,
        "allowed_tools": ("read_file", "run_tests"),
        "retry_budget": 2,
        "require_fresh_session": True,
        "network_policy": "deny",
        "review_depth": "criterion",
        "safety_ceiling": "medium",
        "released": False,
    }
    base.update(updates)
    return ExecutorProfile.model_validate(base, strict=True)


def policy(**updates: object) -> ProfilePolicy:
    base: dict[str, object] = {
        "max_files_per_action": 3,
        "max_criteria_per_action": 3,
        "max_prompt_bytes": 16384,
        "max_retry_budget": 3,
        "allowed_tools": ("read_file", "run_tests", "search"),
        "allow_network_broker": False,
        "maximum_safety_ceiling": "medium",
    }
    base.update(updates)
    return ProfilePolicy.model_validate(base, strict=True)


def context(content: str = "The source seal is abc.") -> ContextManifest:
    return ContextManifest(
        action_id="action:one",
        role="executor",
        items=(
            ContextItem(
                context_id="context:truth",
                classification="trusted_project_truth",
                source_digest=DIGEST,
                content=content,
            ),
        ),
    )


def spec(**updates: object) -> PromptSpec:
    base: dict[str, object] = {
        "action_id": "action:one",
        "role": "Implement only the current bounded action.",
        "repository": "repo:stage5 at the supplied source seal",
        "goal": "Implement the current criterion without widening scope.",
        "finish_line": ("criterion:a passes", "criterion:b passes"),
        "allowed_scope": ("src/one.py", "tests/test_one.py"),
        "forbidden_scope": ("secrets/private.txt",),
        "checks": ("run focused tests",),
        "evidence": ("return test transcript digest",),
        "stop_conditions": ("stop on repository drift",),
        "unavailable_tools": "Stop and report the unavailable tool.",
        "final_response_format": "Return status, checks, and evidence digests.",
        "requested_tools": ("read_file", "run_tests"),
        "requested_permissions": ("WORKSPACE_READ", "MEDIATED_WRITE"),
        "examples": (),
    }
    base.update(updates)
    return PromptSpec.model_validate(base, strict=True)


def calibration(profile_digest: str) -> CalibrationRecord:
    return CalibrationRecord(
        calibration_id="calibration:one",
        profile_digest=profile_digest,
        provider="provider:test",
        model_snapshot="model-2026-07-13-snapshot-17",
        tool_versions=("read_file@1",),
        settings_digest=DIGEST,
        prompt_digest=DIGEST,
        observed_at="2026-07-13T00:00:00Z",
        environment_digest=DIGEST,
        partition="calibration",
        compliance_rate=1.0,
        skip_rate=0.0,
        scope_adherence_rate=1.0,
        evidence_quality_rate=1.0,
        broker_evidence_digest=DIGEST,
        qualifying_security_spine=True,
    )


def test_prompt_compiles_deterministically_with_current_action_first() -> None:
    compiler = PromptCompiler(policy())
    first = compiler.compile(spec(), context(), profile())
    second = compiler.compile(spec(), context(), profile())
    assert first == second
    assert first.text.startswith("## CURRENT ACTION\naction:one\n\n## STOP CONDITIONS")
    assert first.prompt_digest.startswith("sha256:")
    assert first.profile_digest == profile().digest


@pytest.mark.parametrize(
    ("profile_updates", "policy_updates"),
    (
        ({"max_files_per_action": 4}, {}),
        ({"max_criteria_per_action": 4}, {}),
        ({"max_prompt_bytes": 20000}, {}),
        ({"retry_budget": 4}, {}),
        ({"allowed_tools": ("shell",)}, {}),
        ({"network_policy": "broker_only"}, {}),
        ({"safety_ceiling": "high"}, {}),
    ),
)
def test_profile_cannot_silently_exceed_policy(
    profile_updates: dict[str, object],
    policy_updates: dict[str, object],
) -> None:
    with pytest.raises(AuthorizationDenied) as denied:
        PromptCompiler(policy(**policy_updates)).validate_profile(profile(**profile_updates))
    assert denied.value.code == "PROFILE_AUTHORITY_EXCEEDED"


def test_oversized_work_is_automatically_decomposed() -> None:
    chunks = PromptCompiler(policy()).decompose(
        files=("src/a.py", "src/b.py", "src/c.py", "src/d.py", "src/e.py"),
        criteria=("a", "b", "c", "d", "e"),
        profile=profile(),
    )
    assert len(chunks) == 3
    assert all(len(chunk["files"]) <= 2 and len(chunk["criteria"]) <= 2 for chunk in chunks)
    assert tuple(item for chunk in chunks for item in chunk["files"]) == (
        "src/a.py",
        "src/b.py",
        "src/c.py",
        "src/d.py",
        "src/e.py",
    )


@pytest.mark.parametrize(
    ("changed_spec", "changed_context", "code"),
    (
        ({"goal": "TODO decide"}, None, "PROMPT_PLACEHOLDER"),
        (
            {"allowed_scope": ("src/one.py",), "forbidden_scope": ("src/one.py",)},
            None,
            "PROMPT_STRUCTURAL_CONTRADICTION",
        ),
        ({"requested_tools": ("shell",)}, None, "PROMPT_TOOL_DENIED"),
        ({"requested_permissions": ("RAW_SECRETS",)}, None, "PROMPT_PERMISSION_DENIED"),
        ({}, "ARCHITECT_ONLY future action", "PROMPT_PRIVATE_LEAK"),
    ),
)
def test_prompt_linter_fails_closed(
    changed_spec: dict[str, object],
    changed_context: str | None,
    code: str,
) -> None:
    with pytest.raises((ValidationError, AuthorizationDenied)) as denied:
        PromptCompiler(policy()).compile(spec(**changed_spec), context(changed_context or "trusted truth"), profile())
    assert denied.value.code == code


def test_prompt_size_and_action_binding_are_enforced() -> None:
    small = profile(max_prompt_bytes=512)
    with pytest.raises(ValidationError) as size:
        PromptCompiler(policy()).compile(spec(goal="x" * 1000), context(), small)
    assert size.value.code == "PROMPT_SIZE_EXCEEDED"
    wrong_context = context().model_copy(update={"action_id": "action:other"})
    with pytest.raises(ValidationError) as binding:
        PromptCompiler(policy()).compile(spec(), wrong_context, profile())
    assert binding.value.code == "PROMPT_CONTEXT_BINDING_MISMATCH"


def test_released_profile_requires_pinned_calibration_evidence() -> None:
    released = profile(released=True)
    compiler = PromptCompiler(policy())
    with pytest.raises(ValidationError) as missing:
        compiler.require_release_calibration(released, ())
    assert missing.value.code == "PROFILE_CALIBRATION_REQUIRED"
    compiler.require_release_calibration(released, (calibration(released.digest),))
    with pytest.raises(PydanticValidationError):
        CalibrationRecord(**{**calibration(released.digest).model_dump(), "model_snapshot": "latest"})
    with pytest.raises(PydanticValidationError):
        CalibrationRecord(**{**calibration(released.digest).model_dump(), "qualifying_security_spine": False})


def test_context_is_typed_and_handoff_compaction_preserves_risk_state() -> None:
    unresolved = UncertaintyItem(uncertainty_id="uncertainty:one", statement="Provider behavior is unknown")
    handoff = HandoffState(
        action_id="action:one",
        decisions=("deny network",),
        blockers=("missing provider snapshot",),
        conflicts=("two source digests disagree",),
        uncertainties=(unresolved,),
        next_legal_action="obtain a pinned provider snapshot",
        exploration_notes=("discard this stale path",),
    )
    compact = handoff.compact()
    assert compact.exploration_notes == ()
    assert compact.blockers == handoff.blockers
    assert compact.conflicts == handoff.conflicts
    assert compact.uncertainties == handoff.uncertainties
    with pytest.raises(PydanticValidationError):
        UncertaintyItem(uncertainty_id="uncertainty:bad", statement="claimed resolved", status="resolved")


def test_all_seven_offline_profile_classes_are_strict_and_unreleased() -> None:
    root = Path(__file__).resolve().parents[2]
    payload = json.loads((root / "profiles/OFFLINE_EXECUTOR_PROFILES.json").read_text(encoding="utf-8"))
    profiles = tuple(
        ExecutorProfile.model_validate_json(canonical_json(item), strict=True) for item in payload["profiles"]
    )
    assert payload["assurance"] == "OFFLINE_FIXTURES_NOT_RELEASED_NOT_CALIBRATED"
    assert len(profiles) == 7
    assert len({item.executor_class for item in profiles}) == 7
    assert all(item.released is False for item in profiles)
