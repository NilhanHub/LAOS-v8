from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from laos_v8.cli import main
from laos_v8.evidence import EvidenceBroker
from laos_v8.state import CanonicalState


def output(capsys: Any) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def test_denial_backup_restore_and_trust_recovery_cli(tmp_path: Path, capsys: Any) -> None:
    state_path = tmp_path / "state.sqlite3"
    with CanonicalState(state_path) as state:
        state.create_aggregate("task:cli", "task", "planned", {}, "actor:architect")
        epoch = state.set_emergency_stop("actor:architect", "operator test")

    assert main(["explain-denial", "CAPSULE_REPLAY_DENIED"]) == 0
    assert output(capsys)["status"] == "KNOWN"

    backup = tmp_path / "backup.sqlite3"
    assert main(["backup", str(state_path), str(backup)]) == 0
    assert output(capsys)["status"] == "PASS"
    restored = tmp_path / "restored.sqlite3"
    assert main(["restore", str(backup), str(restored)]) == 0
    assert output(capsys)["status"] == "PASS"

    assert (
        main(
            [
                "trust-recover",
                str(state_path),
                "--actor",
                "actor:architect",
                "--reason",
                "reviewed recovery",
                "--expected-epoch",
                str(epoch),
            ]
        )
        == 0
    )
    assert output(capsys)["trust_epoch"] == epoch + 1


def test_evidence_export_and_purge_cli(tmp_path: Path, capsys: Any, digest: str) -> None:
    state_path = tmp_path / "state.sqlite3"
    store = tmp_path / "store"
    with CanonicalState(state_path) as state:
        captured = EvidenceBroker(store, state).capture(
            b"cli proof",
            result_seal=digest,
            criterion_id="criterion:cli",
            classification="internal",
            collector="test",
            actor_id="actor:verifier",
        )
    destination = tmp_path / "export"
    assert (
        main(
            [
                "evidence-export",
                str(state_path),
                str(store),
                captured.digest,
                str(destination),
                "--classification",
                "internal",
                "--actor",
                "actor:operator",
            ]
        )
        == 0
    )
    assert output(capsys)["status"] == "PASS"
    assert (
        main(
            [
                "evidence-purge",
                str(state_path),
                str(store),
                captured.digest,
                "--classification",
                "internal",
                "--actor",
                "actor:operator",
                "--reason",
                "retention decision",
                "--confirm-digest",
                captured.digest,
            ]
        )
        == 0
    )
    assert output(capsys)["purged_digest"] == captured.digest
