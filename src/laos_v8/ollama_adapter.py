"""Pinned, local-only Ollama adapter for the Stage 4 development experiment."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass

from .errors import ResourceLimitError, SecurityError

OLLAMA_ORIGIN = "http://127.0.0.1:11434"


@dataclass(frozen=True, slots=True)
class OllamaModelPin:
    tag: str
    blob_sha256: str


class PinnedOllamaAdapter:
    """Invoke one exact local model with no tools and bounded JSON output."""

    def __init__(
        self,
        pin: OllamaModelPin,
        *,
        executable: str | None = None,
        timeout_seconds: int = 120,
        output_bytes: int = 65_536,
    ) -> None:
        self.pin = pin
        self.executable = executable or shutil.which("ollama") or ""
        self.timeout_seconds = timeout_seconds
        self.output_bytes = output_bytes

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

    def __call__(self, prompt: str) -> str:
        self.verify_pin()
        request_body = json.dumps(
            {
                "model": self.pin.tag,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "keep_alive": "0",
                "options": {"temperature": 0, "seed": 80401, "num_predict": 1024},
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
