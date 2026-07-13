"""Canonical content hashing and DSSE-compatible typed signature preimages."""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785
from pydantic import BaseModel

from .errors import ValidationError


def canonical_json(value: BaseModel | dict[str, Any] | list[Any]) -> bytes:
    plain = value.model_dump(mode="json", exclude_none=False) if isinstance(value, BaseModel) else value
    try:
        return rfc8785.dumps(plain)
    except rfc8785.CanonicalizationError as exc:
        raise ValidationError("record cannot be RFC 8785 canonicalized", code="CANONICALIZATION_FAILED") from exc


def content_digest(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def dsse_pae(payload_type: str, payload: bytes) -> bytes:
    """Return DSSE pre-authentication encoding for exact payload bytes."""
    type_bytes = payload_type.encode("utf-8", errors="strict")
    return b"DSSEv1 %d %b %d %b" % (len(type_bytes), type_bytes, len(payload), payload)


def signature_domain(key_purpose: str, payload_type: str, payload: bytes) -> bytes:
    if key_purpose not in {"capsule", "event_anchor", "release"}:
        raise ValidationError("unknown signing key purpose", code="UNKNOWN_KEY_PURPOSE")
    domain_type = f"application/vnd.nilhan.laos.signature.{key_purpose}.v1+{payload_type}"
    return dsse_pae(domain_type, payload)
