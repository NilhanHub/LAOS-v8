"""Digest-pinned, network-denied Docker sandbox provider."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from .errors import ResourceLimitError, SecurityError
from .policy import ResourceBudget

DOCKER_IMAGE = (
    "docker.io/library/python:3.14.3-alpine3.23@sha256:581c14606911610c6b61e569714e92a726c1ef2437dd034824f644f6d9df6e9d"
)
SANDBOX_PROFILE = "docker-linux-amd64-stage3-v1"


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


class DockerSandbox:
    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("docker") or ""

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

    def run(self, request: SandboxRequest) -> SandboxResult:
        available, detail = self.availability()
        if not available:
            raise SecurityError(
                "qualifying Docker sandbox is unavailable",
                code="SANDBOX_UNAVAILABLE",
                context={"detail": detail},
            )
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
            [self.executable, "ps", "-q", "--filter", "label=dev.nilhan.laos.stage3=true"],
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
