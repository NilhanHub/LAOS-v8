"""Minimal, safe Stage 3 operator explanations and diagnostics."""

from __future__ import annotations

from typing import TypedDict

from .errors import SecurityError
from .sandbox import DOCKER_IMAGE, SANDBOX_PROFILE, DockerSandbox


class DenialExplanation(TypedDict):
    status: str
    code: str
    meaning: str
    operator_action: str
    retry_requires_changed_authority_or_state: bool


_DENIALS: dict[str, tuple[str, str]] = {
    "AUTHORIZATION_DENIED": (
        "The authenticated actor lacks current authority for the operation.",
        "Inspect identity, expiry, revocation epoch, and the exact capability binding; do not bypass the broker.",
    ),
    "POLICY_DENIED": (
        "The current versioned policy denied the requested capability or context.",
        "Inspect the structured rule IDs and request inputs; change policy only through authorized governance.",
    ),
    "PATH_REPARSE_DENIED": (
        "A symlink, junction, or reparse point could escape the authorized root.",
        "Use a regular in-root path in a disposable workspace and remove the link indirection.",
    ),
    "REPOSITORY_SEAL_MISMATCH": (
        "Repository bytes or metadata no longer match the authorized base or result seal.",
        "Stop, reconstruct from the accepted base, and issue fresh authority bound to the new seal if appropriate.",
    ),
    "CAPSULE_REPLAY_DENIED": (
        "The single-use Action Capsule was already redeemed.",
        "Do not retry it; reconcile the recorded attempt and issue a new capsule only after review.",
    ),
    "SANDBOX_UNAVAILABLE": (
        "The qualifying pinned sandbox provider is unavailable.",
        "Inspect the automatic Docker Desktop startup detail and rerun doctor; direct host execution is unsupported.",
    ),
    "EVIDENCE_TAMPERED": (
        "Canonical evidence bytes do not match their registered content digest.",
        "Stop acceptance, preserve forensic state, and follow the evidence-compromise procedure.",
    ),
    "TRUST_RECOVERY_EPOCH_CONFLICT": (
        "Recovery was not bound to the current stopped trust epoch.",
        "Read trust status, investigate the newer event, and obtain fresh explicit recovery authority.",
    ),
}


def explain_denial(code: str) -> DenialExplanation:
    normalized = code.strip().upper()
    meaning, action = _DENIALS.get(
        normalized,
        (
            "The code is not in the minimal Stage 3 public explanation catalogue.",
            "Preserve the structured error and audit event, then consult the current error registry or reviewer.",
        ),
    )
    return {
        "status": "KNOWN" if normalized in _DENIALS else "UNKNOWN",
        "code": normalized,
        "meaning": meaning,
        "operator_action": action,
        "retry_requires_changed_authority_or_state": True,
    }


def sandbox_diagnostic() -> dict[str, object]:
    sandbox = DockerSandbox()
    try:
        readiness = sandbox.ensure_available()
        available = readiness.available
        detail = readiness.detail
        started = readiness.started
        elapsed_ms = readiness.elapsed_ms
    except SecurityError as exc:
        available = False
        detail = str((exc.detail.context or {}).get("detail", exc.code))
        started = False
        elapsed_ms = 0
    return {
        "profile": SANDBOX_PROFILE,
        "image": DOCKER_IMAGE,
        "available": available,
        "detail": detail,
        "automatic_start_attempted": True,
        "automatically_started": started,
        "startup_elapsed_ms": elapsed_ms,
        "direct_host_execution_supported": False,
        "production_assurance_claimed": False,
    }
