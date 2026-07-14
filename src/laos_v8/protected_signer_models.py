"""Strict records exchanged with the local protected signer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import KeyPurpose

KeyStatus = Literal["active", "reserved", "revoked", "retired_historical"]


class SigningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    request_id: str = Field(pattern=r"^sign:[a-f0-9]{32}$")
    requested_at: str
    payload_b64: str = Field(min_length=1, max_length=2_700_000)
    payload_type: str = Field(pattern=r"^application/vnd\.nilhan\.laos\.[a-z0-9.-]+\+json$")
    key_purpose: KeyPurpose
    issuer: str = Field(min_length=1, max_length=256)
    audience: str = Field(min_length=1, max_length=256)
    issued_at: str
    expires_at: str | None = None


class SignerKeyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    key_id: str = Field(pattern=r"^key:[a-f0-9]{32}$")
    public_key_b64: str = Field(min_length=40, max_length=64)
    purpose: KeyPurpose
    generation: int = Field(ge=1)
    status: KeyStatus
    created_at: str
    retired_at: str | None = None
    revoked_at: str | None = None
    revocation_reason_digest: str | None = Field(default=None, pattern=r"^sha256:[a-f0-9]{64}$")

    @model_validator(mode="after")
    def lifecycle_fields_agree(self) -> SignerKeyRecord:
        if self.status == "revoked" and (self.revoked_at is None or self.revocation_reason_digest is None):
            raise ValueError("SIGNER_REVOCATION_METADATA_REQUIRED")
        if self.status == "retired_historical" and self.retired_at is None:
            raise ValueError("SIGNER_RETIREMENT_METADATA_REQUIRED")
        return self


class SignerPublicBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    record_version: Literal["1.0.0"] = "1.0.0"
    signer_instance_id: str = Field(pattern=r"^signer:[a-f0-9]{32}$")
    assurance: Literal["STAGE_5_LOCAL_PROTECTED_SIGNER_SINGLE_OPERATOR"]
    keys: tuple[SignerKeyRecord, ...] = Field(min_length=4, max_length=64)

    @model_validator(mode="after")
    def unique_keys_and_active_purposes(self) -> SignerPublicBundle:
        ids = [item.key_id for item in self.keys]
        if len(ids) != len(set(ids)):
            raise ValueError("SIGNER_DUPLICATE_KEY_ID")
        for purpose in ("capsule", "event_anchor", "pack_manifest"):
            active = [item for item in self.keys if item.purpose == purpose and item.status == "active"]
            if len(active) != 1:
                raise ValueError("SIGNER_ACTIVE_PURPOSE_KEY_REQUIRED")
        release = [item for item in self.keys if item.purpose == "release" and item.status == "reserved"]
        if len(release) != 1:
            raise ValueError("SIGNER_RELEASE_KEY_MUST_BE_RESERVED")
        return self
