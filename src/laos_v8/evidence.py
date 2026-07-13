"""Broker-owned content-addressed evidence capture and verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import AuthorizationDenied, EvidenceError, ValidationError
from .safe_paths import SafeRoot
from .state import CanonicalState


@dataclass(frozen=True, slots=True)
class CapturedEvidence:
    digest: str
    relative_path: str
    bytes: int
    result_seal: str
    criterion_id: str
    classification: str
    collector: str


class EvidenceBroker:
    def __init__(self, root: Path, state: CanonicalState, *, max_object_bytes: int = 1_073_741_824) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "objects").mkdir(exist_ok=True)
        self.root = SafeRoot(root)
        self.state = state
        self.max_object_bytes = max_object_bytes

    def capture(
        self,
        payload: bytes,
        *,
        result_seal: str,
        criterion_id: str,
        classification: str,
        collector: str,
        actor_id: str,
    ) -> CapturedEvidence:
        digest = hashlib.sha256(payload).hexdigest()
        qualified = f"sha256:{digest}"
        if (
            self.state.connection.execute("SELECT 1 FROM evidence_tombstones WHERE digest = ?", (qualified,)).fetchone()
            is not None
        ):
            raise EvidenceError("purged evidence digest cannot be rebound", code="EVIDENCE_TOMBSTONED")
        relative = f"objects/{digest[:2]}/{digest}"
        parent = self.root.root / "objects" / digest[:2]
        parent.mkdir(exist_ok=True)
        target = self.root.for_write(relative)
        created = False
        if target.exists():
            existing = self.root.read_bytes(relative, max_bytes=self.max_object_bytes)
            if existing != payload:
                raise EvidenceError("content-address collision", code="EVIDENCE_DIGEST_COLLISION")
        else:
            self.root.write_bytes_atomic(relative, payload, max_bytes=self.max_object_bytes)
            created = True
        with self.state.transaction() as connection:
            if (
                connection.execute("SELECT 1 FROM evidence_tombstones WHERE digest = ?", (qualified,)).fetchone()
                is not None
            ):
                if created:
                    target.unlink(missing_ok=True)
                raise EvidenceError("purged evidence digest cannot be rebound", code="EVIDENCE_TOMBSTONED")
            connection.execute(
                "INSERT OR IGNORE INTO evidence_objects(digest, result_seal, criterion_id, classification, "
                "collector, bytes, relative_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (qualified, result_seal, criterion_id, classification, collector, len(payload), relative),
            )
            binding = connection.execute(
                "SELECT result_seal, criterion_id, classification, collector, bytes, relative_path "
                "FROM evidence_objects WHERE digest = ?",
                (qualified,),
            ).fetchone()
            expected = (result_seal, criterion_id, classification, collector, len(payload), relative)
            observed = tuple(binding) if binding is not None else ()
            if observed != expected:
                raise EvidenceError("evidence digest already has a different binding", code="EVIDENCE_REBIND_DENIED")
            self.state._event(
                connection,
                aggregate_id=criterion_id,
                actor_id=actor_id,
                event_code="EVIDENCE_CAPTURED",
                outcome="allowed",
                detail={"digest": qualified, "result_seal": result_seal, "classification": classification},
            )
        return CapturedEvidence(qualified, relative, len(payload), result_seal, criterion_id, classification, collector)

    def verify(self, evidence: CapturedEvidence) -> bytes:
        payload = self.root.read_bytes(evidence.relative_path, max_bytes=self.max_object_bytes)
        observed = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if observed != evidence.digest:
            raise EvidenceError("evidence object digest mismatch", code="EVIDENCE_TAMPERED")
        row = self.state.connection.execute(
            "SELECT result_seal, criterion_id FROM evidence_objects WHERE digest = ?", (evidence.digest,)
        ).fetchone()
        if (
            row is None
            or str(row["result_seal"]) != evidence.result_seal
            or str(row["criterion_id"]) != evidence.criterion_id
        ):
            raise EvidenceError("evidence binding is missing or changed", code="EVIDENCE_BINDING_INVALID")
        return payload

    def export_object(
        self,
        digest: str,
        destination: Path,
        *,
        expected_classification: str,
        actor_id: str,
    ) -> dict[str, Any]:
        """Export one verified object into a new operator-controlled directory."""
        row = self.state.connection.execute("SELECT * FROM evidence_objects WHERE digest = ?", (digest,)).fetchone()
        if row is None:
            raise EvidenceError("evidence object is not registered", code="EVIDENCE_MISSING")
        classification = str(row["classification"])
        if classification != expected_classification:
            raise AuthorizationDenied(
                "evidence classification confirmation does not match",
                code="EVIDENCE_CLASSIFICATION_DENIED",
            )
        captured = CapturedEvidence(
            digest=digest,
            relative_path=str(row["relative_path"]),
            bytes=int(row["bytes"]),
            result_seal=str(row["result_seal"]),
            criterion_id=str(row["criterion_id"]),
            classification=classification,
            collector=str(row["collector"]),
        )
        payload = self.verify(captured)
        try:
            destination.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise ValidationError("evidence export destination must be new", code="EVIDENCE_EXPORT_EXISTS") from exc
        export_root = SafeRoot(destination)
        manifest = {
            "record_version": "1.0.0",
            "digest": captured.digest,
            "bytes": captured.bytes,
            "result_seal": captured.result_seal,
            "criterion_id": captured.criterion_id,
            "classification": captured.classification,
            "collector": captured.collector,
            "object": "object.bin",
            "assurance": "STAGE_3_OPERATOR_EXPORT_NOT_PRODUCTION_ATTESTATION",
        }
        export_root.write_bytes_atomic("object.bin", payload, max_bytes=self.max_object_bytes)
        export_root.write_bytes_atomic(
            "manifest.json",
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            max_bytes=1_048_576,
        )
        self.state.record_event(
            aggregate_id=captured.criterion_id,
            actor_id=actor_id,
            event_code="EVIDENCE_EXPORTED",
            outcome="allowed",
            detail={"digest": captured.digest, "classification": captured.classification},
        )
        return manifest

    def purge(
        self,
        digest: str,
        *,
        expected_classification: str,
        actor_id: str,
        reason: str,
    ) -> None:
        """Tombstone and delete one verified object through a recoverable outbox step."""
        if not reason.strip():
            raise ValidationError("evidence purge reason is required", code="EVIDENCE_PURGE_REASON_REQUIRED")
        row = self.state.connection.execute("SELECT * FROM evidence_objects WHERE digest = ?", (digest,)).fetchone()
        if row is None:
            raise EvidenceError("evidence object is not registered", code="EVIDENCE_MISSING")
        if str(row["classification"]) != expected_classification:
            raise AuthorizationDenied(
                "evidence classification confirmation does not match",
                code="EVIDENCE_CLASSIFICATION_DENIED",
            )
        captured = CapturedEvidence(
            digest=digest,
            relative_path=str(row["relative_path"]),
            bytes=int(row["bytes"]),
            result_seal=str(row["result_seal"]),
            criterion_id=str(row["criterion_id"]),
            classification=str(row["classification"]),
            collector=str(row["collector"]),
        )
        self.verify(captured)
        outbox_key = f"evidence-purge:{digest}"
        with self.state.transaction() as connection:
            connection.execute(
                "INSERT INTO outbox(idempotency_key, aggregate_id, operation, payload_digest, state) "
                "VALUES (?, ?, 'evidence_purge', ?, 'pending')",
                (outbox_key, captured.criterion_id, digest),
            )
            connection.execute(
                "INSERT INTO evidence_tombstones"
                "(digest, classification, relative_path, purged_by, reason_digest) VALUES (?, ?, ?, ?, ?)",
                (
                    digest,
                    captured.classification,
                    captured.relative_path,
                    actor_id,
                    f"sha256:{hashlib.sha256(reason.encode('utf-8')).hexdigest()}",
                ),
            )
            connection.execute("DELETE FROM evidence_objects WHERE digest = ?", (digest,))
            self.state._event(
                connection,
                aggregate_id=captured.criterion_id,
                actor_id=actor_id,
                event_code="EVIDENCE_PURGE_PREPARED",
                outcome="allowed",
                detail={"digest": digest, "classification": captured.classification},
            )
        self.reconcile_purges(actor_id=actor_id)

    def reconcile_purges(self, *, actor_id: str) -> int:
        """Complete pending tombstoned evidence deletions after a crash or retry."""
        rows = self.state.connection.execute(
            "SELECT t.digest, t.relative_path, o.idempotency_key FROM evidence_tombstones t "
            "JOIN outbox o ON o.payload_digest = t.digest AND o.operation = 'evidence_purge' "
            "WHERE o.state IN ('pending', 'outcome_unknown')"
        ).fetchall()
        for row in rows:
            target = self.root.for_write(str(row["relative_path"]))
            target.unlink(missing_ok=True)
            with self.state.transaction() as connection:
                connection.execute(
                    "UPDATE outbox SET state = 'reconciled' WHERE idempotency_key = ?",
                    (str(row["idempotency_key"]),),
                )
                self.state._event(
                    connection,
                    aggregate_id=None,
                    actor_id=actor_id,
                    event_code="EVIDENCE_PURGED",
                    outcome="allowed",
                    detail={"digest": str(row["digest"])},
                )
        return len(rows)
