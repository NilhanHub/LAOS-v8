from __future__ import annotations

import pytest

from laos_v8.errors import UnsupportedRecordVersion, ValidationError
from laos_v8.migrations import MigrationRegistry
from laos_v8.models import AcceptanceCriterion, Requirement
from laos_v8.schema_registry import validate_references

NOW = "2026-07-13T00:00:00Z"


def requirement() -> Requirement:
    return Requirement(
        record_id="requirement:req-1",
        project_id="project:demo",
        created_at=NOW,
        title="Requirement",
        description="Must fail closed.",
        priority="P0",
        scope="MUST_V8_0",
        criterion_ids=("criterion:criterion-1",),
    )


def criterion(requirement_id: str = "requirement:req-1") -> AcceptanceCriterion:
    return AcceptanceCriterion(
        record_id="criterion:criterion-1",
        project_id="project:demo",
        created_at=NOW,
        title="Criterion",
        requirement_id=requirement_id,
        statement="Malformed records are rejected.",
        evidence_level="L2",
        state="open",
    )


def test_semantic_reference_validation() -> None:
    validate_references((requirement(), criterion()))
    with pytest.raises(ValidationError) as captured:
        validate_references((requirement(), criterion("requirement:missing")))
    assert captured.value.code == "UNRESOLVED_REFERENCE"


def test_duplicate_logical_ids_are_rejected() -> None:
    with pytest.raises(ValidationError) as captured:
        validate_references((requirement(), requirement()))
    assert captured.value.code == "DUPLICATE_LOGICAL_ID"


def test_unknown_migration_is_never_guessed() -> None:
    registry = MigrationRegistry()
    record = {"record_type": "requirement", "record_version": "0.9.0"}
    with pytest.raises(UnsupportedRecordVersion):
        registry.migrate(record, "1.0.0")
