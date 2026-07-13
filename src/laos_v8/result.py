"""Stable machine-readable operation results and structured events."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from .errors import LaosError

T = TypeVar("T")


class ResultEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    version: Literal["1.0.0"] = "1.0.0"
    status: Literal["ok", "denied", "error"]
    value: T | None = None
    error: dict[str, Any] | None = None
    events: tuple[dict[str, Any], ...] = ()

    @classmethod
    def denied(cls, error: LaosError, events: tuple[dict[str, Any], ...]) -> ResultEnvelope[Any]:
        return cls(status="denied", error=error.as_dict()["error"], events=events)
