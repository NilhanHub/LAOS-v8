from __future__ import annotations

import json
from pathlib import Path

import pytest

from laos_v8.canonical import canonical_json, content_digest, dsse_pae, signature_domain
from laos_v8.errors import StateConflict, ValidationError
from laos_v8.transitions import TRANSITION_TABLES, serialized_transition_tables

ROOT = Path(__file__).resolve().parents[2]


def test_rfc8785_and_dsse_golden_vector() -> None:
    golden = json.loads((ROOT / "schemas" / "golden" / "canonicalization-v1.json").read_text(encoding="utf-8"))
    canonical = canonical_json(golden["input"])
    assert canonical.hex() == golden["canonical_utf8_hex"]
    assert content_digest(golden["input"]) == golden["sha256"]
    assert dsse_pae(golden["dsse_payload_type"], canonical).hex() == golden["dsse_pae_hex"]


def test_signature_purposes_are_domain_separated() -> None:
    payload = b"{}"
    capsule = signature_domain("capsule", "application/json", payload)
    release = signature_domain("release", "application/json", payload)
    assert capsule != release
    with pytest.raises(ValidationError):
        signature_domain("shared", "application/json", payload)


def test_transition_tables_are_separate_and_fail_closed() -> None:
    assert set(TRANSITION_TABLES) == {
        "engagement",
        "task",
        "action_attempt",
        "criterion",
        "side_effect",
        "promotion_intent",
        "release",
    }
    TRANSITION_TABLES["task"].require("planned", "ready")
    with pytest.raises(StateConflict) as captured:
        TRANSITION_TABLES["task"].require("planned", "accepted")
    assert captured.value.code == "ILLEGAL_STATE_TRANSITION"
    assert serialized_transition_tables()["format_version"] == "1.0.0"
