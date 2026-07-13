from __future__ import annotations

import json
from typing import Any

import pytest

from laos_v8.errors import UnknownRecordType, UnsupportedRecordVersion, ValidationError
from laos_v8.models import RECORD_MODELS, Requirement
from laos_v8.schema_registry import SCHEMA_DIALECT, schema_registry, validate_record_bytes


def test_every_canonical_record_has_a_draft_2020_12_schema() -> None:
    registry = schema_registry()
    assert len(RECORD_MODELS) == 40
    assert len(registry) == 40
    assert all(schema["$schema"] == SCHEMA_DIALECT for schema in registry.values())
    assert all(schema["additionalProperties"] is False for schema in registry.values())


def test_valid_record_uses_the_unified_registry(requirement_bytes: Any) -> None:
    record = validate_record_bytes(requirement_bytes())
    assert isinstance(record, Requirement)
    assert record.priority == "P0"


@pytest.mark.parametrize(
    ("overrides", "location"),
    [
        ({"priority": "urgent"}, ("priority",)),
        ({"extra": "prohibited"}, ()),
        ({"record_id": "bad id"}, ("record_id",)),
        ({"criterion_ids": []}, ("criterion_ids",)),
    ],
)
def test_malformed_records_fail_closed(
    requirement_bytes: Any, overrides: dict[str, Any], location: tuple[str, ...]
) -> None:
    with pytest.raises(ValidationError) as captured:
        validate_record_bytes(requirement_bytes(**overrides))
    assert captured.value.code == "JSON_SCHEMA_FAILED"
    assert tuple(captured.value.detail.location) == location


def test_unknown_record_type_fails_closed(requirement_bytes: Any) -> None:
    with pytest.raises(UnknownRecordType):
        validate_record_bytes(requirement_bytes(record_type="invented"))


def test_unknown_record_version_is_not_guessed(requirement_bytes: Any) -> None:
    with pytest.raises(UnsupportedRecordVersion):
        validate_record_bytes(requirement_bytes(record_version="2.0.0"))


def test_strict_types_do_not_coerce(requirement_bytes: Any) -> None:
    raw = json.loads(requirement_bytes())
    raw["criterion_ids"] = "criterion:criterion-1"
    with pytest.raises(ValidationError):
        validate_record_bytes(json.dumps(raw).encode())
