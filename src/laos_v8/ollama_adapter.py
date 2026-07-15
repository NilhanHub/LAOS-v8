"""Pinned, local-only Ollama adapter for the Stage 4 development experiment."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from typing import Literal, Protocol

from .canonical import canonical_json
from .errors import ResourceLimitError, SecurityError

OLLAMA_ORIGIN = "http://127.0.0.1:11434"
JsonSchema = dict[str, object]
_OLLAMA_GRAMMAR_UNSUPPORTED = frozenset({"title", "maxLength", "maxItems"})


def ollama_grammar_schema(schema: JsonSchema) -> JsonSchema:
    """Project validation-only limits out of Ollama's grammar schema.

    Ollama 0.31 rejects these keywords while parsing its generation grammar. The
    original Pydantic model remains the authoritative post-generation validator.
    """

    def project(value: object) -> object:
        if isinstance(value, dict):
            return {
                str(key): project(item)
                for key, item in value.items()
                if str(key) not in _OLLAMA_GRAMMAR_UNSUPPORTED
            }
        if isinstance(value, list):
            return [project(item) for item in value]
        return value

    projected = project(schema)
    if not isinstance(projected, dict):
        raise TypeError("projected Ollama schema is not an object")
    return projected


class StructuredOutputProvider(Protocol):
    """A local provider that is constrained by an exact JSON Schema."""

    def __call__(self, prompt: str, *, output_schema: JsonSchema) -> str: ...


@dataclass(frozen=True, slots=True)
class OllamaModelPin:
    tag: str
    blob_sha256: str


@dataclass(frozen=True, slots=True)
class OllamaGenerationSettings:
    """The complete request policy bound into calibration and capture evidence."""

    temperature: int = 0
    seed: int = 80401
    num_predict: int = 1024
    keep_alive: Literal["0"] = "0"
    model_tools: Literal[False] = False
    external_network: Literal["deny"] = "deny"
    fresh_session: Literal[True] = True

    def as_dict(self) -> dict[str, object]:
        return {
            "temperature": self.temperature,
            "seed": self.seed,
            "num_predict": self.num_predict,
            "keep_alive": self.keep_alive,
            "model_tools": self.model_tools,
            "external_network": self.external_network,
            "fresh_session": self.fresh_session,
        }

    @property
    def digest(self) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(self.as_dict())).hexdigest()}"


class PinnedOllamaAdapter:
    """Invoke one exact local model with no tools and bounded JSON output."""

    def __init__(
        self,
        pin: OllamaModelPin,
        *,
        executable: str | None = None,
        timeout_seconds: int = 120,
        output_bytes: int = 65_536,
        settings: OllamaGenerationSettings | None = None,
    ) -> None:
        self.pin = pin
        self.executable = executable or shutil.which("ollama") or ""
        self.timeout_seconds = timeout_seconds
        self.output_bytes = output_bytes
        self.settings = settings or OllamaGenerationSettings()

    def verify_pin(self) -> None:
        if not self.executable:
            raise SecurityError("Ollama is unavailable", code="OLLAMA_UNAVAILABLE")
        completed = subprocess.run(  # noqa: S603 - resolved executable and fixed arguments
            [self.executable, "show", self.pin.tag, "--modelfile"],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        if completed.returncode:
            raise SecurityError("pinned Ollama model is unavailable", code="OLLAMA_MODEL_UNAVAILABLE")
        marker = f"sha256-{self.pin.blob_sha256}"
        if marker not in completed.stdout:
            raise SecurityError("Ollama model blob does not match the pin", code="OLLAMA_MODEL_PIN_MISMATCH")

    def __call__(self, prompt: str, *, output_schema: JsonSchema | None = None) -> str:
        self.verify_pin()
        response_format: str | JsonSchema = output_schema if output_schema is not None else "json"
        request_body = json.dumps(
            {
                "model": self.pin.tag,
                "prompt": prompt,
                "stream": False,
                "format": response_format,
                "keep_alive": self.settings.keep_alive,
                "options": {
                    "temperature": self.settings.temperature,
                    "seed": self.settings.seed,
                    "num_predict": self.settings.num_predict,
                },
            }
        ).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310 - origin is a fixed loopback constant
            f"{OLLAMA_ORIGIN}/api/generate",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = response.read(self.output_bytes + 1)
        except TimeoutError as exc:
            raise ResourceLimitError("local model call timed out", code="MODEL_TIMEOUT") from exc
        except OSError as exc:
            raise SecurityError("local Ollama endpoint is unavailable", code="OLLAMA_ENDPOINT_UNAVAILABLE") from exc
        if len(payload) > self.output_bytes:
            raise ResourceLimitError("local model output limit exceeded", code="MODEL_OUTPUT_LIMIT")
        try:
            decoded = json.loads(payload)
            output = decoded["response"]
        except (KeyError, TypeError, ValueError) as exc:
            raise SecurityError("local model response is invalid", code="MODEL_RESPONSE_INVALID") from exc
        if not isinstance(output, str):
            raise SecurityError("local model response is not text", code="MODEL_RESPONSE_INVALID")
        return output

    @property
    def identity_digest(self) -> str:
        material = f"ollama:{self.pin.tag}:sha256:{self.pin.blob_sha256}".encode()
        return f"sha256:{hashlib.sha256(material).hexdigest()}"
