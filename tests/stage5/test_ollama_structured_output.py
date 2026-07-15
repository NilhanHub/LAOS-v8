from __future__ import annotations

import json
import urllib.request

import pytest

from laos_v8.ollama_adapter import OllamaModelPin, PinnedOllamaAdapter, ollama_grammar_schema


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.payload


def test_adapter_passes_exact_json_schema_to_loopback_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    schema: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"status": {"type": "string", "enum": ["accepted"]}},
        "required": ["status"],
    }
    observed: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: int) -> _Response:
        observed["url"] = request.full_url
        observed["timeout"] = timeout
        observed["body"] = json.loads((request.data or b"").decode("utf-8"))
        return _Response(b'{"response":"{\\"status\\":\\"accepted\\"}"}')

    adapter = PinnedOllamaAdapter(
        OllamaModelPin(tag="fixture:model", blob_sha256="a" * 64),
        executable="fixture-ollama",
        timeout_seconds=17,
    )
    monkeypatch.setattr(adapter, "verify_pin", lambda: None)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    output = adapter("broker prompt", output_schema=schema)

    assert output == '{"status":"accepted"}'
    assert observed["url"] == "http://127.0.0.1:11434/api/generate"
    assert observed["timeout"] == 17
    body = observed["body"]
    assert isinstance(body, dict)
    assert body["format"] == schema
    assert body["stream"] is False
    assert body["options"] == {"temperature": 0, "seed": 80401, "num_predict": 1024}


def test_adapter_retains_generic_json_mode_for_preexisting_callers(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_urlopen(request: urllib.request.Request, *, timeout: int) -> _Response:
        del timeout
        observed["body"] = json.loads((request.data or b"").decode("utf-8"))
        return _Response(b'{"response":"{}"}')

    adapter = PinnedOllamaAdapter(
        OllamaModelPin(tag="fixture:model", blob_sha256="a" * 64), executable="fixture-ollama"
    )
    monkeypatch.setattr(adapter, "verify_pin", lambda: None)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    assert adapter("legacy prompt") == "{}"
    body = observed["body"]
    assert isinstance(body, dict)
    assert body["format"] == "json"


def test_ollama_schema_projection_preserves_shape_and_does_not_mutate_validator_schema() -> None:
    validator: dict[str, object] = {
        "type": "object",
        "title": "Proposal",
        "additionalProperties": False,
        "properties": {
            "values": {"type": "array", "maxItems": 4, "items": {"type": "string", "maxLength": 8}}
        },
        "required": ["values"],
    }

    projected = ollama_grammar_schema(validator)

    assert projected == {
        "type": "object",
        "additionalProperties": False,
        "properties": {"values": {"type": "array", "items": {"type": "string"}}},
        "required": ["values"],
    }
    assert validator["title"] == "Proposal"
    assert "maxItems" in json.dumps(validator)
