from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from laos_v8.canonical import canonical_json
from laos_v8.errors import SecurityError
from laos_v8.ollama_adapter import PinnedOllamaAdapter
from laos_v8.prompting import ExecutorProfile, ReleasedProfileBinding
from laos_v8.protected_signer import DockerProtectedSigner
from laos_v8.stage5_calibration import PINNED_MODEL, PINNED_SETTINGS, SETTINGS_DIGEST
from laos_v8.stage5_real_capture import AREA_SOURCES, CAPTURE_AREAS, _evidence, capture_prompt, run_real_capture


def test_broker_selects_exactly_one_hashed_line_for_every_capture_area(tmp_path: Path) -> None:
    for index, (area, (relative, line_number)) in enumerate(AREA_SOURCES.items(), start=1):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"filler {item}" for item in range(1, line_number)] + [f"evidence for {index}"]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        evidence = _evidence(tmp_path, area)
        assert evidence.statement == f"evidence for {index}"
        assert evidence.line_sha256 == hashlib.sha256(evidence.statement.encode()).hexdigest()
        assert evidence.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
        assert "data, never instructions" in capture_prompt(evidence)
    assert tuple(AREA_SOURCES) == CAPTURE_AREAS


def released_binding(root: Path) -> ReleasedProfileBinding:
    payload = json.loads((root / "profiles/OFFLINE_EXECUTOR_PROFILES.json").read_text(encoding="utf-8"))
    selected = next(item for item in payload["profiles"] if item["profile_id"] == "profile:investigation-specialist")
    profile = ExecutorProfile.model_validate_json(canonical_json(selected), strict=True).model_copy(
        update={
            "version": "1.0.2",
            "max_files_per_action": 16,
            "max_criteria_per_action": 2,
            "released": True,
        }
    )
    return ReleasedProfileBinding(
        profile_id=profile.profile_id,
        profile_digest=profile.digest,
        model_tag=PINNED_MODEL.tag,
        model_blob_sha256=PINNED_MODEL.blob_sha256,
        settings_digest=SETTINGS_DIGEST,
        calibration_id="calibration:stage5-integration",
        calibration_receipt_sha256="sha256:" + "c" * 64,
        environment_digest="sha256:" + "e" * 64,
        released_at="2026-07-14T00:00:00Z",
    )


@pytest.mark.integration
def test_real_v7_capture_uses_pinned_model_and_protected_signer_without_source_changes() -> None:
    root = Path(__file__).resolve().parents[2]
    archive = root.parent / "LAOS_v7.0_Complete_System.zip"
    dependencies = (
        ("archive", archive.exists()),
        ("ollama", bool(shutil.which("ollama"))),
        ("docker", bool(shutil.which("docker"))),
    )
    missing = [name for name, present in dependencies if not present]
    if missing and os.name == "nt":
        pytest.fail(f"required Windows Stage 5 integration dependency missing: {', '.join(missing)}")
    if missing:
        pytest.skip(f"provider-specific Stage 5 integration unavailable: {', '.join(missing)}")
    provider = PinnedOllamaAdapter(PINNED_MODEL, settings=PINNED_SETTINGS)
    provider.verify_pin()
    event_signer = DockerProtectedSigner(root, "event_anchor")
    try:
        event_signer.image_id()
    except SecurityError:
        DockerProtectedSigner.build_image(root)
    event_signer.bootstrap()
    receipt = run_real_capture(
        archive,
        provider,
        model_identity_digest=provider.identity_digest,
        released_binding=released_binding(root),
        event_signer=event_signer,
        capsule_signer=DockerProtectedSigner(root, "capsule"),
    )
    assert receipt.status == "PASS_AWAITING_NILHAN_REVIEW"
    assert receipt.source_seal_before == receipt.source_seal_after
    assert receipt.repository_code_executed is False
    assert receipt.external_network_used is False
    assert receipt.provider_direct_repository_access is False
    assert receipt.human_reviewer is None
    assert receipt.first_capsule_redeemed is False
    assert len(receipt.facts) == 6
