"""Single-host transactional SQLite state with same-transaction audit events."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .errors import AuthorizationDenied, EvidenceError, SecurityError, StateConflict, ValidationError
from .transitions import TRANSITION_TABLES

SCHEMA_VERSION = 2

DDL = """
CREATE TABLE IF NOT EXISTS actors (
    actor_id TEXT PRIMARY KEY,
    principal TEXT NOT NULL UNIQUE,
    roles_json TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    session_fingerprint TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revocation_epoch INTEGER NOT NULL,
    disabled INTEGER NOT NULL DEFAULT 0 CHECK (disabled IN (0, 1))
) STRICT;
CREATE TABLE IF NOT EXISTS capability_grants (
    grant_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL REFERENCES actors(actor_id),
    project_id TEXT NOT NULL,
    base_seal TEXT NOT NULL,
    audience TEXT NOT NULL,
    capabilities_json TEXT NOT NULL,
    policy_digest TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revocation_epoch INTEGER NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS aggregates (
    aggregate_id TEXT PRIMARY KEY,
    aggregate_kind TEXT NOT NULL,
    state TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 0),
    payload_json TEXT NOT NULL,
    payload_digest TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    aggregate_id TEXT,
    actor_id TEXT NOT NULL,
    event_code TEXT NOT NULL,
    outcome TEXT NOT NULL,
    error_code TEXT,
    occurred_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    detail_digest TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS capsule_redemptions (
    capsule_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    attempt_sequence INTEGER NOT NULL CHECK (attempt_sequence > 0),
    token_hash TEXT NOT NULL,
    redeemed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
CREATE TABLE IF NOT EXISTS action_claims (
    action_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    base_seal TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    claimed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
CREATE TABLE IF NOT EXISTS outbox (
    idempotency_key TEXT PRIMARY KEY,
    aggregate_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('pending', 'dispatched', 'confirmed', 'outcome_unknown', 'reconciled')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
CREATE TABLE IF NOT EXISTS evidence_objects (
    digest TEXT PRIMARY KEY,
    result_seal TEXT NOT NULL,
    criterion_id TEXT NOT NULL,
    classification TEXT NOT NULL,
    collector TEXT NOT NULL,
    bytes INTEGER NOT NULL CHECK (bytes >= 0),
    relative_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
CREATE TABLE IF NOT EXISTS evidence_tombstones (
    digest TEXT PRIMARY KEY,
    classification TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    purged_by TEXT NOT NULL,
    reason_digest TEXT NOT NULL,
    purged_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
CREATE TABLE IF NOT EXISTS control_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    emergency_stopped INTEGER NOT NULL CHECK (emergency_stopped IN (0, 1)),
    trust_epoch INTEGER NOT NULL CHECK (trust_epoch >= 0),
    reason TEXT NOT NULL
) STRICT;
INSERT OR IGNORE INTO control_state(singleton, emergency_stopped, trust_epoch, reason) VALUES (1, 0, 0, '');
"""


def _digest(value: object) -> str:
    wrapper: dict[str, Any] = {"value": value}
    return f"sha256:{hashlib.sha256(canonical_json(wrapper)).hexdigest()}"


def _validate_local_database(path: Path) -> Path:
    absolute = path.resolve(strict=False)
    value = str(absolute)
    if value.startswith(("\\\\", "//")):
        raise SecurityError("network filesystem SQLite is unsupported", code="SQLITE_NETWORK_PATH_DENIED")
    absolute.parent.mkdir(parents=True, exist_ok=True)
    return absolute


@dataclass(frozen=True, slots=True)
class AggregateState:
    aggregate_id: str
    aggregate_kind: str
    state: str
    version: int
    payload: dict[str, Any]
    payload_digest: str


class CanonicalState:
    """One-process SQLite reference monitor for the supported single-host profile."""

    def __init__(self, path: Path) -> None:
        self.path = _validate_local_database(path)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA synchronous = FULL")
        self.connection.execute("PRAGMA busy_timeout = 30000")
        observed = str(self.connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0]).upper()
        if observed != "DELETE":
            raise SecurityError("safe SQLite rollback journal could not be selected", code="SQLITE_JOURNAL_UNSAFE")
        version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        has_laos_tables = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'control_state'"
        ).fetchone()
        if version == 0 and has_laos_tables is not None:
            self.connection.close()
            raise ValidationError("unversioned existing state is unsupported", code="STATE_SCHEMA_UNVERSIONED")
        if version not in {0, SCHEMA_VERSION}:
            self.connection.close()
            raise ValidationError("state schema migration is unavailable", code="STATE_SCHEMA_VERSION_UNSUPPORTED")
        self.connection.executescript(DDL)
        action_columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(action_claims)").fetchall()}
        if "base_seal" not in action_columns:
            self.connection.close()
            raise SecurityError("state schema does not match its version", code="STATE_SCHEMA_SHAPE_INVALID")
        self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> CanonicalState:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield self.connection
            except Exception:
                self.connection.execute("ROLLBACK")
                raise
            else:
                self.connection.execute("COMMIT")

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        *,
        aggregate_id: str | None,
        actor_id: str,
        event_code: str,
        outcome: str,
        error_code: str | None = None,
        detail: object | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO audit_events"
            "(event_id, aggregate_id, actor_id, event_code, outcome, error_code, detail_digest) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                f"event:{uuid.uuid4().hex}",
                aggregate_id,
                actor_id,
                event_code,
                outcome,
                error_code,
                _digest(detail or {}),
            ),
        )

    def create_aggregate(
        self, aggregate_id: str, aggregate_kind: str, state: str, payload: dict[str, Any], actor_id: str
    ) -> AggregateState:
        serialized = canonical_json(payload).decode("utf-8")
        digest = _digest(payload)
        with self.transaction() as connection:
            try:
                connection.execute(
                    "INSERT INTO aggregates VALUES (?, ?, ?, 0, ?, ?)",
                    (aggregate_id, aggregate_kind, state, serialized, digest),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict("aggregate already exists", code="AGGREGATE_EXISTS") from exc
            self._event(
                connection,
                aggregate_id=aggregate_id,
                actor_id=actor_id,
                event_code="AGGREGATE_CREATED",
                outcome="allowed",
                detail={"state": state, "digest": digest},
            )
        return AggregateState(aggregate_id, aggregate_kind, state, 0, payload, digest)

    def record_event(
        self,
        *,
        aggregate_id: str | None,
        actor_id: str,
        event_code: str,
        outcome: str,
        error_code: str | None = None,
        detail: object | None = None,
    ) -> None:
        with self.transaction() as connection:
            self._event(
                connection,
                aggregate_id=aggregate_id,
                actor_id=actor_id,
                event_code=event_code,
                outcome=outcome,
                error_code=error_code,
                detail=detail,
            )

    def transition(
        self,
        aggregate_id: str,
        *,
        expected_version: int,
        target_state: str,
        payload: dict[str, Any],
        actor_id: str,
    ) -> AggregateState:
        serialized = canonical_json(payload).decode("utf-8")
        digest = _digest(payload)
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM aggregates WHERE aggregate_id = ?", (aggregate_id,)).fetchone()
            if row is None:
                raise StateConflict("aggregate does not exist", code="AGGREGATE_MISSING")
            table = TRANSITION_TABLES.get(str(row["aggregate_kind"]))
            if table is None:
                raise StateConflict("aggregate transition table is unknown", code="TRANSITION_TABLE_MISSING")
            table.require(str(row["state"]), target_state)
            updated = connection.execute(
                "UPDATE aggregates SET state = ?, version = version + 1, payload_json = ?, payload_digest = ? "
                "WHERE aggregate_id = ? AND version = ?",
                (target_state, serialized, digest, aggregate_id, expected_version),
            )
            if updated.rowcount != 1:
                raise StateConflict("aggregate compare-and-swap failed", code="STATE_VERSION_CONFLICT")
            self._event(
                connection,
                aggregate_id=aggregate_id,
                actor_id=actor_id,
                event_code="STATE_TRANSITION",
                outcome="allowed",
                detail={"from": row["state"], "to": target_state, "version": expected_version + 1},
            )
        return AggregateState(
            aggregate_id, str(row["aggregate_kind"]), target_state, expected_version + 1, payload, digest
        )

    def get_aggregate(self, aggregate_id: str) -> AggregateState:
        row = self.connection.execute("SELECT * FROM aggregates WHERE aggregate_id = ?", (aggregate_id,)).fetchone()
        if row is None:
            raise StateConflict("aggregate does not exist", code="AGGREGATE_MISSING")
        return AggregateState(
            str(row["aggregate_id"]),
            str(row["aggregate_kind"]),
            str(row["state"]),
            int(row["version"]),
            json.loads(str(row["payload_json"])),
            str(row["payload_digest"]),
        )

    def redeem_capsule(self, capsule_id: str, actor_id: str, attempt_sequence: int, token_hash: str) -> None:
        denied = False
        with self.transaction() as connection:
            try:
                connection.execute(
                    "INSERT INTO capsule_redemptions"
                    "(capsule_id, actor_id, attempt_sequence, token_hash) VALUES (?, ?, ?, ?)",
                    (capsule_id, actor_id, attempt_sequence, token_hash),
                )
            except sqlite3.IntegrityError:
                self._event(
                    connection,
                    aggregate_id=capsule_id,
                    actor_id=actor_id,
                    event_code="CAPSULE_REPLAY_DENIED",
                    outcome="denied",
                    error_code="CAPSULE_REPLAY_DENIED",
                )
                denied = True
            else:
                self._event(
                    connection,
                    aggregate_id=capsule_id,
                    actor_id=actor_id,
                    event_code="CAPSULE_REDEEMED",
                    outcome="allowed",
                    detail={"attempt_sequence": attempt_sequence},
                )
        if denied:
            raise AuthorizationDenied("capsule was already redeemed", code="CAPSULE_REPLAY_DENIED")

    def claim_action(self, action_id: str, actor_id: str, base_seal: str, lease_expires_at: str) -> None:
        with self.transaction() as connection:
            connection.execute(
                "DELETE FROM action_claims WHERE lease_expires_at <= strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
            )
            try:
                connection.execute(
                    "INSERT INTO action_claims(action_id, actor_id, base_seal, lease_expires_at) VALUES (?, ?, ?, ?)",
                    (action_id, actor_id, base_seal, lease_expires_at),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict("action is already claimed", code="ACTION_ALREADY_CLAIMED") from exc
            self._event(
                connection,
                aggregate_id=action_id,
                actor_id=actor_id,
                event_code="ACTION_CLAIMED",
                outcome="allowed",
                detail={"base_seal": base_seal, "lease_expires_at": lease_expires_at},
            )

    def enqueue(self, idempotency_key: str, aggregate_id: str, operation: str, payload_digest: str) -> None:
        with self.transaction() as connection:
            try:
                connection.execute(
                    "INSERT INTO outbox(idempotency_key, aggregate_id, operation, payload_digest, state) "
                    "VALUES (?, ?, ?, ?, 'pending')",
                    (idempotency_key, aggregate_id, operation, payload_digest),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict("duplicate outbox idempotency key", code="OUTBOX_DUPLICATE_KEY") from exc
            self._event(
                connection,
                aggregate_id=aggregate_id,
                actor_id="system:outbox",
                event_code="OUTBOX_PREPARED",
                outcome="allowed",
                detail={"idempotency_key": idempotency_key, "operation": operation},
            )

    def set_emergency_stop(self, actor_id: str, reason: str) -> int:
        if not reason.strip():
            raise ValidationError("emergency-stop reason is required", code="EMERGENCY_REASON_REQUIRED")
        with self.transaction() as connection:
            connection.execute(
                "UPDATE control_state SET emergency_stopped = 1, trust_epoch = trust_epoch + 1, reason = ? "
                "WHERE singleton = 1",
                (reason,),
            )
            epoch = int(connection.execute("SELECT trust_epoch FROM control_state WHERE singleton = 1").fetchone()[0])
            self._event(
                connection,
                aggregate_id=None,
                actor_id=actor_id,
                event_code="EMERGENCY_STOP",
                outcome="allowed",
                detail={"reason": reason, "trust_epoch": epoch},
            )
        return epoch

    def recover_trust(self, actor_id: str, reason: str, *, expected_epoch: int) -> int:
        """Clear an emergency stop only through an explicit epoch-bound recovery."""
        if not reason.strip():
            raise ValidationError("trust-recovery reason is required", code="TRUST_RECOVERY_REASON_REQUIRED")
        with self.transaction() as connection:
            updated = connection.execute(
                "UPDATE control_state SET emergency_stopped = 0, trust_epoch = trust_epoch + 1, reason = ? "
                "WHERE singleton = 1 AND emergency_stopped = 1 AND trust_epoch = ?",
                (reason, expected_epoch),
            )
            if updated.rowcount != 1:
                raise StateConflict(
                    "trust recovery requires the current stopped epoch",
                    code="TRUST_RECOVERY_EPOCH_CONFLICT",
                )
            epoch = int(connection.execute("SELECT trust_epoch FROM control_state WHERE singleton = 1").fetchone()[0])
            self._event(
                connection,
                aggregate_id=None,
                actor_id=actor_id,
                event_code="TRUST_RECOVERED",
                outcome="allowed",
                detail={"reason": reason, "previous_epoch": expected_epoch, "trust_epoch": epoch},
            )
        return epoch

    def control_status(self) -> tuple[bool, int, str]:
        row = self.connection.execute(
            "SELECT emergency_stopped, trust_epoch, reason FROM control_state WHERE singleton = 1"
        ).fetchone()
        return bool(row[0]), int(row[1]), str(row[2])

    def integrity_check(self) -> None:
        result = str(self.connection.execute("PRAGMA integrity_check").fetchone()[0])
        if result != "ok":
            raise EvidenceError("SQLite integrity check failed", code="SQLITE_INTEGRITY_FAILED")

    def backup(self, destination: Path) -> str:
        target = _validate_local_database(destination)
        with contextlib.closing(sqlite3.connect(target)) as output:
            self.connection.backup(output)
            if str(output.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
                raise EvidenceError("SQLite backup integrity check failed", code="SQLITE_BACKUP_INVALID")
        return f"sha256:{hashlib.sha256(target.read_bytes()).hexdigest()}"

    @staticmethod
    def restore(source: Path, destination: Path) -> str:
        """Restore a validated same-version backup to a new local path."""
        backup = _validate_local_database(source)
        target = _validate_local_database(destination)
        if not backup.is_file():
            raise ValidationError("SQLite backup does not exist", code="SQLITE_BACKUP_MISSING")
        if target.exists():
            raise StateConflict("restore destination already exists", code="SQLITE_RESTORE_TARGET_EXISTS")
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.restore")
        try:
            with contextlib.closing(sqlite3.connect(f"{backup.as_uri()}?mode=ro", uri=True)) as input_database:
                if str(input_database.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
                    raise EvidenceError("SQLite backup integrity check failed", code="SQLITE_BACKUP_INVALID")
                if int(input_database.execute("PRAGMA user_version").fetchone()[0]) != SCHEMA_VERSION:
                    raise ValidationError("SQLite backup schema version is unsupported", code="SQLITE_BACKUP_VERSION")
                with contextlib.closing(sqlite3.connect(temporary)) as output:
                    input_database.backup(output)
                    if str(output.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
                        raise EvidenceError("restored SQLite integrity check failed", code="SQLITE_RESTORE_INVALID")
            with temporary.open("r+b") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return f"sha256:{hashlib.sha256(target.read_bytes()).hexdigest()}"
