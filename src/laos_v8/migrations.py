"""Explicit record migration registry; unknown versions are never guessed."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .errors import UnsupportedRecordVersion

Migration = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class MigrationKey:
    record_type: str
    from_version: str
    to_version: str


class MigrationRegistry:
    def __init__(self) -> None:
        self._migrations: dict[MigrationKey, Migration] = {}

    def register(self, key: MigrationKey, migration: Migration) -> None:
        if key in self._migrations:
            raise ValueError(f"duplicate migration: {key}")
        self._migrations[key] = migration

    def migrate(self, record: dict[str, Any], to_version: str) -> dict[str, Any]:
        record_type = record.get("record_type")
        from_version = record.get("record_version")
        if not isinstance(record_type, str) or not isinstance(from_version, str):
            raise UnsupportedRecordVersion("record_type and record_version are required for migration")
        if from_version == to_version:
            return dict(record)
        key = MigrationKey(record_type, from_version, to_version)
        migration = self._migrations.get(key)
        if migration is None:
            raise UnsupportedRecordVersion(
                f"no explicit migration for {record_type} {from_version} -> {to_version}",
                context={"record_type": record_type, "from_version": from_version, "to_version": to_version},
            )
        return migration(dict(record))
