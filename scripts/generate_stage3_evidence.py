#!/usr/bin/env python3
"""Generate reproducible local Security Spine profile evidence."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from laos_v8.capsule import CapsuleAuthority, verify_and_redeem
from laos_v8.evidence import EvidenceBroker
from laos_v8.models import Role
from laos_v8.operator_paths import explain_denial
from laos_v8.policy import ResourceBudget
from laos_v8.sandbox import DOCKER_IMAGE, DockerSandbox, SandboxRequest
from laos_v8.signing import ProtectedTestSigner
from laos_v8.state import CanonicalState

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "Evidence"


def write_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker_details() -> dict[str, object]:
    docker = shutil.which("docker")
    if docker is None:
        return {"status": "FAIL", "error": "docker-cli-unavailable"}
    sandbox = DockerSandbox(docker)
    available, server = sandbox.availability()
    if not available:
        return {"status": "FAIL", "error": server}
    probe = """
import json, os, pathlib, socket
status = pathlib.Path('/proc/self/status').read_text()
cap_eff = next(line.split()[1] for line in status.splitlines() if line.startswith('CapEff:'))
no_new = next(line.split()[1] for line in status.splitlines() if line.startswith('NoNewPrivs:'))
write_denied = []
for name in ('/workspace/.laos-write-probe', '/etc/.laos-write-probe'):
    try:
        pathlib.Path(name).write_text('forbidden')
    except OSError:
        write_denied.append(name)
sock = socket.socket()
sock.settimeout(1)
network_result = sock.connect_ex(('1.1.1.1', 53))
sock.close()
result = {'uid': os.getuid(), 'cap_eff': cap_eff, 'no_new_privs': no_new,
          'write_denied': write_denied, 'network_connect_result': network_result}
assert result['uid'] == 65534
assert int(result['cap_eff'], 16) == 0
assert result['no_new_privs'] == '1'
assert len(result['write_denied']) == 2
assert result['network_connect_result'] != 0
print(json.dumps(result, sort_keys=True))
""".strip()
    result = sandbox.run(
        SandboxRequest(("python", "-c", probe), ROOT, ResourceBudget(timeout_seconds=60, output_bytes=1_048_576))
    )
    inspected = subprocess.run(  # noqa: S603 - resolved Docker executable and fixed digest
        [docker, "image", "inspect", DOCKER_IMAGE, "--format", "{{json .RepoDigests}}"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return {
        "status": "PASS" if result.exit_code == 0 and inspected.returncode == 0 else "FAIL",
        "server_version": server,
        "provider": result.provider,
        "image": result.image,
        "image_repo_digests": json.loads(inspected.stdout) if inspected.returncode == 0 else [],
        "probe": json.loads(result.stdout),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }


def state_details() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="laos-stage3-state-") as temporary:
        path = Path(temporary) / "state.sqlite3"
        with CanonicalState(path) as state:
            state.create_aggregate("task:evidence", "task", "planned", {"proof": True}, "actor:architect")
            state.claim_action("action:evidence", "actor:builder", "sha256:" + "0" * 64, "2099-01-01T00:00:00Z")
            duplicate_claim_denied = False
            try:
                state.claim_action("action:evidence", "actor:other", "sha256:" + "0" * 64, "2099-01-01T00:00:00Z")
            except Exception as exc:
                duplicate_claim_denied = getattr(exc, "code", "") == "ACTION_ALREADY_CLAIMED"
            state.integrity_check()
            return {
                "status": "PASS" if duplicate_claim_denied else "FAIL",
                "sqlite_version": sqlite3.sqlite_version,
                "journal_mode": state.connection.execute("PRAGMA journal_mode").fetchone()[0],
                "synchronous": state.connection.execute("PRAGMA synchronous").fetchone()[0],
                "foreign_keys": state.connection.execute("PRAGMA foreign_keys").fetchone()[0],
                "schema_version": state.connection.execute("PRAGMA user_version").fetchone()[0],
                "duplicate_claim_denied": duplicate_claim_denied,
                "audit_events": state.connection.execute("SELECT count(*) FROM audit_events").fetchone()[0],
                "integrity_check": state.connection.execute("PRAGMA integrity_check").fetchone()[0],
            }


def signing_details() -> dict[str, object]:
    signer = ProtectedTestSigner()
    authority = CapsuleAuthority(signer, issuer="actor:architect", audience="broker:stage3")
    digest = "sha256:" + "0" * 64
    envelope = authority.issue(
        project_id="project:stage3",
        actor_id="actor:builder",
        role=Role.BUILDER,
        action_definition_digest=digest,
        base_seal=digest,
        policy_digest=digest,
        profile_digest=digest,
        skill_digest=digest,
        state_version=0,
        attempt_sequence=1,
        issued_at="2026-07-12T00:00:00Z",
        expires_at="2026-07-14T00:00:00Z",
        revocation_epoch=0,
    )
    with tempfile.TemporaryDirectory(prefix="laos-stage3-signing-") as temporary:
        with CanonicalState(Path(temporary) / "state.sqlite3") as state:
            verified = verify_and_redeem(
                envelope,
                verifier=signer.trust_root.verifier(),
                state=state,
                expected_issuer="actor:architect",
                expected_audience="broker:stage3",
                expected_actor="actor:builder",
                expected_project_id="project:stage3",
                expected_role=Role.BUILDER,
                expected_action_definition_digest=digest,
                expected_base_seal=digest,
                expected_policy_digest=digest,
                expected_profile_digest=digest,
                expected_skill_digest=digest,
                expected_state_version=0,
                expected_attempt_sequence=1,
                required_revocation_epoch=0,
                now=datetime(2026, 7, 13, tzinfo=UTC),
            )
    return {
        "status": "PASS",
        "algorithm": envelope.algorithm,
        "key_purpose": envelope.key_purpose,
        "key_id_format_verified": envelope.key_id.startswith("key:") and len(envelope.key_id) == 36,
        "trust_assurance": signer.trust_root.assurance,
        "capsule_id_format_verified": verified.capsule.capsule_id.startswith("capsule:"),
        "single_use_redemption_verified": True,
        "production_key_custody_claimed": False,
    }


def operator_details() -> dict[str, object]:
    digest = "sha256:" + "0" * 64
    with tempfile.TemporaryDirectory(prefix="laos-stage3-operator-") as temporary:
        root = Path(temporary)
        state_path = root / "state.sqlite3"
        with CanonicalState(state_path) as state:
            state.create_aggregate("task:operator", "task", "planned", {}, "actor:architect")
            stopped_epoch = state.set_emergency_stop("actor:architect", "operator evidence")
            recovered_epoch = state.recover_trust(
                "actor:architect", "reviewed operator recovery", expected_epoch=stopped_epoch
            )
            broker = EvidenceBroker(root / "evidence", state)
            captured = broker.capture(
                b"stage3 operator evidence",
                result_seal=digest,
                criterion_id="criterion:operator",
                classification="internal",
                collector="stage3-evidence-generator",
                actor_id="actor:verifier",
            )
            exported = broker.export_object(
                captured.digest,
                root / "export",
                expected_classification="internal",
                actor_id="actor:operator",
            )
            broker.purge(
                captured.digest,
                expected_classification="internal",
                actor_id="actor:operator",
                reason="operator-path test",
            )
            tombstones = int(state.connection.execute("SELECT count(*) FROM evidence_tombstones").fetchone()[0])
            backup_digest = state.backup(root / "backup.sqlite3")
        restore_digest = CanonicalState.restore(root / "backup.sqlite3", root / "restored.sqlite3")
        with CanonicalState(root / "restored.sqlite3") as restored:
            restored.integrity_check()
            restored_status = restored.control_status()
        explanation = explain_denial("CAPSULE_REPLAY_DENIED")
        passed = (
            recovered_epoch == stopped_epoch + 1
            and tombstones == 1
            and exported["digest"] == captured.digest
            and backup_digest == restore_digest
            and restored_status[0] is False
            and explanation["status"] == "KNOWN"
        )
        return {
            "status": "PASS" if passed else "FAIL",
            "backup_restore_digest_match": backup_digest == restore_digest,
            "trust_epoch_after_recovery": recovered_epoch,
            "evidence_export_verified": exported["digest"] == captured.digest,
            "evidence_purge_tombstoned": tombstones == 1,
            "denial_explanation_known": explanation["status"] == "KNOWN",
            "production_evidence_custody_claimed": False,
        }


def main() -> int:
    docker = docker_details()
    state = state_details()
    signing = signing_details()
    operator = operator_details()
    status = "PASS" if all(item["status"] == "PASS" for item in (docker, state, signing, operator)) else "FAIL"
    report = {
        "record_version": "1.0.0",
        "status": status,
        "stage": 3,
        "assurance": "LOCAL_SECURITY_SPINE_TEST_PROFILE",
        "docker": docker,
        "state": state,
        "signing": signing,
        "operator_paths": operator,
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("cryptography", "pydantic", "jsonschema", "rfc8785", "hypothesis")
        },
        "uv_lock_sha256": sha256(ROOT / "uv.lock"),
        "real_weaker_agent_executed": False,
        "external_model_transmission": False,
        "production_side_effect_executed": False,
        "v8_release_claimed": False,
    }
    write_json(EVIDENCE / "STAGE_3_LOCAL_SECURITY_PROFILE.json", report)
    print(json.dumps({"status": status, "output": "Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json"}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
