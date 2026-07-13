from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture
def common() -> dict[str, Any]:
    return {
        "record_version": "1.0.0",
        "record_id": "requirement:req-1",
        "project_id": "project:demo",
        "created_at": "2026-07-13T00:00:00Z",
    }


@pytest.fixture
def requirement_bytes(common: dict[str, Any]) -> Callable[..., bytes]:
    def build(**overrides: Any) -> bytes:
        record = {
            **common,
            "record_type": "requirement",
            "title": "Strict parser",
            "description": "Reject malformed trusted records.",
            "priority": "P0",
            "scope": "MUST_V8_0",
            "criterion_ids": ["criterion:criterion-1"],
            **overrides,
        }
        return json.dumps(record, separators=(",", ":")).encode("utf-8")

    return build
