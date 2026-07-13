"""Cross-language value types for trusted LAOS records."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

RecordId = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*:[A-Za-z0-9][A-Za-z0-9._-]{0,126}$")
]
ProjectId = Annotated[str, StringConstraints(pattern=r"^project:[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")]
Sha256Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
UtcTimestamp = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"),
]
MediaType = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$")]
StableCode = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")]


def _safe_relative_path(value: str) -> str:
    if not value or "\\" in value or value.startswith(("/", "~")):
        raise ValueError("path must be a non-empty normalized POSIX relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path contains an empty, current, or parent segment")
    if ":" in parts[0]:
        raise ValueError("path contains a drive, scheme, or alternate stream prefix")
    return value


SafeRelativePath = Annotated[str, StringConstraints(max_length=1024), AfterValidator(_safe_relative_path)]
