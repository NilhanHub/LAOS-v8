from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from laos_v8.cli import main


def test_doctor_cli_is_structured(tmp_path: Path, capsys: object) -> None:
    sandbox = {
        "profile": "docker-linux-amd64-stage6-v1",
        "image": "pinned-test-image",
        "available": False,
        "detail": "docker-engine-unavailable",
        "automatic_start_attempted": False,
        "automatically_started": False,
        "startup_elapsed_ms": 0,
        "direct_host_execution_supported": False,
        "production_assurance_claimed": False,
    }
    with patch("laos_v8.cli.sandbox_diagnostic", return_value=sandbox):
        assert main(["--root", str(tmp_path), "doctor"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["status"] == "PASS"
    assert output["connected_privileged_profile_claimed"] is False


def test_migration_discovery_cli_is_read_only(capsys: object) -> None:
    root = Path(__file__).resolve().parents[2]
    archive = root / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"
    assert main(["migration-discover", str(archive)]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["mode"] == "READ_ONLY_NO_EXTRACTION"
    assert output["migration_status"] == "DISCOVERY_ONLY_NOT_MIGRATED"
