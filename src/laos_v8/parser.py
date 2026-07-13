"""Strict JSON boundary parser with duplicate-key and resource-limit rejection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import DuplicateKeyError, ParseError, ResourceLimitError


@dataclass(frozen=True, slots=True)
class ParseLimits:
    max_bytes: int = 1_048_576
    max_depth: int = 32
    max_string_length: int = 65_536
    max_collection_length: int = 10_000
    max_total_nodes: int = 100_000


def _reject_constant(value: str) -> None:
    raise ParseError(f"non-I-JSON numeric constant is prohibited: {value}", code="JSON_NON_FINITE_NUMBER")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key}", context={"key": key})
        result[key] = value
    return result


def _check_limits(value: Any, limits: ParseLimits, *, depth: int = 0, nodes: list[int] | None = None) -> None:
    counter = nodes if nodes is not None else [0]
    counter[0] += 1
    if counter[0] > limits.max_total_nodes:
        raise ResourceLimitError("JSON node limit exceeded", context={"max_total_nodes": limits.max_total_nodes})
    if depth > limits.max_depth:
        raise ResourceLimitError("JSON nesting depth exceeded", context={"max_depth": limits.max_depth})
    if isinstance(value, str):
        if len(value) > limits.max_string_length:
            raise ResourceLimitError(
                "JSON string length exceeded", context={"max_string_length": limits.max_string_length}
            )
        return
    if isinstance(value, dict):
        if len(value) > limits.max_collection_length:
            raise ResourceLimitError(
                "JSON object length exceeded", context={"max_collection_length": limits.max_collection_length}
            )
        for key, child in value.items():
            _check_limits(key, limits, depth=depth + 1, nodes=counter)
            _check_limits(child, limits, depth=depth + 1, nodes=counter)
    elif isinstance(value, list):
        if len(value) > limits.max_collection_length:
            raise ResourceLimitError(
                "JSON array length exceeded", context={"max_collection_length": limits.max_collection_length}
            )
        for child in value:
            _check_limits(child, limits, depth=depth + 1, nodes=counter)


def strict_loads(payload: bytes, limits: ParseLimits | None = None) -> Any:
    active_limits = limits or ParseLimits()
    if len(payload) > active_limits.max_bytes:
        raise ResourceLimitError("JSON byte limit exceeded", context={"max_bytes": active_limits.max_bytes})
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ParseError("payload is not strict UTF-8", code="JSON_INVALID_UTF8", location=(exc.start,)) from exc
    try:
        result = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (DuplicateKeyError, ParseError):
        raise
    except json.JSONDecodeError as exc:
        raise ParseError(exc.msg, location=(exc.lineno, exc.colno), context={"position": exc.pos}) from exc
    _check_limits(result, active_limits)
    return result
