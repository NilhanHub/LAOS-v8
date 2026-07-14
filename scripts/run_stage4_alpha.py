#!/usr/bin/env python3
"""Run the real local-model Stage 4 Alpha vertical trust slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from laos_v8.alpha import (
    apply_and_submit,
    parse_bounded_proposal,
    promote_reviewed,
    proposal_prompt,
    reconcile_promotion,
    reconstruct_and_check,
    review_result,
)
from laos_v8.brokers import CommandBroker, WorkspaceBroker
from laos_v8.canonical import canonical_json
from laos_v8.capsule import CapsuleAuthority, verify_and_redeem
from laos_v8.errors import AuthorizationDenied
from laos_v8.evidence import EvidenceBroker
from laos_v8.identity import IdentityService
from laos_v8.model_broker import LocalOnlyModelBroker, ModelCallRequest
from laos_v8.models import Role
from laos_v8.ollama_adapter import OllamaModelPin, PinnedOllamaAdapter
from laos_v8.policy import PolicyEngine, minimal_stage4_alpha_policy
from laos_v8.repository_truth import build_manifest
from laos_v8.sandbox import DockerSandbox
from laos_v8.signing import ProtectedTestSigner
from laos_v8.state import CanonicalState
from laos_v8.workspace import CandidateWorkspace

MODEL_TAG = "qwen2.5-coder:1.5b"
MODEL_BLOB = "29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104"
TASK = (
    "Change no path except src/calculator.py. Set the replacement JSON value to exactly this complete Python file: "
    "def add(a: int, b: int) -> int:\\n    return a + b\\n"
)


def _git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Git is unavailable")
    completed = subprocess.run(  # noqa: S603 - resolved Git with structured arguments
        [git, "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout.strip()


def _fixture(source_fixture: Path, destination: Path) -> Path:
    shutil.copytree(source_fixture, destination)
    _git(destination, "init", "-b", "master")
    _git(destination, "config", "user.name", "LAOS Alpha Fixture")
    _git(destination, "config", "user.email", "alpha-fixture.invalid")
    _git(destination, "config", "core.autocrlf", "false")
    (destination / ".gitattributes").write_bytes(b".gitattributes text eol=lf\n*.py text eol=lf\n")
    _git(destination, "add", "--all")
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_DATE": "2026-07-13T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-07-13T00:00:00Z",
        }
    )
    _git(destination, "commit", "-m", "Stage 4 known-defect fixture", env=env)
    return destination


def _ts(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def run(repo: Path, output: Path, ollama_executable: str | None) -> dict[str, object]:
    if output.exists():
        raise RuntimeError(f"output must not already exist: {output}")
    output.mkdir(parents=True)
    now = datetime.now(UTC)
    expires = now + timedelta(hours=2)
    profile = minimal_stage4_alpha_policy()
    sandbox = DockerSandbox()
    sandbox.ensure_available()

    with tempfile.TemporaryDirectory(prefix="laos-stage4-alpha-") as temporary:
        work = Path(temporary)
        authoritative = _fixture(repo / "tests/fixtures/stage4_alpha/source", work / "authoritative")
        base = build_manifest(authoritative, seal_kind="base")
        candidate = CandidateWorkspace.create(authoritative, work / "candidate")
        with CanonicalState(output / "state.sqlite3") as state:
            identity = IdentityService(state)
            actor_specs = (
                ("builder:alpha", Role.BUILDER, "principal:builder", "session:builder", "workspace:builder"),
                ("verifier:alpha", Role.VERIFIER, "principal:verifier", "session:verifier", "workspace:verifier"),
                ("reviewer:alpha", Role.REVIEWER, "principal:reviewer", "session:reviewer", "workspace:reviewer"),
            )
            actors = {}
            for actor_id, role, principal, session, workspace in actor_specs:
                token = identity.register(
                    actor_id=actor_id,
                    principal=principal,
                    roles=(role,),
                    session_fingerprint=session,
                    workspace_id=workspace,
                    expires_at=_ts(expires),
                    revocation_epoch=0,
                )
                actors[actor_id] = identity.authenticate(token, required_epoch=0)

            builder = actors["builder:alpha"]
            verifier_actor = actors["verifier:alpha"]
            reviewer = actors["reviewer:alpha"]
            action_digest = f"sha256:{hashlib.sha256(canonical_json({'task': TASK})).hexdigest()}"
            signer = ProtectedTestSigner("capsule")
            authority = CapsuleAuthority(signer, issuer="authority:alpha", audience="laos-stage4-alpha")
            envelope = authority.issue(
                project_id="project:alpha",
                actor_id=builder.actor_id,
                role=Role.BUILDER,
                action_definition_digest=action_digest,
                base_seal=base.seal,
                policy_digest=profile.digest,
                profile_digest=profile.digest,
                skill_digest="sha256:" + "4" * 64,
                state_version=0,
                attempt_sequence=1,
                issued_at=_ts(now),
                expires_at=_ts(expires),
                revocation_epoch=0,
            )
            redeem_args = dict(
                verifier=signer.trust_root.verifier(),
                state=state,
                expected_issuer="authority:alpha",
                expected_audience="laos-stage4-alpha",
                expected_actor=builder.actor_id,
                expected_project_id="project:alpha",
                expected_role=Role.BUILDER,
                expected_action_definition_digest=action_digest,
                expected_base_seal=base.seal,
                expected_policy_digest=profile.digest,
                expected_profile_digest=profile.digest,
                expected_skill_digest="sha256:" + "4" * 64,
                expected_state_version=0,
                expected_attempt_sequence=1,
                required_revocation_epoch=0,
                now=now + timedelta(seconds=1),
            )
            verified = verify_and_redeem(envelope, **redeem_args)
            replay_denied = False
            try:
                verify_and_redeem(envelope, **redeem_args)
            except AuthorizationDenied as exc:
                replay_denied = exc.code == "CAPSULE_REPLAY_DENIED"

            source = (candidate.root / "src/calculator.py").read_text(encoding="utf-8")
            adapter = PinnedOllamaAdapter(
                OllamaModelPin(MODEL_TAG, MODEL_BLOB), executable=ollama_executable
            )
            model_result = LocalOnlyModelBroker(adapter).invoke(
                ModelCallRequest(
                    signed_instruction=proposal_prompt(TASK, source, allowed_path="src/calculator.py"),
                    trusted_truth=("Only src/calculator.py is writable.",),
                    untrusted_content=(source,),
                )
            )
            proposal = parse_bounded_proposal(model_result.output, allowed_path="src/calculator.py")
            (output / "model-proposal.json").write_text(
                json.dumps(proposal.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            submission = apply_and_submit(
                candidate,
                WorkspaceBroker(candidate.root, state, PolicyEngine(profile)),
                builder,
                proposal,
                policy_version=profile.version,
                policy_digest=profile.digest,
            )
            evidence_broker = EvidenceBroker(output / "objects", state)
            checked = reconstruct_and_check(
                submission,
                verifier_root=work / "verifier",
                protected_test=repo / "tests/fixtures/stage4_alpha/protected/acceptance.py",
                command_broker=CommandBroker(state, PolicyEngine(profile), sandbox, evidence_broker),
                verifier=verifier_actor,
                criterion_id="criterion:alpha-addition",
                policy_version=profile.version,
                policy_digest=profile.digest,
                budget=profile.budget,
            )
            if checked.result.exit_code != 0:
                failure = {
                    "assurance": "FAILED_ALPHA_CHECK_NOT_PROMOTED",
                    "exit_code": checked.result.exit_code,
                    "stderr": checked.result.stderr.decode("utf-8", errors="replace"),
                    "stdout": checked.result.stdout.decode("utf-8", errors="replace"),
                }
                (output / "failure.json").write_text(
                    json.dumps(failure, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
            verdict = review_result(
                builder=builder,
                reviewer=reviewer,
                evidence_broker=evidence_broker,
                evidence=checked.evidence,
                result_seal=submission.result.seal,
                check_exit_code=checked.result.exit_code,
            )
            before = reconcile_promotion(authoritative, submission, target_ref="refs/heads/master")
            receipt = promote_reviewed(authoritative, submission, verdict, target_ref="refs/heads/master")
            after = reconcile_promotion(authoritative, submission, target_ref="refs/heads/master")
            patch = _git(candidate.root, "diff", f"{candidate.base_commit}..{submission.commit}")
            (output / "candidate.patch").write_text(patch + "\n", encoding="utf-8", newline="\n")
            report: dict[str, object] = {
                "assurance": "STAGE_4_ALPHA_PROOF_ONLY_NOT_PRODUCTION_OR_FINAL_EFFICACY",
                "base_commit": candidate.base_commit,
                "base_seal": base.seal,
                "capsule_id": verified.capsule.capsule_id,
                "capsule_replay_denied": replay_denied,
                "check_exit_code": checked.result.exit_code,
                "criterion_id": "criterion:alpha-addition",
                "criterion_sha256": hashlib.sha256(
                    (repo / "tests/fixtures/stage4_alpha/protected/acceptance.py").read_bytes()
                ).hexdigest(),
                "evidence_digest": checked.evidence.digest,
                "evidence_result_seal": checked.evidence.result_seal,
                "model_blob_sha256": MODEL_BLOB,
                "model_identity_digest": adapter.identity_digest,
                "model_request_digest": model_result.request_digest,
                "promotion_reconciliation_after": after,
                "promotion_reconciliation_before": before,
                "promotion_status": receipt.status,
                "result_commit": submission.commit,
                "result_seal": submission.result.seal,
                "reviewer_id": verdict.reviewer_id,
                "reviewer_verdict": verdict.verdict,
                "sandbox_image": checked.result.image,
                "sandbox_network": checked.result.network,
                "sandbox_profile": checked.result.provider,
                "sandbox_root_filesystem": checked.result.root_filesystem,
                "task": TASK,
            }
            (output / "run.json").write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
            )
            state_export = {
                "assurance": "IMMUTABLE_STAGE_4_BOOTSTRAP_EXPORT_NOT_LIVE_STATE",
                "audit_events": [
                    dict(row)
                    for row in state.connection.execute(
                        "SELECT aggregate_id, actor_id, event_code, outcome, error_code, occurred_at, detail_digest "
                        "FROM audit_events ORDER BY occurred_at, event_id"
                    ).fetchall()
                ],
                "capsule_redemptions": [
                    dict(row)
                    for row in state.connection.execute(
                        "SELECT capsule_id, actor_id, attempt_sequence, token_hash, redeemed_at "
                        "FROM capsule_redemptions"
                    ).fetchall()
                ],
                "evidence_objects": [
                    dict(row)
                    for row in state.connection.execute(
                        "SELECT digest, result_seal, criterion_id, classification, collector, bytes, relative_path "
                        "FROM evidence_objects"
                    ).fetchall()
                ],
            }
            (output / "state-export.json").write_text(
                json.dumps(state_export, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ollama-executable")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    report = run(repo, args.output.resolve(), args.ollama_executable)
    (args.output.resolve() / "state.sqlite3").unlink()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
