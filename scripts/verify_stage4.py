#!/usr/bin/env python3
"""Fail-closed verifier for the Stage 4 Alpha review candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_BLOB = "29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104"


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify() -> list[str]:
    checks: list[str] = []
    status = load("IMPLEMENTATION_STATUS.json")
    require(status["stage_3_status"] == "COMPLETE", "Stage 3 is not complete")
    require(status["stage_4_status"] == "AWAITING_NILHAN_AND_INDEPENDENT_REVIEWER_GO_NO_GO", "Stage 4 status overclaim")
    require(status["real_weaker_agent_executed"] is True, "real local model execution is not recorded")
    require(
        status["v8_runtime_exists"] is False and status["v8_release_exists"] is False,
        "v8 runtime/release overclaim",
    )
    checks.append("program_truth")

    protocol = load("ALPHA_EXPERIMENT_PROTOCOL.json")
    require(protocol["claim_boundary"] == "ALPHA_PROOF_ONLY_NOT_FINAL_EFFICACY_OR_RELEASE", "claim boundary changed")
    require(protocol["model"]["blob_sha256"] == MODEL_BLOB, "model pin changed")
    require(protocol["model"]["tools"] == [], "model gained tools")
    require(protocol["writable_paths"] == ["src/calculator.py"], "Alpha write scope changed")
    checks.append("experiment_contract")

    runtime = load("Evidence/STAGE_4_ALPHA_RUNTIME/run.json")
    require(runtime["check_exit_code"] == 0, "protected criterion failed")
    require(runtime["capsule_replay_denied"] is True, "capsule replay was not denied")
    require(runtime["model_blob_sha256"] == MODEL_BLOB, "runtime used another model")
    require(runtime["evidence_result_seal"] == runtime["result_seal"], "evidence/result binding mismatch")
    protected = ROOT / "tests/fixtures/stage4_alpha/protected/acceptance.py"
    require(hashlib.sha256(protected.read_bytes()).hexdigest() == runtime["criterion_sha256"], "criterion changed")
    require(runtime["reviewer_id"] == "reviewer:alpha" and runtime["reviewer_verdict"] == "pass", "review failed")
    require(runtime["promotion_status"] == "PROMOTED", "CAS promotion did not complete")
    require(runtime["promotion_reconciliation_before"] == "retry_safe", "pre-promotion recovery is unsafe")
    require(runtime["promotion_reconciliation_after"] == "already_promoted", "post-promotion recovery is unsafe")
    require(
        runtime["sandbox_network"] == "none" and runtime["sandbox_root_filesystem"] == "read-only",
        "sandbox weakened",
    )
    object_digest = runtime["evidence_digest"].removeprefix("sha256:")
    object_path = ROOT / "Evidence/STAGE_4_ALPHA_RUNTIME/objects/objects" / object_digest[:2] / object_digest
    require(object_path.is_file(), "broker evidence object is missing")
    require(hashlib.sha256(object_path.read_bytes()).hexdigest() == object_digest, "broker evidence was mutated")
    state_export = load("Evidence/STAGE_4_ALPHA_RUNTIME/state-export.json")
    bindings = state_export["evidence_objects"]
    require(len(bindings) == 1 and bindings[0]["digest"] == runtime["evidence_digest"], "binding export mismatch")
    require(bindings[0]["result_seal"] == runtime["result_seal"], "exported result binding mismatch")
    require(not (ROOT / "Evidence/STAGE_4_ALPHA_RUNTIME/state.sqlite3").exists(), "mutable runtime state was retained")
    checks.append("real_alpha_runtime")

    pilot = load("Evidence/STAGE_4_ALPHA_PILOT.json")
    require(pilot["assurance"] == "DEVELOPMENT_PILOT_ONLY_NOT_FINAL_EFFICACY", "pilot overclaims efficacy")
    require(pilot["seed"] == 80401 and len(pilot["records"]) == 8, "pilot assignment changed")
    required_conditions = {
        "broad_prompt",
        "resource_matched_structured_prompt",
        "v7_prompt",
        "alpha_trust_slice",
    }
    require(set(pilot["summary"]) == required_conditions, "pilot conditions are incomplete")
    require(all(item["trials"] == 2 for item in pilot["summary"].values()), "pilot is not balanced")
    checks.append("randomized_development_pilot")

    coverage = load("STAGE_4_ALPHA_COVERAGE.json")["coverage"]
    require(len(coverage) == 13, "Alpha coverage ledger is incomplete")
    require(coverage[-1]["status"] == "AWAITING_REVIEW", "go/no-go was overstated")
    review = load("Evidence/STAGE_4_REVIEW.json")
    require(review["status"] == "AWAITING_REVIEW" and review["scope_frozen"] is False, "review status is dishonest")
    stage4 = next(row for row in load("PROGRAM_STAGE_LEDGER.json")["stages"] if row["stage"] == 4)
    require(stage4["status"] == "REVIEW_CANDIDATE" and stage4["owner"] == "Codex", "stage ledger mismatch")
    checks.append("coverage_and_review_gate")
    return checks


def main() -> int:
    checks = verify()
    print(json.dumps({"status": "PASS_AWAITING_TWO_PARTY_GO_NO_GO_REVIEW", "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
