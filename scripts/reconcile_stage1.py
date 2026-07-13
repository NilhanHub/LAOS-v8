#!/usr/bin/env python3
"""Build deterministic Stage 1 governance ledgers and regression fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md"
PLAN_SHA256 = hashlib.sha256(PLAN.read_bytes()).hexdigest()
DATE = "2026-07-13"

MILESTONE_TITLES = {
    0: "Recovery, baseline, and governance",
    1: "v7.0.1 emergency correctness branch",
    2: "Typed v8 kernel and strict validation",
    3: "Repository truth, safe paths, identity, and transactional state",
    4: "Policy engine and risk classification",
    5: "Pack separation, signing, and leak prevention",
    6: "Anti-Skip Action Engine",
    7: "Model profiles, prompt compiler, and context control",
    8: "New-build compiler and existing-application capture/continuation",
    9: "Command broker, sandbox, and clean verifier",
    10: "Evidence engine and criterion-level closure",
    11: "Verification depth and independent review",
    12: "Side effects, approvals, recovery, and anti-thrashing",
    13: "Tamper-evident events, artifacts, provenance, and release truth",
    14: "Real weaker-agent evaluation laboratory",
    15: "Documentation, migration, and operator experience",
    16: "Pre-evaluation red team and post-evaluation durable publication",
}

MILESTONE_TO_STAGES = {
    0: [1], 1: [1], 2: [2], 3: [3], 4: [3], 5: [3, 5], 6: [4, 5],
    7: [5], 8: [5], 9: [3, 6], 10: [4, 6], 11: [4, 6], 12: [3, 7],
    13: [8], 14: [9], 15: [2, 8], 16: [9, 10],
}

REVISION_REQUIREMENT_MILESTONES = [
    13, 2, 5, 6, 7, 5, 5, 6, 11, 9, 7, 4, 10, 2, 7, 10,
    13, 16, 9, 6, 4, 3, 6, 5, 3, 12, 13, 14, 16, 12, 15,
]

STAGES = [
    (1, "Recovery and program truth", [], "COMPLETED"),
    (2, "Typed kernel and platform contracts", [1], "PLANNED"),
    (3, "Mandatory Security Spine", [2], "PLANNED"),
    (4, "Alpha Vertical Trust Slice", [3], "PLANNED"),
    (5, "Core product workflows", [4], "PLANNED"),
    (6, "Execution assurance", [5], "PLANNED"),
    (7, "Side effects and recovery", [6], "PLANNED"),
    (8, "Release engineering and operator readiness", [7], "PLANNED"),
    (9, "Candidate red team and sealed evaluation", [8], "PLANNED"),
    (10, "Evaluated-revision publication", [9], "PLANNED"),
]

BLOCKER_STAGE = {
    **{f"RB-{n:03d}": 3 for n in (1, 2, 3, 5, 7, 8, 9, 10)},
    "RB-004": 5, "RB-006": 2, "RB-011": 6, "RB-012": 6,
    "RB-013": 6, "RB-014": 6, "RB-015": 7, "RB-016": 8,
    "RB-017": 8, "RB-018": 8, "RB-019": 8, "RB-020": 8,
    "RB-021": 7, "RB-022": 9, "RB-023": 9, "RB-024": 9,
    "RB-025": 10,
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def reconcile_requirements() -> None:
    path = ROOT / "REQUIREMENTS_LEDGER.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    existing_ids = {requirement["id"] for requirement in data["requirements"]}
    plan_text = PLAN.read_text(encoding="utf-8")
    section_15 = plan_text.split("## 15. New improvements added beyond the earlier master plan", 1)[1].split("## 16. Program risk register", 1)[0]
    additions = re.findall(r"^\d+\. \*\*([^*]+):\*\* (.+)$", section_15, flags=re.MULTILINE)
    if len(additions) != 31:
        raise RuntimeError(f"expected 31 Revision 1.1 requirements, found {len(additions)}")
    for index, ((title, description), milestone) in enumerate(zip(additions, REVISION_REQUIREMENT_MILESTONES), start=1):
        requirement_id = f"REQ-REVISION_1_1-{index:03d}"
        if requirement_id not in existing_ids:
            data["requirements"].append({
                "category": "REVISION_1_1",
                "description": f"{title}: {description}",
                "id": requirement_id,
                "priority": "P0",
                "source": "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md",
                "status": "PLANNED",
                "target_milestones": [milestone],
                "verification_required": True,
            })
    for requirement in data["requirements"]:
        milestones = requirement["target_milestones"]
        stages = sorted({stage for milestone in milestones for stage in MILESTONE_TO_STAGES[milestone]})
        requirement["source"] = "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md"
        requirement["source_plan_revision"] = "1.1"
        requirement["source_plan_sha256"] = PLAN_SHA256
        requirement["implementation_stages"] = stages
        requirement["scope_classification"] = "MUST_V8_0" if requirement["priority"] == "P0" else "SHOULD_V8_0"
        requirement["scope_status"] = "PROVISIONAL_UNTIL_ALPHA_FREEZE"
        requirement["owner"] = f"stage-{stages[-1]}-implementation-owner"
        requirement["independent_reviewer"] = "Nilhan"
        requirement["evidence_status"] = "OPEN"
        requirement["release_blocking"] = requirement["priority"] == "P0"
        if 1 in milestones and requirement["status"] != "BASELINED":
            requirement["status"] = "FIXTURED_OPEN"
            requirement["evidence_status"] = "STAGE_1_FIXTURE"
    data.update({
        "ledger_version": "1.1.0",
        "reconciled_on": DATE,
        "authority": "LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md Revision 1.1",
        "authority_sha256": PLAN_SHA256,
        "scope_note": "P0/P1 mapping is provisional until the post-Alpha scope freeze.",
        "requirement_count": len(data["requirements"]),
        "stage0_historical_requirement_count": 210,
        "revision_1_1_added_requirement_count": 31,
    })
    write_json(path, data)


def create_stage_and_milestone_ledgers() -> None:
    stage_rows = []
    for number, name, depends_on, status in STAGES:
        stage_rows.append({
            "stage": number, "name": name, "depends_on": depends_on, "status": status,
            "scope_classification": "MUST_V8_0_EXECUTION_ENVELOPE",
            "owner": "Codex" if number == 1 else f"stage-{number}-implementation-owner",
            "independent_reviewer": "Nilhan" if number == 1 else f"stage-{number}-independent-reviewer",
            "entry_gate": "Stage 0 verified" if number == 1 else f"Stage {number - 1} exit gate passed",
            "exit_gate_reference": "LAOS_v8_TEN_STAGE_IMPLEMENTATION_PLAN.md",
            "evidence_policy": "BOOTSTRAP" if number < 6 else "V8_PROTECTED_EVIDENCE_PATH",
            "rollback": "Return to the previous immutable Git tag and evidence snapshot; never rewrite historical evidence.",
        })
    write_json(ROOT / "PROGRAM_STAGE_LEDGER.json", {
        "ledger_version": "1.0.0", "authority_sha256": PLAN_SHA256, "stages": stage_rows,
    })

    milestone_rows = []
    for number, title in MILESTONE_TITLES.items():
        milestone_rows.append({
            "milestone": number, "title": title, "implementation_stages": MILESTONE_TO_STAGES[number],
            "depends_on_stage": [] if min(MILESTONE_TO_STAGES[number]) == 1 else [min(MILESTONE_TO_STAGES[number]) - 1],
            "scope_classification": "MUST_V8_0",
            "owner": "Codex" if number in (0, 1) else f"milestone-{number}-implementation-owner",
            "independent_reviewer": "Nilhan" if number in (0, 1) else f"milestone-{number}-independent-reviewer",
            "external_dependencies": [],
            "estimate_range": "To be calibrated before entry; no calendar promise is made at Stage 1.",
            "deliverables_and_non_goals": f"Normative in Revision 1.1 Milestone {number}; unlisted integration claims remain OPEN.",
            "acceptance_criteria": f"Revision 1.1 Milestone {number} exit gate plus affected stable release blockers.",
            "required_evidence": "Bootstrap evidence until v8 evidence custody is independently accepted; then rerun through v8.",
            "rollback_recovery": "Revert authority to the last accepted immutable tag and retain the failed attempt as evidence.",
            "open_cross_subsystem_requirements": number not in (0, 1),
        })
    write_json(ROOT / "MILESTONE_LEDGER.json", {
        "ledger_version": "1.0.0", "authority_sha256": PLAN_SHA256,
        "discipline": "Pulled-forward slices satisfy Security Spine/Alpha only and do not close full later milestones.",
        "milestones": milestone_rows,
    })


def create_blockers() -> None:
    text = PLAN.read_text(encoding="utf-8")
    matches = re.findall(r"\*\*(RB-\d{3}) — ([^:]+):\*\* (.+)", text)
    if len(matches) != 25:
        raise RuntimeError(f"expected 25 release blockers, found {len(matches)}")
    rows = []
    for blocker_id, title, criterion in matches:
        rows.append({
            "id": blocker_id, "title": title, "criterion": criterion,
            "owner_stage": BLOCKER_STAGE[blocker_id], "status": "OPEN",
            "builder_write_authority": False,
            "waiverability": "CONDITIONAL_HIGH_ONLY" if blocker_id == "RB-022" else "NON_WAIVABLE_FOR_CLAIMED_SUPPORT_ROW",
            "evidence_digests": [], "independent_verifier": "UNASSIGNED_UNTIL_OWNER_STAGE",
        })
    write_json(ROOT / "RELEASE_BLOCKERS.json", {
        "ledger_version": "1.0.0", "authority_sha256": PLAN_SHA256,
        "canonicality": "Bootstrap view; protected transactional state becomes canonical when implemented.",
        "count": len(rows), "blockers": rows,
    })


def create_threat_register() -> None:
    text = (ROOT / "THREAT_MODEL_DRAFT.md").read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if re.match(r"\| TM-\d{3} \|", line):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows.append({
                "id": cells[0], "threat": cells[1], "attack_path": cells[2], "impact": cells[3],
                "required_controls": cells[4], "mandatory_test": cells[5], "status": "OPEN",
            })
    additions = [
        ("TM-041", "Unsafe repository promotion", "Builder mutates authority or promotes against a stale base", "Accepted source diverges", "Isolated clone, broker delta, clean reconstruction, PromotionIntent and Git CAS", "Stale-base and crash-point promotion suite"),
        ("TM-042", "Model-provider boundary bypass", "Prompts, tools, retention or provider region bypass local policy", "Data loss or hidden authority", "Mediated model-call broker, minimization, provider row and tool denial", "Transmission-canary and built-in-tool denial suite"),
        ("TM-043", "Path TOCTOU and Windows alias escape", "Reparse, short-name, ADS, hard-link or concurrent swap defeats string validation", "External host access", "Final-handle containment and supported-platform fail-closed policy", "Windows reparse and concurrent-swap corpus"),
        ("TM-044", "Indeterminate external outcome replay", "Receipt is lost after irreversible provider acceptance", "Duplicate consequential action", "OUTCOME_UNKNOWN, reconciliation and no automatic irreversible retry", "Crash after dispatch before receipt persistence"),
        ("TM-045", "Local audit truncation or fork", "Compromised host rewrites or forks local event history", "False audit narrative", "Same-transaction events plus independent external anchors", "Gap, fork, rollback and stale-anchor suite"),
        ("TM-046", "Cryptographic context confusion", "Valid signature is reused across object, key purpose, issuer or audience", "Unauthorized authority", "Typed domain separation, key purposes, rotation and revocation", "Cross-object and wrong-purpose signature suite"),
        ("TM-047", "Privileged offline authority", "Offline verifier is treated as an issuer or dispatcher", "Unrevocable privileged action", "Offline v8.0 verification/read-only support row", "Offline issuance and redemption denial"),
        ("TM-048", "Holdout contamination or selective stopping", "Final tasks influence tuning or repeated evaluation", "Invalid efficacy claim", "Preregistration, sealed custody, fixed stopping and new holdout after behavior change", "Holdout access and rerun audit"),
        ("TM-049", "Sensitive evidence retention", "Raw prompts, screenshots or API data persist beyond policy", "Privacy, secret or contractual breach", "Pre-persistence classification, minimization, encryption, purge and holds", "Retention, purge and backup-deletion suite"),
        ("TM-050", "Trust-root compromise without recovery", "Signer, control host, identity or evidence broker is compromised", "System-wide false authority", "Kill switch, mass revocation, quarantine, rotation, recovery point and re-attestation", "Executable compromise recovery drill"),
    ]
    for values in additions:
        rows.append({
            "id": values[0], "threat": values[1], "attack_path": values[2], "impact": values[3],
            "required_controls": values[4], "mandatory_test": values[5], "status": "OPEN",
        })
    write_json(ROOT / "THREAT_REGISTER.json", {
        "register_version": "1.1.0", "authority_sha256": PLAN_SHA256,
        "count": len(rows), "threats": rows,
    })


def create_scope_support_performance() -> None:
    capabilities = [
        ("new_build_compiler", "MUST_V8_0", 5),
        ("existing_application_capture_continuation", "MUST_V8_0", 5),
        ("action_evidence_review_promotion", "MUST_V8_0", 6),
        ("recovery_and_migration", "MUST_V8_0", 8),
        ("side_effect_deny_all_protocol", "MUST_V8_0", 7),
        ("production_side_effect_adapters", "DEFER_V8_X_UNLESS_ALPHA_RETAINS", 7),
        ("offline_privileged_operation", "DEFER_V8_X", None),
        ("non_git_authoritative_mutation", "DEFER_V8_X", None),
        ("distributed_canonical_state", "DEFER_V8_X", None),
    ]
    write_json(ROOT / "SCOPE_LEDGER.json", {
        "ledger_version": "1.0.0", "status": "PROVISIONAL_UNTIL_ALPHA_FREEZE",
        "equivalent_scope_rule": True,
        "capabilities": [{"capability": c, "classification": s, "owner_stage": o, "status": "OPEN" if o else "DEFERRED"} for c, s, o in capabilities],
    })
    support = [
        ("connected-windows-local-git", "PLANNED", True),
        ("connected-linux-local-git", "PLANNED", True),
        ("offline-verification-read-only", "PLANNED", False),
        ("offline-privileged-authority", "UNSUPPORTED_V8_0", False),
        ("direct-host-unmediated", "UNSUPPORTED", False),
        ("non-git-authoritative-mutation", "UNSUPPORTED_V8_0", False),
        ("network-filesystem-sqlite", "UNSUPPORTED", False),
        ("distributed-canonical-state", "DEFER_V8_X", False),
    ]
    write_json(ROOT / "SUPPORTED_ENVIRONMENTS.json", {
        "matrix_version": "0.1.0", "claim_status": "NO_RUNTIME_SUPPORT_CLAIM",
        "rows": [{"id": i, "status": s, "privileged_connected_mode": p, "evidence": []} for i, s, p in support],
    })
    metrics = ["manifest_time_memory", "pack_size_latency", "state_contention", "sandbox_startup", "evidence_growth", "full_suite_duration", "flake_rate", "tokens", "cost", "retries", "human_minutes"]
    write_json(ROOT / "PERFORMANCE_LEDGER.json", {
        "ledger_version": "0.1.0", "status": "DEFINITIONS_REQUIRED_BEFORE_ALPHA",
        "metrics": [{"id": metric, "budget": None, "measurement": "OPEN", "owner_stage": 2} for metric in metrics],
    })


def create_migration_matrix() -> None:
    rows = [
        ("project_blueprints", "v7 JSON blueprint", "v8 versioned typed model", 5),
        ("capture_app_intelligence", "v7 capture return", "strict validated capture aggregate", 5),
        ("continuation_fingerprint", "v7 inconsistent digest", "versioned source/base seal", 3),
        ("task_state", "mutable v7 JSON", "transactional v8 state", 3),
        ("evidence", "project-writable files", "broker-controlled CAS plus signed index", 6),
        ("side_effect_records", "v7 journal", "outbox plus indeterminate outcome lifecycle", 7),
        ("release_integrity", "static/mutable ambiguity", "clean static artifacts and runtime initialization", 8),
    ]
    write_json(ROOT / "MIGRATION_MATRIX.json", {
        "matrix_version": "0.1.0", "source": "LAOS v7.0 immutable archive",
        "policy": {"copy_on_write": True, "dry_run": True, "deterministic_mapping_report": True, "unknown_field_quarantine": True, "idempotent_rerun": True, "rollback": True, "coexistence_rules_required": True},
        "rows": [{"feature": a, "v7_source": b, "v8_target": c, "owner_stage": d, "status": "OPEN"} for a, b, c, d in rows],
    })


def create_backlog() -> None:
    rows = []
    for number, name, depends_on, status in STAGES:
        stage_tasks = [
            {"id": f"S{number}-CONTRACT", "title": "Satisfy the stage contract in the ten-stage plan", "status": status},
            {"id": f"S{number}-EVIDENCE", "title": "Capture evidence and rerun affected earlier gates", "status": "OPEN"},
            {"id": f"S{number}-REVIEW", "title": "Obtain required independent review", "status": "OPEN"},
        ]
        if number == 1 and status == "COMPLETED":
            for task in stage_tasks:
                task["status"] = "COMPLETED"
        rows.append({
            "stage": number, "name": name, "depends_on": depends_on, "status": status,
            "tasks": stage_tasks,
        })
    write_json(ROOT / "IMPLEMENTATION_BACKLOG.json", {
        "backlog_version": "1.1.0", "authority_sha256": PLAN_SHA256,
        "historical_backlog": "design_inputs/LAOS_v8_IMPLEMENTATION_BACKLOG.json",
        "stages": rows,
    })


def create_adr_register() -> None:
    existing_owner = {1: 5, 2: 3, 3: 3, 4: 2, 5: 5, 6: 6, 7: 8}
    existing = [
        (1, "Trust-zone separation", "ACCEPTED"), (2, "Runtime-state separation", "ACCEPTED"),
        (3, "SQLite and migrations", "ACCEPTED_REVIEW_REQUIRED_STAGE_2"),
        (4, "Schema/model source of truth", "ACCEPTED_REVIEW_REQUIRED_STAGE_2"),
        (5, "Signing, identity and capabilities", "ACCEPTED_REVIEW_REQUIRED_STAGE_2"),
        (6, "Sandbox provider interface", "ACCEPTED_REVIEW_REQUIRED_STAGE_3"),
        (7, "Release and provenance", "ACCEPTED_REVIEW_REQUIRED_STAGE_8"),
    ]
    proposed = [
        (8, "Deployment and enforcement contract", 3), (9, "Base/result seals and CAS promotion", 3),
        (10, "Typed signing envelope and key lifecycle", 3), (11, "Evaluation and holdout custody", 8),
        (12, "Offline verification-only support profile", 3), (13, "Indeterminate side-effect outcomes", 7),
        (14, "Evidence custody and external anchoring", 6),
    ]
    rows = [{"id": f"ADR-{n:04d}", "title": t, "status": s, "owner_stage": existing_owner[n]} for n, t, s in existing]
    rows.extend({"id": f"ADR-{n:04d}", "title": t, "status": "PROPOSED", "owner_stage": stage} for n, t, stage in proposed)
    write_json(ROOT / "ADR_REGISTER.json", {"register_version": "1.1.0", "adrs": rows})


def create_fixtures() -> None:
    fixtures = [
        ("FX-V7-001", "canonical_fingerprint_consistency", ["REG-001", "REG-002"], 3, "Two v7 workflows can produce different fingerprints for the same unchanged file set.", "One versioned manifest algorithm and ignore policy produces identical golden vectors."),
        ("FX-V7-002", "one_byte_repository_drift", ["REG-004"], 3, "A pre-claim tracked-file mutation can become part of the claimed baseline.", "Authority is bound to an Architect-approved base seal and one-byte drift is denied."),
        ("FX-V7-003", "malformed_app_intelligence", ["REG-003"], 2, "Syntactically valid but structurally or semantically invalid capture data may pass heuristic checks.", "Draft 2020-12 plus semantic validation rejects the fixture with a stable error."),
        ("FX-V7-004", "pre_claim_mutation", ["REG-004"], 3, "Forbidden edits made before claim can be hidden by baseline timing.", "Pre-authority source seal mismatch prevents claim and records a denial."),
        ("FX-V7-005", "path_and_link_escape", ["REG-005", "REG-006", "REG-014", "REG-016"], 3, "String/path and link semantics can omit or escape repository observation.", "Final-handle containment rejects traversal, symlink, junction, reparse, ADS and alias escapes."),
        ("FX-V7-006", "unsafe_archive", ["REG-016"], 3, "v7 archive checks do not establish full quotas, link handling or race-safe extraction assurance.", "Safe extraction rejects traversal, duplicates, links, case collisions and resource-limit violations."),
        ("FX-V7-007", "shell_command_hazard", ["REG-013"], 6, "Contracted commands execute with shell=True and interpret metacharacters.", "Structured argv through a qualifying sandbox is default; untrusted repository code remains sandboxed."),
        ("FX-V7-008", "continuation_freshness", ["REG-001", "REG-002", "REG-004", "REG-017"], 5, "Capture/continuation identity can disagree or lack a guaranteed reconciliation path.", "Capture fingerprint, base seal and continuation freshness agree; drift requires governed recapture."),
    ]
    target = ROOT / "tests" / "fixtures" / "v7_regressions"
    target.mkdir(parents=True, exist_ok=True)
    for fixture_id, slug, regression_ids, stage, baseline, expected in fixtures:
        write_json(target / f"{fixture_id.lower()}_{slug}.json", {
            "fixture_version": "1.0.0", "id": fixture_id, "title": slug.replace("_", " "),
            "classification": "V7_BASELINE_WEAKNESS_V8_OPEN_REQUIREMENT",
            "source_regressions": regression_ids, "source_archive_sha256": "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d",
            "baseline_expected": baseline, "v8_required": expected, "owner_stage": stage,
            "setup": ["Use an isolated temporary Git repository or in-memory archive generated by the test harness.", "Do not mutate the sealed v7 archive."],
            "actions": ["Apply the fixture-specific mutation or malformed input.", "Run the owning v8 contract when implemented."],
            "oracle": ["The v7 observation remains baseline evidence, not a passing v8 result.", "The owning v8 stage must fail closed with current seal-bound evidence."],
            "status": "FIXTURE_SPECIFIED_IMPLEMENTATION_OPEN",
        })


def update_regression_catalog() -> None:
    path = ROOT / "issues" / "REGRESSION_CATALOG.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    fixture_by_reg = {}
    for fixture in sorted((ROOT / "tests" / "fixtures" / "v7_regressions").glob("*.json")):
        item = json.loads(fixture.read_text(encoding="utf-8"))
        for reg in item["source_regressions"]:
            fixture_by_reg.setdefault(reg, []).append(fixture.relative_to(ROOT).as_posix())
    for item in data["items"]:
        if item["id"] in fixture_by_reg:
            item["regression_test_status"] = "FIXTURE_SPECIFIED_IMPLEMENTATION_OPEN"
            item["fixture_paths"] = fixture_by_reg[item["id"]]
            item["implementation_stage"] = MILESTONE_TO_STAGES[item["target_milestone"]][-1]
    data["catalog_version"] = "1.1.0"
    data["reconciled_on"] = DATE
    data["fixture_only_track"] = True
    write_json(path, data)


def main() -> None:
    reconcile_requirements()
    create_stage_and_milestone_ledgers()
    create_blockers()
    create_threat_register()
    create_scope_support_performance()
    create_migration_matrix()
    create_backlog()
    create_adr_register()
    create_fixtures()
    update_regression_catalog()


if __name__ == "__main__":
    main()
