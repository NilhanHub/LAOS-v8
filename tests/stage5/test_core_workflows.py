from __future__ import annotations

import base64
import hashlib
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from laos_v8.action_engine import ActionNode
from laos_v8.canonical import canonical_json
from laos_v8.capture import (
    CAPTURE_RETURN_MEDIA_TYPE,
    AppIntelligenceReturn,
    ArchitectCaptureAcceptance,
    CaptureFact,
    FactDisposition,
    compile_continuation,
    create_capture_request,
    validate_capture_return,
)
from laos_v8.errors import AuthorizationDenied, RepositoryDrift, StateConflict
from laos_v8.new_build import (
    Blueprint,
    BlueprintAcceptance,
    CriterionNode,
    GenesisCompiler,
    NewBuildRequest,
    ProductObjective,
    RequirementNode,
    ReviewedTemplate,
    TemplateFile,
    TemplateRegistry,
)
from laos_v8.signing import ProtectedTestSigner

DIGEST = "sha256:" + "a" * 64


def run_git(root: Path, *args: str) -> str:
    executable = shutil.which("git")
    assert executable is not None
    completed = subprocess.run(  # noqa: S603 - resolved executable and fixture-controlled arguments
        [executable, "-C", str(root), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def repository(root: Path) -> Path:
    root.mkdir()
    (root / "app.txt").write_text("version one\n", encoding="utf-8")
    run_git(root, "init", "--initial-branch=main")
    run_git(root, "add", "--all")
    run_git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture.invalid", "commit", "-m", "fixture")
    return root


def current_action() -> ActionNode:
    return ActionNode(
        action_id="action:first",
        title="First governed action",
        objective="Implement the accepted first criterion",
        criterion_ids=("criterion:first",),
        allowed_files=("src/first.py",),
        permissions=("WORKSPACE_READ", "MEDIATED_WRITE"),
        max_attempts=2,
    )


def test_capture_to_continuation_round_trip_and_drift_denial(tmp_path: Path) -> None:
    repo = repository(tmp_path / "repo")
    request, before = create_capture_request(
        repo,
        capture_id="capture:one",
        project_id="project:existing",
        capture_tool="laos-read-only-capture",
        capture_tool_version="1.0.0",
        issued_at="2026-07-13T00:00:00Z",
        expires_at="2026-07-14T00:00:00Z",
    )
    assert request.repository_seal == before.seal
    assert "PRODUCT_CODE_WRITE" in request.denied_capabilities
    assert "REPOSITORY_CODE_EXECUTION" in request.denied_capabilities
    fact = CaptureFact(
        fact_id="fact:one",
        area="architecture_components_data",
        statement="The fixture contains one text component.",
        evidence_refs=("evidence:app-text-hash",),
        confidence=1.0,
        contradictions=(),
        unknowns=(),
        data_classification="internal",
        captured_at="2026-07-13T00:10:00Z",
        freshness_seconds=86400,
    )
    returned = AppIntelligenceReturn(
        capture_id=request.capture_id,
        project_id=request.project_id,
        repository_seal=request.repository_seal,
        capture_tool=request.capture_tool,
        capture_tool_version=request.capture_tool_version,
        facts=(fact,),
        completed_at="2026-07-13T00:11:00Z",
    )
    signer = ProtectedTestSigner("event_anchor")
    payload = canonical_json(returned.model_dump(mode="json"))
    envelope = signer.sign(
        payload,
        payload_type=CAPTURE_RETURN_MEDIA_TYPE,
        key_purpose="event_anchor",
        issuer="capture:broker",
        audience="architect:stage5",
        issued_at="2026-07-13T00:11:00Z",
        expires_at="2026-07-14T00:00:00Z",
    )
    validated = validate_capture_return(
        request,
        envelope,
        repository=repo,
        verifier=signer.trust_root.verifier(),
        expected_issuer="capture:broker",
        expected_audience="architect:stage5",
        now=datetime(2026, 7, 13, 1, tzinfo=UTC),
    )
    acceptance = ArchitectCaptureAcceptance(
        acceptance_id="acceptance:capture-one",
        capture_digest=validated.capture_digest,
        architect_principal="architect:nilhan-system",
        human_reviewer="Nilhan",
        dispositions=(FactDisposition(fact_id="fact:one", status="accepted", rationale="Evidence matches."),),
        preservation_rules=("preserve app.txt behavior",),
        continuation_constraints=("do not execute repository code before sandbox authorization",),
        accepted_at="2026-07-13T01:00:00Z",
    )
    continuation = compile_continuation(
        repo,
        validated,
        acceptance,
        first_action=current_action(),
        now=datetime(2026, 7, 13, 2, tzinfo=UTC),
    )
    assert continuation.base_seal == request.repository_seal
    assert continuation.accepted_fact_ids == ("fact:one",)
    assert continuation.first_action.action_id == "action:first"

    (repo / "app.txt").write_text("one-byte-drift!\n", encoding="utf-8")
    with pytest.raises(RepositoryDrift) as drift:
        compile_continuation(
            repo,
            validated,
            acceptance,
            first_action=current_action(),
            now=datetime(2026, 7, 13, 2, tzinfo=UTC),
        )
    assert drift.value.code == "REPOSITORY_SEAL_MISMATCH"


def test_capture_rejects_stale_malformed_misbound_and_incomplete_acceptance(tmp_path: Path) -> None:
    repo = repository(tmp_path / "repo")
    request, _ = create_capture_request(
        repo,
        capture_id="capture:one",
        project_id="project:existing",
        capture_tool="capture",
        capture_tool_version="1",
        issued_at="2026-07-13T00:00:00Z",
        expires_at="2026-07-13T01:00:00Z",
    )
    signer = ProtectedTestSigner("event_anchor")
    returned = AppIntelligenceReturn(
        capture_id="capture:other",
        project_id=request.project_id,
        repository_seal=request.repository_seal,
        capture_tool=request.capture_tool,
        capture_tool_version=request.capture_tool_version,
        facts=(
            CaptureFact(
                fact_id="fact:one",
                area="repository_identity_environment",
                statement="A Git repository exists.",
                evidence_refs=("evidence:git",),
                confidence=1.0,
                contradictions=(),
                unknowns=(),
                data_classification="internal",
                captured_at="2026-07-13T00:10:00Z",
                freshness_seconds=3600,
            ),
        ),
        completed_at="2026-07-13T00:11:00Z",
    )
    payload = canonical_json(returned.model_dump(mode="json"))
    envelope = signer.sign(
        payload,
        payload_type=CAPTURE_RETURN_MEDIA_TYPE,
        key_purpose="event_anchor",
        issuer="capture:broker",
        audience="architect:stage5",
        issued_at="2026-07-13T00:11:00Z",
        expires_at="2026-07-14T00:00:00Z",
    )
    with pytest.raises(AuthorizationDenied) as stale:
        validate_capture_return(
            request,
            envelope,
            repository=repo,
            verifier=signer.trust_root.verifier(),
            expected_issuer="capture:broker",
            expected_audience="architect:stage5",
            now=datetime(2026, 7, 13, 2, tzinfo=UTC),
        )
    assert stale.value.code == "CAPTURE_REQUEST_EXPIRED"
    with pytest.raises(AuthorizationDenied) as binding:
        validate_capture_return(
            request.model_copy(update={"expires_at": "2026-07-14T00:00:00Z"}),
            envelope,
            repository=repo,
            verifier=signer.trust_root.verifier(),
            expected_issuer="capture:broker",
            expected_audience="architect:stage5",
            now=datetime(2026, 7, 13, 2, tzinfo=UTC),
        )
    assert binding.value.code == "CAPTURE_RETURN_BINDING_MISMATCH"
    with pytest.raises(PydanticValidationError):
        CaptureFact(
            fact_id="fact:no-evidence",
            area="repository_identity_environment",
            statement="Unsupported material claim",
            evidence_refs=(),
            confidence=0.1,
            contradictions=(),
            unknowns=("source unknown",),
            data_classification="internal",
            captured_at="2026-07-13T00:00:00Z",
            freshness_seconds=1,
        )


def template() -> ReviewedTemplate:
    payload = b"# Governed app\n"
    return ReviewedTemplate(
        template_id="template:minimal",
        toolchain=("python@3.11",),
        dependencies=(),
        licenses=("Proprietary",),
        provenance=("review:Nilhan:2026-07-13",),
        compatible_environments=("windows-python-3.11",),
        files=(
            TemplateFile(
                path="README.md",
                content_b64=base64.b64encode(payload).decode("ascii"),
                sha256=hashlib.sha256(payload).hexdigest(),
            ),
        ),
    )


def blueprint(**objective_updates: object) -> Blueprint:
    objective_values: dict[str, object] = {
        "goals": ("Build a governed application",),
        "users": ("Nilhan",),
        "constraints": ("offline by default",),
        "non_goals": ("production deployment",),
        "data_classes": ("internal",),
        "risk_posture": "medium",
        "target_support_environment": "windows-python-3.11",
        "unresolved_decisions": (),
    }
    objective_values.update(objective_updates)
    return Blueprint(
        blueprint_id="blueprint:one",
        version=1,
        objective=ProductObjective.model_validate(objective_values, strict=True),
        requirements=(
            RequirementNode(
                requirement_id="requirement:one",
                statement="Create the first module",
                depends_on=(),
            ),
        ),
        criteria=(
            CriterionNode(
                criterion_id="criterion:first",
                requirement_id="requirement:one",
                statement="Module exists",
            ),
        ),
        security_boundaries=("no network",),
        budget=("one file",),
        initial_scope=("src/first.py",),
    )


def build_inputs() -> tuple[ReviewedTemplate, Blueprint, NewBuildRequest, BlueprintAcceptance]:
    selected = template()
    plan = blueprint()
    request = NewBuildRequest(
        request_id="new-build:one",
        project_id="project:new-app",
        blueprint_digest=plan.digest,
        template_digest=selected.digest,
        initial_action=current_action(),
    )
    acceptance = BlueprintAcceptance(
        acceptance_id="acceptance:blueprint-one",
        blueprint_digest=plan.digest,
        architect_proposal_envelope_digest=DIGEST,
        human_reviewer="Nilhan",
        accepted_at="2026-07-13T00:00:00Z",
        expires_at="2026-07-14T00:00:00Z",
    )
    return selected, plan, request, acceptance


def test_new_build_round_trip_is_sealed_and_idempotent(tmp_path: Path) -> None:
    selected, plan, request, acceptance = build_inputs()
    destination = tmp_path / "new-app"
    compiler = GenesisCompiler(TemplateRegistry((selected,)), tmp_path / "control")
    first = compiler.compile(
        request,
        plan,
        acceptance,
        destination=destination,
        now="2026-07-13T01:00:00Z",
    )
    second = compiler.compile(
        request,
        plan,
        acceptance,
        destination=destination,
        now="2026-07-13T01:00:00Z",
    )
    assert first == second
    assert run_git(destination, "rev-parse", "HEAD") == first.genesis_commit
    assert first.first_action.action_id == "action:first"
    assert (destination / ".laos" / "blueprint.json").is_file()
    assert first.source_seal != first.base_seal


def test_new_build_blocks_stale_substitution_collision_and_untrusted_template(tmp_path: Path) -> None:
    selected, plan, request, acceptance = build_inputs()
    compiler = GenesisCompiler(TemplateRegistry((selected,)), tmp_path / "control")
    with pytest.raises(AuthorizationDenied) as stale:
        compiler.compile(
            request,
            plan,
            acceptance,
            destination=tmp_path / "stale",
            now="2026-07-15T00:00:00Z",
        )
    assert stale.value.code == "GENESIS_ACCEPTANCE_EXPIRED"
    with pytest.raises(AuthorizationDenied) as untrusted:
        compiler.compile(
            request.model_copy(update={"template_digest": DIGEST}),
            plan,
            acceptance,
            destination=tmp_path / "untrusted",
            now="2026-07-13T01:00:00Z",
        )
    assert untrusted.value.code == "TEMPLATE_UNTRUSTED"

    destination = tmp_path / "app"
    compiler.compile(request, plan, acceptance, destination=destination, now="2026-07-13T01:00:00Z")
    conflicting = request.model_copy(update={"request_id": "new-build:changed"})
    with pytest.raises(StateConflict) as conflict:
        compiler.compile(conflicting, plan, acceptance, destination=destination, now="2026-07-13T01:00:00Z")
    assert conflict.value.code == "GENESIS_INTENT_CONFLICT"
    (destination / "README.md").write_text("substituted\n", encoding="utf-8")
    with pytest.raises(RepositoryDrift):
        compiler.compile(request, plan, acceptance, destination=destination, now="2026-07-13T01:00:00Z")


def test_blueprint_and_template_fail_closed_on_missing_truth() -> None:
    with pytest.raises(PydanticValidationError):
        blueprint(unresolved_decisions=("Choose authentication",))
    with pytest.raises(PydanticValidationError):
        Blueprint(
            blueprint_id="blueprint:orphan",
            version=1,
            objective=blueprint().objective,
            requirements=(RequirementNode(requirement_id="requirement:one", statement="Required", depends_on=()),),
            criteria=(
                CriterionNode(
                    criterion_id="criterion:one",
                    requirement_id="requirement:missing",
                    statement="Orphan",
                ),
            ),
            security_boundaries=("deny network",),
            budget=("bounded",),
            initial_scope=("src/one.py",),
        )
    payload = b"malicious"
    with pytest.raises(PydanticValidationError):
        TemplateFile(
            path=".git/config",
            content_b64=base64.b64encode(payload).decode("ascii"),
            sha256=hashlib.sha256(payload).hexdigest(),
        )
    with pytest.raises(PydanticValidationError):
        TemplateFile(
            path="README.md",
            content_b64=base64.b64encode(payload).decode("ascii"),
            sha256="0" * 64,
        )


@pytest.mark.parametrize(
    "path",
    (".GIT/config", ".Git/config", ".LAOS/state.json", "README.md.", "README.md ", "NUL.txt"),
)
def test_template_rejects_windows_control_aliases(path: str) -> None:
    payload = b"bounded"
    with pytest.raises(PydanticValidationError):
        TemplateFile(
            path=path,
            content_b64=base64.b64encode(payload).decode("ascii"),
            sha256=hashlib.sha256(payload).hexdigest(),
        )


def test_template_rejects_case_insensitive_path_collisions() -> None:
    payload = b"bounded"
    encoded = base64.b64encode(payload).decode("ascii")
    digest = hashlib.sha256(payload).hexdigest()
    with pytest.raises(PydanticValidationError):
        ReviewedTemplate(
            template_id="template:collision",
            toolchain=("python@3.11",),
            dependencies=(),
            licenses=("Proprietary",),
            provenance=("review:Nilhan",),
            compatible_environments=("windows-python-3.11",),
            files=(
                TemplateFile(path="README.md", content_b64=encoded, sha256=digest),
                TemplateFile(path="readme.md", content_b64=encoded, sha256=digest),
            ),
        )


def test_genesis_ignores_host_git_filter_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = tmp_path / "filter-executed.txt"
    filter_script = tmp_path / "filter.py"
    filter_script.write_text(
        "import pathlib, sys\npathlib.Path(sys.argv[1]).write_text('executed')\n"
        "sys.stdout.buffer.write(sys.stdin.buffer.read())\n",
        encoding="utf-8",
    )
    git_config = tmp_path / "malicious.gitconfig"
    python_path = Path(sys.executable).as_posix()
    script_path = filter_script.as_posix()
    marker_path = marker.as_posix()
    git_config.write_text(
        f'[filter "evil"]\n\tclean = "{python_path}" "{script_path}" "{marker_path}"\n\trequired = true\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(git_config))
    attributes = b"*.txt filter=evil\n"
    payload = b"safe payload\n"
    selected = ReviewedTemplate(
        template_id="template:git-filter",
        toolchain=("python@3.11",),
        dependencies=(),
        licenses=("Proprietary",),
        provenance=("review:Nilhan",),
        compatible_environments=("windows-python-3.11",),
        files=(
            TemplateFile(
                path=".gitattributes",
                content_b64=base64.b64encode(attributes).decode("ascii"),
                sha256=hashlib.sha256(attributes).hexdigest(),
            ),
            TemplateFile(
                path="payload.txt",
                content_b64=base64.b64encode(payload).decode("ascii"),
                sha256=hashlib.sha256(payload).hexdigest(),
            ),
        ),
    )
    plan = blueprint()
    request = NewBuildRequest(
        request_id="new-build:git-filter",
        project_id="project:git-filter",
        blueprint_digest=plan.digest,
        template_digest=selected.digest,
        initial_action=current_action(),
    )
    acceptance = BlueprintAcceptance(
        acceptance_id="acceptance:git-filter",
        blueprint_digest=plan.digest,
        architect_proposal_envelope_digest=DIGEST,
        human_reviewer="Nilhan",
        accepted_at="2026-07-13T00:00:00Z",
        expires_at="2026-07-14T00:00:00Z",
    )
    GenesisCompiler(TemplateRegistry((selected,)), tmp_path / "control").compile(
        request,
        plan,
        acceptance,
        destination=tmp_path / "safe-app",
        now="2026-07-13T01:00:00Z",
    )
    assert not marker.exists()
