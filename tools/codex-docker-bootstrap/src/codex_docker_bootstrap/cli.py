"""Argument-preserving Docker and Docker Compose launchers for Windows."""

from __future__ import annotations

import json
import msvcrt
import os
import subprocess
import sys
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

EXIT_BOOTSTRAP_FAILED = 125
EXIT_UNSAFE_INSTALL = 126
EXIT_DOCKER_MISSING = 127
START_COMMAND_TIMEOUT_SECONDS = 150
TOTAL_START_TIMEOUT_SECONDS = 180
PROBE_TIMEOUT_SECONDS = 15
POLL_SECONDS = 2.0
MAX_LOG_BYTES = 1_048_576


class BootstrapError(RuntimeError):
    def __init__(self, code: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class Readiness:
    status: str
    started: bool
    server_version: str
    desktop_status: str
    elapsed_ms: int


def _program_files() -> Path:
    value = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles")
    if not value:
        raise BootstrapError("DOCKER_TRUSTED_ROOT_MISSING", "Program Files is unavailable", EXIT_UNSAFE_INSTALL)
    return Path(value)


def _trusted_paths(kind: str, *, program_files: Path | None = None) -> tuple[Path, ...]:
    root = program_files or _program_files()
    docker_root = root / "Docker" / "Docker"
    if kind == "docker":
        return (docker_root / "resources" / "bin" / "docker.exe",)
    if kind == "compose":
        return (docker_root / "resources" / "bin" / "docker-compose.exe",)
    if kind == "desktop":
        return (docker_root / "Docker Desktop.exe",)
    raise ValueError(f"unknown Docker binary kind: {kind}")


def resolve_real_binary(
    kind: str,
    *,
    program_files: Path | None = None,
    wrapper_path: Path | None = None,
) -> Path:
    wrapper = (wrapper_path or Path(sys.argv[0])).resolve(strict=False)
    for candidate in _trusted_paths(kind, program_files=program_files):
        if not candidate.is_file():
            continue
        resolved = candidate.resolve(strict=True)
        if resolved == wrapper:
            raise BootstrapError("DOCKER_WRAPPER_RECURSION", "Docker wrapper recursion denied", EXIT_UNSAFE_INSTALL)
        return resolved
    raise BootstrapError("DOCKER_REAL_BINARY_MISSING", f"trusted {kind} executable is missing", EXIT_DOCKER_MISSING)


def _probe_engine(real_docker: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(  # noqa: S603 - trusted absolute executable with fixed arguments
            [str(real_docker), "info", "--format", "{{.ServerVersion}}"],
            text=True,
            capture_output=True,
            check=False,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    version = completed.stdout.strip()
    return completed.returncode == 0 and bool(version), version


def _log_event(status: str, *, code: str, elapsed_ms: int) -> None:
    log = Path.home() / ".codex" / "logs" / "docker-bootstrap.jsonl"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists() and log.stat().st_size >= MAX_LOG_BYTES:
            rotated = log.with_suffix(".jsonl.1")
            if rotated.exists():
                rotated.unlink()
            log.replace(rotated)
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "status": status,
            "code": code,
            "elapsed_ms": elapsed_ms,
        }
        with log.open("a", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError:
        pass


@contextmanager
def _startup_lock(timeout_seconds: int) -> Iterator[None]:
    path = Path.home() / ".codex" / "state" / "docker-bootstrap.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    if path.stat().st_size == 0:
        handle.write(b"0")
        handle.flush()
    deadline = time.monotonic() + timeout_seconds
    acquired = False
    try:
        while time.monotonic() < deadline:
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                acquired = True
                break
            except OSError:
                time.sleep(0.25)
        if not acquired:
            raise BootstrapError("DOCKER_START_MUTEX_TIMEOUT", "Docker startup lock timed out", EXIT_BOOTSTRAP_FAILED)
        yield
    finally:
        if acquired:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        handle.close()


def _desktop_cli_unavailable(completed: subprocess.CompletedProcess[str]) -> bool:
    combined = f"{completed.stdout}\n{completed.stderr}".casefold()
    return "unknown command" in combined or "is not a docker command" in combined


def _start_desktop(real_docker: Path) -> None:
    try:
        completed = subprocess.run(  # noqa: S603 - trusted absolute executable with fixed arguments
            [str(real_docker), "desktop", "start", "--timeout", str(START_COMMAND_TIMEOUT_SECONDS)],
            text=True,
            capture_output=True,
            check=False,
            timeout=START_COMMAND_TIMEOUT_SECONDS + 5,
        )
    except subprocess.TimeoutExpired as exc:
        raise BootstrapError(
            "DOCKER_DESKTOP_START_TIMEOUT",
            "Docker Desktop start timed out",
            EXIT_BOOTSTRAP_FAILED,
        ) from exc
    except OSError as exc:
        raise BootstrapError(
            "DOCKER_DESKTOP_START_FAILED",
            "Docker Desktop start failed",
            EXIT_BOOTSTRAP_FAILED,
        ) from exc
    if completed.returncode == 0:
        return
    if not _desktop_cli_unavailable(completed):
        raise BootstrapError("DOCKER_DESKTOP_START_FAILED", "Docker Desktop start failed", EXIT_BOOTSTRAP_FAILED)
    desktop = resolve_real_binary("desktop")
    try:
        subprocess.Popen(  # noqa: S603 - trusted absolute GUI executable and no shell
            [str(desktop)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
    except OSError as exc:
        raise BootstrapError(
            "DOCKER_DESKTOP_LAUNCH_FAILED",
            "Docker Desktop launch failed",
            EXIT_BOOTSTRAP_FAILED,
        ) from exc


def ensure_desktop(*, timeout_seconds: int = TOTAL_START_TIMEOUT_SECONDS) -> Readiness:
    started_at = time.monotonic()
    real_docker = resolve_real_binary("docker")
    ready, version = _probe_engine(real_docker)
    if ready:
        return Readiness("ready", False, version, "running", int((time.monotonic() - started_at) * 1000))
    try:
        with _startup_lock(timeout_seconds):
            ready, version = _probe_engine(real_docker)
            if ready:
                return Readiness("ready", False, version, "running", int((time.monotonic() - started_at) * 1000))
            _start_desktop(real_docker)
            deadline = started_at + timeout_seconds
            while time.monotonic() < deadline:
                ready, version = _probe_engine(real_docker)
                if ready:
                    elapsed = int((time.monotonic() - started_at) * 1000)
                    _log_event("ready", code="DOCKER_DESKTOP_STARTED", elapsed_ms=elapsed)
                    return Readiness("ready", True, version, "running", elapsed)
                time.sleep(POLL_SECONDS)
            raise BootstrapError(
                "DOCKER_ENGINE_READY_TIMEOUT",
                "Docker engine readiness timed out",
                EXIT_BOOTSTRAP_FAILED,
            )
    except BootstrapError as exc:
        _log_event("failed", code=exc.code, elapsed_ms=int((time.monotonic() - started_at) * 1000))
        raise


def _docker_bypasses_start(args: Sequence[str]) -> bool:
    if not args:
        return True
    return args[0] in {"--help", "-h", "--version", "-v", "help", "completion", "desktop"}


def _compose_bypasses_start(args: Sequence[str]) -> bool:
    if not args:
        return True
    return args[0] in {"--help", "-h", "--version", "version", "help", "completion"}


def _forward(kind: str, args: Sequence[str]) -> int:
    try:
        real = resolve_real_binary(kind)
        bypass = _docker_bypasses_start(args) if kind == "docker" else _compose_bypasses_start(args)
        if not bypass:
            ensure_desktop()
        completed = subprocess.run([str(real), *args], check=False)  # noqa: S603 - trusted executable, exact argv
        return completed.returncode
    except BootstrapError as exc:
        print(f"codex-docker-bootstrap: {exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError:
        print("codex-docker-bootstrap: DOCKER_EXECUTION_FAILED", file=sys.stderr)
        return EXIT_BOOTSTRAP_FAILED


def docker_main() -> int:
    return _forward("docker", tuple(sys.argv[1:]))


def compose_main() -> int:
    return _forward("compose", tuple(sys.argv[1:]))


def ensure_main() -> int:
    json_output = "--json" in sys.argv[1:]
    try:
        readiness = ensure_desktop()
    except BootstrapError as exc:
        payload = {"status": "failed", "code": exc.code, "message": str(exc)}
        if json_output:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"{exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code
    if json_output:
        print(json.dumps(asdict(readiness), sort_keys=True))
    else:
        print(f"Docker Desktop is ready (server {readiness.server_version}).")
    return 0
