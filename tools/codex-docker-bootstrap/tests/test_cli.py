from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from codex_docker_bootstrap import cli


def trusted_tree(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    docker_root = tmp_path / "Docker" / "Docker"
    binary_root = docker_root / "resources" / "bin"
    binary_root.mkdir(parents=True)
    docker = binary_root / "docker.exe"
    compose = binary_root / "docker-compose.exe"
    desktop = docker_root / "Docker Desktop.exe"
    for item in (docker, compose, desktop):
        item.write_bytes(b"fixture")
    wrapper = tmp_path / "wrapper" / "docker.exe"
    return docker, compose, desktop, wrapper


def test_trusted_resolution_and_recursion_denial(tmp_path: Path) -> None:
    docker, compose, desktop, wrapper = trusted_tree(tmp_path)
    assert cli.resolve_real_binary("docker", program_files=tmp_path, wrapper_path=wrapper) == docker
    assert cli.resolve_real_binary("compose", program_files=tmp_path, wrapper_path=wrapper) == compose
    assert cli.resolve_real_binary("desktop", program_files=tmp_path, wrapper_path=wrapper) == desktop
    with pytest.raises(cli.BootstrapError) as recursion:
        cli.resolve_real_binary("docker", program_files=tmp_path, wrapper_path=docker)
    assert recursion.value.exit_code == cli.EXIT_UNSAFE_INSTALL


def test_missing_real_binary_is_stable(tmp_path: Path) -> None:
    with pytest.raises(cli.BootstrapError) as missing:
        cli.resolve_real_binary("docker", program_files=tmp_path, wrapper_path=tmp_path / "docker.exe")
    assert missing.value.exit_code == cli.EXIT_DOCKER_MISSING
    assert missing.value.code == "DOCKER_REAL_BINARY_MISSING"


@pytest.mark.parametrize(
    "args",
    ((), ("--version",), ("--help",), ("help",), ("completion", "powershell"), ("desktop", "stop")),
)
def test_docker_local_and_desktop_commands_bypass_start(args: tuple[str, ...]) -> None:
    assert cli._docker_bypasses_start(args) is True


def test_engine_commands_require_start() -> None:
    assert cli._docker_bypasses_start(("info",)) is False
    assert cli._docker_bypasses_start(("run", "--rm", "image")) is False
    assert cli._compose_bypasses_start(("up", "-d")) is False
    assert cli._compose_bypasses_start(("version",)) is True


def test_forward_preserves_exact_arguments_and_exit_code(tmp_path: Path) -> None:
    real = tmp_path / "docker.exe"
    arguments = ("run", "value with spaces", 'quote"value', "semi;colon", "unicode-ල")
    completed = Mock(returncode=37)
    with (
        patch.object(cli, "resolve_real_binary", return_value=real),
        patch.object(cli, "ensure_desktop"),
        patch.object(cli.subprocess, "run", return_value=completed) as run,
    ):
        assert cli._forward("docker", arguments) == 37
    run.assert_called_once_with([str(real), *arguments], check=False)


def test_start_cli_failure_is_fail_closed(tmp_path: Path) -> None:
    result = subprocess.CompletedProcess([str(tmp_path / "docker.exe")], 1, "", "desktop failed")
    with patch.object(cli.subprocess, "run", return_value=result):
        with pytest.raises(cli.BootstrapError) as failed:
            cli._start_desktop(tmp_path / "docker.exe")
    assert failed.value.exit_code == cli.EXIT_BOOTSTRAP_FAILED


def test_concurrent_ensure_starts_only_once(tmp_path: Path) -> None:
    state = {"ready": False, "starts": 0}
    state_lock = threading.Lock()

    def probe(_real: Path) -> tuple[bool, str]:
        with state_lock:
            return state["ready"], "29.5.3" if state["ready"] else ""

    def start(_real: Path) -> None:
        with state_lock:
            state["starts"] += 1
        time.sleep(0.05)
        with state_lock:
            state["ready"] = True

    results: list[cli.Readiness] = []
    with (
        patch.object(cli, "resolve_real_binary", return_value=tmp_path / "docker.exe"),
        patch.object(cli, "_probe_engine", side_effect=probe),
        patch.object(cli, "_start_desktop", side_effect=start),
        patch.object(cli, "_log_event"),
        patch.object(cli, "POLL_SECONDS", 0.01),
    ):
        threads = [
            threading.Thread(target=lambda: results.append(cli.ensure_desktop(timeout_seconds=2)))
            for _ in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert state["starts"] == 1
    assert len(results) == 2
    assert sum(item.started for item in results) == 1


def test_log_event_does_not_accept_or_record_command_arguments(tmp_path: Path) -> None:
    assert "args" not in cli._log_event.__annotations__
    with patch.object(Path, "home", return_value=tmp_path):
        cli._log_event("ready", code="DOCKER_DESKTOP_STARTED", elapsed_ms=10)
    payload = (tmp_path / ".codex/logs/docker-bootstrap.jsonl").read_text(encoding="utf-8")
    assert "DOCKER_DESKTOP_STARTED" in payload
    assert "command" not in payload and "argument" not in payload
