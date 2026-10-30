"""Strict manifest and response models. Validation does not normalize signed values."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import MAX_FILE_BYTES

Identifier = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]
Timestamp = Annotated[str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")]
Status = Literal["ACCEPTED", "QUARANTINED"]
Reason = Literal["VALID", "INVALID_METADATA", "UNKNOWN_OR_REVOKED_KEY", "SENDER_KEY_MISMATCH",
                 "INVALID_SIGNATURE", "HASH_MISMATCH", "SIZE_MISMATCH"]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


def valid_timestamp(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return value


class Metadata(StrictModel):
    sample_id: Identifier
    collected_at: Timestamp
    data_type: Literal["csv", "json", "txt"]
    synthetic: Literal[True]

    @field_validator("synthetic", mode="before")
    @classmethod
    def only_true(cls, value):
        if value is not True:
            raise ValueError("Only explicitly synthetic data is permitted.")
        return value

    @field_validator("collected_at")
    @classmethod
    def calendar_date(cls, value):
        return valid_timestamp(value)


class Manifest(StrictModel):
    schema_version: Literal[1]
    laboratory_id: Identifier
    file_name: Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
    file_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    file_size_bytes: Annotated[int, Field(ge=1, le=MAX_FILE_BYTES)]
    signed_at: Timestamp
    key_id: Identifier
    metadata: Metadata

    @field_validator("schema_version", mode="before")
    @classmethod
    def exact_version(cls, value):
        if type(value) is not int or value != 1:
            raise ValueError("Only integer schema version 1 is supported.")
        return value

    @field_validator("signed_at")
    @classmethod
    def calendar_date(cls, value):
        return valid_timestamp(value)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if ".." in self.file_name or not self.file_name.endswith("." + self.metadata.data_type):
            raise ValueError("File name must match the declared data type and contain no paths.")
        if self.metadata.collected_at > self.signed_at:
            raise ValueError("Collection time must not follow signing time.")
        return self


class Check(StrictModel):
    name: Literal["metadata", "trusted_key", "sender", "signature", "file_name", "size", "sha256"]
    status: Literal["PASS", "FAIL", "SKIPPED"]


class VerificationResult(StrictModel):
    verification_id: str
    status: Status
    reason_code: Reason
    details: str
    received_at: str
    claimed_laboratory_id: str | None
    claimed_key_id: str | None
    verified_laboratory_id: str | None
    verified_key_id: str | None
    metadata_authenticated: bool
    file_name: str | None
    file_size_bytes: int
    computed_sha256: str
    manifest: Manifest | None
    checks: list[Check]


class Laboratory(StrictModel):
    laboratory_id: str
    name: str
    sector: str
    role: str


class AuditEvent(StrictModel):
    event_id: int
    verification_id: str | None
    created_at: str
    actor_laboratory_id: str
    event_type: str
    details: str
