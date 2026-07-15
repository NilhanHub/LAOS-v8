"""Minimal Stage 2/3 operator CLI with fail-closed recovery paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import AuthorizationDenied, LaosError, ValidationError
from .evidence import EvidenceBroker
from .migration_discovery import discover_v7
from .operator_paths import explain_denial, sandbox_diagnostic
from .platform_profile import doctor
from .protected_signer import DockerProtectedSigner
from .schema_registry import export_schemas
from .stage6_cli import configure as configure_stage6_commands
from .stage6_cli import handle as handle_stage6_command
from .state import CanonicalState


def _root(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd().resolve()


def _existing_file(value: str, *, code: str) -> Path:
    path = Path(value).resolve(strict=False)
    if not path.is_file():
        raise ValidationError("required operator input file is missing", code=code)
    return path


def _existing_directory(value: str, *, code: str) -> Path:
    path = Path(value).resolve(strict=False)
    if not path.is_dir():
        raise ValidationError("required operator input directory is missing", code=code)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="laos")
    parser.add_argument("--root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("status")
    schemas = commands.add_parser("export-schemas")
    schemas.add_argument("destination")
    migration = commands.add_parser("migration-discover")
    migration.add_argument("v7_archive")
    denial = commands.add_parser("explain-denial")
    denial.add_argument("code")
    backup = commands.add_parser("backup")
    backup.add_argument("state")
    backup.add_argument("destination")
    restore = commands.add_parser("restore")
    restore.add_argument("backup")
    restore.add_argument("destination")
    trust_status = commands.add_parser("trust-status")
    trust_status.add_argument("state")
    trust_recover = commands.add_parser("trust-recover")
    trust_recover.add_argument("state")
    trust_recover.add_argument("--actor", required=True)
    trust_recover.add_argument("--reason", required=True)
    trust_recover.add_argument("--expected-epoch", required=True, type=int)
    evidence_export = commands.add_parser("evidence-export")
    evidence_export.add_argument("state")
    evidence_export.add_argument("store")
    evidence_export.add_argument("digest")
    evidence_export.add_argument("destination")
    evidence_export.add_argument("--classification", required=True)
    evidence_export.add_argument("--actor", required=True)
    evidence_purge = commands.add_parser("evidence-purge")
    evidence_purge.add_argument("state")
    evidence_purge.add_argument("store")
    evidence_purge.add_argument("digest")
    evidence_purge.add_argument("--classification", required=True)
    evidence_purge.add_argument("--actor", required=True)
    evidence_purge.add_argument("--reason", required=True)
    evidence_purge.add_argument("--confirm-digest", required=True)
    evidence_reconcile = commands.add_parser("evidence-reconcile-purges")
    evidence_reconcile.add_argument("state")
    evidence_reconcile.add_argument("store")
    evidence_reconcile.add_argument("--actor", required=True)
    commands.add_parser("signer-build")
    signer_bootstrap = commands.add_parser("signer-bootstrap")
    signer_bootstrap.add_argument("--purpose", default="capsule", choices=("capsule", "event_anchor", "pack_manifest"))
    signer_doctor = commands.add_parser("signer-doctor")
    signer_doctor.add_argument("--purpose", default="capsule", choices=("capsule", "event_anchor", "pack_manifest"))
    signer_rotate = commands.add_parser("signer-rotate")
    signer_rotate.add_argument("--purpose", required=True, choices=("capsule", "event_anchor", "pack_manifest"))
    signer_revoke = commands.add_parser("signer-revoke")
    signer_revoke.add_argument("--purpose", required=True, choices=("capsule", "event_anchor", "pack_manifest"))
    signer_revoke.add_argument("--key-id", required=True)
    signer_revoke.add_argument("--reason", required=True)
    configure_stage6_commands(commands)
    args = parser.parse_args(argv)
    root = _root(args.root)
    try:
        stage6 = handle_stage6_command(args, root)
        if stage6 is not None:
            return stage6
        if args.command == "doctor":
            report = doctor(root).as_dict()
            sandbox = sandbox_diagnostic()
            report["stage3_sandbox"] = sandbox
            report["security_spine_ready"] = bool(sandbox["available"])
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "status":
            status_path = root / "IMPLEMENTATION_STATUS.json"
            print(status_path.read_text(encoding="utf-8"))
            return 0
        if args.command == "export-schemas":
            outputs = export_schemas(Path(args.destination).resolve())
            print(json.dumps({"status": "PASS", "schema_count": len(outputs)}, indent=2))
            return 0
        if args.command == "migration-discover":
            print(json.dumps(discover_v7(Path(args.v7_archive).resolve()), indent=2))
            return 0
        if args.command == "explain-denial":
            print(json.dumps(explain_denial(args.code), indent=2))
            return 0
        if args.command == "signer-build":
            image_id = DockerProtectedSigner.build_image(root)
            print(json.dumps({"status": "PASS", "image_id": image_id}, indent=2))
            return 0
        if args.command in {"signer-bootstrap", "signer-doctor", "signer-rotate", "signer-revoke"}:
            signer = DockerProtectedSigner(root, args.purpose)
            if args.command == "signer-bootstrap":
                print(signer.bootstrap().model_dump_json(indent=2))
            elif args.command == "signer-doctor":
                print(json.dumps(signer.doctor(), indent=2))
            elif args.command == "signer-rotate":
                print(signer.rotate().model_dump_json(indent=2))
            else:
                print(signer.revoke(args.key_id, args.reason).model_dump_json(indent=2))
            return 0
        if args.command == "backup":
            state_path = _existing_file(args.state, code="STATE_DATABASE_MISSING")
            with CanonicalState(state_path) as state:
                digest = state.backup(Path(args.destination))
            print(json.dumps({"status": "PASS", "backup_digest": digest}, indent=2))
            return 0
        if args.command == "restore":
            source = _existing_file(args.backup, code="SQLITE_BACKUP_MISSING")
            digest = CanonicalState.restore(source, Path(args.destination))
            print(json.dumps({"status": "PASS", "restored_digest": digest}, indent=2))
            return 0
        if args.command == "trust-status":
            state_path = _existing_file(args.state, code="STATE_DATABASE_MISSING")
            with CanonicalState(state_path) as state:
                stopped, epoch, reason = state.control_status()
            print(json.dumps({"emergency_stopped": stopped, "trust_epoch": epoch, "reason": reason}, indent=2))
            return 0
        if args.command == "trust-recover":
            state_path = _existing_file(args.state, code="STATE_DATABASE_MISSING")
            with CanonicalState(state_path) as state:
                epoch = state.recover_trust(args.actor, args.reason, expected_epoch=args.expected_epoch)
            print(json.dumps({"status": "PASS", "emergency_stopped": False, "trust_epoch": epoch}, indent=2))
            return 0
        if args.command in {"evidence-export", "evidence-purge", "evidence-reconcile-purges"}:
            state_path = _existing_file(args.state, code="STATE_DATABASE_MISSING")
            store = _existing_directory(args.store, code="EVIDENCE_STORE_MISSING")
            with CanonicalState(state_path) as state:
                broker = EvidenceBroker(store, state)
                if args.command == "evidence-export":
                    manifest = broker.export_object(
                        args.digest,
                        Path(args.destination),
                        expected_classification=args.classification,
                        actor_id=args.actor,
                    )
                    print(json.dumps({"status": "PASS", "manifest": manifest}, indent=2))
                elif args.command == "evidence-purge":
                    if args.confirm_digest != args.digest:
                        raise AuthorizationDenied(
                            "evidence purge digest confirmation does not match",
                            code="EVIDENCE_PURGE_CONFIRMATION_DENIED",
                        )
                    broker.purge(
                        args.digest,
                        expected_classification=args.classification,
                        actor_id=args.actor,
                        reason=args.reason,
                    )
                    print(json.dumps({"status": "PASS", "purged_digest": args.digest}, indent=2))
                else:
                    count = broker.reconcile_purges(actor_id=args.actor)
                    print(json.dumps({"status": "PASS", "reconciled": count}, indent=2))
            return 0
    except LaosError as exc:
        print(json.dumps(exc.as_dict(), indent=2), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
