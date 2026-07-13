"""Stable LAOS error hierarchy and machine-readable envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    code: str
    message: str
    location: tuple[str | int, ...] = ()
    context: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "location": list(self.location),
            "context": self.context or {},
        }


class LaosError(RuntimeError):
    """Base error with a stable public code and safe structured representation."""

    default_code: ClassVar[str] = "LAOS_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        location: tuple[str | int, ...] = (),
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.detail = ErrorDetail(code or self.default_code, message, location, context)

    @property
    def code(self) -> str:
        return self.detail.code

    def as_dict(self) -> dict[str, Any]:
        return {"error": self.detail.as_dict()}


class ValidationError(LaosError):
    default_code = "VALIDATION_FAILED"


class SecurityError(LaosError):
    default_code = "SECURITY_CONTROL_FAILED"


class AuthorizationDenied(SecurityError):
    default_code = "AUTHORIZATION_DENIED"


class PolicyDenied(AuthorizationDenied):
    default_code = "POLICY_DENIED"


class StateConflict(LaosError):
    default_code = "STATE_CONFLICT"


class RepositoryDrift(StateConflict):
    default_code = "REPOSITORY_DRIFT"


class EvidenceError(LaosError):
    default_code = "EVIDENCE_INVALID"


class ReviewError(LaosError):
    default_code = "REVIEW_INVALID"


class SideEffectError(LaosError):
    default_code = "SIDE_EFFECT_FAILED"


class ReleaseError(LaosError):
    default_code = "RELEASE_INVALID"


class ParseError(ValidationError):
    default_code = "JSON_PARSE_FAILED"


class DuplicateKeyError(ParseError):
    default_code = "JSON_DUPLICATE_KEY"


class ResourceLimitError(ValidationError):
    default_code = "INPUT_RESOURCE_LIMIT"


class UnknownRecordType(ValidationError):
    default_code = "UNKNOWN_RECORD_TYPE"


class UnsupportedRecordVersion(ValidationError):
    default_code = "UNSUPPORTED_RECORD_VERSION"


ERROR_CODE_REGISTRY: dict[str, type[LaosError]] = {
    cls.default_code: cls
    for cls in (
        LaosError,
        ValidationError,
        SecurityError,
        AuthorizationDenied,
        PolicyDenied,
        StateConflict,
        RepositoryDrift,
        EvidenceError,
        ReviewError,
        SideEffectError,
        ReleaseError,
        ParseError,
        DuplicateKeyError,
        ResourceLimitError,
        UnknownRecordType,
        UnsupportedRecordVersion,
    )
}
