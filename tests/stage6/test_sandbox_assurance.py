from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from laos_v8.clean_verifier import CleanVerifier
from laos_v8.errors import SecurityError, ValidationError
from laos_v8.policy import ResourceBudget
from laos_v8.sandbox import CommandSpec, DockerSandbox, SandboxResult


def _budget() -> ResourceBudget:
    return ResourceBudget(timeout_seconds=30, memory_bytes=134_217_728, processes=16, output_bytes=65_536)


def test_command_spec_rejects_shell_environment_and_unsafe_paths(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="environment") as environment:
        CommandSpec(
            argv=("python", "-V"),
            workspace=tmp_path,
            budget=_budget(),
            environment=(("TOKEN", "secret"),),
        )
    assert environment.value.code == "SANDBOX_ENVIRONMENT_DENIED"

    with pytest.raises(ValidationError, match="working directory") as traversal:
        CommandSpec(argv=("python", "-V"), workspace=tmp_path, budget=_budget(), relative_workdir="../escape")
    assert traversal.value.code == "SANDBOX_WORKDIR_DENIED"

    with pytest.raises(ValidationError, match="shell") as shell:
        CommandSpec(argv=("sh", "-c", "echo unsafe"), workspace=tmp_path, budget=_budget())
    assert shell.value.code == "SANDBOX_SHELL_DENIED"


def test_stage6_command_mounts_source_read_only_and_output_separately(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    spec = CommandSpec(
        argv=("python", "-m", "compileall", "-q", "/workspace"),
        workspace=source,
        output_workspace=output,
        relative_workdir=".",
        budget=_budget(),
    )
    command = DockerSandbox("docker").build_spec_command(spec, name="laos-stage6-test")
    joined = "\n".join(command)
    assert "src=" + str(source.resolve()) + ",dst=/workspace,readonly" in joined
    assert "src=" + str(output.resolve()) + ",dst=/outputs" in joined
    assert "--network\nnone" in joined
    assert "--read-only" in command
    assert "--cap-drop\nALL" in joined
    assert "no-new-privileges:true" in command
    assert "/var/run/docker.sock" not in joined


class _FakeSandbox:
    assurance_profile = DockerSandbox("docker").assurance_profile

    def run_spec(self, spec: CommandSpec) -> SandboxResult:
        assert spec.workspace.name == "source"
        return SandboxResult(
            provider=self.assurance_profile.provider_id,
            image=self.assurance_profile.image,
            exit_code=0,
            stdout=b"verified",
            stderr=b"",
            stdout_digest="sha256:" + hashlib.sha256(b"verified").hexdigest(),
            stderr_digest="sha256:" + hashlib.sha256(b"").hexdigest(),
        )


def test_clean_verifier_uses_disposable_copy_and_detects_source_drift(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "app.py").write_text("print('bounded')\n", encoding="utf-8")
    verifier = CleanVerifier(_FakeSandbox())
    receipt = verifier.verify(
        candidate,
        argv=("python", "-m", "compileall", "-q", "/workspace"),
        budget=_budget(),
        criterion_ids=("criterion:stage6-sandbox",),
        source_commit="a" * 40,
        source_tree="b" * 40,
    )
    assert receipt.status == "PASS"
    assert receipt.source_digest == receipt.post_verification_source_digest
    assert receipt.verifier_workspace_id != str(candidate.resolve())
    assert (candidate / "app.py").read_text(encoding="utf-8") == "print('bounded')\n"


def test_clean_verifier_creates_control_mountpoint_only_in_disposable_copy(tmp_path: Path) -> None:
    class MountpointSandbox(_FakeSandbox):
        def run_spec(self, spec: CommandSpec) -> SandboxResult:
            assert (spec.workspace / ".laos-protected-checks").is_dir()
            return super().run_spec(spec)

    candidate = tmp_path / "candidate"
    checks = tmp_path / "checks"
    candidate.mkdir()
    checks.mkdir()
    (candidate / "app.py").write_text("pass\n", encoding="utf-8")
    receipt = CleanVerifier(MountpointSandbox()).verify(
        candidate,
        argv=("python", "/workspace/.laos-protected-checks/check.py"),
        budget=_budget(),
        criterion_ids=("criterion:stage6-protected-check",),
        source_commit="a" * 40,
        source_tree="b" * 40,
        protected_check_workspace=checks,
    )
    assert receipt.status == "PASS"
    assert not (candidate / ".laos-protected-checks").exists()


def test_clean_verifier_fails_closed_on_nonzero_check(tmp_path: Path) -> None:
    class Failing(_FakeSandbox):
        def run_spec(self, spec: CommandSpec) -> SandboxResult:
            result = super().run_spec(spec)
            return SandboxResult(
                provider=result.provider,
                image=result.image,
                exit_code=7,
                stdout=result.stdout,
                stderr=result.stderr,
                stdout_digest=result.stdout_digest,
                stderr_digest=result.stderr_digest,
            )

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "app.py").write_text("pass\n", encoding="utf-8")
    with pytest.raises(SecurityError, match="clean verification") as error:
        CleanVerifier(Failing()).verify(
            candidate,
            argv=("python", "-V"),
            budget=_budget(),
            criterion_ids=("criterion:stage6-sandbox",),
            source_commit="a" * 40,
            source_tree="b" * 40,
        )
    assert error.value.code == "CLEAN_VERIFICATION_FAILED"
