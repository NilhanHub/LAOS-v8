"""Minimal Stage 2 operator CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .migration_discovery import discover_v7
from .platform_profile import doctor
from .schema_registry import export_schemas


def _root(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd().resolve()


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
    args = parser.parse_args(argv)
    root = _root(args.root)
    if args.command == "doctor":
        print(json.dumps(doctor(root).as_dict(), indent=2))
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
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
