"""Digest-pinned, network-denied Docker sandbox provider."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from .errors import ResourceLimitError, SecurityError, ValidationError
from .policy import ResourceBudget
from .safe_paths import REPARSE_POINT

DOCKER_IMAGE = (
    "docker.io/library/python:3.14.3-alpine3.23@sha256:581c14606911610c6b61e569714e92a726c1ef2437dd034824f644f6d9df6e9d"
)
SANDBOX_PROFILE = "docker-linux-amd64-stage6-v1"
DOCKER_START_TIMEOUT_SECONDS = 180
DOCKER_START_COMMAND_TIMEOUT_SECONDS = 150
DOCKER_POLL_SECONDS = 2.0
ALLOWED_ENVIRONMENT = frozenset({"LANG", "LC_ALL", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "TZ"})


class SandboxAssuranceProfile(BaseModel):
    """Machine-readable assurance boundary for a sandbox provider."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: str = Field(default="1.0.0", pattern=r"^1\.0\.0$")
    provider_id: str
    image: str
    maximum_risk: str = Field(default="moderate", pattern=r"^moderate$")
    source_read_only: bool = True
    root_filesystem_read_only: bool = True
    network: str = Field(default="none", pattern=r"^none$")
    unrestricted_host_fallback: bool = False
    real_credentials: bool = False


@dataclass(frozen=True, slots=True)
class CommandSpec:
    """Structured Stage 6 command contract; shell strings are never accepted."""

    argv: tuple[str, ...]
    workspace: Path
    budget: ResourceBudget
    relative_workdir: str = "."
    output_workspace: Path | None = None
    protected_check_workspace: Path | None = None
    execution_role: Literal["builder", "verifier"] = "builder"
    environment: tuple[tuple[str, str], ...] = ()
    record_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.record_version != "1.0.0":
            raise ValidationError("command specification version is unsupported", code="SANDBOX_SPEC_VERSION")
        if not self.argv or any(not isinstance(item, str) or not item or "\x00" in item for item in self.argv):
            raise ValidationError("sandbox command is empty or invalid", code="SANDBOX_COMMAND_EMPTY")
        if self.argv[0].casefold() in {"sh", "bash", "cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh"}:
            raise ValidationError("shell execution is denied by the Stage 6 profile", code="SANDBOX_SHELL_DENIED")
        if self.relative_workdir != ".":
            candidate = self.relative_workdir.replace("\\", "/")
            parts = candidate.split("/")
            if candidate.startswith("/") or ":" in candidate or any(part in {"", ".", ".."} for part in parts):
                raise ValidationError("sandbox working directory is unsafe", code="SANDBOX_WORKDIR_DENIED")
        seen: set[str] = set()
        for name, value in self.environment:
            if name not in ALLOWED_ENVIRONMENT or name in seen or "\x00" in value or len(value) > 4096:
                raise ValidationError("sandbox environment entry is denied", code="SANDBOX_ENVIRONMENT_DENIED")
            seen.add(name)
        if self.protected_check_workspace is not None and self.execution_role != "verifier":
            raise ValidationError(
                "protected checks may be mounted only by the clean verifier",
                code="PROTECTED_CHECK_MOUNT_DENIED",
            )


@runtime_checkable
class SandboxProvider(Protocol):
    assurance_profile: SandboxAssuranceProfile

    def run_spec(self, spec: CommandSpec) -> SandboxResult: ...


def _default_docker_executable() -> str:
    if os.name == "nt":
        program_files = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles")
        if program_files:
            trusted = Path(program_files) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
            if trusted.is_file():
                return str(trusted.resolve(strict=True))
    return shutil.which("docker") or ""


def _desktop_executable() -> Path | None:
    program_files = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles")
    if not program_files:
        return None
    candidate = Path(program_files) / "Docker" / "Docker" / "Docker Desktop.exe"
    return candidate.resolve(strict=True) if candidate.is_file() else None


@contextmanager
def _docker_startup_lock(timeout_seconds: int) -> Iterator[None]:
    if os.name != "nt":
        yield
        return
    import msvcrt

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
            raise SecurityError(
                "Docker Desktop startup lock timed out",
                code="SANDBOX_UNAVAILABLE",
                context={"detail": "docker-startup-lock-timeout", "automatic_start_attempted": True},
            )
        yield
    finally:
        if acquired:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        handle.close()


@dataclass(frozen=True, slots=True)
class SandboxRequest:
    argv: tuple[str, ...]
    workspace: Path
    budget: ResourceBudget


@dataclass(frozen=True, slots=True)
class SandboxResult:
    provider: str
    image: str
    exit_code: int
    stdout: bytes
    stderr: bytes
    stdout_digest: str
    stderr_digest: str
    network: str = "none"
    root_filesystem: str = "read-only"


@dataclass(frozen=True, slots=True)
class DockerReadiness:
    available: bool
    started: bool
    server_version: str
    detail: str
    elapsed_ms: int


class DockerSandbox:
    assurance_profile = SandboxAssuranceProfile(provider_id=SANDBOX_PROFILE, image=DOCKER_IMAGE)

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or _default_docker_executable()

    def availability(self) -> tuple[bool, str]:
        if not self.executable:
            return False, "docker-cli-unavailable"
        completed = subprocess.run(  # noqa: S603 - resolved Docker executable and fixed info request
            [self.executable, "info", "--format", "{{.ServerVersion}}"],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        if completed.returncode:
            return False, "docker-engine-unavailable"
        return True, completed.stdout.strip()

    def ensure_available(self, *, timeout_seconds: int = DOCKER_START_TIMEOUT_SECONDS) -> DockerReadiness:
        started_at = time.monotonic()
        available, detail = self.availability()
        if available:
            return DockerReadiness(True, False, detail, "already-running", int((time.monotonic() - started_at) * 1000))
        if not self.executable:
            raise SecurityError(
                "Docker CLI is unavailable",
                code="SANDBOX_UNAVAILABLE",
                context={"detail": "docker-cli-unavailable", "automatic_start_attempted": False},
            )
        if os.name != "nt":
            raise SecurityError(
                "qualifying Docker engine is unavailable",
                code="SANDBOX_UNAVAILABLE",
                context={"detail": detail, "automatic_start_attempted": False},
            )
        with _docker_startup_lock(timeout_seconds):
            available, detail = self.availability()
            if available:
                return DockerReadiness(
                    True,
                    False,
                    detail,
                    "started-by-concurrent-controller",
                    int((time.monotonic() - started_at) * 1000),
                )
            return self._start_windows_desktop(started_at=started_at, timeout_seconds=timeout_seconds)

    def _start_windows_desktop(self, *, started_at: float, timeout_seconds: int) -> DockerReadiness:
        command_timeout = max(1, min(DOCKER_START_COMMAND_TIMEOUT_SECONDS, timeout_seconds - 30))
        try:
            completed = subprocess.run(  # noqa: S603 - resolved executable and fixed Desktop start arguments
                [self.executable, "desktop", "start", "--timeout", str(command_timeout)],
                text=True,
                capture_output=True,
                check=False,
                timeout=command_timeout + 5,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SecurityError(
                "Docker Desktop automatic start failed",
                code="SANDBOX_UNAVAILABLE",
                context={"detail": "docker-desktop-start-failed", "automatic_start_attempted": True},
            ) from exc
        if completed.returncode:
            combined = f"{completed.stdout}\n{completed.stderr}".casefold()
            unavailable = "unknown command" in combined or "is not a docker command" in combined
            desktop = _desktop_executable() if unavailable else None
            if desktop is None:
                raise SecurityError(
                    "Docker Desktop automatic start failed",
                    code="SANDBOX_UNAVAILABLE",
                    context={"detail": "docker-desktop-start-failed", "automatic_start_attempted": True},
                )
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
                raise SecurityError(
                    "Docker Desktop automatic launch failed",
                    code="SANDBOX_UNAVAILABLE",
                    context={"detail": "docker-desktop-launch-failed", "automatic_start_attempted": True},
                ) from exc
        deadline = started_at + timeout_seconds
        while time.monotonic() < deadline:
            available, detail = self.availability()
            if available:
                return DockerReadiness(
                    True,
                    True,
                    detail,
                    "automatically-started",
                    int((time.monotonic() - started_at) * 1000),
                )
            time.sleep(DOCKER_POLL_SECONDS)
        raise SecurityError(
            "Docker engine did not become ready after automatic startup",
            code="SANDBOX_UNAVAILABLE",
            context={"detail": "docker-engine-ready-timeout", "automatic_start_attempted": True},
        )

    def build_command(self, request: SandboxRequest, *, name: str) -> list[str]:
        workspace = request.workspace.resolve(strict=True)
        if not workspace.is_dir() or "," in str(workspace):
            raise SecurityError("sandbox workspace path is unsupported", code="SANDBOX_WORKSPACE_DENIED")
        if not request.argv:
            raise SecurityError("sandbox command is empty", code="SANDBOX_COMMAND_EMPTY")
        budget = request.budget
        return [
            self.executable,
            "run",
            "--rm",
            "--name",
            name,
            "--label",
            "dev.nilhan.laos.stage3=true",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            str(budget.processes),
            "--memory",
            str(budget.memory_bytes),
            "--cpus",
            str(budget.cpu_count),
            "--user",
            "65534:65534",
            "--workdir",
            "/workspace",
            "--mount",
            f"type=bind,src={workspace},dst=/workspace,readonly",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=67108864",  # noqa: S108 - isolated container tmpfs
            DOCKER_IMAGE,
            *request.argv,
        ]

    @staticmethod
    def _safe_workspace(path: Path, *, code: str) -> Path:
        resolved = path.resolve(strict=True)
        if not resolved.is_dir() or "," in str(resolved):
            raise SecurityError("sandbox workspace path is unsupported", code=code)
        current = resolved
        while True:
            info = current.lstat()
            if current.is_symlink() or getattr(info, "st_file_attributes", 0) & REPARSE_POINT:
                raise SecurityError("sandbox workspace contains a link or reparse point", code=code)
            if current.parent == current:
                break
            current = current.parent
        return resolved

    def build_spec_command(self, spec: CommandSpec, *, name: str) -> list[str]:
        workspace = self._safe_workspace(spec.workspace, code="SANDBOX_WORKSPACE_DENIED")
        workdir = "/workspace" if spec.relative_workdir == "." else f"/workspace/{spec.relative_workdir}"
        command = [
            self.executable,
            "run",
            "--rm",
            "--init",
            "--name",
            name,
            "--label",
            "dev.nilhan.laos.stage6=true",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            str(spec.budget.processes),
            "--memory",
            str(spec.budget.memory_bytes),
            "--cpus",
            str(spec.budget.cpu_count),
            "--user",
            "65534:65534",
            "--workdir",
            workdir,
            "--mount",
            f"type=bind,src={workspace},dst=/workspace,readonly",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=67108864",  # noqa: S108 - isolated container tmpfs
        ]
        if spec.output_workspace is not None:
            output = self._safe_workspace(spec.output_workspace, code="SANDBOX_OUTPUT_WORKSPACE_DENIED")
            command.extend(("--mount", f"type=bind,src={output},dst=/outputs"))
        if spec.protected_check_workspace is not None:
            checks = self._safe_workspace(spec.protected_check_workspace, code="PROTECTED_CHECK_WORKSPACE_DENIED")
            command.extend(("--mount", f"type=bind,src={checks},dst=/protected_checks,readonly"))
        for name_key, value in spec.environment:
            command.extend(("--env", f"{name_key}={value}"))
        command.extend((DOCKER_IMAGE, *spec.argv))
        return command

    def run_spec(self, spec: CommandSpec) -> SandboxResult:
        self.ensure_available()
        name = f"laos-stage6-{uuid.uuid4().hex[:16]}"
        command = self.build_spec_command(spec, name=name)
        try:
            completed = subprocess.run(  # noqa: S603 - structured Docker argv; no shell and no host fallback
                command,
                capture_output=True,
                check=False,
                timeout=spec.budget.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            subprocess.run(  # noqa: S603 - generated container name and fixed emergency cleanup
                [self.executable, "rm", "-f", name], capture_output=True, check=False, timeout=15
            )
            raise ResourceLimitError("sandbox command timed out", code="SANDBOX_TIMEOUT") from exc
        stdout = completed.stdout[: spec.budget.output_bytes]
        stderr = completed.stderr[: spec.budget.output_bytes]
        if len(completed.stdout) > len(stdout) or len(completed.stderr) > len(stderr):
            raise ResourceLimitError("sandbox output limit exceeded", code="SANDBOX_OUTPUT_LIMIT")
        return SandboxResult(
            provider=self.assurance_profile.provider_id,
            image=self.assurance_profile.image,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            stdout_digest=f"sha256:{hashlib.sha256(stdout).hexdigest()}",
            stderr_digest=f"sha256:{hashlib.sha256(stderr).hexdigest()}",
        )

    def run(self, request: SandboxRequest) -> SandboxResult:
        self.ensure_available()
        name = f"laos-stage3-{uuid.uuid4().hex[:16]}"
        command = self.build_command(request, name=name)
        try:
            completed = subprocess.run(  # noqa: S603 - fully structured broker command; shell is never used
                command,
                capture_output=True,
                check=False,
                timeout=request.budget.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            subprocess.run(  # noqa: S603 - fixed emergency cleanup for generated container name
                [self.executable, "rm", "-f", name], capture_output=True, check=False, timeout=15
            )
            raise ResourceLimitError("sandbox command timed out", code="SANDBOX_TIMEOUT") from exc
        stdout = completed.stdout[: request.budget.output_bytes]
        stderr = completed.stderr[: request.budget.output_bytes]
        if len(completed.stdout) > len(stdout) or len(completed.stderr) > len(stderr):
            raise ResourceLimitError("sandbox output limit exceeded", code="SANDBOX_OUTPUT_LIMIT")
        return SandboxResult(
            SANDBOX_PROFILE,
            DOCKER_IMAGE,
            completed.returncode,
            stdout,
            stderr,
            f"sha256:{hashlib.sha256(stdout).hexdigest()}",
            f"sha256:{hashlib.sha256(stderr).hexdigest()}",
        )

    def emergency_terminate(self) -> int:
        if not self.executable:
            return 0
        listed = subprocess.run(  # noqa: S603 - fixed label-filtered Docker query
            [self.executable, "ps", "-q", "--filter", "label=dev.nilhan.laos.stage6=true"],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        identifiers = [item for item in listed.stdout.splitlines() if item]
        if identifiers:
            subprocess.run(  # noqa: S603 - IDs came from the fixed daemon label query
                [self.executable, "rm", "-f", *identifiers], capture_output=True, check=False, timeout=30
            )
        return len(identifiers)
