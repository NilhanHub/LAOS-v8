"""Versioned Draft 2020-12 schemas and unified structural/semantic validation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from .errors import UnknownRecordType, UnsupportedRecordVersion, ValidationError
from .models import RECORD_MODELS, RecordBase, model_for_record_type
from .parser import ParseLimits, strict_loads

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_BASE = "https://schemas.nilhan.dev/laos/v8/"


def schema_for_model(model: type[RecordBase]) -> dict[str, Any]:
    schema = model.model_json_schema(mode="validation", ref_template="#/$defs/{model}")
    record_type = str(model.model_fields["record_type"].default)
    return {"$schema": SCHEMA_DIALECT, "$id": f"{SCHEMA_BASE}{record_type}/1.0.0", **schema}


def schema_registry() -> dict[str, dict[str, Any]]:
    return {str(model.model_fields["record_type"].default): schema_for_model(model) for model in RECORD_MODELS}


def _format_schema_error(error: JsonSchemaValidationError) -> ValidationError:
    location = tuple(error.absolute_path)
    return ValidationError(
        error.message,
        code="JSON_SCHEMA_FAILED",
        location=location,
        context={"validator": error.validator, "schema_path": list(error.absolute_schema_path)},
    )


def validate_record_bytes(payload: bytes, limits: ParseLimits | None = None) -> RecordBase:
    parsed = strict_loads(payload, limits)
    if not isinstance(parsed, dict):
        raise ValidationError("trusted record must be a JSON object", code="RECORD_NOT_OBJECT")
    record_type = parsed.get("record_type")
    if not isinstance(record_type, str):
        raise UnknownRecordType("record_type is required and must be a string")
    model = model_for_record_type(record_type)
    if model is None:
        raise UnknownRecordType(f"unknown record_type: {record_type}", context={"record_type": record_type})
    if parsed.get("record_version") != "1.0.0":
        raise UnsupportedRecordVersion(
            f"unsupported {record_type} record_version",
            context={"received": parsed.get("record_version"), "supported": ["1.0.0"]},
        )
    schema = schema_for_model(model)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(parsed), key=lambda item: list(item.absolute_path))
    if errors:
        raise _format_schema_error(errors[0])
    try:
        # Pydantic's strict JSON mode preserves strict scalar typing while accepting
        # the JSON array representation used for immutable tuple fields.
        return model.model_validate_json(payload, strict=True)
    except PydanticValidationError as exc:
        first = exc.errors(include_url=False)[0]
        raise ValidationError(
            first["msg"],
            code="SEMANTIC_VALIDATION_FAILED",
            location=tuple(first["loc"]),
            context={"type": first["type"]},
        ) from exc


def validate_references(records: Iterable[RecordBase]) -> None:
    materialized = tuple(records)
    ids = [record.record_id for record in materialized]
    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate logical record_id", code="DUPLICATE_LOGICAL_ID")
    known = set(ids)
    reference_suffixes = ("_id", "_ids")
    for record in materialized:
        for field, value in record.model_dump(mode="json").items():
            if field in {"record_id", "project_id"} or not field.endswith(reference_suffixes):
                continue
            values = value if isinstance(value, list) else [value]
            for reference in values:
                if isinstance(reference, str) and reference not in known:
                    raise ValidationError(
                        f"unresolved record reference: {reference}",
                        code="UNRESOLVED_REFERENCE",
                        location=(record.record_id, field),
                    )


def export_schemas(destination: Path) -> list[Path]:
    import json

    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for record_type, schema in sorted(schema_registry().items()):
        path = destination / f"{record_type}.schema.json"
        path.write_bytes((json.dumps(schema, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        outputs.append(path)
    return outputs
